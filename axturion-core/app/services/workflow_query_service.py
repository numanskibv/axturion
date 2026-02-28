"""
WorkflowQueryService

Read-only queries related to workflows and stage transitions.
Used by UI to determine allowed user actions.
"""

from sqlalchemy.orm import Session
from uuid import UUID
from app.core.request_context import RequestContext
from app.domain.application.models import Application
from app.domain.workflow.models import Workflow, WorkflowTransition


class OrganizationAccessError(Exception):
    pass


def _coerce_uuid(value: str | UUID) -> UUID:
    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError("Application not found") from exc


def get_allowed_transitions(
    db: Session,
    ctx: RequestContext,
    application_id: str,
):
    """
    Return all allowed target stages for the application's current stage.
    """

    app_uuid = _coerce_uuid(application_id)
    app = db.query(Application).filter(Application.id == app_uuid).first()
    if not app:
        raise ValueError("Application not found")
    if app.organization_id != ctx.organization_id:
        raise OrganizationAccessError("Cross-organization access is forbidden")

    current_stage = app.stage

    allowed_to_rows = (
        db.query(WorkflowTransition.to_stage)
        .filter(
            WorkflowTransition.organization_id == ctx.organization_id,
            WorkflowTransition.workflow_id == app.workflow_id,
            WorkflowTransition.from_stage == current_stage,
        )
        .all()
    )
    allowed_to_stages = [row[0] for row in allowed_to_rows]

    return {
        "from_stage": current_stage,
        "allowed_to_stages": allowed_to_stages,
    }


def list_workflows(
    db: Session,
    ctx: RequestContext,
):
    """Return a lightweight list of workflows for the current organization."""

    rows = (
        db.query(Workflow.id, Workflow.name, Workflow.active)
        .filter(Workflow.organization_id == ctx.organization_id)
        .order_by(Workflow.name.asc(), Workflow.id.asc())
        .all()
    )

    return [
        {
            "id": workflow_id,
            "name": name,
            "active": bool(active),
        }
        for (workflow_id, name, active) in rows
    ]
