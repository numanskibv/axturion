from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class RequestContext:
    organization_id: UUID
    actor_id: str
    role: str | None = None
    scopes: set[str] = field(default_factory=set)
