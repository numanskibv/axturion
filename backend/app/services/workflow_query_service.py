"""
WorkflowQueryService

Read-only queries related to workflows and stage transitions.
Used by UI to determine allowed user actions.
"""

from sqlalchemy.orm import Session
from app.domain.application.models import Application
from app.domain.workflow.models import WorkflowTransition


def get_allowed_transitions(
    db: Session,
    application_id: str,
):
    """
    Return all allowed target stages for the application's current stage.
    """

    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise ValueError("Application not found")

    current_stage = app.stage

    allowed_to_rows = (
        db.query(WorkflowTransition.to_stage)
        .filter(
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
