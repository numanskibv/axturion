import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.db import Base

class Job(Base):
    __tablename__ = "job"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    department = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())