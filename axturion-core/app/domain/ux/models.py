import uuid
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.core.db import Base


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UXConfig(Base):
    __tablename__ = "ux_config"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "module",
            name="uq_ux_config_org_module",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        nullable=False,
        index=True,
    )

    module = Column(String, nullable=False)  # e.g. "applications"

    # Portable across SQLite (tests) and Postgres (prod).
    config = Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False)

    created_at = Column(DateTime, default=_utcnow_naive, nullable=False)
    updated_at = Column(
        DateTime,
        default=_utcnow_naive,
        onupdate=_utcnow_naive,
        nullable=False,
    )


class PendingUXRollback(Base):
    __tablename__ = "pending_ux_rollback"

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "module",
            name="uq_pending_ux_rollback_org_module",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        nullable=False,
        index=True,
    )

    module = Column(String, nullable=False)
    requested_by = Column(UUID(as_uuid=True), nullable=False)
    version = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
