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


def _seed_workflow(db):
    from app.domain.organization.models import Organization
    from app.domain.identity.models import OrganizationMembership, User
    from app.domain.workflow.models import Workflow

    org = Organization(name="org")
    db.add(org)
    db.commit()
    db.refresh(org)

    wf = Workflow(organization_id=org.id, name="wf")
    db.add(wf)
    db.commit()
    db.refresh(wf)

    def make_user(role: str):
        user = User(email=f"{role}@local", is_active=True)
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

    return org, wf, make_user


def test_recruiter_cannot_modify_workflow(client: TestClient, db):
    org, wf, make_user = _seed_workflow(db)
    recruiter = make_user("recruiter")

    resp = client.post(
        f"/workflow-editor/{wf.id}/stages",
        json={"name": "screening"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 403


def test_hr_admin_can_modify_workflow(client: TestClient, db):
    org, wf, make_user = _seed_workflow(db)
    admin = make_user("hr_admin")

    resp = client.post(
        f"/workflow-editor/{wf.id}/stages",
        json={"name": "screening"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(admin.id),
        },
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "screening"


def test_auditor_cannot_modify_workflow(client: TestClient, db):
    org, wf, make_user = _seed_workflow(db)
    auditor = make_user("auditor")

    resp = client.post(
        f"/workflow-editor/{wf.id}/stages",
        json={"name": "screening"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )

    assert resp.status_code == 403
