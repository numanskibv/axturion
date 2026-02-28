from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.log_context import correlation_id_var
from app.core.request_context import RequestContext
from app.domain.job.models import Job
from app.services.activity_service import create_activity
from app.services.audit_service import append_audit_log


logger = logging.getLogger(__name__)


class JobNotFoundError(Exception):
    pass


class JobAlreadyClosedError(Exception):
    pass


class JobClosedError(Exception):
    pass


class OrganizationAccessError(Exception):
    pass


def _coerce_uuid(value) -> UUID:
    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise JobNotFoundError() from exc


def create_job(
    db: Session,
    ctx: RequestContext,
    title: str,
    description: str | None = None,
):
    job = Job(
        organization_id=ctx.organization_id,
        title=title,
        description=description,
        status="open",
    )
    db.add(job)
    db.flush()
    db.refresh(job)

    payload = {"title": title, "description": description}

    logger.info(
        "job_created",
        extra={
            "action": "job_created",
            "correlation_id": correlation_id_var.get("-"),
            "organization_id": str(ctx.organization_id),
            "actor_id": str(ctx.actor_id),
            "job_id": str(job.id),
        },
    )

    append_audit_log(
        db,
        ctx,
        entity_type="job",
        entity_id=str(job.id),
        action="job_created",
        payload=payload,
    )

    create_activity(
        db,
        organization_id=ctx.organization_id,
        entity_type="job",
        entity_id=str(job.id),
        activity_type="job_created",
        payload=payload,
    )

    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, ctx: RequestContext, job_id):
    job_uuid = _coerce_uuid(job_id)

    job = db.query(Job).filter(Job.id == job_uuid).first()
    if not job:
        raise JobNotFoundError()
    if job.organization_id != ctx.organization_id:
        raise OrganizationAccessError()
    return job


def list_jobs(db: Session, ctx: RequestContext, limit: int = 50, offset: int = 0):
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    return (
        db.query(Job)
        .filter(Job.organization_id == ctx.organization_id)
        .order_by(Job.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_job(
    db: Session,
    ctx: RequestContext,
    job_id,
    title: str | None = None,
    description: str | None = None,
):
    job = get_job(db, ctx, job_id)

    if job.status == "closed":
        raise JobClosedError()

    changed = {}
    if title is not None:
        job.title = title
        changed["title"] = title
    if description is not None:
        job.description = description
        changed["description"] = description

    logger.info(
        "job_updated",
        extra={
            "action": "job_updated",
            "correlation_id": correlation_id_var.get("-"),
            "organization_id": str(ctx.organization_id),
            "actor_id": str(ctx.actor_id),
            "job_id": str(job.id),
        },
    )

    append_audit_log(
        db,
        ctx,
        entity_type="job",
        entity_id=str(job.id),
        action="job_updated",
        payload=changed,
    )

    create_activity(
        db,
        organization_id=ctx.organization_id,
        entity_type="job",
        entity_id=str(job.id),
        activity_type="job_updated",
        payload=changed,
    )

    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def close_job(db: Session, ctx: RequestContext, job_id):
    job = get_job(db, ctx, job_id)

    if job.status == "closed":
        raise JobAlreadyClosedError()

    job.status = "closed"
    job.closed_at = datetime.now(timezone.utc)

    logger.info(
        "job_closed",
        extra={
            "action": "job_closed",
            "correlation_id": correlation_id_var.get("-"),
            "organization_id": str(ctx.organization_id),
            "actor_id": str(ctx.actor_id),
            "job_id": str(job.id),
        },
    )

    append_audit_log(
        db,
        ctx,
        entity_type="job",
        entity_id=str(job.id),
        action="job_closed",
        payload={},
    )

    create_activity(
        db,
        organization_id=ctx.organization_id,
        entity_type="job",
        entity_id=str(job.id),
        activity_type="job_closed",
        payload={},
    )

    db.add(job)
    db.commit()
    db.refresh(job)
    return job
