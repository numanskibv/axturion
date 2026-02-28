from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.api.deps import get_request_context, require_scope
from app.core.request_context import RequestContext
from app.domain.audit.models import AuditLog
from app.domain.ux.models import PendingUXRollback
from app.services.policy_service import get_policy
from app.services.ux_service import get_ux_config, upsert_ux_config
from app.core.scopes import UX_READ, UX_WRITE
from app.api.schemas.ux import (
    UXConfigResponse,
    UXConfigRollbackRequest,
    UXRollbackPendingResponse,
    UXConfigDiff,
    UXFieldDiff,
    UXFlagChanged,
    UXConfigVersionItem,
    UXModuleConfigSchema,
    UXModuleConfigWriteSchema,
)
from app.services.audit_service import append_audit_log

router = APIRouter(prefix="/ux", tags=["ux"])


_ALLOWED_LAYOUTS: set[str] = {"default", "compact", "dense"}
_ALLOWED_THEMES: set[str] = {"dark", "light", "defense"}


def _normalize_flags(value: Any) -> dict[str, bool] | None:
    if not isinstance(value, dict):
        return None

    normalized: dict[str, bool] = {}
    for key, flag_value in value.items():
        if isinstance(key, str) and isinstance(flag_value, bool):
            normalized[key] = flag_value

    return normalized or None


def _normalize_config(raw: Any) -> dict[str, Any]:
    # Preserve unknown keys, but harden known ones.
    if not isinstance(raw, dict):
        return {}

    config: dict[str, Any] = dict(raw)

    layout = config.get("layout")
    if isinstance(layout, str) and layout in _ALLOWED_LAYOUTS:
        config["layout"] = layout
    else:
        config.pop("layout", None)

    theme = config.get("theme")
    if isinstance(theme, str) and theme in _ALLOWED_THEMES:
        config["theme"] = theme
    else:
        config.pop("theme", None)

    flags = _normalize_flags(config.get("flags"))
    if flags is not None:
        config["flags"] = flags
    else:
        config.pop("flags", None)

    return config


def _snapshot_config(raw: Any) -> dict[str, Any]:
    """Strict snapshot config for versioning/rollback.

    Returns only allowed keys and values. Unknown keys are dropped.
    """

    if not isinstance(raw, dict):
        return {}

    snapshot: dict[str, Any] = {}

    layout = raw.get("layout")
    if isinstance(layout, str) and layout in _ALLOWED_LAYOUTS:
        snapshot["layout"] = layout

    theme = raw.get("theme")
    if isinstance(theme, str) and theme in _ALLOWED_THEMES:
        snapshot["theme"] = theme

    flags = _normalize_flags(raw.get("flags"))
    if flags is not None:
        snapshot["flags"] = flags

    return snapshot


def _audit_payload_to_dict(payload_text: str | None) -> dict[str, Any]:
    if not payload_text:
        return {}
    try:
        parsed = json.loads(payload_text)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _compute_diff(
    prev_snapshot: dict[str, Any] | None, snapshot: dict[str, Any]
) -> UXConfigDiff | None:
    if prev_snapshot is None:
        return None

    diff = UXConfigDiff()

    prev_layout = (
        prev_snapshot.get("layout") if isinstance(prev_snapshot, dict) else None
    )
    curr_layout = snapshot.get("layout")
    if prev_layout != curr_layout:
        diff.layout = UXFieldDiff.model_validate(
            {"from": prev_layout, "to": curr_layout}
        )

    prev_theme = prev_snapshot.get("theme") if isinstance(prev_snapshot, dict) else None
    curr_theme = snapshot.get("theme")
    if prev_theme != curr_theme:
        diff.theme = UXFieldDiff.model_validate({"from": prev_theme, "to": curr_theme})

    prev_flags_raw = (
        prev_snapshot.get("flags") if isinstance(prev_snapshot, dict) else None
    )
    curr_flags_raw = snapshot.get("flags")

    prev_flags = prev_flags_raw if isinstance(prev_flags_raw, dict) else {}
    curr_flags = curr_flags_raw if isinstance(curr_flags_raw, dict) else {}

    prev_keys = set(prev_flags.keys())
    curr_keys = set(curr_flags.keys())

    added = sorted(k for k in (curr_keys - prev_keys) if isinstance(k, str))
    removed = sorted(k for k in (prev_keys - curr_keys) if isinstance(k, str))

    changed: list[UXFlagChanged] = []
    for key in sorted(k for k in (prev_keys & curr_keys) if isinstance(k, str)):
        prev_val = prev_flags.get(key)
        curr_val = curr_flags.get(key)
        if prev_val != curr_val:
            # Values should already be bool due to snapshot sanitization.
            changed.append(
                UXFlagChanged.model_validate(
                    {"key": key, "from": prev_val, "to": curr_val}
                )
            )

    if added:
        diff.flags_added = added
    if removed:
        diff.flags_removed = removed
    if changed:
        diff.flags_changed = changed

    # Only return a diff if something actually changed.
    if (
        diff.layout is None
        and diff.theme is None
        and diff.flags_added is None
        and diff.flags_removed is None
        and diff.flags_changed is None
    ):
        return None

    return diff


