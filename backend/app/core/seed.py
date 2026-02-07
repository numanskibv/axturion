from sqlalchemy.orm import Session
import json

from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition
from app.domain.automation.models import AutomationRule

def seed_workflow(db: Session):
    existing = db.query(Workflow).first()
    if existing:
        return

    wf = Workflow(name="default hiring")
    db.add(wf)
    db.flush()

    stages = ["applied", "screening", "interview", "offer", "hired"]

    for i, stage in enumerate(stages):
        db.add(WorkflowStage(
            workflow_id=wf.id,
            name=stage,
            order=i
        ))

    transitions = [
        ("applied", "screening"),
        ("screening", "interview"),
        ("interview", "offer"),
        ("offer", "hired"),
    ]

    for f, t in transitions:
        db.add(WorkflowTransition(
            workflow_id=wf.id,
            from_stage=f,
            to_stage=t
        ))

    db.commit()
    
    from app.domain.models import AutomationRule
import json

def seed_automation(db: Session):
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
        action_payload=json.dumps({
            "type": "task",
            "message": "Schedule interview with candidate"
        })
    )
    db.add(rule)
    db.commit()