from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB

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
