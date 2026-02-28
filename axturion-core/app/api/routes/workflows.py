from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_request_context, require_scope
from app.api.schemas.workflows import WorkflowListItem
from app.core.scopes import WORKFLOW_READ
from app.core.request_context import RequestContext
from app.core.db import get_db
from app.services.workflow_editor_service import (
    get_workflow_definition,
    OrganizationAccessError,
)
from app.services.workflow_query_service import list_workflows

router = APIRouter(tags=["workflows"])


@router.get(
    "",
    summary="List workflows",
    description="""
Returns a lightweight list of workflows for the current organization.

Scope: Requires workflow read scope.
Org boundary: Results are filtered by the request context organization.
Performance: No stages/transitions are joined or returned.
""",
    response_model=list[WorkflowListItem],
)
def list_workflows_endpoint(
    _: None = Depends(require_scope(WORKFLOW_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    return list_workflows(db, ctx)


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
