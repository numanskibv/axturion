import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.db import Base


class Job(Base):
    __tablename__ = "job"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        nullable=False,
    )
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default="open")
    closed_at = Column(DateTime(timezone=True), nullable=True)
    department = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
