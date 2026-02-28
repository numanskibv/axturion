import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.db import Base


class Workflow(Base):
    __tablename__ = "workflow"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        nullable=False,
    )
    name = Column(String, nullable=False)
    active = Column(Boolean, nullable=False, default=True)


class WorkflowStage(Base):
    __tablename__ = "workflow_stage"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        nullable=False,
    )
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow.id"))
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=True)


class WorkflowTransition(Base):
    __tablename__ = "workflow_transition"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        nullable=False,
    )
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow.id"))
    from_stage = Column(String, nullable=False)
    to_stage = Column(String, nullable=False)

    requires_approval = Column(Boolean, nullable=False, default=False)


class PendingStageTransition(Base):
    __tablename__ = "pending_stage_transition"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        nullable=False,
    )

    application_id = Column(
        UUID(as_uuid=True),
        ForeignKey("application.id"),
        nullable=False,
    )

    target_stage = Column(String, nullable=False)

    initiated_by_user_id = Column(UUID(as_uuid=True), nullable=False)
    initiated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    approved_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
