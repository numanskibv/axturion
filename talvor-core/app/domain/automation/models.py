import uuid
from sqlalchemy import JSON, Column, DateTime, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.db import Base


class AutomationRule(Base):
    __tablename__ = "automation_rule"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        nullable=False,
    )
    name = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    enabled = Column(String, nullable=False, default="true")
    condition_key = Column(String, nullable=True)
    condition_value = Column(String, nullable=True)
    action_type = Column(String, nullable=False)
    action_payload = Column(Text, nullable=True)


class Activity(Base):
    __tablename__ = "activity"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        nullable=False,
    )
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    type = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
