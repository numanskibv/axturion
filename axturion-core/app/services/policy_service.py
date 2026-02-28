from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.request_context import RequestContext
from app.domain.governance.models import PolicyConfig
from app.services.audit_service import append_audit_log


def get_policy(db: Session, ctx: RequestContext) -> PolicyConfig:
    policy = (
        db.query(PolicyConfig)
        .filter(PolicyConfig.organization_id == ctx.organization_id)
        .one_or_none()
    )

    if policy is not None:
        return policy

    policy = PolicyConfig(organization_id=ctx.organization_id)
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def _snapshot(policy: PolicyConfig) -> dict[str, Any]:
    return {
        "organization_id": str(policy.organization_id),
        "require_4eyes_on_hire": bool(policy.require_4eyes_on_hire),
        "require_4eyes_on_ux_rollback": bool(policy.require_4eyes_on_ux_rollback),
        "candidate_retention_days": (
            int(policy.candidate_retention_days)
            if policy.candidate_retention_days is not None
            else None
        ),
        "audit_retention_days": (
            int(policy.audit_retention_days)
            if policy.audit_retention_days is not None
            else None
        ),
        "created_at": policy.created_at,
        "updated_at": policy.updated_at,
    }


def update_policy(
    db: Session,
    ctx: RequestContext,
    payload: dict[str, Any],
    *,
    commit: bool = True,
) -> PolicyConfig:
    policy = get_policy(db, ctx)

    if "require_4eyes_on_hire" in payload:
        policy.require_4eyes_on_hire = payload["require_4eyes_on_hire"]
    if "require_4eyes_on_ux_rollback" in payload:
        policy.require_4eyes_on_ux_rollback = payload["require_4eyes_on_ux_rollback"]
    if "candidate_retention_days" in payload:
        policy.candidate_retention_days = payload["candidate_retention_days"]
    if "audit_retention_days" in payload:
        policy.audit_retention_days = payload["audit_retention_days"]

    # Flush so updated_at is set before we snapshot for the audit log.
    db.flush()

    append_audit_log(
        db,
        ctx,
        entity_type="policy",
        entity_id=str(ctx.organization_id),
        action="policy_updated",
        payload=_snapshot(policy),
    )

    if commit:
        db.commit()
        db.refresh(policy)

    return policy
