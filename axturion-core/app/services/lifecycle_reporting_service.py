from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from statistics import median
from typing import Any
from uuid import UUID

from sqlalchemy import String, cast, func
from sqlalchemy.orm import Session

from app.core.request_context import RequestContext
from app.domain.application.models import Application
from app.domain.audit.models import AuditLog
from app.domain.workflow.models import Workflow
from app.reporting.window import ReportingWindow


class WorkflowNotFoundError(Exception):
    pass


_STAGE_CHANGE_ACTIONS: tuple[str, ...] = (
    "stage_changed",
    # 4-eyes stage transitions use a different audit action name.
    "stage_transition_approved",
)


def _transition_actions() -> set[str]:
    return {"stage_changed", "stage_transition_approved"}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_dt(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_stage_change(
    action: str | None, payload_text: str | None
) -> tuple[str, str] | None:
    if not action:
        return None
    if not payload_text:
        return None

    if action == "stage_changed":
        # Historical payload format: "from->to".
        if "->" not in payload_text:
            return None
        from_stage, to_stage = payload_text.split("->", 1)
        from_stage = from_stage.strip()
        to_stage = to_stage.strip()
        if not from_stage or not to_stage:
            return None
        return (from_stage, to_stage)

    # Structured payload (JSON) expected for stage_transition_approved.
    try:
        parsed = json.loads(payload_text)
    except Exception:
        return None
    if not isinstance(parsed, dict):
        return None

    from_stage = parsed.get("from_stage")
    to_stage = parsed.get("to_stage")
    if not isinstance(from_stage, str) or not isinstance(to_stage, str):
        return None
    from_stage = from_stage.strip()
    to_stage = to_stage.strip()
    if not from_stage or not to_stage:
        return None
    return (from_stage, to_stage)


def _nearest_rank_percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    if p <= 0.0:
        return float(sorted_values[0])
    if p >= 1.0:
        return float(sorted_values[-1])

    k = int(math.ceil(p * len(sorted_values)))
    idx = max(0, min(len(sorted_values) - 1, k - 1))
    return float(sorted_values[idx])


def list_stage_aging(
    db: Session,
    ctx: RequestContext,
    *,
    workflow_id: UUID | None = None,
    window: ReportingWindow,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    transition_actions = _transition_actions()

    last_transition_q = db.query(
        AuditLog.entity_id.label("application_id"),
        func.max(AuditLog.created_at).label("last_transition_at"),
    ).filter(
        AuditLog.organization_id == ctx.organization_id,
        AuditLog.entity_type == "application",
        AuditLog.action.in_(transition_actions),
    )

    if window.is_active():
        if window.from_datetime is not None:
            last_transition_q = last_transition_q.filter(
                AuditLog.created_at >= window.from_datetime
            )
        if window.to_datetime is not None:
            last_transition_q = last_transition_q.filter(
                AuditLog.created_at < window.to_datetime
            )

    last_transition_sq = last_transition_q.group_by(AuditLog.entity_id).subquery(
        "last_transition"
    )

    q = (
        db.query(
            Application.id,
            Application.workflow_id,
            Application.stage,
            Application.created_at,
            last_transition_sq.c.last_transition_at,
        )
        .outerjoin(
            last_transition_sq,
            func.replace(last_transition_sq.c.application_id, "-", "")
            == func.replace(cast(Application.id, String), "-", ""),
        )
        .filter(
            Application.organization_id == ctx.organization_id,
            Application.status != "closed",
        )
        .order_by(Application.created_at.desc(), Application.id.asc())
    )

    if workflow_id is not None:
        q = q.filter(Application.workflow_id == workflow_id)

    rows = q.offset(offset).limit(limit).all()
    if not rows:
        return []

    now = _now_utc()
    items: list[dict[str, Any]] = []
    for app_id, wf_id, stage, created_at, last_transition_at in rows:
        created = _coerce_dt(created_at) or now
        last_change = _coerce_dt(last_transition_at)
        basis = last_change if last_change is not None else created
        age_seconds = int(max(0.0, (now - basis).total_seconds()))

        items.append(
            {
                "application_id": app_id,
                "workflow_id": wf_id,
                "current_stage": str(stage),
                "age_seconds": age_seconds,
            }
        )

    return items


def stage_duration_summary(
    db: Session,
    ctx: RequestContext,
    *,
    workflow_id: UUID,
) -> list[dict[str, Any]]:
    workflow = (
        db.query(Workflow)
        .filter(
            Workflow.id == workflow_id,
            Workflow.organization_id == ctx.organization_id,
        )
        .first()
    )
    if not workflow:
        raise WorkflowNotFoundError()

    apps = (
        db.query(Application.id, Application.closed_at)
        .filter(
            Application.organization_id == ctx.organization_id,
            Application.workflow_id == workflow_id,
            Application.status == "closed",
        )
        .all()
    )
    if not apps:
        return []

    closed_at_by_id: dict[str, datetime] = {}
    app_ids: list[str] = []
    for app_id, closed_at in apps:
        closed = _coerce_dt(closed_at)
        if closed is None:
            continue
        app_ids.append(str(app_id))
        closed_at_by_id[str(app_id)] = closed

    if not app_ids:
        return []

    rows = (
        db.query(
            AuditLog.entity_id,
            AuditLog.action,
            AuditLog.payload,
            AuditLog.created_at,
            AuditLog.seq,
        )
        .filter(
            AuditLog.organization_id == ctx.organization_id,
            AuditLog.entity_type == "application",
            AuditLog.action.in_(_STAGE_CHANGE_ACTIONS),
            AuditLog.entity_id.in_(app_ids),
        )
        .order_by(
            AuditLog.entity_id.asc(), AuditLog.created_at.asc(), AuditLog.seq.asc()
        )
        .all()
    )

    durations_by_stage: dict[str, list[float]] = {}

    current_app_id: str | None = None
    events: list[tuple[datetime, str, str]] = []

    def flush_events(app_id: str, events_to_flush: list[tuple[datetime, str, str]]):
        if not events_to_flush:
            return
        closed_at = closed_at_by_id.get(app_id)
        if closed_at is None:
            return

        # Only contiguous durations between stage changes.
        for i in range(len(events_to_flush) - 1):
            start_at, _from_stage, to_stage = events_to_flush[i]
            end_at, _n_from, _n_to = events_to_flush[i + 1]
            duration = (end_at - start_at).total_seconds()
            if duration <= 0:
                continue
            durations_by_stage.setdefault(to_stage, []).append(float(duration))

        # Final stage: end at closed_at.
        last_at, _from_stage, last_to = events_to_flush[-1]
        final_duration = (closed_at - last_at).total_seconds()
        if final_duration > 0:
            durations_by_stage.setdefault(last_to, []).append(float(final_duration))

    for entity_id, action, payload, created_at, _seq in rows:
        app_id = str(entity_id)
        if current_app_id is None:
            current_app_id = app_id

        if app_id != current_app_id:
            flush_events(current_app_id, events)
            events = []
            current_app_id = app_id

        ts = _coerce_dt(created_at)
        if ts is None:
            continue

        parsed = _parse_stage_change(str(action), payload)
        if parsed is None:
            continue
        from_stage, to_stage = parsed
        events.append((ts, from_stage, to_stage))

    if current_app_id is not None:
        flush_events(current_app_id, events)

    items: list[dict[str, Any]] = []
    for stage, durations in sorted(durations_by_stage.items(), key=lambda kv: kv[0]):
        if not durations:
            continue
        durations_sorted = sorted(float(x) for x in durations if x is not None)
        if not durations_sorted:
            continue

        count = len(durations_sorted)
        avg = float(sum(durations_sorted) / float(count))
        med = float(median(durations_sorted))
        p90 = _nearest_rank_percentile(durations_sorted, 0.90)

        items.append(
            {
                "stage": stage,
                "count": int(count),
                "avg_duration_seconds": avg,
                "median_duration_seconds": med,
                "p90_duration_seconds": p90,
            }
        )

    return items


def time_to_close_stats(
    db: Session,
    ctx: RequestContext,
    *,
    workflow_id: UUID | None = None,
    result: str | None = None,
) -> dict[str, Any]:
    q = (
        db.query(Application.created_at, Application.closed_at)
        .filter(
            Application.organization_id == ctx.organization_id,
            Application.status == "closed",
            Application.created_at.isnot(None),
            Application.closed_at.isnot(None),
        )
        .order_by(Application.created_at.asc())
    )

    if workflow_id is not None:
        q = q.filter(Application.workflow_id == workflow_id)
    if result is not None:
        q = q.filter(Application.result == str(result))

    durations: list[float] = []
    for created_at, closed_at in q.all():
        created = _coerce_dt(created_at)
        closed = _coerce_dt(closed_at)
        if created is None or closed is None:
            continue
        seconds = (closed - created).total_seconds()
        if seconds < 0:
            continue
        durations.append(float(seconds))

    if not durations:
        return {
            "count": 0,
            "avg_seconds": 0.0,
            "median_seconds": 0.0,
            "p90_seconds": 0.0,
            "min_seconds": 0,
            "max_seconds": 0,
        }

    durations_sorted = sorted(durations)
    count = len(durations_sorted)
    avg = float(sum(durations_sorted) / float(count))
    med = float(median(durations_sorted))
    p90 = _nearest_rank_percentile(durations_sorted, 0.90)
    min_s = int(durations_sorted[0])
    max_s = int(durations_sorted[-1])

    return {
        "count": int(count),
        "avg_seconds": avg,
        "median_seconds": med,
        "p90_seconds": p90,
        "min_seconds": min_s,
        "max_seconds": max_s,
    }
