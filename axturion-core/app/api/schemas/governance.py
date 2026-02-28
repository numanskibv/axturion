from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PolicyConfigSchema(BaseModel):
    organization_id: str
    require_4eyes_on_hire: bool = False
    require_4eyes_on_ux_rollback: bool = False
    candidate_retention_days: int | None = Field(default=None, ge=1)
    audit_retention_days: int | None = Field(default=None, ge=1)
    created_at: datetime
    updated_at: datetime


class PolicyConfigWriteSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    require_4eyes_on_hire: bool = False
    require_4eyes_on_ux_rollback: bool = False
    candidate_retention_days: int | None = Field(default=None, ge=1)
    audit_retention_days: int | None = Field(default=None, ge=1)


class RetentionPreviewSchema(BaseModel):
    candidate_retention_days: int | None
    audit_retention_days: int | None
    candidates_eligible_for_deletion: int
    audit_entries_eligible_for_deletion: int
