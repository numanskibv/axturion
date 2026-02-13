from app.workflow.service import move_application_stage
from app.domain.application.models import Application
from app.domain.workflow.models import WorkflowStage, WorkflowTransition
from app.domain.automation.models import Activity
from app.domain.workflow.models import Workflow


##  This test verifies that when an application stage is changed, an Activity record is created to log this event.


def test_stage_change_creates_activity(db):
    # Arrange: create workflow
    workflow = Workflow(name="Test Workflow")
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    # Arrange: application + workflow transition
    application = Application(
        workflow_id=workflow.id,
        stage="applied",
    )
    db.add(application)

    transition = WorkflowTransition(
        workflow_id=workflow.id,
        from_stage="applied",
        to_stage="screening",
    )
    db.add(transition)

    db.commit()

    # Act: move stage
    move_application_stage(db, application.id, "screening")

    # Assert: activity created
    activities = db.query(Activity).all()

    assert len(activities) == 1
    assert activities[0].type == "stage_changed"
    assert activities[0].payload["from_stage"] == "applied"
    assert activities[0].payload["to_stage"] == "screening"


def test_stage_change_updates_stage_entered_at(db):
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

    application = Application(
        workflow_id=workflow.id,
        stage="applied",
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    original_timestamp = application.stage_entered_at

    move_application_stage(db, application.id, "screening")
    db.refresh(application)

    assert application.stage == "screening"
    assert application.stage_entered_at != original_timestamp
