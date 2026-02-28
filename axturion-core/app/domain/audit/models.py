import uuid
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.db import Base


class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        UniqueConstraint("organization_id", "seq", name="uq_audit_org_seq"),
        Index("ix_audit_org_seq", "organization_id", "seq"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        nullable=False,
    )
    actor_id = Column(String, nullable=True)
    entity_type = Column(String)
    entity_id = Column(String)
    action = Column(String)
    payload = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    prev_hash = Column(String(64), nullable=True)
    hash = Column(String(64), nullable=False)
    seq = Column(Integer, nullable=False)
