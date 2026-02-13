from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.workflow_query_service import get_allowed_transitions

router = APIRouter(tags=["workflow-queries"])


# API endpoint to retrieve allowed stage transitions for a given application.
@router.get(
    "/applications/{application_id}/allowed-transitions",
    summary="Get allowed stage transitions for application",
    description="""
Returns all valid target stages for the application's current stage.

Results are strictly scoped to the application's workflow.

This endpoint supports UI decision logic and validation transparency.
""",
)
def allowed_transitions(application_id: str, db: Session = Depends(get_db)):
    """List allowed target stages for an application from its current stage."""
    try:
        return get_allowed_transitions(db, application_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
