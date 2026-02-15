import os
import subprocess
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, APIRouter
from sqlalchemy.orm import Session
from app.core.db import (
    engine,
    Base,
    SessionLocal,
    ensure_activity_payload_column,
    get_db,
    wait_for_db,
)
from app.core.seed import seed_workflow
from app.core.seed import seed_automation
from app.api.routes import (
    applications,
    activity,
    workflows,
    workflow_queries,
    workflow_editor,
    reporting,
)

from app.services.health_service import (
    check_database,
    check_migrations,
    get_app_version,
    get_build_hash,
    get_uptime_seconds,
)

# Ensure all models are imported so SQLAlchemy sees them
from app.domain.job.models import Job
from app.domain.candidate.models import Candidate
from app.domain.application.models import Application
from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition
from app.domain.audit.models import AuditLog
from app.domain.automation.models import AutomationRule, Activity
from app.core.logging_config import configure_logging

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Compose can start the API container before Postgres is ready.
    wait_for_db()
    ensure_activity_payload_column()

    with SessionLocal() as db:
        seed_workflow(db)
        seed_automation(db)

    yield


app = FastAPI(
    title="MATS API",
    version="0.5.0",
    description="""
MATS (Modular Application Tracking System) is a workflow-driven recruitment infrastructure platform.

This API provides:
- Workflow configuration
- Application lifecycle control
- Audit and activity tracking
- Governance-aligned reporting

All operations are strictly workflow-scoped.
Designed for on-premise, modular, and extensible deployments.
""",
    lifespan=lifespan,
)
app.include_router(reporting.router)
app.include_router(applications.router, prefix="/applications")
app.include_router(activity.router, prefix="/activity")
app.include_router(workflows.router, prefix="/workflows")
app.include_router(workflow_queries.router, prefix="/workflow-queries")
app.include_router(workflow_editor.router, prefix="/workflow-editor")


router = APIRouter()


@router.get(
    "/live",
    summary="Liveness probe",
    description="Returns if the application process is alive.",
)
def liveness():
    return {"status": "alive"}


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Checks if the system is ready to serve traffic.",
)
def readiness(db: Session = Depends(get_db)):
    db_ok = check_database(db)
    migrations_ok = check_migrations(db)

    return {
        "status": "ready" if db_ok and migrations_ok else "not_ready",
        "database": db_ok,
        "migrations": migrations_ok,
    }


@router.get(
    "/health",
    summary="System health overview",
    description="Returns extended system health including version, uptime and build metadata.",
)
def health(db: Session = Depends(get_db)):
    db_ok = check_database(db)
    migrations_ok = check_migrations(db)

    overall = "ok" if db_ok and migrations_ok else "degraded"

    return {
        "status": overall,
        "database": "ok" if db_ok else "down",
        "migrations": "up_to_date" if migrations_ok else "out_of_date",
        "version": get_app_version(),
        "build_hash": get_build_hash(),
        "uptime_seconds": get_uptime_seconds(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


app.include_router(router)


