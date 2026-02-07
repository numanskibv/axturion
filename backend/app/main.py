from fastapi import FastAPI
from app.core.db import engine, Base, SessionLocal, ensure_activity_payload_column
from app.core.seed import seed_workflow
from app.core.seed import seed_automation
from app.api.routes import applications, activity, workflows, workflow_queries, workflow_editor

# Ensure all models are imported so SQLAlchemy sees them
from app.domain.job.models import Job
from app.domain.candidate.models import Candidate
from app.domain.application.models import Application
from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition
from app.domain.audit.models import AuditLog
from app.domain.automation.models import AutomationRule, Activity

app = FastAPI(title="ATS Platform")

app.include_router(applications.router, prefix="/applications", tags=["applications"])
app.include_router(activity.router, prefix="/activity", tags=["activity"])
app.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
app.include_router(
    workflow_queries.router, prefix="/workflow-queries", tags=["workflow-queries"]
)
app.include_router(workflow_editor.router, prefix="/workflow-editor", tags=["workflow-editor"])

Base.metadata.create_all(bind=engine)
ensure_activity_payload_column()

with SessionLocal() as db:
    seed_workflow(db)
    seed_automation(db)


@app.get("/health")
def health():
    return {"status": "ok"}


def run():
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
