from __future__ import annotations

import logging
import os
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.log_context import correlation_id_var
from app.core.db import get_db
from app.core.request_context import RequestContext
from app.core.roles import resolve_scopes_from_role
from app.domain.identity.models import OrganizationMembership, User


logger = logging.getLogger(__name__)


def get_request_context(
    x_org_id: str | None = Header(default=None, alias="X-Org-Id"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_scopes: str | None = Header(default=None, alias="X-Scopes"),
    db: Session = Depends(get_db),
) -> RequestContext:
    if not x_org_id:
        raise HTTPException(status_code=401, detail="Missing X-Org-Id")
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id")

    try:
        organization_id = UUID(str(x_org_id))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid X-Org-Id")

    try:
        user_id = UUID(str(x_user_id))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid X-User-Id")

    env = os.getenv("ENV", "dev").lower()

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not bool(user.is_active):
        raise HTTPException(status_code=403, detail="Forbidden")

    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.is_active.is_(True),
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Forbidden")

    role: str = str(membership.role).strip()
    scopes: set[str] = resolve_scopes_from_role(role)

    logger.info(
        "role_resolved",
        extra={
            "action": "role_resolved",
            "role": role,
            "correlation_id": correlation_id_var.get("-"),
            "organization_id": str(organization_id),
            "actor_id": str(user_id),
        },
    )

    # Dev-mode override for tests/manual debugging: allow explicit scope headers,
    # but only as a restriction (subset), never an expansion.
    if env == "dev" and x_scopes:
        requested = {s.strip() for s in x_scopes.split(",") if s.strip()}
        if not requested.issubset(scopes):
            raise HTTPException(status_code=403, detail="Forbidden")
        scopes = requested

    return RequestContext(
        organization_id=organization_id,
        actor_id=str(user_id),
        role=role,
        scopes=scopes,
    )


def require_scope(required_scope: str):
    def _require_scope(ctx: RequestContext = Depends(get_request_context)) -> None:
        if required_scope not in ctx.scopes:
            logger.info(
                "authorization_denied",
                extra={
                    "action": "authorization_denied",
                    "required_scope": required_scope,
                    "correlation_id": correlation_id_var.get("-"),
                    "organization_id": str(ctx.organization_id),
                    "actor_id": str(ctx.actor_id),
                },
            )
            raise HTTPException(status_code=403, detail="Forbidden")

    return _require_scope
