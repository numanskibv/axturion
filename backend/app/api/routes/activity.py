from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.domain.automation.models import Activity


router = APIRouter()


@router.get("/{entity_type}/{entity_id}")
def get_timeline(entity_type: str, entity_id: str, db: Session = Depends(get_db)):
    items = (
        db.query(Activity)
        .filter(Activity.entity_type == entity_type, Activity.entity_id == entity_id)
        .order_by(Activity.created_at.desc())
        .all()
    )

    return [
        {
            "type": a.type,
            "message": a.message,
            "created_at": a.created_at,
        }
        for a in items
    ]
