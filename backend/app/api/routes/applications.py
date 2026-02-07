from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.workflow.service import (
    ApplicationNotFoundError,
    InvalidStageTransitionError,
    move_application_stage,
)


router = APIRouter()


class MoveStageRequest(BaseModel):
    new_stage: str


@router.post("/{app_id}/move-stage")
def move_stage(app_id: str, body: MoveStageRequest, db: Session = Depends(get_db)):
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
