from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.workflow_editor_service import get_workflow_definition

router = APIRouter()


@router.get("/{workflow_id}")
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    try:
        return get_workflow_definition(db, workflow_id)
    except ValueError as e:
        # Service-level error → nette API response
        raise HTTPException(status_code=404, detail=str(e))
