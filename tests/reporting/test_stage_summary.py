import pytest

from app.services.reporting_service import get_stage_summary
from app.domain.application.models import Application
from app.domain.workflow.models import Workflow, WorkflowStage


def test_stage_summary_includes_zero_count_stages(db):
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
    db.commit()

    result = get_stage_summary(db, workflow.id)
    stages = {s["stage"]: s["count"] for s in result["stages"]}

    assert stages["applied"] == 0
    assert stages["screening"] == 0


def test_stage_summary_does_not_leak_between_workflows(db):
    # Workflow A
    workflow_a = Workflow(name="Workflow A")
    db.add(workflow_a)
    db.commit()
    db.refresh(workflow_a)

    db.add_all(
        [
            WorkflowStage(workflow_id=workflow_a.id, name="applied", order=1),
            WorkflowStage(workflow_id=workflow_a.id, name="screening", order=2),
        ]
    )

    # Workflow B
    workflow_b = Workflow(name="Workflow B")
    db.add(workflow_b)
    db.commit()
    db.refresh(workflow_b)

    db.add_all(
        [
            WorkflowStage(workflow_id=workflow_b.id, name="applied", order=1),
        ]
    )

    db.commit()

    # Applications
    db.add_all(
        [
            Application(workflow_id=workflow_a.id, stage="applied"),
            Application(workflow_id=workflow_a.id, stage="screening"),
            Application(workflow_id=workflow_b.id, stage="applied"),
            Application(workflow_id=workflow_b.id, stage="applied"),
        ]
    )
    db.commit()

    result_a = get_stage_summary(db, workflow_a.id)
    result_b = get_stage_summary(db, workflow_b.id)

    stages_a = {s["stage"]: s["count"] for s in result_a["stages"]}
    stages_b = {s["stage"]: s["count"] for s in result_b["stages"]}

    # Workflow A must only see its own applications
    assert stages_a["applied"] == 1
    assert stages_a["screening"] == 1

    # Workflow B must only see its own applications
    assert stages_b["applied"] == 2
