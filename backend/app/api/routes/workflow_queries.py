from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.workflow_query_service import get_allowed_transitions

router = APIRouter()


# API endpoint to retrieve allowed stage transitions for a given application.
@router.get("/applications/{application_id}/allowed-transitions")
def allowed_transitions(application_id: str, db: Session = Depends(get_db)):
    try:
        return get_allowed_transitions(db, application_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


from app.services.workflow_editor_service import (
    add_workflow_stage,
    WorkflowNotFoundError,
    DuplicateStageNameError,
)
from app.api.schemas.workflow_editor import (
    CreateWorkflowStageRequest,
    WorkflowStageCreatedResponse,
)


# API endpoint to create a new stage in a workflow.
# It validates the input and handles potential errors such as workflow not found or duplicate stage names.
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
