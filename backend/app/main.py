from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.core.db import (
    engine,
    Base,
    SessionLocal,
    ensure_activity_payload_column,
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

# Ensure all models are imported so SQLAlchemy sees them
from app.domain.job.models import Job
from app.domain.candidate.models import Candidate
from app.domain.application.models import Application
from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition
from app.domain.audit.models import AuditLog
from app.domain.automation.models import AutomationRule, Activity


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
    version="0.4.0",
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


@app.get("/health")
def health():
    return {"status": "ok"}


def run():
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
