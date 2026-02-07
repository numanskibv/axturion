import json

from sqlalchemy.orm import Session

from app.domain.automation.models import AutomationRule
from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition


def seed_workflow(db: Session) -> None:
    existing = db.query(Workflow).first()
    if existing:
        return

    wf = Workflow(name="default hiring")
    db.add(wf)
    db.flush()

    stages = ["applied", "screening", "interview", "offer", "hired"]
    for i, stage in enumerate(stages):
        db.add(
            WorkflowStage(
                workflow_id=wf.id,
                name=stage,
                order=i,
            )
        )

    transitions = [
        ("applied", "screening"),
        ("screening", "interview"),
        ("interview", "offer"),
        ("offer", "hired"),
    ]
    for from_stage, to_stage in transitions:
        db.add(
            WorkflowTransition(
                workflow_id=wf.id,
                from_stage=from_stage,
                to_stage=to_stage,
            )
        )

    db.commit()


def seed_automation(db: Session) -> None:
    existing = db.query(AutomationRule).first()
    if existing:
        return

    rule = AutomationRule(
        name="When moved to interview -> create activity + send email",
        event_type="application.stage_changed",
        enabled="true",
        condition_key="to_stage",
        condition_value="interview",
        action_type="create_activity",
        action_payload=json.dumps(
            {
                "type": "task",
                "message": "Schedule interview with candidate",
            }
        ),
    )
    db.add(rule)
    db.commit()
