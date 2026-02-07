from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.automation.models import Activity
from app.api.schemas.activity import ActivityResponse


router = APIRouter()


@router.get("/activities", response_model=list[ActivityResponse])
def list_activities(db: Session = Depends(get_db)):
    return db.query(Activity).order_by(Activity.created_at.desc()).all()


@router.get("/{entity_type}/{entity_id}", response_model=list[ActivityResponse])
def get_timeline(entity_type: str, entity_id: str, db: Session = Depends(get_db)):
    items = (
        db.query(Activity)
        .filter(Activity.entity_type == entity_type, Activity.entity_id == entity_id)
        .order_by(Activity.created_at.desc())
        .all()
    )

    return items
