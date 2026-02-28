from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_request_context, require_scope
from app.core.db import get_db
from app.core.request_context import RequestContext
from app.core.scopes import WORKFLOW_READ, WORKFLOW_WRITE
from app.api.schemas.governance import (
    PolicyConfigSchema,
    PolicyConfigWriteSchema,
    RetentionPreviewSchema,
)
from app.domain.audit.models import AuditLog
from app.domain.candidate.models import Candidate
from app.services.policy_service import get_policy, update_policy
from app.services.retention_service import get_retention_config


router = APIRouter(prefix="/governance", tags=["governance"])


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@router.get(
    "/policy",
    response_model=PolicyConfigSchema,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def fetch_policy(
    _: None = Depends(require_scope(WORKFLOW_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    policy = get_policy(db, ctx)
    return PolicyConfigSchema(
        organization_id=str(policy.organization_id),
        require_4eyes_on_hire=bool(policy.require_4eyes_on_hire),
        require_4eyes_on_ux_rollback=bool(policy.require_4eyes_on_ux_rollback),
        stage_aging_sla_days=int(policy.stage_aging_sla_days),
        default_language=str(policy.default_language),
        candidate_retention_days=policy.candidate_retention_days,
        audit_retention_days=policy.audit_retention_days,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


@router.put(
    "/policy",
    response_model=PolicyConfigSchema,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def put_policy(
    payload: PolicyConfigWriteSchema,
    _: None = Depends(require_scope(WORKFLOW_WRITE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=422, detail="at least one field is required")

    policy = update_policy(db, ctx, updates)
    return PolicyConfigSchema(
        organization_id=str(policy.organization_id),
        require_4eyes_on_hire=bool(policy.require_4eyes_on_hire),
        require_4eyes_on_ux_rollback=bool(policy.require_4eyes_on_ux_rollback),
        stage_aging_sla_days=int(policy.stage_aging_sla_days),
        default_language=str(policy.default_language),
        candidate_retention_days=policy.candidate_retention_days,
        audit_retention_days=policy.audit_retention_days,
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


@router.get(
    "/retention/preview",
    response_model=RetentionPreviewSchema,
    response_model_exclude_unset=True,
)
def preview_retention(
    _: None = Depends(require_scope(WORKFLOW_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    cfg = get_retention_config(db, ctx)

    candidates_eligible = 0
    if cfg["candidate_retention_days"] is not None:
        cutoff = _now_utc() - timedelta(days=int(cfg["candidate_retention_days"]))
        candidates_eligible = int(
            db.query(func.count(Candidate.id))
            .filter(
                Candidate.organization_id == ctx.organization_id,
                Candidate.created_at <= cutoff,
            )
            .scalar()
            or 0
        )

    audit_eligible = 0
    if cfg["audit_retention_days"] is not None:
        cutoff = _now_utc() - timedelta(days=int(cfg["audit_retention_days"]))
        audit_eligible = int(
            db.query(func.count(AuditLog.id))
            .filter(
                AuditLog.organization_id == ctx.organization_id,
                AuditLog.created_at <= cutoff,
            )
            .scalar()
            or 0
        )

    return RetentionPreviewSchema(
        candidate_retention_days=cfg["candidate_retention_days"],
        audit_retention_days=cfg["audit_retention_days"],
        candidates_eligible_for_deletion=candidates_eligible,
        audit_entries_eligible_for_deletion=audit_eligible,
    )
