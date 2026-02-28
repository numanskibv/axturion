import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def client(db, monkeypatch):
    """System-level client wired to sqlite in-memory."""

    from app.main import app
    import app.core.db as core_db
    from app.core.config import Settings

    engine = db.get_bind()
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr("app.main.core_db.wait_for_db", lambda: None)
    monkeypatch.setattr("app.main.core_db.init_db", lambda _settings: None)
    monkeypatch.setattr("app.main.verify_startup", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.main.seed_identity", lambda _db: None)
    monkeypatch.setattr("app.main.seed_workflow", lambda _db: None)
    monkeypatch.setattr("app.main.seed_automation", lambda _db: None)

    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: Settings(DATABASE_URL=str(engine.url), ENV="test", LOG_LEVEL="INFO"),
    )

    monkeypatch.setattr(core_db, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.main.core_db", core_db)

    app.dependency_overrides[core_db.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def _seed_workflow_with_stage(db, org_name: str, workflow_name: str, stage_name: str):
    from app.domain.organization.models import Organization
    from app.domain.identity.models import OrganizationMembership, User
    from app.domain.workflow.models import Workflow, WorkflowStage

    org = Organization(name=org_name)
    db.add(org)
    db.commit()
    db.refresh(org)

    wf = Workflow(organization_id=org.id, name=workflow_name)
    db.add(wf)
    db.commit()
    db.refresh(wf)

    stage = WorkflowStage(
        organization_id=org.id,
        workflow_id=wf.id,
        name=stage_name,
        order=1,
    )
    db.add(stage)
    db.commit()

    return org, wf


def _make_user(db, org, role: str, email: str):
    from app.domain.identity.models import OrganizationMembership, User

    user = User(email=email, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(
        OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role=role,
            is_active=True,
        )
    )
    db.commit()
    return user


def test_recruiter_can_create_application(client: TestClient, db):
    org, wf = _seed_workflow_with_stage(db, "org", "wf", "applied")
    recruiter = _make_user(db, org, "recruiter", "recruiter@local")

    resp = client.post(
        "/applications",
        json={"workflow_id": str(wf.id), "candidate_id": None, "job_id": None},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["workflow_id"] == str(wf.id)
    assert data["stage"] == "applied"
    assert data["status"] == "open"


def test_auditor_cannot_create_application(client: TestClient, db):
    org, wf = _seed_workflow_with_stage(db, "org", "wf", "applied")
    auditor = _make_user(db, org, "auditor", "auditor@local")

    resp = client.post(
        "/applications",
        json={"workflow_id": str(wf.id)},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )

    assert resp.status_code == 403


def test_wrong_org_workflow_returns_403(client: TestClient, db):
    org1, wf1 = _seed_workflow_with_stage(db, "org1", "wf1", "applied")
    org2, _wf2 = _seed_workflow_with_stage(db, "org2", "wf2", "applied")

    recruiter = _make_user(db, org2, "recruiter", "recruiter2@local")

    resp = client.post(
        "/applications",
        json={"workflow_id": str(wf1.id)},
        headers={
            "X-Org-Id": str(org2.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 403


def test_missing_workflow_returns_404(client: TestClient, db):
    from uuid import uuid4

    org, _wf = _seed_workflow_with_stage(db, "org", "wf", "applied")
    recruiter = _make_user(db, org, "recruiter", "recruiter3@local")

    resp = client.post(
        "/applications",
        json={"workflow_id": str(uuid4())},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 404
