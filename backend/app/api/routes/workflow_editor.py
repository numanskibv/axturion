from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_request_context, require_scope
from app.core.scopes import WORKFLOW_WRITE
from app.core.request_context import RequestContext
from app.core.db import get_db
from app.services.workflow_editor_service import (
    get_workflow_definition,
    add_workflow_stage,
    add_workflow_transition,
    remove_workflow_transition,
    OrganizationAccessError,
    WorkflowNotFoundError,
    DuplicateStageNameError,
    StageNotFoundError,
    DuplicateTransitionError,
    InvalidTransitionError,
    TransitionNotFoundError,
)
from app.api.schemas.workflow_editor import (
    WorkflowDefinitionResponse,
    CreateWorkflowStageRequest,
    WorkflowStageCreatedResponse,
    WorkflowTransitionResponse,
)

router = APIRouter(
    tags=["workflow-editor"]
)  # API router for workflow editor-related endpoints.


@router.get(  # Endpoint to retrieve the full definition of a workflow, including its stages and transitions.
    "/{workflow_id}/definition",
    summary="Get workflow definition for editing",
    description="""
Returns the complete workflow definition used by governance tooling and workflow editors.

Insight: Provides the ordered stages and the allowed transitions that define the controlled application path.
Scope: Strictly workflow-scoped; the response is limited to the specified workflow.
Integrity expectations: Stage names are treated as stable identifiers within the workflow and transitions must remain consistent.
Returns: A structured definition including stages (with order) and transitions.
Errors: Returns not-found when the workflow does not exist.
""",
    response_model=WorkflowDefinitionResponse,
)
def read_workflow_definition(  # Handler function for the endpoint to get a workflow definition by its ID.
    workflow_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    """Retrieve the editable workflow definition (stages and transitions)."""
    try:
        workflow = get_workflow_definition(db, ctx, workflow_id)
    except OrganizationAccessError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow


@router.post(
    "/{workflow_id}/stages",
    summary="Add stage to workflow",
    description="""
Creates a new stage within the specified workflow.

Scope: Strictly workflow-scoped; the stage is created only within the identified workflow.
Integrity rules: Stage names must be unique within the workflow.
Ordering: If an explicit order is not provided, the stage is appended to the end.
Returns: The created stage with its assigned order.
Errors: Returns not-found when the workflow does not exist; returns a validation error on duplicate stage names.
""",
    response_model=WorkflowStageCreatedResponse,
    status_code=201,
)
def create_workflow_stage(
    workflow_id: str,
    body: CreateWorkflowStageRequest,
    _: None = Depends(require_scope(WORKFLOW_WRITE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    """Create a stage within a workflow, enforcing name uniqueness and ordering rules."""
    try:
        stage = add_workflow_stage(
            db,
            ctx,
            workflow_id=workflow_id,
            name=body.name,
            order=body.order,
        )
        return stage
    except OrganizationAccessError:
        raise HTTPException(
            status_code=403, detail="Cross-organization access is forbidden"
        )
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except DuplicateStageNameError:
        raise HTTPException(status_code=400, detail="Stage name already exists")


class WorkflowTransitionRequest(BaseModel):
    from_stage: str
    to_stage: str


@router.post(
    "/{workflow_id}/transitions",
    summary="Add transition between workflow stages",
    description="""
Creates a valid transition between two stages within the workflow.

Integrity rules:
- Both stages must exist
- No duplicate transitions allowed
- Self-transitions are rejected

Transitions define allowed application movement paths.
""",
    response_model=WorkflowTransitionResponse,
    status_code=201,
)
def create_workflow_transition(
    workflow_id: str,
    body: WorkflowTransitionRequest,
    _: None = Depends(require_scope(WORKFLOW_WRITE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    """Create a workflow transition, enforcing basic integrity constraints."""
    try:
        transition = add_workflow_transition(
            db,
            ctx,
            workflow_id=workflow_id,
            from_stage=body.from_stage,
            to_stage=body.to_stage,
        )
        return transition
    except OrganizationAccessError:
        raise HTTPException(
            status_code=403, detail="Cross-organization access is forbidden"
        )
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except StageNotFoundError:
        raise HTTPException(status_code=404, detail="Stage not found")
    except DuplicateTransitionError:
        raise HTTPException(status_code=400, detail="Transition already exists")
    except InvalidTransitionError:
        raise HTTPException(status_code=400, detail="Invalid transition")


@router.delete(
    "/{workflow_id}/transitions",
    summary="Remove workflow transition",
    description="""
Deletes an existing transition within a workflow.

If the transition does not exist,
a not-found error is returned.

This operation affects allowed stage movements.
""",
    status_code=204,
)
def delete_workflow_transition(
    workflow_id: str,
    body: WorkflowTransitionRequest,
    _: None = Depends(require_scope(WORKFLOW_WRITE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    """Remove a workflow transition if it exists; otherwise return not-found."""
    try:
        remove_workflow_transition(
            db,
            ctx,
            workflow_id=workflow_id,
            from_stage=body.from_stage,
            to_stage=body.to_stage,
        )
    except OrganizationAccessError:
        raise HTTPException(
            status_code=403, detail="Cross-organization access is forbidden"
        )
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except TransitionNotFoundError:
        raise HTTPException(status_code=404, detail="Transition not found")

    return Response(status_code=204)
