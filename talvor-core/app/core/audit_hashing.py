from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def _coerce_dt(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def canonical_audit_payload(audit_log_row) -> bytes:
    """Return deterministic bytes for hashing an audit log.

    Includes only stable, semantic fields. `payload` is canonicalized JSON.
    """

    payload_raw = getattr(audit_log_row, "payload", None)
    payload_value: Any

    if payload_raw is None:
        payload_value = None
    elif isinstance(payload_raw, (dict, list, int, float, bool)):
        payload_value = payload_raw
    else:
        payload_str = str(payload_raw)
        try:
            payload_value = json.loads(payload_str)
        except Exception:
            payload_value = payload_str

    created_at = getattr(audit_log_row, "created_at", None)
    if created_at is None:
        created_at_iso = ""
    else:
        created_at_iso = _coerce_dt(created_at).isoformat()

    body = {
        "organization_id": str(getattr(audit_log_row, "organization_id", "")),
        "actor_id": str(getattr(audit_log_row, "actor_id", "") or ""),
        "entity_type": str(getattr(audit_log_row, "entity_type", "") or ""),
        "entity_id": str(getattr(audit_log_row, "entity_id", "") or ""),
        "action": str(getattr(audit_log_row, "action", "") or ""),
        "payload": payload_value,
        "created_at": created_at_iso,
        "seq": int(getattr(audit_log_row, "seq", 0) or 0),
    }

    return _canonical_json(body).encode("utf-8")


def compute_hash(prev_hash: str | None, canonical_bytes: bytes) -> str:
    prefix = (prev_hash or "").encode("utf-8")
    h = hashlib.sha256()
    h.update(prefix)
    h.update(b"\n")
    h.update(canonical_bytes)
    return h.hexdigest()
