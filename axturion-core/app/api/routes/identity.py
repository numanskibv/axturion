from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_request_context
from app.api.schemas.identity import IdentityMeResponse
from app.core.db import get_db
from app.core.language import resolve_language
from app.core.log_context import correlation_id_var
from app.core.request_context import RequestContext
from app.domain.identity.models import User
from app.services.policy_service import get_policy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/me", tags=["identity"])


@router.get(
    "",
    summary="Get current identity",
    description="""
Returns the current request identity context for the calling user.

Includes effective language resolved from user override + org policy default.
""",
    response_model=IdentityMeResponse,
)
def get_me(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    user_id = UUID(str(ctx.actor_id))
    user = db.query(User).filter(User.id == user_id).one()

    policy = get_policy(db, ctx)

    effective_language = resolve_language(
        org_default=policy.default_language,
        user_override=user.language,
    )

    correlation_id = correlation_id_var.get("-")

    logger.info(
        "identity_me_read",
        extra={
            "action": "identity_me_read",
            "organization_id": str(ctx.organization_id),
            "actor_id": str(user_id),
            "correlation_id": correlation_id,
        },
    )

    return IdentityMeResponse(
        organization_id=ctx.organization_id,
        user_id=user_id,
        role=str(ctx.role or ""),
        scopes=sorted(ctx.scopes),
        language=user.language,
        default_language=policy.default_language,
        effective_language=effective_language,
        correlation_id=correlation_id,
        ux={},
        features={},
    )
