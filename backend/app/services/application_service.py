from datetime import datetime, timezone
import json
from uuid import UUID

from sqlalchemy.orm import Session
from app.domain.application.models import Application
from app.core.request_context import RequestContext

from app.core.log_context import correlation_id_var
from app.domain.workflow.models import Workflow, WorkflowStage
from app.services.activity_service import create_activity
from app.services.audit_service import append_audit_log

import logging

logger = logging.getLogger(__name__)


class ApplicationNotFoundError(Exception):
    pass


class ApplicationAlreadyClosedError(Exception):
    pass


class OrganizationAccessError(Exception):
    pass


class WorkflowNotFoundError(Exception):
    pass


class WorkflowHasNoStagesError(Exception):
    pass


def _coerce_uuid(value) -> UUID:
    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ApplicationNotFoundError() from exc


def close_application(
    db: Session,
    ctx: RequestContext,
    application_id,
    result: str | None = None,
):
    app_uuid = _coerce_uuid(application_id)

    application = db.query(Application).filter(Application.id == app_uuid).first()

    if not application:
        raise ApplicationNotFoundError()

    if application.organization_id != ctx.organization_id:
        raise OrganizationAccessError()

    if application.status == "closed":
        raise ApplicationAlreadyClosedError()

    application.status = "closed"
    application.closed_at = datetime.now(timezone.utc)

    if result is not None:
        application.result = str(result)

        logger.info(
            "application_closed",
            extra={
                "action": "application_closed",
                "correlation_id": correlation_id_var.get("-"),
                "organization_id": str(ctx.organization_id),
                "actor_id": str(ctx.actor_id),
                "application_id": str(application.id),
                "result": str(result),
            },
        )

        append_audit_log(
            db,
            ctx,
            entity_type="application",
            entity_id=str(application.id),
            action="application_closed",
            payload={"result": str(result)},
        )

        create_activity(
            db,
            organization_id=ctx.organization_id,
            entity_type="application",
            entity_id=str(application.id),
            activity_type="application_closed",
            payload={"result": str(result)},
        )
    else:
        # Backward-compatible behavior: legacy callers close without a result.
        logger.info(
            "application_closed",
            extra={
                "action": "application_closed",
                "correlation_id": correlation_id_var.get("-"),
                "organization_id": str(ctx.organization_id),
                "actor_id": str(ctx.actor_id),
                "application_id": str(application.id),
            },
        )

    db.add(application)
    db.commit()
    db.refresh(application)

    return application


def create_application(
    db: Session,
    ctx: RequestContext,
    workflow_id: str | UUID,
    candidate_id: str | UUID | None = None,
    job_id: str | UUID | None = None,
):
    workflow_uuid = _coerce_uuid(workflow_id)

    workflow = db.query(Workflow).filter(Workflow.id == workflow_uuid).first()
    if not workflow:
        raise WorkflowNotFoundError()
    if workflow.organization_id != ctx.organization_id:
        raise OrganizationAccessError()

    initial_stage_row = (
        db.query(WorkflowStage.name)
        .filter(
            WorkflowStage.organization_id == ctx.organization_id,
            WorkflowStage.workflow_id == workflow_uuid,
        )
        .order_by(
            WorkflowStage.order.is_(None),
            WorkflowStage.order,
            WorkflowStage.name,
        )
        .first()
    )

    if not initial_stage_row:
        raise WorkflowHasNoStagesError()

    initial_stage = initial_stage_row[0]

    application = Application(
        organization_id=ctx.organization_id,
        workflow_id=workflow_uuid,
        stage=initial_stage,
        status="open",
    )
    db.add(application)
    db.flush()
    db.refresh(application)

    payload = {
        "workflow_id": str(workflow_uuid),
        "candidate_id": str(candidate_id) if candidate_id is not None else None,
        "job_id": str(job_id) if job_id is not None else None,
        "initial_stage": initial_stage,
    }

    logger.info(
        "application_created",
        extra={
            "action": "application_created",
            "correlation_id": correlation_id_var.get("-"),
            "organization_id": str(ctx.organization_id),
            "actor_id": str(ctx.actor_id),
            "application_id": str(application.id),
        },
    )

    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(application.id),
        action="application_created",
        payload=payload,
    )

    create_activity(
        db,
        organization_id=ctx.organization_id,
        entity_type="application",
        entity_id=str(application.id),
        activity_type="application_created",
        payload=payload,
    )

    db.commit()
    db.refresh(application)

    return application
