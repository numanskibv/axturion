from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditVerifyError(BaseModel):
    seq: int
    audit_log_id: UUID
    reason: str

    model_config = ConfigDict(from_attributes=True)


class AuditVerifyResponse(BaseModel):
    ok: bool
    checked: int
    first_seq: int | None = None
    last_seq: int | None = None
    error: AuditVerifyError | None = None

    model_config = ConfigDict(from_attributes=True)
