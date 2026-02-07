from app.services.workflow_editor_service import get_workflow_definition
from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition

# Test that get_workflow_definition returns the correct stages and transitions for a workflow
# This is a service-level test that directly tests the service function without going through the API layer.
# It uses the real database (not mocks) to ensure that the SQLAlchemy queries work as expected.
# The test sets up a workflow with two stages and one transition, 
# then calls the service function and checks that the returned data matches what was set up.

def test_get_workflow_definition_returns_stages_and_transitions(db):
    # Arrange: workflow
    workflow = Workflow(name="Test Workflow")
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    # Arrange: stages (intentionally out of order)
    stage_applied = WorkflowStage(
        workflow_id=workflow.id,
        name="applied",
        order=2,
    )
    stage_screening = WorkflowStage(
        workflow_id=workflow.id,
        name="screening",
        order=1,
    )
    db.add_all([stage_applied, stage_screening])

    # Arrange: transition
    transition = WorkflowTransition(
        workflow_id=workflow.id,
        from_stage="applied",
        to_stage="screening",
    )
    db.add(transition)

    db.commit()

    # Act
    result = get_workflow_definition(db, str(workflow.id))

    # Assert: workflow basics
    assert result["id"] == str(workflow.id)
    assert result["name"] == "Test Workflow"

    # Assert: stages are ordered
    stages = result["stages"]
    assert len(stages) == 2
    assert stages[0]["name"] == "screening"
    assert stages[1]["name"] == "applied"

    # Assert: transitions
    transitions = result["transitions"]
    assert len(transitions) == 1
    assert transitions[0]["from_stage"] == "applied"
    assert transitions[0]["to_stage"] == "screening"