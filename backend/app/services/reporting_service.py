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

from datetime import datetime, timezone

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
        db.query(Application.stage, func.count(Application.id))
        .filter(Application.workflow_id == workflow_id)
        .group_by(Application.stage)
        .all()
    )

    count_map = {stage: count for stage, count in counts}

    return {
        "workflow_id": str(workflow.id),
        "workflow_name": workflow.name,
        "stages": [
            {"stage": stage.name, "count": count_map.get(stage.name, 0)}
            for stage in stages
        ],
    }


def get_stage_duration_summary(db: Session, workflow_id, now: datetime | None = None):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise WorkflowNotFoundError()

    if now is None:
        now = datetime.utcnow()

    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)

    stages_for_workflow = (
        db.query(WorkflowStage)
        .filter(WorkflowStage.workflow_id == workflow_id)
        .order_by(WorkflowStage.order)
        .all()
    )

    workflow_stage_names = {stage.name for stage in stages_for_workflow}

    applications = (
        db.query(Application).filter(Application.workflow_id == workflow_id).all()
    )

    stage_data: dict[str, dict[str, float | int]] = {}

    for stage_name in workflow_stage_names:
        stage_data[stage_name] = {
            "total_duration": 0.0,
            "count": 0,
        }

    for app in applications:
        if not app.stage_entered_at:
            continue

        entered_at = app.stage_entered_at
        if entered_at.tzinfo is None:
            entered_at = entered_at.replace(tzinfo=timezone.utc)
        else:
            entered_at = entered_at.astimezone(timezone.utc)

        duration = (now - entered_at).total_seconds() / 86400

        if app.stage not in stage_data:
            stage_data[app.stage] = {
                "total_duration": 0.0,
                "count": 0,
            }

        stage_data[app.stage]["total_duration"] += duration
        stage_data[app.stage]["count"] += 1

    stages = []

    for stage in stages_for_workflow:
        data = stage_data[stage.name]
        if data["count"]:
            avg = data["total_duration"] / data["count"]
            average_days = round(avg, 2)
        else:
            average_days = 0.0

        stages.append(
            {
                "stage": stage.name,
                "average_days": average_days,
                "count": data["count"],
            }
        )

    extra_stage_names = sorted(
        stage_name
        for stage_name in stage_data.keys()
        if stage_name not in workflow_stage_names
    )

    for stage_name in extra_stage_names:
        data = stage_data[stage_name]
        if data["count"]:
            avg = data["total_duration"] / data["count"]
            average_days = round(avg, 2)
        else:
            average_days = 0.0

        stages.append(
            {
                "stage": stage_name,
                "average_days": average_days,
                "count": data["count"],
            }
        )

    return {
        "workflow_id": str(workflow.id),
        "workflow_name": workflow.name,
        "stages": stages,
    }
