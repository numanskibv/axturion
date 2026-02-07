"""
WorkflowEditorService

This service is responsible for creating and modifying workflows,
their stages and transitions.

It is used by:
- admin configuration UI
- setup wizards
- module installers

This service must ensure workflow integrity.
"""

from sqlalchemy.orm import Session
from typing import List

from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition

def get_workflow_definition(db: Session, workflow_id: str):
    """
    Return the full workflow definition:
    - stages (ordered)
    - transitions
    """

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise ValueError(f"Workflow {workflow_id} not found")

    stages = (
        db.query(WorkflowStage)
        .filter(WorkflowStage.workflow_id == workflow_id)
        .order_by(WorkflowStage.order)
        .all()
    )

    transitions = (
        db.query(WorkflowTransition)
        .filter(WorkflowTransition.workflow_id == workflow_id)
        .all()
    )

    return {
        "id": str(workflow.id),
        "name": workflow.name,
        "stages": [
            {
                "id": str(stage.id),
                "name": stage.name,
                "order": stage.order,
            }
            for stage in stages
        ],
        "transitions": [
            {
                "id": str(transition.id),
                "from_stage": transition.from_stage,
                "to_stage": transition.to_stage,
            }
            for transition in transitions
        ],
    }