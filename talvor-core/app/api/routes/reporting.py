from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.api.deps import get_request_context, require_scope
from app.core.scopes import REPORTING_READ
from app.core.request_context import RequestContext
from app.api.schemas.approvals import ApprovalsSummaryResponse
from app.services.approvals_service import approval_summary
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
def stage_summary(
    workflow_id: str,
    _: None = Depends(require_scope(REPORTING_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    try:
        return get_stage_summary(db, ctx, workflow_id)
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
def stage_duration(
    workflow_id: str,
    _: None = Depends(require_scope(REPORTING_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    try:
        return get_stage_duration_summary(db, ctx, workflow_id)
    except WorkflowNotFoundError:
        raise HTTPException(status_code=404, detail="Workflow not found")


@router.get(
    "/approvals/summary",
    summary="Pending approvals summary",
    description=(
        "Provides an organization-scoped summary of pending stage transition approvals.\n\n"
        "Authorization: Requires reporting read scope.\n"
        "Organization boundary: Only includes pending approvals for the current organization.\n"
        "Use-case: Dashboards and operational reporting without enumerating all pending items."
    ),
    response_model=ApprovalsSummaryResponse,
)
def approvals_summary(
    _: None = Depends(require_scope(REPORTING_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    return approval_summary(db, ctx)
