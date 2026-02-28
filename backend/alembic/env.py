from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.db import Base

# Force-load all models so metadata is populated
from app.domain.application.models import Application
from app.domain.workflow.models import (
    Workflow,
    WorkflowStage,
    WorkflowTransition,
)
from app.domain.automation.models import AutomationRule, Activity
from app.domain.audit.models import AuditLog
from app.domain.job.models import Job
from app.domain.candidate.models import Candidate
from app.domain.organization.models import Organization

# Alembic Config object (alembic.ini)
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# TODO: koppel hier later je SQLAlchemy MetaData (voor autogenerate)
target_metadata = Base.metadata


def get_database_url() -> str:
    # 1) DATABASE_URL env var
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    # 2) alembic.ini sqlalchemy.url
    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url:
        return ini_url

    raise RuntimeError(
        "No database URL configured (set DATABASE_URL or sqlalchemy.url)"
    )


def run_migrations_offline() -> None:
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
