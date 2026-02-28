from __future__ import annotations

import json
import zipfile
from datetime import datetime
from io import BytesIO
from typing import Any

from sqlalchemy.orm import Session

from app.core.request_context import RequestContext
from app.domain.application.models import Application
from app.domain.audit.models import AuditLog
from app.domain.candidate.models import Candidate
from app.domain.job.models import Job
from app.services.approvals_service import list_pending_approvals
from app.services.audit_service import verify_audit_chain


MAX_AUDIT_ENTRIES = 200_000


def _json_default(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def generate_compliance_bundle(db: Session, ctx: RequestContext) -> bytes:
    total_count = (
        db.query(AuditLog.id)
        .filter(AuditLog.organization_id == ctx.organization_id)
        .count()
    )

    max_seq_row = (
        db.query(AuditLog.seq)
        .filter(AuditLog.organization_id == ctx.organization_id)
        .order_by(AuditLog.seq.desc())
        .first()
    )
    max_seq = 0 if not max_seq_row else int(max_seq_row[0])

    export_truncated = int(total_count) > int(MAX_AUDIT_ENTRIES)
    if export_truncated and max_seq > 0:
        start_seq = max(1, max_seq - int(MAX_AUDIT_ENTRIES) + 1)
    else:
        start_seq = 1

    audit_query = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == ctx.organization_id,
            AuditLog.seq >= start_seq,
        )
        .order_by(AuditLog.seq.asc())
        .yield_per(1000)
    )
    audit_rows = list(audit_query)

    verification = verify_audit_chain(db, ctx, limit=None, rows=audit_rows)
    verification = {
        **verification,
        "export_truncated": bool(export_truncated),
        "exported_count": int(len(audit_rows)),
        "total_count": int(total_count),
    }

    pending_approvals = list_pending_approvals(db, ctx, limit=200, offset=0)

    total_jobs = (
        db.query(Job.id).filter(Job.organization_id == ctx.organization_id).count()
    )
    total_candidates = (
        db.query(Candidate.id)
        .filter(Candidate.organization_id == ctx.organization_id)
        .count()
    )
    total_applications = (
        db.query(Application.id)
        .filter(Application.organization_id == ctx.organization_id)
        .count()
    )
    closed_applications = (
        db.query(Application.id)
        .filter(
            Application.organization_id == ctx.organization_id,
            Application.status == "closed",
        )
        .count()
    )
    open_applications = max(0, int(total_applications) - int(closed_applications))

    lifecycle_summary = {
        "total_jobs": int(total_jobs),
        "total_candidates": int(total_candidates),
        "total_applications": int(total_applications),
        "open_applications": int(open_applications),
        "closed_applications": int(closed_applications),
    }

    audit_chain = [
        {
            "id": str(r.id),
            "organization_id": str(r.organization_id),
            "seq": int(r.seq),
            "prev_hash": r.prev_hash,
            "hash": r.hash,
            "actor_id": r.actor_id,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "action": r.action,
            "payload": r.payload,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in audit_rows
    ]

    buf = BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "audit_chain.json",
            json.dumps(
                audit_chain,
                ensure_ascii=False,
                separators=(",", ":"),
                default=_json_default,
            ),
        )
        zf.writestr(
            "audit_verification.json",
            json.dumps(
                verification,
                ensure_ascii=False,
                separators=(",", ":"),
                default=_json_default,
            ),
        )
        zf.writestr(
            "approvals_snapshot.json",
            json.dumps(
                pending_approvals,
                ensure_ascii=False,
                separators=(",", ":"),
                default=_json_default,
            ),
        )
        zf.writestr(
            "lifecycle_summary.json",
            json.dumps(
                lifecycle_summary,
                ensure_ascii=False,
                separators=(",", ":"),
                default=_json_default,
            ),
        )

    return buf.getvalue()
