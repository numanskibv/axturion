"""
ActivityService

This service manages creation and retrieval of timeline activities.
Activities are immutable records used to show what happened to an entity
(application, candidate, job) over time.
"""

from sqlalchemy.orm import Session
from app.domain.automation.models import Activity


def create_activity(
    db: Session,
    entity_type: str,
    entity_id: str,
    activity_type: str,
    message: str,
):
    """
    Create a new Activity timeline item.

    This function is used by:
    - automation rules
    - manual recruiter actions
    - system events (emails, stage changes)

    Activities are immutable and append-only.
    """
    activity = Activity(
        entity_type=entity_type,
        entity_id=entity_id,
        type=activity_type,
        message=message,
    )
    db.add(activity)
    db.flush()
    db.refresh(activity)
    return activity
