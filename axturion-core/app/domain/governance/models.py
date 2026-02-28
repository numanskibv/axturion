from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.core.db import Base


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PolicyConfig(Base):
    __tablename__ = "policy_config"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        primary_key=True,
        nullable=False,
    )

    require_4eyes_on_hire = Column(Boolean, default=False, nullable=False)
    require_4eyes_on_ux_rollback = Column(Boolean, default=False, nullable=False)

    # SLA for stage aging highlighting in the Command dashboard.
    stage_aging_sla_days = Column(Integer, default=7, nullable=False)

    candidate_retention_days = Column(Integer, nullable=True)
    audit_retention_days = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=_utcnow_naive, nullable=False)
    updated_at = Column(
        DateTime, default=_utcnow_naive, onupdate=_utcnow_naive, nullable=False
    )
