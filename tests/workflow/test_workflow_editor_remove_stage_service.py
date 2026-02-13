import pytest

from app.services.workflow_editor_service import remove_workflow_stage, StageInUseError
from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition
from app.domain.application.models import Application


def test_remove_workflow_stage_fails_if_used_in_transition(db):
    workflow = Workflow(name="Test Workflow")
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    db.add_all(
        [
            WorkflowStage(workflow_id=workflow.id, name="applied", order=1),
            WorkflowStage(workflow_id=workflow.id, name="screening", order=2),
        ]
    )

    db.add(
        WorkflowTransition(
            workflow_id=workflow.id,
            from_stage="applied",
            to_stage="screening",
        )
    )
    db.commit()

    with pytest.raises(StageInUseError):
        remove_workflow_stage(db, workflow.id, "applied")


def test_remove_workflow_stage_fails_if_used_by_application(db):
    workflow = Workflow(name="Test Workflow")
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    db.add_all(
        [
            WorkflowStage(workflow_id=workflow.id, name="applied", order=1),
            WorkflowStage(workflow_id=workflow.id, name="screening", order=2),
        ]
    )

    application = Application(workflow_id=workflow.id, stage="applied")
    db.add(application)
    db.commit()

    with pytest.raises(StageInUseError):
        remove_workflow_stage(db, workflow.id, "applied")


def test_remove_workflow_stage_succeeds_when_unused(db):
    workflow = Workflow(name="Test Workflow")
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    stage_applied = WorkflowStage(workflow_id=workflow.id, name="applied", order=1)
    stage_screening = WorkflowStage(workflow_id=workflow.id, name="screening", order=2)
    db.add_all([stage_applied, stage_screening])
    db.commit()

    remove_workflow_stage(db, workflow.id, "applied")

    remaining = (
        db.query(WorkflowStage)
        .filter(WorkflowStage.workflow_id == workflow.id)
        .order_by(WorkflowStage.order)
        .all()
    )

    assert [s.name for s in remaining] == ["screening"]
    assert [s.order for s in remaining] == [1]


def test_remove_workflow_stage_reorders_remaining_stages(db):
    workflow = Workflow(name="Test Workflow")
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    db.add_all(
        [
            WorkflowStage(workflow_id=workflow.id, name="applied", order=1),
            WorkflowStage(workflow_id=workflow.id, name="screening", order=2),
            WorkflowStage(workflow_id=workflow.id, name="onsite", order=3),
        ]
    )
    db.commit()

    remove_workflow_stage(db, workflow.id, "screening")

    remaining = (
        db.query(WorkflowStage)
        .filter(WorkflowStage.workflow_id == workflow.id)
        .order_by(WorkflowStage.order)
        .all()
    )

    assert [s.name for s in remaining] == ["applied", "onsite"]
    assert [s.order for s in remaining] == [1, 2]
