from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.log_context import correlation_id_var
from app.core.request_context import RequestContext
from app.domain.candidate.models import Candidate
from app.services.activity_service import create_activity
from app.services.audit_service import append_audit_log


logger = logging.getLogger(__name__)


class CandidateNotFoundError(Exception):
    pass


class CandidateEmailConflictError(Exception):
    pass


class OrganizationAccessError(Exception):
    pass


def _coerce_uuid(value) -> UUID:
    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise CandidateNotFoundError() from exc


def create_candidate(
    db: Session,
    ctx: RequestContext,
    full_name: str,
    email: str | None = None,
    phone: str | None = None,
    notes: str | None = None,
) -> Candidate:
    if email is not None:
        existing = (
            db.query(Candidate.id)
            .filter(
                Candidate.organization_id == ctx.organization_id,
                Candidate.email == email,
            )
            .first()
        )
        if existing:
            raise CandidateEmailConflictError()

    candidate = Candidate(
        organization_id=ctx.organization_id,
        name=full_name,
        email=email,
        phone=phone,
        notes=notes,
    )

    db.add(candidate)
    db.flush()
    db.refresh(candidate)

    payload = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "notes": notes,
    }

    logger.info(
        "candidate_created",
        extra={
            "action": "candidate_created",
            "correlation_id": correlation_id_var.get("-"),
            "organization_id": str(ctx.organization_id),
            "actor_id": str(ctx.actor_id),
            "candidate_id": str(candidate.id),
        },
    )

    append_audit_log(
        db,
        ctx,
        entity_type="candidate",
        entity_id=str(candidate.id),
        action="candidate_created",
        payload=payload,
    )

    create_activity(
        db,
        organization_id=ctx.organization_id,
        entity_type="candidate",
        entity_id=str(candidate.id),
        activity_type="candidate_created",
        payload=payload,
    )

    db.commit()
    db.refresh(candidate)
    return candidate


def get_candidate(db: Session, ctx: RequestContext, candidate_id) -> Candidate:
    candidate_uuid = _coerce_uuid(candidate_id)

    candidate = (
        db.query(Candidate)
        .filter(
            Candidate.id == candidate_uuid,
            Candidate.organization_id == ctx.organization_id,
        )
        .first()
    )

    if not candidate:
        raise CandidateNotFoundError()

    return candidate


def list_candidates(db: Session, ctx: RequestContext, limit: int = 50, offset: int = 0):
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    return (
        db.query(Candidate)
        .filter(Candidate.organization_id == ctx.organization_id)
        .order_by(Candidate.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def update_candidate(
    db: Session,
    ctx: RequestContext,
    candidate_id,
    full_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    notes: str | None = None,
) -> Candidate:
    candidate_uuid = _coerce_uuid(candidate_id)

    candidate = db.query(Candidate).filter(Candidate.id == candidate_uuid).first()
    if not candidate:
        raise CandidateNotFoundError()

    if candidate.organization_id != ctx.organization_id:
        raise OrganizationAccessError()

    if email is not None and email != candidate.email:
        existing = (
            db.query(Candidate.id)
            .filter(
                Candidate.organization_id == ctx.organization_id,
                Candidate.email == email,
                Candidate.id != candidate.id,
            )
            .first()
        )
        if existing:
            raise CandidateEmailConflictError()

    changed: dict[str, str | None] = {}
    if full_name is not None:
        candidate.name = full_name
        changed["full_name"] = full_name
    if email is not None:
        candidate.email = email
        changed["email"] = email
    if phone is not None:
        candidate.phone = phone
        changed["phone"] = phone
    if notes is not None:
        candidate.notes = notes
        changed["notes"] = notes

    logger.info(
        "candidate_updated",
        extra={
            "action": "candidate_updated",
            "correlation_id": correlation_id_var.get("-"),
            "organization_id": str(ctx.organization_id),
            "actor_id": str(ctx.actor_id),
            "candidate_id": str(candidate.id),
        },
    )

    append_audit_log(
        db,
        ctx,
        entity_type="candidate",
        entity_id=str(candidate.id),
        action="candidate_updated",
        payload=changed,
    )

    create_activity(
        db,
        organization_id=ctx.organization_id,
        entity_type="candidate",
        entity_id=str(candidate.id),
        activity_type="candidate_updated",
        payload=changed,
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate
