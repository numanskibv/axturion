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


def _coerce_uuid(value: str | UUID) -> UUID:
    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid workflow_id") from exc


def get_workflow_definition(db: Session, workflow_id: str):
    """
    Return the full workflow definition including:
    - ordered stages
    - allowed transitions

    This is used by admin tooling and workflow editors.
    """

    workflow_uuid = _coerce_uuid(workflow_id)

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


class StageNotFoundError(Exception):
    pass


class StageInUseError(Exception):
    pass


class DuplicateTransitionError(Exception):
    pass


class InvalidTransitionError(Exception):
    pass


class TransitionNotFoundError(Exception):
    pass


def add_workflow_transition(
    db: Session,
    workflow_id: str | UUID,
    from_stage: str,
    to_stage: str,
):
    if from_stage == to_stage:
        raise InvalidTransitionError()

    try:
        workflow_uuid = _coerce_uuid(workflow_id)
    except ValueError:
        raise WorkflowNotFoundError()

    workflow = db.query(Workflow).filter(Workflow.id == workflow_uuid).first()
    if not workflow:
        raise WorkflowNotFoundError()

    from_exists = (
        db.query(WorkflowStage.id)
        .filter(
            WorkflowStage.workflow_id == workflow_uuid,
            WorkflowStage.name == from_stage,
        )
        .first()
    )
    if not from_exists:
        raise StageNotFoundError()

    to_exists = (
        db.query(WorkflowStage.id)
        .filter(
            WorkflowStage.workflow_id == workflow_uuid,
            WorkflowStage.name == to_stage,
        )
        .first()
    )
    if not to_exists:
        raise StageNotFoundError()

    existing = (
        db.query(WorkflowTransition.id)
        .filter(
            WorkflowTransition.workflow_id == workflow_uuid,
            WorkflowTransition.from_stage == from_stage,
            WorkflowTransition.to_stage == to_stage,
        )
        .first()
    )
    if existing:
        raise DuplicateTransitionError()

    transition = WorkflowTransition(
        workflow_id=workflow_uuid,
        from_stage=from_stage,
        to_stage=to_stage,
    )

    db.add(transition)
    db.commit()
    db.refresh(transition)

    return transition


def remove_workflow_transition(
    db: Session,
    workflow_id: str | UUID,
    from_stage: str,
    to_stage: str,
):
    try:
        workflow_uuid = _coerce_uuid(workflow_id)
    except ValueError:
        raise WorkflowNotFoundError()

    workflow = db.query(Workflow).filter(Workflow.id == workflow_uuid).first()
    if not workflow:
        raise WorkflowNotFoundError()

    transition = (
        db.query(WorkflowTransition)
        .filter(
            WorkflowTransition.workflow_id == workflow_uuid,
            WorkflowTransition.from_stage == from_stage,
            WorkflowTransition.to_stage == to_stage,
        )
        .first()
    )
    if not transition:
        raise TransitionNotFoundError()

    db.delete(transition)
    db.commit()

    return None


def remove_workflow_stage(
    db: Session,
    workflow_id: str | UUID,
    stage_name: str,
):
    try:
        workflow_uuid = _coerce_uuid(workflow_id)
    except ValueError:
        raise WorkflowNotFoundError()

    workflow = db.query(Workflow).filter(Workflow.id == workflow_uuid).first()
    if not workflow:
        raise WorkflowNotFoundError()

    stage = (
        db.query(WorkflowStage)
        .filter(
            WorkflowStage.workflow_id == workflow_uuid,
            WorkflowStage.name == stage_name,
        )
        .first()
    )
    if not stage:
        raise StageNotFoundError()

    from sqlalchemy import or_

    transition_in_use = (
        db.query(WorkflowTransition.id)
        .filter(
            WorkflowTransition.workflow_id == workflow_uuid,
            or_(
                WorkflowTransition.from_stage == stage_name,
                WorkflowTransition.to_stage == stage_name,
            ),
        )
        .first()
    )
    if transition_in_use:
        raise StageInUseError()

    from app.domain.application.models import Application

    app_in_use = (
        db.query(Application.id)
        .filter(
            Application.workflow_id == workflow_uuid,
            Application.stage == stage_name,
        )
        .first()
    )
    if app_in_use:
        raise StageInUseError()

    db.delete(stage)
    db.commit()

    return None


def add_workflow_stage(
    db: Session,
    workflow_id: str | UUID,
    name: str,
    order: int | None = None,
):
    """
    Add a stage to a workflow.

    - If order is None, append to the end
    - Stage names must be unique per workflow
    """

    try:
        workflow_uuid = _coerce_uuid(workflow_id)
    except ValueError:
        # Preserve previous behavior: invalid IDs behaved like "not found".
        raise WorkflowNotFoundError()

    workflow = db.query(Workflow).filter(Workflow.id == workflow_uuid).first()
    if not workflow:
        raise WorkflowNotFoundError()

    # Enforce unique stage name per workflow
    existing = (
        db.query(WorkflowStage)
        .filter(
            WorkflowStage.workflow_id == workflow_uuid,
            WorkflowStage.name == name,
        )
        .first()
    )
    if existing:
        raise DuplicateStageNameError()

    if order is None:
        max_order = (
            db.query(func.max(WorkflowStage.order))
            .filter(WorkflowStage.workflow_id == workflow_uuid)
            .scalar()
        )
        order = (max_order or 0) + 1

    stage = WorkflowStage(
        workflow_id=workflow_uuid,
        name=name,
        order=order,
    )

    db.add(stage)
    db.commit()
    db.refresh(stage)

    return stage
