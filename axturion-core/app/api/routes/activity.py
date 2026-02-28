from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_request_context
from app.core.request_context import RequestContext
from app.core.db import get_db
from app.domain.automation.models import Activity
from app.api.schemas.activity import ActivityResponse


router = APIRouter(tags=["activity"])


@router.get(
    "/activities",
    summary="List recent activity records",
    description="""
Returns activity records ordered from most recent to oldest.

Scope: Global; returns records across all entities and workflows.
Governance value: Supports high-level operational visibility and audit transparency.
Integrity model: Activities are immutable and append-only.
Returns: A chronological list of activity items.
""",
    response_model=list[ActivityResponse],
)
def list_activities(
    limit: int = 50,
    offset: int = 0,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    """List recent activity records across the system."""

    MAX_LIMIT = 500
    limit = min(int(limit), MAX_LIMIT)
    offset = max(0, int(offset))

    return (
        db.query(Activity)
        .filter(Activity.organization_id == ctx.organization_id)
        .order_by(Activity.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


@router.get(
    "/{entity_type}/{entity_id}",
    summary="Retrieve activity timeline",
    description="""
Returns chronological activity records for an entity.

Activities are immutable and append-only.

This endpoint supports:
- Audit transparency
- Operational traceability
- Governance review
""",
    response_model=list[ActivityResponse],
)
def get_timeline(
    entity_type: str,
    entity_id: str,
    limit: int = 50,
    offset: int = 0,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    """Retrieve the activity timeline for a specific entity."""

    MAX_LIMIT = 500
    limit = min(int(limit), MAX_LIMIT)
    offset = max(0, int(offset))

    items = (
        db.query(Activity)
        .filter(
            Activity.organization_id == ctx.organization_id,
            Activity.entity_type == entity_type,
            Activity.entity_id == entity_id,
        )
        .order_by(Activity.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return items
