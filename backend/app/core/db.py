import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()


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
