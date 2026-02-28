from datetime import datetime, timedelta, timezone

from app.services.reporting_service import get_stage_duration_summary
from app.domain.workflow.models import Workflow, WorkflowStage
from app.domain.application.models import Application


def test_stage_duration_summary_is_workflow_scoped_and_calculates_average(db, org, ctx):
    # Create workflow A
    workflow_a = Workflow(name="Workflow A", organization_id=org.id)
    db.add(workflow_a)
    db.commit()
    db.refresh(workflow_a)

    db.add_all(
        [
            WorkflowStage(
                organization_id=org.id,
                workflow_id=workflow_a.id,
                name="applied",
                order=1,
            ),
            WorkflowStage(
                organization_id=org.id,
                workflow_id=workflow_a.id,
                name="screening",
                order=2,
            ),
        ]
    )
    db.commit()

    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    # Applications in workflow A
    app1 = Application(
        organization_id=org.id,
        workflow_id=workflow_a.id,
        stage="applied",
        stage_entered_at=now - timedelta(days=4),
    )

    app2 = Application(
        organization_id=org.id,
        workflow_id=workflow_a.id,
        stage="applied",
        stage_entered_at=now - timedelta(days=2),
    )

    db.add_all([app1, app2])
    db.commit()

    # Create workflow B (to test isolation)
    workflow_b = Workflow(name="Workflow B", organization_id=org.id)
    db.add(workflow_b)
    db.commit()
    db.refresh(workflow_b)

    db.add(
        WorkflowStage(
            organization_id=org.id, workflow_id=workflow_b.id, name="applied", order=1
        )
    )
    db.commit()

    db.add(
        Application(
            organization_id=org.id,
            workflow_id=workflow_b.id,
            stage="applied",
            stage_entered_at=now - timedelta(days=10),
        )
    )
    db.commit()

    # Act
    result = get_stage_duration_summary(db, ctx, workflow_a.id, now=now)

    stages = {s["stage"]: s for s in result["stages"]}

    # Average of 4 and 2 days = 3 days
    assert stages["applied"]["count"] == 2
    assert stages["applied"]["average_days"] == 3.0

    # Ensure no leakage from workflow B
    assert stages["applied"]["count"] != 3
