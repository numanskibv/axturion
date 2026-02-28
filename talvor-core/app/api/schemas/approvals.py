from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PendingApprovalItem(BaseModel):
    application_id: UUID
    target_stage: str
    initiated_by_user_id: UUID
    initiated_at: datetime
    age_seconds: int

    workflow_id: UUID | None = None
    current_stage: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalsSummaryResponse(BaseModel):
    total_pending: int
    avg_pending_age_seconds: float
    oldest_pending_age_seconds: int

    model_config = ConfigDict(from_attributes=True)
