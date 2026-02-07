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
from sqlalchemy import func


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


class WorkflowNotFoundError(Exception):
    pass


class DuplicateStageNameError(Exception):
    pass


def add_workflow_stage(
    db: Session,
    workflow_id,
    name: str,
    order: int | None = None,
):
    """
    Add a stage to a workflow.

    - If order is None, append to the end
    - Stage names must be unique per workflow
    """

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise WorkflowNotFoundError()

    # Enforce unique stage name per workflow
    existing = (
        db.query(WorkflowStage)
        .filter(
            WorkflowStage.workflow_id == workflow_id,
            WorkflowStage.name == name,
        )
        .first()
    )
    if existing:
        raise DuplicateStageNameError()

    if order is None:
        max_order = (
            db.query(func.max(WorkflowStage.order))
            .filter(WorkflowStage.workflow_id == workflow_id)
            .scalar()
        )
        order = (max_order or 0) + 1

    stage = WorkflowStage(
        workflow_id=workflow_id,
        name=name,
        order=order,
    )

    db.add(stage)
    db.commit()
    db.refresh(stage)

    return stage
