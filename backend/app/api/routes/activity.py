from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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
MVP limitations: No server-side filtering or pagination is provided by this endpoint.
""",
    response_model=list[ActivityResponse],
)
def list_activities(db: Session = Depends(get_db)):
    """List recent activity records across the system."""
    return db.query(Activity).order_by(Activity.created_at.desc()).all()


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
def get_timeline(entity_type: str, entity_id: str, db: Session = Depends(get_db)):
    """Retrieve the activity timeline for a specific entity."""
    items = (
        db.query(Activity)
        .filter(Activity.entity_type == entity_type, Activity.entity_id == entity_id)
        .order_by(Activity.created_at.desc())
        .all()
    )

    return items
