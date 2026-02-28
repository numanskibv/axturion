"""audit hash chaining

Revision ID: 4d6b1a8c2f41
Revises: 1f3a0a2b9c10
Create Date: 2026-02-28

"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "4d6b1a8c2f41"
down_revision = "1f3a0a2b9c10"
branch_labels = None
depends_on = None


def _coerce_dt(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _canonical_json(value) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def _canonical_audit_bytes(
    *,
    organization_id,
    actor_id,
    entity_type,
    entity_id,
    action,
    payload,
    created_at,
    seq,
) -> bytes:
    payload_value = None
    if payload is None:
        payload_value = None
    else:
        payload_str = str(payload)
        try:
            payload_value = json.loads(payload_str)
        except Exception:
            payload_value = payload_str

    created_iso = "" if created_at is None else _coerce_dt(created_at).isoformat()

    body = {
        "organization_id": str(organization_id),
        "actor_id": str(actor_id or ""),
        "entity_type": str(entity_type or ""),
        "entity_id": str(entity_id or ""),
        "action": str(action or ""),
        "payload": payload_value,
        "created_at": created_iso,
        "seq": int(seq or 0),
    }

    return _canonical_json(body).encode("utf-8")


def _compute_hash(prev_hash: str | None, canonical_bytes: bytes) -> str:
    h = hashlib.sha256()
    h.update((prev_hash or "").encode("utf-8"))
    h.update(b"\n")
    h.update(canonical_bytes)
    return h.hexdigest()


def upgrade() -> None:
    op.add_column("audit_log", sa.Column("actor_id", sa.String(), nullable=True))

    op.add_column(
        "audit_log", sa.Column("prev_hash", sa.String(length=64), nullable=True)
    )
    op.add_column("audit_log", sa.Column("hash", sa.String(length=64), nullable=True))
    op.add_column("audit_log", sa.Column("seq", sa.Integer(), nullable=True))

    bind = op.get_bind()

    audit_log = sa.table(
        "audit_log",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("organization_id", postgresql.UUID(as_uuid=True)),
        sa.column("actor_id", sa.String()),
        sa.column("entity_type", sa.String()),
        sa.column("entity_id", sa.String()),
        sa.column("action", sa.String()),
        sa.column("payload", sa.Text()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("prev_hash", sa.String(length=64)),
        sa.column("hash", sa.String(length=64)),
        sa.column("seq", sa.Integer()),
    )

    org_rows = bind.execute(sa.text("SELECT DISTINCT organization_id FROM audit_log"))
    org_ids = [row[0] for row in org_rows.fetchall()]

    for org_id in org_ids:
        rows = bind.execute(
            sa.select(
                audit_log.c.id,
                audit_log.c.organization_id,
                audit_log.c.actor_id,
                audit_log.c.entity_type,
                audit_log.c.entity_id,
                audit_log.c.action,
                audit_log.c.payload,
                audit_log.c.created_at,
            )
            .where(audit_log.c.organization_id == org_id)
            .order_by(audit_log.c.created_at.asc(), audit_log.c.id.asc())
        ).fetchall()

        prev = None
        seq = 0
        for r in rows:
            seq += 1
            canonical = _canonical_audit_bytes(
                organization_id=r.organization_id,
                actor_id=r.actor_id,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                action=r.action,
                payload=r.payload,
                created_at=r.created_at,
                seq=seq,
            )
            h = _compute_hash(prev, canonical)

            bind.execute(
                sa.update(audit_log)
                .where(audit_log.c.id == r.id)
                .values(seq=seq, prev_hash=prev, hash=h)
            )
            prev = h

    op.alter_column("audit_log", "hash", nullable=False)
    op.alter_column("audit_log", "seq", nullable=False)

    op.create_unique_constraint(
        "uq_audit_org_seq", "audit_log", ["organization_id", "seq"]
    )
    op.create_index(
        "ix_audit_org_seq", "audit_log", ["organization_id", "seq"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_audit_org_seq", table_name="audit_log")
    op.drop_constraint("uq_audit_org_seq", "audit_log", type_="unique")

    op.drop_column("audit_log", "seq")
    op.drop_column("audit_log", "hash")
    op.drop_column("audit_log", "prev_hash")
    op.drop_column("audit_log", "actor_id")
