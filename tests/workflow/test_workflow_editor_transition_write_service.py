import pytest

from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition
from app.services.workflow_editor_service import (
    add_workflow_transition,
    remove_workflow_transition,
    DuplicateTransitionError,
    InvalidTransitionError,
    StageNotFoundError,
    TransitionNotFoundError,
)


def test_add_workflow_transition_fails_if_stage_missing(db, org, ctx):
    workflow = Workflow(name="Test Workflow", organization_id=org.id)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    db.add(
        WorkflowStage(
            organization_id=org.id, workflow_id=workflow.id, name="applied", order=1
        )
    )
    db.commit()

    with pytest.raises(StageNotFoundError):
        add_workflow_transition(db, ctx, workflow.id, "applied", "screening")


def test_add_workflow_transition_fails_on_duplicate(db, org, ctx):
    workflow = Workflow(name="Test Workflow", organization_id=org.id)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    db.add_all(
        [
            WorkflowStage(
                organization_id=org.id, workflow_id=workflow.id, name="applied", order=1
            ),
            WorkflowStage(
                organization_id=org.id,
                workflow_id=workflow.id,
                name="screening",
                order=2,
            ),
        ]
    )
    db.commit()

    add_workflow_transition(db, ctx, workflow.id, "applied", "screening")

    with pytest.raises(DuplicateTransitionError):
        add_workflow_transition(db, ctx, workflow.id, "applied", "screening")


def test_add_workflow_transition_fails_on_self_loop(db, org, ctx):
    workflow = Workflow(name="Test Workflow", organization_id=org.id)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    db.add(
        WorkflowStage(
            organization_id=org.id, workflow_id=workflow.id, name="applied", order=1
        )
    )
    db.commit()

    with pytest.raises(InvalidTransitionError):
        add_workflow_transition(db, ctx, workflow.id, "applied", "applied")


def test_remove_workflow_transition_succeeds(db, org, ctx):
    workflow = Workflow(name="Test Workflow", organization_id=org.id)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    db.add_all(
        [
            WorkflowStage(
                organization_id=org.id, workflow_id=workflow.id, name="applied", order=1
            ),
            WorkflowStage(
                organization_id=org.id,
                workflow_id=workflow.id,
                name="screening",
                order=2,
            ),
        ]
    )
    db.add(
        WorkflowTransition(
            organization_id=org.id,
            workflow_id=workflow.id,
            from_stage="applied",
            to_stage="screening",
        )
    )
    db.commit()

    remove_workflow_transition(db, ctx, workflow.id, "applied", "screening")

    remaining = (
        db.query(WorkflowTransition)
        .filter(WorkflowTransition.workflow_id == workflow.id)
        .all()
    )
    assert remaining == []


def test_remove_workflow_transition_fails_when_missing(db, org, ctx):
    workflow = Workflow(name="Test Workflow", organization_id=org.id)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    db.add_all(
        [
            WorkflowStage(
                organization_id=org.id, workflow_id=workflow.id, name="applied", order=1
            ),
            WorkflowStage(
                organization_id=org.id,
                workflow_id=workflow.id,
                name="screening",
                order=2,
            ),
        ]
    )
    db.commit()

    with pytest.raises(TransitionNotFoundError):
        remove_workflow_transition(db, ctx, workflow.id, "applied", "screening")
