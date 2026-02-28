from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.audit_hashing import canonical_audit_payload, compute_hash
from app.core.request_context import RequestContext
from app.domain.audit.models import AuditLog
from app.domain.organization.models import Organization


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _payload_to_text(payload: Any) -> str | None:
    if payload is None:
        return None
    if isinstance(payload, str):
        return payload
    return json.dumps(payload, default=str)


def append_audit_log(
    db: Session,
    ctx: RequestContext,
    *,
    entity_type: str,
    entity_id: str,
    action: str,
    payload: Any = None,
    created_at: datetime | None = None,
) -> AuditLog:
    """Append an audit log entry with tamper-evident hash chaining.

    Chaining is per-organization. Sequence and hash are computed inside the
    current transaction.
    """

    # Serialize concurrent writers for the same org (especially important for
    # the first audit row where there is no prior audit_log row to lock).
    db.query(Organization.id).filter(
        Organization.id == ctx.organization_id
    ).with_for_update().one()

    last = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == ctx.organization_id)
        .order_by(AuditLog.seq.desc())
        .with_for_update()
        .first()
    )

    next_seq = 1 if last is None else int(last.seq) + 1
    prev_hash = None if last is None else str(last.hash)

    if created_at is not None and os.getenv("ENV", "dev").lower() == "prod":
        raise ValueError("created_at override is not allowed in prod")

    effective_created_at = _now_utc() if created_at is None else created_at
    if effective_created_at.tzinfo is None:
        effective_created_at = effective_created_at.replace(tzinfo=timezone.utc)
    else:
        effective_created_at = effective_created_at.astimezone(timezone.utc)

    log = AuditLog(
        organization_id=ctx.organization_id,
        actor_id=str(ctx.actor_id) if ctx.actor_id else None,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        payload=_payload_to_text(payload),
        created_at=effective_created_at,
        seq=next_seq,
        prev_hash=prev_hash,
        hash="",  # computed below
    )

    canonical = canonical_audit_payload(log)
    log.hash = compute_hash(prev_hash, canonical)

    db.add(log)
    # Ensure subsequent audit appends in the same transaction see this row,
    # so sequence numbers remain unique.
    db.flush()
    return log


class AuditVerificationError(Exception):
    def __init__(self, *, seq: int, audit_log_id: str, reason: str):
        super().__init__(reason)
        self.seq = seq
        self.audit_log_id = audit_log_id
        self.reason = reason