@router.get(
    "/{module}",
    response_model=UXConfigResponse,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def fetch_ux_config(
    module: str,
    _: None = Depends(require_scope(UX_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    record = get_ux_config(db, ctx, module)
    if record is None:
        return UXConfigResponse(module=module.strip(), config=UXModuleConfigSchema())

    normalized_config = _normalize_config(record.config)
    return UXConfigResponse(
        module=record.module,
        config=UXModuleConfigSchema.model_validate(normalized_config),
    )


@router.get(
    "/{module}/versions",
    response_model=list[UXConfigVersionItem],
    response_model_exclude_unset=True,
)
def list_ux_config_versions(
    module: str,
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(require_scope(UX_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    normalized_module = (module or "").strip()
    if not normalized_module:
        raise HTTPException(status_code=422, detail="module is required")

    current = get_ux_config(db, ctx, normalized_module)
    current_snapshot = _snapshot_config(current.config) if current is not None else None

    entity_id = f"{ctx.organization_id}:{normalized_module}"
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    base_query = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == ctx.organization_id,
            AuditLog.entity_type == "ux_config",
            AuditLog.action == "ux_config_updated",
            AuditLog.entity_id == entity_id,
        )
        .order_by(AuditLog.seq.asc())
    )

    rows = base_query.offset(offset).limit(limit).all()
    if not rows:
        return []

    items: list[UXConfigVersionItem] = []
    prev_snapshot: dict[str, Any] | None = None
    if offset > 0:
        prev_row = base_query.offset(offset - 1).limit(1).first()
        if prev_row is not None:
            prev_payload = _audit_payload_to_dict(prev_row.payload)
            prev_snapshot = _snapshot_config(prev_payload.get("config"))

    for idx, row in enumerate(rows, start=offset + 1):
        payload = _audit_payload_to_dict(row.payload)
        raw_config = payload.get("config")
        snapshot = _snapshot_config(raw_config)

        is_active = current_snapshot is not None and snapshot == current_snapshot
        diff = _compute_diff(prev_snapshot, snapshot)

        items.append(
            UXConfigVersionItem(
                version=idx,
                audit_log_id=str(row.id),
                created_at=row.created_at,
                actor_id=str(row.actor_id or ""),
                config=UXModuleConfigSchema.model_validate(snapshot),
                is_active=is_active,
                diff=diff,
            )
        )

        prev_snapshot = snapshot

    return items


@router.post(
    "/{module}",
    response_model=UXConfigResponse,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def update_ux_config(
    module: str,
    payload: UXModuleConfigWriteSchema,
    _: None = Depends(require_scope(UX_WRITE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    config_to_store = payload.model_dump(exclude_none=True, exclude_unset=True)
    record = upsert_ux_config(db, ctx, module, config_to_store, commit=False)

    append_audit_log(
        db,
        ctx,
        entity_type="ux_config",
        entity_id=f"{ctx.organization_id}:{record.module}",
        action="ux_config_updated",
        payload={"module": record.module, "config": config_to_store},
    )

    db.commit()
    db.refresh(record)
    normalized_config = _normalize_config(record.config)
    return UXConfigResponse(
        module=record.module,
        config=UXModuleConfigSchema.model_validate(normalized_config),
    )


@router.put(
    "/{module}",
    response_model=UXConfigResponse,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def put_ux_config(
    module: str,
    payload: UXModuleConfigWriteSchema,
    _: None = Depends(require_scope(UX_WRITE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    config_to_store = payload.model_dump(exclude_none=True, exclude_unset=True)
    record = upsert_ux_config(db, ctx, module, config_to_store, commit=False)

    append_audit_log(
        db,
        ctx,
        entity_type="ux_config",
        entity_id=f"{ctx.organization_id}:{record.module}",
        action="ux_config_updated",
        payload={"module": record.module, "config": config_to_store},
    )

    db.commit()
    db.refresh(record)

    normalized_config = _normalize_config(record.config)
    return UXConfigResponse(
        module=record.module,
        config=UXModuleConfigSchema.model_validate(normalized_config),
    )


@router.post(
    "/{module}/rollback",
    response_model=UXConfigResponse | UXRollbackPendingResponse,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def rollback_ux_config(
    module: str,
    body: UXConfigRollbackRequest,
    response: Response,
    _: None = Depends(require_scope(UX_WRITE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    normalized_module = (module or "").strip()
    if not normalized_module:
        raise HTTPException(status_code=422, detail="module is required")

    entity_id = f"{ctx.organization_id}:{normalized_module}"

    policy = get_policy(db, ctx)
    require_4eyes = bool(policy.require_4eyes_on_ux_rollback)

    pending = (
        db.query(PendingUXRollback)
        .filter(
            PendingUXRollback.organization_id == ctx.organization_id,
            PendingUXRollback.module == normalized_module,
        )
        .with_for_update()
        .one_or_none()
    )

    if require_4eyes:
        try:
            actor_uuid = UUID(str(ctx.actor_id))
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="actor_id must be a UUID")

        if pending is None:
            # Validate version exists before creating a pending approval.
            existing_version_row = (
                db.query(AuditLog.id)
                .filter(
                    AuditLog.organization_id == ctx.organization_id,
                    AuditLog.entity_type == "ux_config",
                    AuditLog.action == "ux_config_updated",
                    AuditLog.entity_id == entity_id,
                )
                .order_by(AuditLog.seq.asc())
                .offset(int(body.version) - 1)
                .limit(1)
                .first()
            )
            if existing_version_row is None:
                raise HTTPException(
                    status_code=404, detail="UX config version not found"
                )

            pending = PendingUXRollback(
                organization_id=ctx.organization_id,
                module=normalized_module,
                requested_by=actor_uuid,
                version=int(body.version),
            )
            db.add(pending)

            append_audit_log(
                db,
                ctx,
                entity_type="ux_config",
                entity_id=entity_id,
                action="ux_rollback_pending",
                payload={
                    "module": normalized_module,
                    "version": int(body.version),
                },
            )

            db.commit()
            response.status_code = 202
            return UXRollbackPendingResponse(approval_required=True)

        # There is already a pending request.
        if int(pending.version) != int(body.version):
            raise HTTPException(
                status_code=409,
                detail="A pending UX rollback exists for this module with a different version",
            )

        if pending.requested_by == actor_uuid:
            raise HTTPException(
                status_code=403, detail="Second approver must be a different user"
            )

        # Approve and execute the rollback, then remove the pending request.
        db.delete(pending)
        append_audit_log(
            db,
            ctx,
            entity_type="ux_config",
            entity_id=entity_id,
            action="ux_rollback_approved",
            payload={
                "module": normalized_module,
                "version": int(body.version),
                "requested_by": str(pending.requested_by),
                "approved_by": str(ctx.actor_id),
            },
        )

        # Continue below to perform the actual rollback and write the canonical rollback audit.

    row = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == ctx.organization_id,
            AuditLog.entity_type == "ux_config",
            AuditLog.action == "ux_config_updated",
            AuditLog.entity_id == entity_id,
        )
        .order_by(AuditLog.seq.asc())
        .offset(int(body.version) - 1)
        .limit(1)
        .first()
    )

    if row is None:
        raise HTTPException(status_code=404, detail="UX config version not found")

    payload = _audit_payload_to_dict(row.payload)
    snapshot = _snapshot_config(payload.get("config"))

    record = upsert_ux_config(db, ctx, normalized_module, snapshot, commit=False)

    append_audit_log(
        db,
        ctx,
        entity_type="ux_config",
        entity_id=f"{ctx.organization_id}:{record.module}",
        action="ux_config_rollback",
        payload={
            "module": record.module,
            "rolled_back_to_version": int(body.version),
        },
    )

    db.commit()
    db.refresh(record)

    normalized_config = _normalize_config(record.config)
    return UXConfigResponse(
        module=record.module,
        config=UXModuleConfigSchema.model_validate(normalized_config),
    )
