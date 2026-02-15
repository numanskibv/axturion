from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.domain.application.models import Application


class ApplicationNotFoundError(Exception):
    pass


class ApplicationAlreadyClosedError(Exception):
    pass


def close_application(db: Session, application_id):
    application = (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )

    if not application:
        raise ApplicationNotFoundError()

    if application.status == "closed":
        raise ApplicationAlreadyClosedError()

    application.status = "closed"
    application.closed_at = datetime.now(timezone.utc)

    db.add(application)
    db.commit()
    db.refresh(application)

    return application