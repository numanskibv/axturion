from __future__ import annotations

from typing import TypedDict

from sqlalchemy.orm import Session

from app.core.request_context import RequestContext
from app.services.policy_service import get_policy


class RetentionConfig(TypedDict):
    candidate_retention_days: int | None
    audit_retention_days: int | None


def get_retention_config(db: Session, ctx: RequestContext) -> RetentionConfig:
    policy = get_policy(db, ctx)
    return {
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
    }
