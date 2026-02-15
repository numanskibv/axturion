import os
import time
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


START_TIME = time.time()


def get_uptime_seconds() -> int:
    return int(time.time() - START_TIME)


def get_app_version() -> str:
    return os.getenv("APP_VERSION", "0.4.0")


def get_build_hash() -> str:
    return os.getenv("BUILD_HASH", "dev")


def check_database(db: Session) -> bool:
    try:
        db.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False


def check_migrations(db: Session) -> bool:
    try:
        result = db.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        return version is not None
    except SQLAlchemyError:
        return False