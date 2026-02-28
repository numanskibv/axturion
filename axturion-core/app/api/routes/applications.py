from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Literal
from uuid import UUID

from app.api.deps import get_request_context, require_scope
from app.core.scopes import (
    APPLICATION_CLOSE,
    APPLICATION_CREATE,
    APPLICATION_MOVE_STAGE,
)
from app.core.request_context import RequestContext
from app.core.db import get_db
from app.services.application_service import (
    close_application,
    create_application,
    ApplicationAlreadyClosedError as CloseApplicationAlreadyClosedError,
    ApplicationNotFoundError as CloseApplicationNotFoundError,
    OrganizationAccessError as CloseApplicationOrganizationAccessError,
    OrganizationAccessError as CreateApplicationOrganizationAccessError,
    WorkflowHasNoStagesError,
    WorkflowNotFoundError,
)
from app.workflow.service import (
    ApplicationNotFoundError,
    InvalidStageTransitionError,
    OrganizationAccessError,
    StageTransitionPendingError,
    StageTransitionSelfApprovalError,
    move_application_stage,
)


router = APIRouter(tags=["applications"])


class MoveStageRequest(BaseModel):
    new_stage: str


class CloseApplicationRequest(BaseModel):
    result: Literal["hired", "rejected"]


class CreateApplicationRequest(BaseModel):
    workflow_id: UUID
    candidate_id: UUID | None = None
    job_id: UUID | None = None


@router.post(
    "",
    summary="Create an application",
    description="""
Creates a new application in the specified workflow.

Authorization: Requires the application create scope.
Organization boundary: The workflow must belong to the caller's organization.
Audit/activity: Records an application creation event.
""",
)
def create(
    body: CreateApplicationRequest,
    _: None = Depends(require_scope(APPLICATION_CREATE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    try:
        created = create_application(
            db,
            ctx,
            workflow_id=body.workflow_id,
            candidate_id=body.candidate_id,
            job_id=body.job_id,
        )
    except WorkflowNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Workflow not found") from exc
    except CreateApplicationOrganizationAccessError as exc:
        raise HTTPException(
            status_code=403,
            detail="Cross-organization access is forbidden",
        ) from exc
    except WorkflowHasNoStagesError as exc:
        raise HTTPException(
            status_code=400,
            detail="Workflow has no stages",
        ) from exc

    return {
        "id": str(created.id),
        "workflow_id": str(created.workflow_id),
        "stage": created.stage,
        "status": created.status,
    }


@router.post(
    "/{app_id}/move-stage",
    summary="Move application to a new stage",
    description="""
Moves an application from its current stage to a specified target stage.

Scope: Workflow-scoped via the application; transition validity is evaluated within the application's workflow.
Integrity rules: The target stage must be reachable from the current stage; invalid transitions are rejected.
Returns: The application identifier and the updated current stage.
Errors: Returns not-found when the application does not exist.
Errors: Returns a validation error when the transition is not allowed, including allowed target stages.
""",
)
def move_stage(
    app_id: str,
    body: MoveStageRequest,
    _: None = Depends(require_scope(APPLICATION_MOVE_STAGE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    """Move an application to a new workflow stage."""
    try:
        updated = move_application_stage(db, ctx, app_id, body.new_stage)
    except StageTransitionPendingError:
        raise HTTPException(
            status_code=202,
            detail="approval_required",
        )
    except StageTransitionSelfApprovalError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OrganizationAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvalidStageTransitionError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(exc),
                "from_stage": exc.from_stage,
                "to_stage": exc.to_stage,
                "allowed_to_stages": exc.allowed_to_stages,
            },
        ) from exc

    return {"id": str(updated.id), "new_stage": updated.stage}


@router.post(
    "/{app_id}/close",
    summary="Close an application",
    description="""
Closes an application with a terminal result.

Authorization: Requires the application close scope.
Organization boundary: Enforced via the application record.
Audit/activity: Records a closure event.
""",
)
def close(
    app_id: str,
    body: CloseApplicationRequest,
    _: None = Depends(require_scope(APPLICATION_CLOSE)),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
):
    try:
        updated = close_application(db, ctx, app_id, body.result)
    except CloseApplicationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Application not found") from exc
    except CloseApplicationOrganizationAccessError as exc:
        raise HTTPException(
            status_code=403,
            detail="Cross-organization access is forbidden",
        ) from exc
    except CloseApplicationAlreadyClosedError as exc:
        raise HTTPException(
            status_code=400, detail="Application already closed"
        ) from exc

    return {"id": str(updated.id), "status": updated.status, "result": updated.result}
