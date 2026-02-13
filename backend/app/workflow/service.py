from datetime import datetime, timezone

from sqlalchemy.orm import Session
from app.automation.service import handle_event
from app.domain.application.models import Application
from app.domain.audit.models import AuditLog
from app.domain.workflow.models import WorkflowTransition
from app.services.activity_service import create_activity


class ApplicationNotFoundError(Exception):
    pass


class InvalidStageTransitionError(Exception):
    def __init__(self, from_stage: str, to_stage: str, allowed_to_stages: list[str]):
        super().__init__(f"Invalid stage transition {from_stage} -> {to_stage}")
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.allowed_to_stages = allowed_to_stages


def move_application_stage(db: Session, application_id, new_stage: str):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise ApplicationNotFoundError("Application not found")

    current_stage = app.stage
    workflow_id = app.workflow_id

    # Workflow-scoped allowed transitions
    allowed_to_rows = (
        db.query(WorkflowTransition.to_stage)
        .filter(
            WorkflowTransition.workflow_id == workflow_id,
            WorkflowTransition.from_stage == current_stage,
        )
        .all()
    )

    allowed_to_stages = [row[0] for row in allowed_to_rows]

    if new_stage not in allowed_to_stages:
        raise InvalidStageTransitionError(
            current_stage,
            new_stage,
            allowed_to_stages,
        )

    # Update stage
    app.stage = new_stage
    app.stage_entered_at = datetime.now(timezone.utc)
    db.add(app)

    # Audit log
    log = AuditLog(
        entity_type="application",
        entity_id=str(app.id),
        action="stage_changed",
        payload=f"{current_stage}->{new_stage}",
    )
    db.add(log)

    # Automation event
    handle_event(
        db,
        "application.stage_changed",
        {
            "entity_type": "application",
            "entity_id": str(app.id),
            "workflow_id": str(workflow_id),
            "from_stage": current_stage,
            "to_stage": new_stage,
        },
    )

    create_activity(
        db,
        entity_type="application",
        entity_id=str(app.id),
        activity_type="stage_changed",
        payload={
            "from_stage": current_stage,
            "to_stage": new_stage,
        },
    )

    db.commit()
    db.refresh(app)

    return app