def verify_audit_chain(
    db: Session,
    ctx: RequestContext,
    *,
    limit: int | None = 1000,
    rows: list[AuditLog] | None = None,
) -> dict[str, Any]:
    """Verify audit chain integrity for the current organization.

    If limit is set, verifies the latest `limit` rows (plus the immediately
    preceding row to seed the chain).
    """

    limit_value: int | None
    if limit is None:
        # Full-chain verification is only allowed for internal callers that
        # provide an explicit row set.
        limit_value = None if rows is not None else 1000
    else:
        limit_value = max(1, min(int(limit), 10_000))

    if rows is not None:
        rows_list = list(rows)
        if not rows_list:
            return {
                "ok": True,
                "checked": 0,
                "first_seq": None,
                "last_seq": None,
                "error": None,
            }

        rows_list.sort(key=lambda r: int(r.seq))
        if limit_value is not None and len(rows_list) > limit_value:
            rows_list = rows_list[-limit_value:]

        start_seq = int(rows_list[0].seq)

        prev_hash: str | None = None
        if start_seq > 1:
            prev_row = (
                db.query(AuditLog.hash)
                .filter(
                    AuditLog.organization_id == ctx.organization_id,
                    AuditLog.seq == (start_seq - 1),
                )
                .first()
            )
            prev_hash = None if not prev_row else str(prev_row[0])

        expected_seq = start_seq
        checked = 0

        for row in rows_list:
            if int(row.seq) != expected_seq:
                return {
                    "ok": False,
                    "checked": checked,
                    "first_seq": start_seq,
                    "last_seq": expected_seq - 1 if checked else None,
                    "error": {
                        "seq": int(row.seq),
                        "audit_log_id": str(row.id),
                        "reason": "non_contiguous_sequence",
                    },
                }

            if (row.prev_hash or None) != (prev_hash or None):
                return {
                    "ok": False,
                    "checked": checked,
                    "first_seq": start_seq,
                    "last_seq": expected_seq - 1 if checked else None,
                    "error": {
                        "seq": int(row.seq),
                        "audit_log_id": str(row.id),
                        "reason": "prev_hash_mismatch",
                    },
                }

            canonical = canonical_audit_payload(row)
            expected_hash = compute_hash(prev_hash, canonical)

            if str(row.hash) != expected_hash:
                return {
                    "ok": False,
                    "checked": checked,
                    "first_seq": start_seq,
                    "last_seq": expected_seq - 1 if checked else None,
                    "error": {
                        "seq": int(row.seq),
                        "audit_log_id": str(row.id),
                        "reason": "hash_mismatch",
                    },
                }

            prev_hash = str(row.hash)
            expected_seq += 1
            checked += 1

        return {
            "ok": True,
            "checked": checked,
            "first_seq": start_seq,
            "last_seq": int(rows_list[-1].seq) if rows_list else None,
            "error": None,
        }

    max_seq_row = (
        db.query(AuditLog.seq)
        .filter(AuditLog.organization_id == ctx.organization_id)
        .order_by(AuditLog.seq.desc())
        .first()
    )
    if not max_seq_row:
        return {
            "ok": True,
            "checked": 0,
            "first_seq": None,
            "last_seq": None,
            "error": None,
        }

    max_seq = int(max_seq_row[0])
    # At this point limit_value is always an int (unlimited is only allowed
    # when rows is provided).
    assert limit_value is not None
    start_seq = max(1, max_seq - limit_value + 1)

    prev_hash: str | None = None
    if start_seq > 1:
        prev_row = (
            db.query(AuditLog.hash)
            .filter(
                AuditLog.organization_id == ctx.organization_id,
                AuditLog.seq == (start_seq - 1),
            )
            .first()
        )
        prev_hash = None if not prev_row else str(prev_row[0])

    rows = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == ctx.organization_id,
            AuditLog.seq >= start_seq,
        )
        .order_by(AuditLog.seq.asc())
        .all()
    )

    expected_seq = start_seq
    checked = 0

    for row in rows:
        if int(row.seq) != expected_seq:
            return {
                "ok": False,
                "checked": checked,
                "first_seq": start_seq,
                "last_seq": expected_seq - 1 if checked else None,
                "error": {
                    "seq": int(row.seq),
                    "audit_log_id": str(row.id),
                    "reason": "non_contiguous_sequence",
                },
            }

        if (row.prev_hash or None) != (prev_hash or None):
            return {
                "ok": False,
                "checked": checked,
                "first_seq": start_seq,
                "last_seq": expected_seq - 1 if checked else None,
                "error": {
                    "seq": int(row.seq),
                    "audit_log_id": str(row.id),
                    "reason": "prev_hash_mismatch",
                },
            }

        canonical = canonical_audit_payload(row)
        expected_hash = compute_hash(prev_hash, canonical)

        if str(row.hash) != expected_hash:
            return {
                "ok": False,
                "checked": checked,
                "first_seq": start_seq,
                "last_seq": expected_seq - 1 if checked else None,
                "error": {
                    "seq": int(row.seq),
                    "audit_log_id": str(row.id),
                    "reason": "hash_mismatch",
                },
            }

        prev_hash = str(row.hash)
        expected_seq += 1
        checked += 1

    return {
        "ok": True,
        "checked": checked,
        "first_seq": start_seq,
        "last_seq": int(rows[-1].seq) if rows else None,
        "error": None,
    }
