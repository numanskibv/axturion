from __future__ import annotations

from contextvars import ContextVar


correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="-")
organization_id_var: ContextVar[str] = ContextVar("organization_id", default="-")
actor_id_var: ContextVar[str] = ContextVar("actor_id", default="-")
