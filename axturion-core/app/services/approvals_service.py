from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.log_context import correlation_id_var
from app.core.request_context import RequestContext
from app.domain.application.models import Application
from app.domain.workflow.models import PendingStageTransition


logger = logging.getLogger(__name__)


class PendingApprovalNotFoundError(Exception):
    pass


def _coerce_uuid(value) -> UUID:
    if isinstance(value, UUID):
        return value

    try:
        return UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise PendingApprovalNotFoundError() from exc


def _coerce_dt(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def list_pending_approvals(
    db: Session,
    ctx: RequestContext,
    limit: int = 50,
    offset: int = 0,
):
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    now = datetime.now(timezone.utc)

    rows = (
        db.query(
            PendingStageTransition,
            Application.workflow_id,
            Application.stage,
        )
        .join(Application, Application.id == PendingStageTransition.application_id)
        .filter(
            PendingStageTransition.organization_id == ctx.organization_id,
            Application.organization_id == ctx.organization_id,
        )
        .order_by(PendingStageTransition.initiated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items: list[dict] = []
    for pending, workflow_id, current_stage in rows:
        initiated_at = _coerce_dt(pending.initiated_at)
        age_seconds = int(max(0.0, (now - initiated_at).total_seconds()))

        items.append(
            {
                "application_id": pending.application_id,
                "workflow_id": workflow_id,
                "current_stage": current_stage,
                "target_stage": pending.target_stage,
                "initiated_by_user_id": pending.initiated_by_user_id,
                "initiated_at": initiated_at,
                "age_seconds": age_seconds,
            }
        )

    logger.info(
        "pending_approvals_listed",
        extra={
            "action": "pending_approvals_listed",
            "correlation_id": correlation_id_var.get("-"),
            "organization_id": str(ctx.organization_id),
            "actor_id": str(ctx.actor_id),
            "count": len(items),
            "limit": limit,
            "offset": offset,
        },
    )

    return items


def get_pending_for_application(
    db: Session,
    ctx: RequestContext,
    application_id,
):
    app_uuid = _coerce_uuid(application_id)

    row = (
        db.query(
            PendingStageTransition,
            Application.workflow_id,
            Application.stage,
        )
        .join(Application, Application.id == PendingStageTransition.application_id)
        .filter(
            PendingStageTransition.organization_id == ctx.organization_id,
            Application.organization_id == ctx.organization_id,
            PendingStageTransition.application_id == app_uuid,
        )
        .first()
    )

    if not row:
        raise PendingApprovalNotFoundError()

    pending, workflow_id, current_stage = row

    now = datetime.now(timezone.utc)
    initiated_at = _coerce_dt(pending.initiated_at)
    age_seconds = int(max(0.0, (now - initiated_at).total_seconds()))

    return {
        "application_id": pending.application_id,
        "workflow_id": workflow_id,
        "current_stage": current_stage,
        "target_stage": pending.target_stage,
        "initiated_by_user_id": pending.initiated_by_user_id,
        "initiated_at": initiated_at,
        "age_seconds": age_seconds,
    }


def approval_summary(db: Session, ctx: RequestContext):
    now = datetime.now(timezone.utc)

    total, oldest_initiated_at = (
        db.query(
            func.count(PendingStageTransition.id),
            func.min(PendingStageTransition.initiated_at),
        )
        .filter(PendingStageTransition.organization_id == ctx.organization_id)
        .one()
    )
    total = int(total or 0)

    if total <= 0:
        avg_age = 0.0
        oldest = 0
    else:
        oldest_dt = _coerce_dt(oldest_initiated_at)
        oldest = int(max(0.0, (now - oldest_dt).total_seconds()))

        dialect = db.get_bind().dialect.name

        avg_seconds: float | None = None
        try:
            if dialect == "sqlite":
                # SQLite: use julianday math to compute epoch deltas.
                now_naive = now.replace(tzinfo=None)
                avg_expr = func.avg(
                    (
                        func.julianday(now_naive)
                        - func.julianday(PendingStageTransition.initiated_at)
                    )
                    * 86400.0
                )
                avg_seconds = (
                    db.query(avg_expr)
                    .filter(
                        PendingStageTransition.organization_id == ctx.organization_id
                    )
                    .scalar()
                )
            else:
                # Postgres (and most others): extract seconds from an interval.
                avg_expr = func.avg(
                    func.extract(
                        "epoch",
                        sa.bindparam("now", now) - PendingStageTransition.initiated_at,
                    )
                )
                avg_seconds = (
                    db.query(avg_expr)
                    .filter(
                        PendingStageTransition.organization_id == ctx.organization_id
                    )
                    .params(now=now)
                    .scalar()
                )
        except Exception:
            avg_seconds = None

        if avg_seconds is None:
            # Fallback: bounded iteration (no .all()) for dialects lacking support.
            MAX_FALLBACK_ROWS = 10_000
            if total <= MAX_FALLBACK_ROWS:
                total_seconds = 0.0
                for (initiated_at,) in (
                    db.query(PendingStageTransition.initiated_at)
                    .filter(
                        PendingStageTransition.organization_id == ctx.organization_id
                    )
                    .yield_per(1000)
                ):
                    initiated_at = _coerce_dt(initiated_at)
                    total_seconds += max(0.0, (now - initiated_at).total_seconds())
                avg_seconds = total_seconds / float(total)
            else:
                avg_seconds = 0.0

        avg_age = float(max(0.0, avg_seconds))

    logger.info(
        "pending_approvals_summarized",
        extra={
            "action": "pending_approvals_summarized",
            "correlation_id": correlation_id_var.get("-"),
            "organization_id": str(ctx.organization_id),
            "actor_id": str(ctx.actor_id),
            "total_pending": total,
        },
    )

    return {
        "total_pending": total,
        "avg_pending_age_seconds": avg_age,
        "oldest_pending_age_seconds": oldest,
    }
