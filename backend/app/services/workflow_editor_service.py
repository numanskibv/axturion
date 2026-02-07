"""
WorkflowEditorService

This service is responsible for creating and modifying workflows,
their stages and transitions.

It is used by:
- admin configuration UI
- setup wizards
- module installers

This service must ensure workflow integrity.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.workflow.models import (
    Workflow,
    WorkflowStage,
    WorkflowTransition,
)


def get_workflow_definition(db: Session, workflow_id: str):
    """
    Return the full workflow definition including:
    - ordered stages
    - allowed transitions

    This is used by admin tooling and workflow editors.
    """

    try:
        workflow_uuid = UUID(str(workflow_id))
    except ValueError as exc:
        raise ValueError("Invalid workflow_id") from exc

    workflow = db.query(Workflow).filter(Workflow.id == workflow_uuid).first()

    if not workflow:
        raise ValueError("Workflow not found")

    stages = (
        db.query(WorkflowStage)
        .filter(WorkflowStage.workflow_id == workflow_uuid)
        .order_by(WorkflowStage.order)
        .all()
    )

    transitions = (
        db.query(WorkflowTransition)
        .filter(WorkflowTransition.workflow_id == workflow_uuid)
        .all()
    )

    return {
        "id": str(workflow.id),
        "name": workflow.name,
        "stages": [
            {
                "id": str(stage.id),
                "name": stage.name,
                "order": stage.order,
            }
            for stage in stages
        ],
        "transitions": [
            {
                "from_stage": transition.from_stage,
                "to_stage": transition.to_stage,
            }
            for transition in transitions
        ],
    }
