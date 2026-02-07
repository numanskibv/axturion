from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.workflow_query_service import get_allowed_transitions

router = APIRouter(prefix="/workflow-queries", tags=["workflow"])


@router.get("/applications/{application_id}/allowed-transitions")
def allowed_transitions(application_id: str, db: Session = Depends(get_db)):
    try:
        return get_allowed_transitions(db, application_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))