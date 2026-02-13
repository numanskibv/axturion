import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.db import Base

class Application(Base):
    __tablename__ = "application"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    workflow_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workflow.id"),
        nullable=False,
    )

    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidate.id"))
    job_id = Column(UUID(as_uuid=True), ForeignKey("job.id"))

    stage = Column(String, default="applied")
    status = Column(String, default="active")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
