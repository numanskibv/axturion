from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.workflow_editor_service import get_workflow_definition
from app.api.schemas.workflow_editor import WorkflowDefinitionResponse

router = APIRouter(prefix="/workflows", tags=["workflow-editor"]) # API router for workflow editor-related endpoints.


@router.get( # Endpoint to retrieve the full definition of a workflow, including its stages and transitions.
    "/{workflow_id}/definition",
    response_model=WorkflowDefinitionResponse,
)
def read_workflow_definition( # Handler function for the endpoint to get a workflow definition by its ID.
    workflow_id: str,
    db: Session = Depends(get_db),
):
    workflow = get_workflow_definition(db, workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return workflow