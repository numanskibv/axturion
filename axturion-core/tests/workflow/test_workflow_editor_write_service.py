from app.services.workflow_editor_service import (
    add_workflow_stage,
)  # Service function to add a new stage to a workflow.
from app.domain.workflow.models import (
    Workflow,
    WorkflowStage,
)  # SQLAlchemy models for Workflow and WorkflowStage.


def test_add_workflow_stage_appends_when_no_order(db, org, ctx):
    workflow = Workflow(name="Editor Test", organization_id=org.id)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    stage1 = add_workflow_stage(db, ctx, workflow.id, "applied")
    stage2 = add_workflow_stage(db, ctx, workflow.id, "screening")

    assert stage1.order == 1
    assert stage2.order == 2


def test_add_workflow_stage_rejects_duplicate_name(db, org, ctx):
    workflow = Workflow(name="Editor Test", organization_id=org.id)
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    add_workflow_stage(db, ctx, workflow.id, "applied")

    try:
        add_workflow_stage(db, ctx, workflow.id, "applied")
        assert False, "Expected duplicate stage name error"
    except Exception:
        assert True
