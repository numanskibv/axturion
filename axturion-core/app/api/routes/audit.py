from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_request_context, require_scope
from app.api.schemas.audit import AuditVerifyResponse
from app.core.db import get_db
from app.core.request_context import RequestContext
from app.core.scopes import AUDIT_READ
from app.services.audit_service import verify_audit_chain


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get(
    "/verify",
    response_model=AuditVerifyResponse,
    summary="Verify audit hash chain",
    description="Verifies the tamper-evident audit hash chain for the current organization.",
)
def verify(
    limit: int = Query(default=1000, ge=1, le=10_000),
    db: Session = Depends(get_db),
    ctx: RequestContext = Depends(get_request_context),
    _: None = Depends(require_scope(AUDIT_READ)),
):
    return verify_audit_chain(db, ctx, limit=limit)
