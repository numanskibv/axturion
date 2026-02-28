from datetime import datetime, timezone
import json
from uuid import UUID

from sqlalchemy.orm import Session
from app.core.request_context import RequestContext
from app.automation.service import handle_event
from app.domain.application.models import Application
from app.domain.workflow.models import PendingStageTransition, WorkflowTransition
from app.services.activity_service import create_activity
from app.services.application_service import ApplicationAlreadyClosedError
from app.services.audit_service import append_audit_log

import logging

logger = logging.getLogger(__name__)


class ApplicationNotFoundError(Exception):
    pass


class InvalidStageTransitionError(Exception):
    def __init__(self, from_stage: str, to_stage: str, allowed_to_stages: list[str]):
        super().__init__(f"Invalid stage transition {from_stage} -> {to_stage}")
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.allowed_to_stages = allowed_to_stages


class OrganizationAccessError(Exception):
    pass


class StageTransitionPendingError(Exception):
    def __init__(self, pending_id: str):
        super().__init__("approval_required")
        self.pending_id = pending_id


class StageTransitionSelfApprovalError(Exception):
    pass


def _coerce_uuid(value) -> UUID:
    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ApplicationNotFoundError("Application not found") from exc


def move_application_stage(
    db: Session,
    ctx: RequestContext,
    application_id,
    new_stage: str,
):
    app_uuid = _coerce_uuid(application_id)

    app = db.query(Application).filter(Application.id == app_uuid).first()
    if not app:
        raise ApplicationNotFoundError("Application not found")
    if app.organization_id != ctx.organization_id:
        raise OrganizationAccessError("Cross-organization access is forbidden")

    if app.status == "closed":
        raise ApplicationAlreadyClosedError()

    current_stage = app.stage
    workflow_id = app.workflow_id

    # Workflow-scoped allowed transitions
    allowed_to_rows = (
        db.query(WorkflowTransition.to_stage)
        .filter(
            WorkflowTransition.organization_id == ctx.organization_id,
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

    transition = (
        db.query(WorkflowTransition)
        .filter(
            WorkflowTransition.organization_id == ctx.organization_id,
            WorkflowTransition.workflow_id == workflow_id,
            WorkflowTransition.from_stage == current_stage,
            WorkflowTransition.to_stage == new_stage,
        )
        .first()
    )

    if not transition:
        raise InvalidStageTransitionError(
            current_stage,
            new_stage,
            allowed_to_stages,
        )

    actor_uuid = UUID(str(ctx.actor_id))

    if bool(getattr(transition, "requires_approval", False)):
        pending = (
            db.query(PendingStageTransition)
            .filter(
                PendingStageTransition.organization_id == ctx.organization_id,
                PendingStageTransition.application_id == app.id,
                PendingStageTransition.target_stage == new_stage,
            )
            .first()
        )

        payload = {
            "workflow_id": str(workflow_id),
            "from_stage": current_stage,
            "to_stage": new_stage,
        }

        if not pending:
            pending = PendingStageTransition(
                organization_id=ctx.organization_id,
                application_id=app.id,
                target_stage=new_stage,
                initiated_by_user_id=actor_uuid,
            )
            db.add(pending)
            db.flush()
            db.refresh(pending)

            payload_with_pending = {**payload, "pending_id": str(pending.id)}

            logger.info(
                "stage_transition_pending",
                extra={
                    "action": "stage_transition_pending",
                    "organization_id": str(ctx.organization_id),
                    "actor_id": str(ctx.actor_id),
                    "entity_type": "application",
                    "entity_id": str(app.id),
                    "from_stage": current_stage,
                    "to_stage": new_stage,
                    "pending_id": str(pending.id),
                },
            )

            append_audit_log(
                db,
                ctx,
                entity_type="application",
                entity_id=str(app.id),
                action="stage_transition_pending",
                payload=payload_with_pending,
            )

            create_activity(
                db,
                organization_id=ctx.organization_id,
                entity_type="application",
                entity_id=str(app.id),
                activity_type="stage_transition_pending",
                payload=payload_with_pending,
            )

            db.commit()
            raise StageTransitionPendingError(pending_id=str(pending.id))

        if pending.initiated_by_user_id == actor_uuid:
            raise StageTransitionSelfApprovalError("Self-approval is forbidden")

        logger.info(
            "stage_transition_approved",
            extra={
                "action": "stage_transition_approved",
                "organization_id": str(ctx.organization_id),
                "actor_id": str(ctx.actor_id),
                "entity_type": "application",
                "entity_id": str(app.id),
                "from_stage": current_stage,
                "to_stage": new_stage,
                "pending_id": str(pending.id),
            },
        )

        app.stage = new_stage
        app.stage_entered_at = datetime.now(timezone.utc)
        db.add(app)

        payload_with_pending = {
            **payload,
            "pending_id": str(pending.id),
            "initiated_by_user_id": str(pending.initiated_by_user_id),
            "approved_by_user_id": str(actor_uuid),
        }

        append_audit_log(
            db,
            ctx,
            entity_type="application",
            entity_id=str(app.id),
            action="stage_transition_approved",
            payload=payload_with_pending,
        )

        handle_event(
            db,
            "application.stage_changed",
            {
                "organization_id": ctx.organization_id,
                "entity_type": "application",
                "entity_id": str(app.id),
                "workflow_id": str(workflow_id),
                "from_stage": current_stage,
                "to_stage": new_stage,
            },
        )

        create_activity(
            db,
            organization_id=ctx.organization_id,
            entity_type="application",
            entity_id=str(app.id),
            activity_type="stage_transition_approved",
            payload=payload_with_pending,
        )

        db.delete(pending)
        db.commit()
        db.refresh(app)
        return app

    logger.info(
        "application_stage_moved",
        extra={
            "action": "application_stage_moved",
            "organization_id": str(ctx.organization_id),
            "actor_id": str(ctx.actor_id),
            "entity_type": "application",
            "entity_id": str(app.id),
            "from_stage": current_stage,
            "to_stage": new_stage,
        },
    )

    # Update stage
    app.stage = new_stage
    app.stage_entered_at = datetime.now(timezone.utc)
    db.add(app)

    # Audit log
    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app.id),
        action="stage_changed",
        payload=f"{current_stage}->{new_stage}",
    )

    # Automation event
    handle_event(
        db,
        "application.stage_changed",
        {
            "organization_id": ctx.organization_id,
            "entity_type": "application",
            "entity_id": str(app.id),
            "workflow_id": str(workflow_id),
            "from_stage": current_stage,
            "to_stage": new_stage,
        },
    )

    create_activity(
        db,
        organization_id=ctx.organization_id,
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
