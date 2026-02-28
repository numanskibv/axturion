from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobCreateRequest(BaseModel):
    title: str
    description: str | None = None


class JobUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None


class JobResponse(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    status: str
    closed_at: datetime | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
