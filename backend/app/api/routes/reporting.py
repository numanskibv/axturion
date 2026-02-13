from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services.reporting_service import get_stage_summary
from app.api.schemas.reporting import WorkflowStageSummaryResponse

router = APIRouter(prefix="/reporting", tags=["reporting"])


@router.get(
    "/workflows/{workflow_id}/stage-summary",
    response_model=WorkflowStageSummaryResponse,
)

def stage_summary(workflow_id: str, db: Session = Depends(get_db)):
    return get_stage_summary(db, workflow_id)
