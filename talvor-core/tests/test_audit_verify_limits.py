from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.core.audit_hashing import canonical_audit_payload, compute_hash
from app.domain.audit.models import AuditLog
from app.services.audit_service import verify_audit_chain


def _seed_audit_chain(db, *, organization_id, actor_id: str, count: int) -> None:
    prev: str | None = None
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)

    rows: list[AuditLog] = []
    for seq in range(1, count + 1):
        row = AuditLog(
            id=uuid.uuid4(),
            organization_id=organization_id,
            actor_id=actor_id,
            entity_type="test",
            entity_id="1",
            action="test",
            payload="{}",
            created_at=base + timedelta(seconds=seq),
            seq=seq,
            prev_hash=prev,
            hash="",
        )
        row.hash = compute_hash(prev, canonical_audit_payload(row))
        prev = row.hash
        rows.append(row)

    # Fast insert; all fields are already populated.
    db.bulk_save_objects(rows)
    db.commit()


def test_verify_limit_none_without_rows_defaults_to_1000(db, ctx):
    _seed_audit_chain(
        db,
        organization_id=ctx.organization_id,
        actor_id=str(ctx.actor_id),
        count=1105,
    )

    result = verify_audit_chain(db, ctx, limit=None, rows=None)
    assert result["ok"] is True
    assert result["checked"] == 1000


def test_verify_limit_caps_at_10000(db, ctx):
    _seed_audit_chain(
        db,
        organization_id=ctx.organization_id,
        actor_id=str(ctx.actor_id),
        count=10010,
    )

    result = verify_audit_chain(db, ctx, limit=20000)
    assert result["ok"] is True
    assert result["checked"] == 10000
