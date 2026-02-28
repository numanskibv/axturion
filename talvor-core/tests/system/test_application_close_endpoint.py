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


def _seed_application(db):
    from app.domain.organization.models import Organization
    from app.domain.identity.models import OrganizationMembership, User
    from app.domain.workflow.models import Workflow
    from app.domain.application.models import Application

    org = Organization(name="org")
    db.add(org)
    db.commit()
    db.refresh(org)

    wf = Workflow(organization_id=org.id, name="wf")
    db.add(wf)
    db.commit()
    db.refresh(wf)

    app = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="applied",
        status="active",
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    return org, app


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


def test_recruiter_can_close_application(client: TestClient, db):
    org, app = _seed_application(db)
    recruiter = _make_user(db, org, "recruiter", "recruiter@local")

    resp = client.post(
        f"/applications/{app.id}/close",
        json={"result": "hired"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    assert resp.json() == {"id": str(app.id), "status": "closed", "result": "hired"}


def test_auditor_cannot_close_application(client: TestClient, db):
    org, app = _seed_application(db)
    auditor = _make_user(db, org, "auditor", "auditor@local")

    resp = client.post(
        f"/applications/{app.id}/close",
        json={"result": "rejected"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )

    assert resp.status_code == 403


def test_wrong_org_cannot_close_application(client: TestClient, db):
    org, app = _seed_application(db)

    recruiter = _make_user(db, org, "recruiter", "recruiter2@local")

    from app.domain.organization.models import Organization

    other_org = Organization(name="other")
    db.add(other_org)
    db.commit()
    db.refresh(other_org)

    resp = client.post(
        f"/applications/{app.id}/close",
        json={"result": "rejected"},
        headers={
            "X-Org-Id": str(other_org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 403


def test_closing_twice_returns_400(client: TestClient, db):
    org, app = _seed_application(db)
    recruiter = _make_user(db, org, "recruiter", "recruiter3@local")

    resp1 = client.post(
        f"/applications/{app.id}/close",
        json={"result": "rejected"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp1.status_code == 200

    resp2 = client.post(
        f"/applications/{app.id}/close",
        json={"result": "rejected"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp2.status_code == 400
