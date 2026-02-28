from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_request_context, require_scope
from app.api.schemas.candidates import (
    CandidateCreateRequest,
    CandidateResponse,
    CandidateUpdateRequest,
)
from app.core.db import get_db
from app.core.request_context import RequestContext
from app.core.scopes import CANDIDATE_CREATE, CANDIDATE_READ, CANDIDATE_UPDATE
from app.services.candidate_service import (
    CandidateEmailConflictError,
    CandidateNotFoundError,
    OrganizationAccessError,
    create_candidate,
    get_candidate,
    list_candidates,
    update_candidate,
)


router = APIRouter(tags=["candidates"])


@router.post(
    "",
    summary="Create candidate",
    description=(
        "Creates a candidate record in the caller's organization.\n\n"
        "Authorization: Requires candidate create scope.\n"
        "Uniqueness: Candidate email must be unique within the organization."
    ),
    response_model=CandidateResponse,
)
def create(
    body: CandidateCreateRequest,
    _: None = Depends(require_scope(CANDIDATE_CREATE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    try:
        candidate = create_candidate(
            db,
            ctx,
            full_name=body.full_name,
            email=body.email,
            phone=body.phone,
            notes=body.notes,
        )
    except CandidateEmailConflictError as exc:
        raise HTTPException(
            status_code=400,
            detail="Candidate email already exists",
        ) from exc

    return CandidateResponse(
        id=candidate.id,
        full_name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        notes=candidate.notes,
        created_at=candidate.created_at,
    )


@router.patch(
    "/{candidate_id}",
    summary="Update candidate",
    description=(
        "Updates a candidate in the caller's organization.\n\n"
        "Authorization: Requires candidate update scope.\n"
        "Organization boundary: Cross-organization access is forbidden.\n"
        "Uniqueness: Candidate email must remain unique within the organization."
    ),
    response_model=CandidateResponse,
)
def update(
    candidate_id: str,
    body: CandidateUpdateRequest,
    _: None = Depends(require_scope(CANDIDATE_UPDATE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    try:
        candidate = update_candidate(
            db,
            ctx,
            candidate_id=candidate_id,
            full_name=body.full_name,
            email=body.email,
            phone=body.phone,
            notes=body.notes,
        )
    except CandidateNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Candidate not found") from exc
    except OrganizationAccessError as exc:
        raise HTTPException(
            status_code=403,
            detail="Cross-organization access is forbidden",
        ) from exc
    except CandidateEmailConflictError as exc:
        raise HTTPException(
            status_code=400,
            detail="Candidate email already exists",
        ) from exc

    return CandidateResponse(
        id=candidate.id,
        full_name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        notes=candidate.notes,
        created_at=candidate.created_at,
    )


@router.get(
    "/{candidate_id}",
    summary="Get candidate",
    description=(
        "Retrieves a candidate by identifier within the caller's organization.\n\n"
        "Authorization: Requires candidate read scope.\n"
        "Organization boundary: Only candidates belonging to the current organization are accessible."
    ),
    response_model=CandidateResponse,
)
def read(
    candidate_id: str,
    _: None = Depends(require_scope(CANDIDATE_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    try:
        candidate = get_candidate(db, ctx, candidate_id)
    except CandidateNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Candidate not found") from exc

    return CandidateResponse(
        id=candidate.id,
        full_name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        notes=candidate.notes,
        created_at=candidate.created_at,
    )


@router.get(
    "",
    summary="List candidates",
    description=(
        "Lists candidates in the caller's organization.\n\n"
        "Authorization: Requires candidate read scope.\n"
        "Organization boundary: Only returns candidates for the current organization.\n"
        "Pagination: Supports limit/offset."
    ),
    response_model=list[CandidateResponse],
)
def list_all(
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(require_scope(CANDIDATE_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    candidates = list_candidates(db, ctx, limit=limit, offset=offset)
    return [
        CandidateResponse(
            id=c.id,
            full_name=c.name,
            email=c.email,
            phone=c.phone,
            notes=c.notes,
            created_at=c.created_at,
        )
        for c in candidates
    ]
