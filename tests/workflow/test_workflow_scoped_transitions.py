import pytest

from app.workflow.service import move_application_stage, InvalidStageTransitionError
from app.domain.application.models import Application
from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition


def test_stage_transitions_are_workflow_scoped(db):
    # 1. Workflow A: applied -> screening
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
    db.add(
        WorkflowTransition(
            workflow_id=workflow_a.id,
            from_stage="applied",
            to_stage="screening",
        )
    )

    # 2. Workflow B: applied -> interview
    workflow_b = Workflow(name="Workflow B")
    db.add(workflow_b)
    db.commit()
    db.refresh(workflow_b)

    db.add_all(
        [
            WorkflowStage(workflow_id=workflow_b.id, name="applied", order=1),
            WorkflowStage(workflow_id=workflow_b.id, name="interview", order=2),
        ]
    )
    db.add(
        WorkflowTransition(
            workflow_id=workflow_b.id,
            from_stage="applied",
            to_stage="interview",
        )
    )

    db.commit()

    # 3. Applications
    app_a = Application(workflow_id=workflow_a.id, stage="applied")
    app_b = Application(workflow_id=workflow_b.id, stage="applied")
    db.add_all([app_a, app_b])
    db.commit()
    db.refresh(app_a)
    db.refresh(app_b)

    # 4. Move Application A to "screening" (should succeed)
    move_application_stage(db, app_a.id, "screening")

    # 5. Attempt to move Application A to "interview" (should fail)
    with pytest.raises(InvalidStageTransitionError) as excinfo_a:
        move_application_stage(db, app_a.id, "interview")

    assert excinfo_a.value.from_stage == "screening"
    assert excinfo_a.value.to_stage == "interview"
    assert excinfo_a.value.allowed_to_stages == []

    # 6. Move Application B to "interview" (should succeed)
    move_application_stage(db, app_b.id, "interview")

    # 7. Attempt to move Application B to "screening" (should fail)
    with pytest.raises(InvalidStageTransitionError) as excinfo_b:
        move_application_stage(db, app_b.id, "screening")

    assert excinfo_b.value.from_stage == "interview"
    assert excinfo_b.value.to_stage == "screening"
    assert excinfo_b.value.allowed_to_stages == []
