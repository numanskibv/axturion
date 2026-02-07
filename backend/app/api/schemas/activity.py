from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ActivityResponse(BaseModel):
    """
    API response schema for timeline activities.

    Activities are immutable, append-only records that describe
    what happened to an entity (application, candidate, job).
    """

    id: UUID
    entity_type: str
    entity_id: str
    type: str
    message: str | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime

    class Config:
        from_attributes = True