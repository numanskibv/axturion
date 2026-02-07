import os
import time
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() in {
    "1",
    "true",
    "yes",
    "y",
}

engine = create_engine(DATABASE_URL, echo=SQLALCHEMY_ECHO)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


def wait_for_db(max_attempts: int = 30, delay_seconds: float = 1.0) -> None:
    """Wait for the configured database to accept connections.

    This prevents the app from crashing during startup when Postgres is still
    booting (common in Docker Compose).
    """

    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            time.sleep(delay_seconds)

    if last_error is not None:
        raise last_error


def ensure_activity_payload_column() -> None:
    """Best-effort dev-time schema sync.

    SQLAlchemy `create_all()` won't add new columns to existing tables.
    This keeps local/docker environments working when we add columns like
    `activity.payload` without requiring an immediate migration.
    """

    try:
        inspector = inspect(engine)
        if "activity" not in inspector.get_table_names():
            return

        columns = {col["name"] for col in inspector.get_columns("activity")}
        if "payload" in columns:
            return

        with engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE activity ADD COLUMN IF NOT EXISTS payload JSON")
            )
    except Exception:
        # Don't block app startup in dev if schema sync fails.
        return


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
