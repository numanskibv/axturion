from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_request_context
from app.core.request_context import RequestContext
from app.core.db import get_db
from app.services.workflow_editor_service import (
    get_workflow_definition,
    OrganizationAccessError,
)

router = APIRouter(tags=["workflows"])


@router.get(
    "/{workflow_id}",
    summary="Retrieve workflow definition",
    description="""
Returns the current workflow configuration for the specified workflow identifier.

Insight: Provides a complete, authoritative view of stages and allowed transitions used to control application movement.
Scope: Strictly workflow-scoped; only the requested workflow is returned.
Integrity expectations: Stage order and transition rules are treated as policy for the workflow.
Returns: A structured workflow definition suitable for administrative review and controlled configuration tooling.
Errors: Returns not-found when the workflow identifier is unknown.
""",
)
def get_workflow(
    workflow_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    """Retrieve a workflow definition by identifier."""
    try:
        return get_workflow_definition(db, ctx, workflow_id)
    except OrganizationAccessError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        # Service-level error → nette API response
        raise HTTPException(status_code=404, detail=str(e))
