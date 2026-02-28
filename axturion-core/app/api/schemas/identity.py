from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.language import Language


class IdentityMeResponse(BaseModel):
    organization_id: UUID
    user_id: UUID
    role: str
    scopes: list[str]

    language: Language | None
    default_language: Language
    effective_language: Language

    correlation_id: str

    ux: dict[str, Any] = Field(default_factory=dict)
    features: dict[str, Any] = Field(default_factory=dict)
