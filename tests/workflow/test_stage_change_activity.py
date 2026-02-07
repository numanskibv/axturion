from app.workflow.service import move_application_stage
from app.domain.application.models import Application
from app.domain.workflow.models import WorkflowTransition
from app.domain.automation.models import Activity

##  This test verifies that when an application stage is changed, an Activity record is created to log this event.

def test_stage_change_creates_activity(db):
    # Arrange: application + workflow transition
    application = Application(stage="applied")
    db.add(application)

    transition = WorkflowTransition(
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