from __future__ import annotations

import logging
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url

from app.core.config import Settings


logger = logging.getLogger(__name__)


def verify_startup(engine: Engine, settings: Settings) -> None:
    """Verify DB connectivity and that Alembic is at head.

    Raises RuntimeError to fail-fast during startup when the DB is not ready.
    """

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

        alembic_ini = Path(__file__).resolve().parents[3] / "alembic.ini"
        alembic_dir = Path(__file__).resolve().parents[3] / "alembic"

        cfg = Config(str(alembic_ini))
        cfg.set_main_option("script_location", str(alembic_dir))
        cfg.set_main_option("sqlalchemy.url", settings.database_url)

        script = ScriptDirectory.from_config(cfg)
        head = script.get_current_head()

        context = MigrationContext.configure(conn)
        current = context.get_current_revision()

    if head is None:
        raise RuntimeError("Alembic head revision not found")
    if current != head:
        raise RuntimeError(
            f"Database migration mismatch: current={current} head={head}"
        )

    url = make_url(settings.database_url)
    db_host = url.host or "-"

    logger.info(
        "startup_verification_passed",
        extra={
            "action": "startup_verification_passed",
            "env": settings.env,
            "db_host": db_host,
        },
    )
