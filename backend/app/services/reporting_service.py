"""
Implement workflow-level reporting for stage summary.

Requirements:
- Workflow must exist
- Must be workflow-scoped
- Count applications per stage within that workflow
- Include stages with zero applications
- No global queries
- Return structured dict (not ORM objects)
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.domain.workflow.models import Workflow, WorkflowStage
from app.domain.application.models import Application


class WorkflowNotFoundError(Exception):
    pass


def get_stage_summary(db: Session, workflow_id):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise WorkflowNotFoundError()

    # Get all stages for workflow
    stages = (
        db.query(WorkflowStage)
        .filter(WorkflowStage.workflow_id == workflow_id)
        .order_by(WorkflowStage.order)
        .all()
    )

    # Count applications per stage (workflow-scoped)
    counts = (
        db.query(
            Application.stage,
            func.count(Application.id)
        )
        .filter(Application.workflow_id == workflow_id)
        .group_by(Application.stage)
        .all()
    )

    count_map = {stage: count for stage, count in counts}

    return {
        "workflow_id": str(workflow.id),
        "workflow_name": workflow.name,
        "stages": [
            {
                "stage": stage.name,
                "count": count_map.get(stage.name, 0)
            }
            for stage in stages
        ]
    }
