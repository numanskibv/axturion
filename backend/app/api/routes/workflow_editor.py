from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.workflow_editor_service import (
    get_workflow_definition,
    add_workflow_stage,
    add_workflow_transition,
    remove_workflow_transition,
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
    prefix="/workflows", tags=["workflow-editor"]
)  # API router for workflow editor-related endpoints.


@router.get(  # Endpoint to retrieve the full definition of a workflow, including its stages and transitions.
    "/{workflow_id}/definition",
    response_model=WorkflowDefinitionResponse,
)
def read_workflow_definition(  # Handler function for the endpoint to get a workflow definition by its ID.
    workflow_id: str,
    db: Session = Depends(get_db),
):
    workflow = get_workflow_definition(db, workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow


@router.post(
    "/{workflow_id}/stages",
    response_model=WorkflowStageCreatedResponse,
    status_code=201,
)
def create_workflow_stage(
    workflow_id: str,
    body: CreateWorkflowStageRequest,
    db: Session = Depends(get_db),
):
    try:
        stage = add_workflow_stage(
            db,
            workflow_id=workflow_id,
            name=body.name,
            order=body.order,
        )
        return stage
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except DuplicateStageNameError:
        raise HTTPException(status_code=400, detail="Stage name already exists")


class WorkflowTransitionRequest(BaseModel):
    from_stage: str
    to_stage: str


@router.post(
    "/{workflow_id}/transitions",
    response_model=WorkflowTransitionResponse,
    status_code=201,
)
def create_workflow_transition(
    workflow_id: str,
    body: WorkflowTransitionRequest,
    db: Session = Depends(get_db),
):
    try:
        transition = add_workflow_transition(
            db,
            workflow_id=workflow_id,
            from_stage=body.from_stage,
            to_stage=body.to_stage,
        )
        return transition
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
    status_code=204,
)
def delete_workflow_transition(
    workflow_id: str,
    body: WorkflowTransitionRequest,
    db: Session = Depends(get_db),
):
    try:
        remove_workflow_transition(
            db,
            workflow_id=workflow_id,
            from_stage=body.from_stage,
            to_stage=body.to_stage,
        )
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
    except TransitionNotFoundError:
        raise HTTPException(status_code=404, detail="Transition not found")

    return Response(status_code=204)
