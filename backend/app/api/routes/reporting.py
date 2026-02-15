from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services.reporting_service import (
    WorkflowNotFoundError,
    get_stage_duration_summary,
    get_stage_summary,
)
from app.api.schemas.reporting import (
    WorkflowStageSummaryResponse,
    WorkflowStageDurationResponse,
)

router = APIRouter(prefix="/reporting", tags=["reporting"])


@router.get(
    "/workflows/{workflow_id}/stage-summary",
    summary="Stage distribution for a workflow",
    description=(
        "Provides a real-time distribution of applications across workflow stages.\n\n"
        "Insight: Shows how work is currently spread across the process, including stages with zero applications.\n"
        "Governance value: Supports operational visibility and bottleneck detection by making WIP concentration explicit.\n"
        "Scope: Strictly workflow-scoped; results only include applications belonging to the specified workflow.\n"
        "MVP limitations: Reflects current state only; it does not reconstruct historical movement or past stage occupancy."
    ),
    response_model=WorkflowStageSummaryResponse,
)
def stage_summary(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return get_stage_summary(db, workflow_id)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.get(
    "/workflows/{workflow_id}/stage-duration",
    summary="Average time spent in the current stage",
    description=(
        "Calculates the average number of days applications have been in their current stage, grouped by stage.\n\n"
        "Insight: Highlights stagnation risk and stage-level dwell time for the workflow’s current workload.\n"
        "Governance value: Enables SLA monitoring and early escalation when stages show prolonged dwell times.\n"
        "Scope: Strictly workflow-scoped; results only include applications belonging to the specified workflow.\n"
        "MVP limitations: Measures only time in the current stage; historical stage-duration reconstruction is not part of the MVP."
    ),
    response_model=WorkflowStageDurationResponse,
)
def stage_duration(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return get_stage_duration_summary(db, workflow_id)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")
