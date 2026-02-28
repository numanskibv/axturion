from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_request_context, require_scope
from app.api.schemas.approvals import PendingApprovalItem
from app.core.db import get_db
from app.core.request_context import RequestContext
from app.core.scopes import REPORTING_READ
from app.services.approvals_service import (
    PendingApprovalNotFoundError,
    get_pending_for_application,
    list_pending_approvals,
)


router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get(
    "/pending",
    summary="List pending stage transition approvals",
    description=(
        "Lists pending stage transition approvals for the caller's organization.\n\n"
        "Authorization: Requires reporting read scope.\n"
        "Organization boundary: Only returns approvals within the current organization.\n"
        "Pagination: Supports limit/offset."
    ),
    response_model=list[PendingApprovalItem],
)
def list_pending(
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(require_scope(REPORTING_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    items = list_pending_approvals(db, ctx, limit=limit, offset=offset)
    return [PendingApprovalItem(**item) for item in items]


@router.get(
    "/pending/{application_id}",
    summary="Get pending approval for an application",
    description=(
        "Retrieves the pending stage transition approval record for a single application, if present.\n\n"
        "Authorization: Requires reporting read scope.\n"
        "Organization boundary: The application must belong to the current organization."
    ),
    response_model=PendingApprovalItem,
)
def get_pending(
    application_id: str,
    _: None = Depends(require_scope(REPORTING_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    try:
        item = get_pending_for_application(db, ctx, application_id)
    except PendingApprovalNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail="Pending approval not found"
        ) from exc

    return PendingApprovalItem(**item)
