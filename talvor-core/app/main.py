import os
import subprocess
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, APIRouter
from sqlalchemy.orm import Session

import app.core.db as core_db
from app.core.config import get_settings
from app.core.log_context import actor_id_var, correlation_id_var, organization_id_var
from app.core.startup_verification import verify_startup
from app.core.seed import seed_automation
from app.core.seed import seed_identity
from app.core.seed import seed_workflow
from app.api.routes import (
    applications,
    activity,
    audit,
    approvals,
    candidates,
    compliance,
    jobs,
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
from app.domain.organization.models import Organization
from app.domain.audit.models import AuditLog
from app.domain.automation.models import AutomationRule, Activity
from app.core.logging_config import configure_logging

import logging
from uuid import UUID, uuid4

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    core_db.init_db(settings)

    # Compose can start the API container before Postgres is ready.
    core_db.wait_for_db()

    # Deterministic startup verification (fail-fast if DB not migrated).
    verify_startup(core_db.engine, settings)

    with core_db.SessionLocal() as db:
        seed_identity(db)
        seed_workflow(db)
        seed_automation(db)

    yield


app = FastAPI(
    title="MATS API",
    version="0.6.0",
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


@app.middleware("http")
async def correlation_middleware(request, call_next):
    correlation_id = str(uuid4())
    request.state.correlation_id = correlation_id

    correlation_token = correlation_id_var.set(correlation_id)

    org_token = None
    actor_token = None
    try:
        org_header = request.headers.get("x-org-id")
        actor_header = request.headers.get("x-user-id") or request.headers.get(
            "x-actor-id"
        )

        if org_header:
            try:
                org_token = organization_id_var.set(str(UUID(str(org_header))))
            except (TypeError, ValueError):
                org_token = organization_id_var.set("-")

        if actor_header:
            actor_token = actor_id_var.set(str(actor_header))

        response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation_id
        return response
    finally:
        correlation_id_var.reset(correlation_token)
        if org_token is not None:
            organization_id_var.reset(org_token)
        if actor_token is not None:
            actor_id_var.reset(actor_token)


app.include_router(reporting.router)
app.include_router(approvals.router)
app.include_router(audit.router)
app.include_router(compliance.router)
app.include_router(applications.router, prefix="/applications")
app.include_router(activity.router, prefix="/activity")
app.include_router(candidates.router, prefix="/candidates")
app.include_router(jobs.router, prefix="/jobs")
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
def readiness(db: Session = Depends(core_db.get_db)):
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
def health(db: Session = Depends(core_db.get_db)):
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
