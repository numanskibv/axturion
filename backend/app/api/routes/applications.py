from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.workflow.service import (
    ApplicationNotFoundError,
    InvalidStageTransitionError,
    move_application_stage,
)


router = APIRouter(tags=["applications"])


class MoveStageRequest(BaseModel):
    new_stage: str


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
def move_stage(app_id: str, body: MoveStageRequest, db: Session = Depends(get_db)):
    """Move an application to a new workflow stage."""
    try:
        updated = move_application_stage(db, app_id, body.new_stage)
    except ApplicationNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
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
