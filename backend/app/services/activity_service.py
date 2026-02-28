"""
ActivityService

This service manages creation and retrieval of timeline activities.
Activities are immutable records used to show what happened to an entity
(application, candidate, job) over time.
"""

import json
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from app.domain.automation.models import Activity

import logging

logger = logging.getLogger(__name__)


def create_activity(
    db: Session,
    organization_id: UUID,
    entity_type: str,
    entity_id: str,
    activity_type: str,
    message: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
):
    """
    Create a new Activity timeline item.

    This function is used by:
    - automation rules
    - manual recruiter actions
    - system events (emails, stage changes)

    Activities are immutable and append-only.
    """
    if message is None:
        message = ""

    activity = Activity(
        organization_id=organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
        type=activity_type,
        message=message,
        payload=payload,
    )

    logger.info(
        "activity_created",
        extra={
            "action": "activity_created",
            "organization_id": str(organization_id),
            "entity_type": entity_type,
            "entity_id": entity_id,
            "activity_type": activity_type,
        },
    )
    db.add(activity)
    db.flush()
    db.refresh(activity)
    return activity
