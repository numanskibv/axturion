import uuid
from sqlalchemy import Column, String, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core.db import Base

class Workflow(Base):
    __tablename__ = "workflow"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

class WorkflowStage(Base):
    __tablename__ = "workflow_stage"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow.id"))
    name = Column(String, nullable=False)
    order = Column(Integer, nullable=True)

class WorkflowTransition(Base):
    __tablename__ = "workflow_transition"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow.id"))
    from_stage = Column(String, nullable=False)
    to_stage = Column(String, nullable=False)