import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.db import Base
import uuid


class Application(Base):
    __tablename__ = "application"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organization.id"),
        nullable=False,
    )

    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow.id"), nullable=False)

    stage = Column(String, nullable=False)

    status = Column(String, nullable=False, default="active")

    result = Column(
        String,
        nullable=True,
    )

    stage_entered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    closed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
