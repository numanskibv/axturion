import os
import time
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import Settings

engine = None
SessionLocal = None

Base = declarative_base()


def init_db(settings: Settings, *, echo: bool | None = None) -> None:
    """Initialize SQLAlchemy engine + Session factory.

    This is intentionally lazy: importing modules must not require env vars.
    """

    global engine, SessionLocal

    if echo is None:
        effective_echo = os.getenv("SQLALCHEMY_ECHO", "false").lower() in {
            "1",
            "true",
            "yes",
            "y",
        }
    else:
        effective_echo = echo
    engine = create_engine(settings.database_url, echo=effective_echo)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _require_initialized() -> tuple[Any, Any]:
    if engine is None or SessionLocal is None:
        raise RuntimeError(
            "Database is not initialized; call init_db(settings) on startup"
        )
    return engine, SessionLocal


def wait_for_db(max_attempts: int = 30, delay_seconds: float = 1.0) -> None:
    """Wait for the configured database to accept connections.

    This prevents the app from crashing during startup when Postgres is still
    booting (common in Docker Compose).
    """

    current_engine, _ = _require_initialized()

    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            with current_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except OperationalError as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            time.sleep(delay_seconds)

    if last_error is not None:
        raise last_error


def get_db():
    _, current_session_local = _require_initialized()

    db = current_session_local()
    try:
        yield db
    finally:
        db.close()
