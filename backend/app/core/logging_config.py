import logging
import os


def configure_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )

    # Prevent Alembic double logging
    logging.getLogger("alembic").propagate = False
    logging.getLogger("alembic.runtime.migration").propagate = False

    # Silence overly verbose libraries if needed
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)