import time
from datetime import datetime

import pytest

from app.domain.application.models import Application
from app.domain.workflow.models import (
    Workflow,
    WorkflowStage,
    WorkflowTransition,
)
from app.services.application_service import (
    ApplicationAlreadyClosedError,
    close_application,
)
from app.workflow.service import move_application_stage


def test_application_initial_lifecycle_fields(db):
    workflow = Workflow(name="Workflow")
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    application = Application(
        workflow_id=workflow.id,
        stage="applied",
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    assert application.status == "active"
    assert application.closed_at is None
    assert application.stage_entered_at is not None
    assert isinstance(application.stage_entered_at, datetime)


def test_stage_change_resets_stage_entered_at(db):
    workflow = Workflow(name="Workflow")
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

    time.sleep(0.01)  # ensure measurable time diff

    move_application_stage(db, application.id, "screening")

    db.refresh(application)

    assert application.stage == "screening"
    assert application.stage_entered_at > original_timestamp
    assert application.status == "active"


def test_close_application_sets_closed_fields(db):
    workflow = Workflow(name="Workflow")
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    application = Application(
        workflow_id=workflow.id,
        stage="applied",
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    close_application(db, application.id)

    db.refresh(application)

    assert application.status == "closed"
    assert application.closed_at is not None


def test_closed_application_cannot_change_stage(db):
    workflow = Workflow(name="Workflow")
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

    close_application(db, application.id)

    with pytest.raises(ApplicationAlreadyClosedError):
        move_application_stage(db, application.id, "screening")
