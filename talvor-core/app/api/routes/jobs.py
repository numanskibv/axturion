from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_request_context, require_scope
from app.api.schemas.jobs import JobCreateRequest, JobResponse, JobUpdateRequest
from app.core.db import get_db
from app.core.request_context import RequestContext
from app.core.scopes import JOB_CLOSE, JOB_CREATE, JOB_READ, JOB_UPDATE
from app.services.job_service import (
    OrganizationAccessError,
    JobAlreadyClosedError,
    JobClosedError,
    JobNotFoundError,
    close_job,
    create_job,
    get_job,
    list_jobs,
    update_job,
)


router = APIRouter(tags=["jobs"])


@router.post(
    "",
    summary="Create job",
    description=(
        "Creates a job posting within the caller's organization.\n\n"
        "Authorization: Requires job create scope.\n"
        "Organization boundary: Jobs are isolated to the current organization."
    ),
    response_model=JobResponse,
)
def create(
    body: JobCreateRequest,
    _: None = Depends(require_scope(JOB_CREATE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    job = create_job(db, ctx, title=body.title, description=body.description)
    return job


@router.get(
    "",
    summary="List jobs",
    description=(
        "Lists jobs within the caller's organization.\n\n"
        "Authorization: Requires job read scope.\n"
        "Organization boundary: Only returns jobs for the current organization.\n"
        "Pagination: Supports limit/offset."
    ),
    response_model=list[JobResponse],
)
def list_all(
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(require_scope(JOB_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    return list_jobs(db, ctx, limit=limit, offset=offset)


@router.get(
    "/{job_id}",
    summary="Get job",
    description=(
        "Retrieves a job by identifier within the caller's organization.\n\n"
        "Authorization: Requires job read scope.\n"
        "Organization boundary: Cross-organization access is forbidden."
    ),
    response_model=JobResponse,
)
def read(
    job_id: str,
    _: None = Depends(require_scope(JOB_READ)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    try:
        return get_job(db, ctx, job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except OrganizationAccessError as exc:
        raise HTTPException(
            status_code=403,
            detail="Cross-organization access is forbidden",
        ) from exc


@router.patch(
    "/{job_id}",
    summary="Update job",
    description=(
        "Updates an existing job within the caller's organization.\n\n"
        "Authorization: Requires job update scope.\n"
        "Integrity: Closed jobs cannot be modified.\n"
        "Organization boundary: Cross-organization access is forbidden."
    ),
    response_model=JobResponse,
)
def update(
    job_id: str,
    body: JobUpdateRequest,
    _: None = Depends(require_scope(JOB_UPDATE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    try:
        return update_job(
            db,
            ctx,
            job_id,
            title=body.title,
            description=body.description,
        )
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except OrganizationAccessError as exc:
        raise HTTPException(
            status_code=403,
            detail="Cross-organization access is forbidden",
        ) from exc
    except JobClosedError as exc:
        raise HTTPException(status_code=400, detail="Job is closed") from exc


@router.post(
    "/{job_id}/close",
    summary="Close job",
    description=(
        "Closes a job within the caller's organization.\n\n"
        "Authorization: Requires job close scope.\n"
        "Integrity: Closing is idempotent-safe; already-closed jobs return a validation error.\n"
        "Organization boundary: Cross-organization access is forbidden."
    ),
    response_model=JobResponse,
)
def close(
    job_id: str,
    _: None = Depends(require_scope(JOB_CLOSE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    try:
        return close_job(db, ctx, job_id)
    except JobNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    except OrganizationAccessError as exc:
        raise HTTPException(
            status_code=403,
            detail="Cross-organization access is forbidden",
        ) from exc
    except JobAlreadyClosedError as exc:
        raise HTTPException(status_code=400, detail="Job already closed") from exc
