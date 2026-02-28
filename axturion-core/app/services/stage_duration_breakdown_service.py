from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.request_context import RequestContext
from app.domain.application.models import Application
from app.domain.audit.models import AuditLog
from app.reporting.window import ReportingWindow


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_dt(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _transition_actions() -> set[str]:
    return {"stage_changed", "stage_transition_approved"}


def _safe_json_dict(payload_text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(payload_text)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _parse_transition_payload(
    *, action: str | None, payload_text: str | None
) -> tuple[str | None, str] | None:
    if not action or not payload_text:
        return None

    payload_text = str(payload_text)

    if action == "stage_changed" and "->" in payload_text:
        from_stage, to_stage = payload_text.split("->", 1)
        from_stage = from_stage.strip() or None
        to_stage = to_stage.strip()
        if not to_stage:
            return None
        return (from_stage, to_stage)

    parsed = _safe_json_dict(payload_text)
    if parsed is None:
        return None

    from_stage_raw = (
        parsed.get("from_stage")
        or parsed.get("from")
        or parsed.get("fromStage")
        or parsed.get("from_stage_name")
    )
    to_stage_raw = (
        parsed.get("to_stage")
        or parsed.get("to")
        or parsed.get("toStage")
        or parsed.get("stage")
    )

    from_stage = from_stage_raw.strip() if isinstance(from_stage_raw, str) else None
    to_stage = to_stage_raw.strip() if isinstance(to_stage_raw, str) else None

    if not to_stage:
        return None

    return (from_stage or None, to_stage)


def _nearest_rank_int(sorted_values: list[int], p: float) -> int:
    if not sorted_values:
        return 0
    if p <= 0.0:
        return int(sorted_values[0])
    if p >= 1.0:
        return int(sorted_values[-1])

    k = int(math.ceil(p * len(sorted_values)))
    idx = max(0, min(len(sorted_values) - 1, k - 1))
    return int(sorted_values[idx])


def _median_int(sorted_values: list[int]) -> int:
    if not sorted_values:
        return 0
    n = len(sorted_values)
    mid = n // 2
    if n % 2 == 1:
        return int(sorted_values[mid])
    return int((sorted_values[mid - 1] + sorted_values[mid]) / 2)


def list_stage_duration_breakdown(
    db: Session,
    ctx: RequestContext,
    *,
    workflow_id: UUID,
    window: ReportingWindow,
) -> list[dict[str, Any]]:
    window.validate()

    window_from = _coerce_dt(window.from_datetime)
    window_to = _coerce_dt(window.to_datetime)

    apps = (
        db.query(
            Application.id,
            Application.stage,
            Application.created_at,
            Application.closed_at,
            Application.status,
        )
        .filter(
            Application.organization_id == ctx.organization_id,
            Application.workflow_id == workflow_id,
        )
        .order_by(Application.created_at.asc(), Application.id.asc())
        .all()
    )

    if not apps:
        return []

    app_ids: list[str] = [str(app_id) for (app_id, _stage, _created_at, _closed_at, _status) in apps]
    app_by_id: dict[str, tuple[str, datetime | None, datetime | None]] = {}
    for app_id, stage, created_at, closed_at, _status in apps:
        app_by_id[str(app_id)] = (str(stage), _coerce_dt(created_at), _coerce_dt(closed_at))

    transition_actions = _transition_actions()

    audit_q = (
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
            AuditLog.action.in_(transition_actions),
            AuditLog.entity_id.in_(app_ids),
        )
        .order_by(
            AuditLog.entity_id.asc(), AuditLog.created_at.asc(), AuditLog.seq.asc()
        )
    )

    if window_to is not None:
        audit_q = audit_q.filter(AuditLog.created_at <= window_to)

    audit_rows = audit_q.all()

    events_by_app: dict[str, list[tuple[datetime, int, str | None, str]]] = {}
    for entity_id, action, payload, created_at, seq in audit_rows:
        app_id = str(entity_id)
        ts = _coerce_dt(created_at)
        if ts is None:
            continue

        parsed = _parse_transition_payload(action=str(action) if action is not None else None, payload_text=payload)
        if parsed is None:
            continue
        from_stage, to_stage = parsed

        events_by_app.setdefault(app_id, []).append(
            (ts, int(seq) if seq is not None else 0, from_stage, to_stage)
        )

    now = _now_utc()
    durations_by_stage: dict[str, list[int]] = {}

    for app_id, (current_stage, created_at, closed_at) in app_by_id.items():
        created = created_at
        if created is None:
            continue

        start_time = created
        if window_from is not None and window_from > start_time:
            start_time = window_from

        end_bound = window_to if window_to is not None else now
        if closed_at is not None and closed_at < end_bound:
            end_bound = closed_at

        if end_bound <= start_time:
            continue

        events = events_by_app.get(app_id, [])
        events.sort(key=lambda e: (e[0], e[1]))

        # Determine active stage at start_time.
        stage_at_start: str | None = None

        last_before = None
        for e in events:
            if e[0] < start_time:
                last_before = e
            else:
                break
        if last_before is not None:
            stage_at_start = last_before[3]
        else:
            first_event = events[0] if events else None
            if first_event is not None and first_event[2]:
                stage_at_start = first_event[2]

        if not stage_at_start:
            stage_at_start = current_stage

        cursor = start_time
        active_stage = stage_at_start

        for ts, _seq, _from_stage, to_stage in events:
            if ts < start_time:
                continue
            if ts > end_bound:
                break

            duration = int(max(0.0, (ts - cursor).total_seconds()))
            if duration > 0:
                durations_by_stage.setdefault(active_stage, []).append(duration)

            active_stage = to_stage
            cursor = ts

        final_duration = int(max(0.0, (end_bound - cursor).total_seconds()))
        if final_duration > 0:
            durations_by_stage.setdefault(active_stage, []).append(final_duration)

    items: list[dict[str, Any]] = []
    for stage, durations in sorted(durations_by_stage.items(), key=lambda kv: kv[0]):
        if not durations:
            continue
        durations_sorted = sorted(int(x) for x in durations if x is not None)
        if not durations_sorted:
            continue

        items.append(
            {
                "stage": stage,
                "count": int(len(durations_sorted)),
                "median_seconds": _median_int(durations_sorted),
                "p90_seconds": _nearest_rank_int(durations_sorted, 0.90),
            }
        )

    return items
