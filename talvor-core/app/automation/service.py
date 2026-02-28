import json
from uuid import UUID
from sqlalchemy.orm import Session
from app.domain.automation.models import AutomationRule, Activity
from app.services.activity_service import create_activity


def handle_event(db: Session, event_type: str, payload: dict):
    organization_id = payload.get("organization_id")
    if not organization_id:
        # Organization boundary is mandatory; ignore events that are missing it.
        return

    if isinstance(organization_id, str):
        try:
            organization_id = UUID(organization_id)
        except ValueError:
            return

    rules = (
        db.query(AutomationRule)
        .filter(
            AutomationRule.organization_id == organization_id,
            AutomationRule.event_type == event_type,
            AutomationRule.enabled == "true",
        )
        .all()
    )

    for rule in rules:
        if rule.condition_key and rule.condition_value:
            if str(payload.get(rule.condition_key)) != str(rule.condition_value):
                continue

        if rule.action_type == "create_activity":
            data = json.loads(rule.action_payload or "{}")
            act = create_activity(
                db=db,
                organization_id=organization_id,
                entity_type=payload.get("entity_type", "application"),
                entity_id=str(payload.get("entity_id")),
                activity_type=data.get("type", "note"),
                message=data.get("message", ""),
            )
            # Activity is added to the current transaction (committed by caller).

        elif rule.action_type == "send_email":
            # later: echte mail service; nu alleen loggen/activities
            data = json.loads(rule.action_payload or "{}")
            act = Activity(  # log email as activity for now
                organization_id=organization_id,
                entity_type=payload.get("entity_type", "application"),
                entity_id=str(payload.get("entity_id")),
                type="email",
                message=f"FAKE EMAIL: {data}",
            )
            db.add(act)

            # No commit here: keep automation effects in the caller's transaction.
