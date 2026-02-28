from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class StageAgingItem(BaseModel):
    application_id: UUID
    workflow_id: UUID
    current_stage: str
    age_seconds: int


class StageDurationSummaryItem(BaseModel):
    stage: str
    count: int
    avg_duration_seconds: float
    median_duration_seconds: float
    p90_duration_seconds: float


class StageDurationBreakdownItem(BaseModel):
    stage: str
    count: int
    median_seconds: int
    p90_seconds: int


class TimeToCloseStatsResponse(BaseModel):
    count: int
    avg_seconds: float
    median_seconds: float
    p90_seconds: float
    min_seconds: int
    max_seconds: int


TimeToCloseResult = Literal["hired", "rejected"]
