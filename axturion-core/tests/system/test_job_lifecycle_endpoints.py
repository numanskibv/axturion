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


def _seed_job(db, org_name: str = "org", title: str = "Analyst"):
    from app.domain.organization.models import Organization
    from app.domain.identity.models import OrganizationMembership, User
    from app.domain.job.models import Job

    org = Organization(name=org_name)
    db.add(org)
    db.commit()
    db.refresh(org)

    job = Job(organization_id=org.id, title=title, description=None, status="open")
    db.add(job)
    db.commit()
    db.refresh(job)

    def make_user(role: str):
        user = User(email=f"{org_name}-{role}@local", is_active=True)
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

    return org, job, make_user


def test_recruiter_cannot_create_job(client: TestClient, db):
    org, _job, make_user = _seed_job(db)
    recruiter = make_user("recruiter")

    resp = client.post(
        "/jobs",
        json={"title": "Engineer", "description": "desc"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 403


def test_hr_admin_can_create_job(client: TestClient, db):
    org, _job, make_user = _seed_job(db)
    admin = make_user("hr_admin")

    resp = client.post(
        "/jobs",
        json={"title": "Engineer", "description": "desc"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(admin.id),
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Engineer"
    assert data["status"] == "open"


def test_auditor_can_read_but_cannot_update_or_close(client: TestClient, db):
    org, job, make_user = _seed_job(db)
    auditor = make_user("auditor")

    read_resp = client.get(
        f"/jobs/{job.id}",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )
    assert read_resp.status_code == 200

    upd_resp = client.patch(
        f"/jobs/{job.id}",
        json={"title": "New"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )
    assert upd_resp.status_code == 403

    close_resp = client.post(
        f"/jobs/{job.id}/close",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )
    assert close_resp.status_code == 403


def test_wrong_org_for_update_and_close_returns_403(client: TestClient, db):
    org1, job, make_user1 = _seed_job(db, org_name="org1")
    org2, _other, make_user2 = _seed_job(db, org_name="org2")

    admin = make_user2("hr_admin")

    upd_resp = client.patch(
        f"/jobs/{job.id}",
        json={"title": "New"},
        headers={
            "X-Org-Id": str(org2.id),
            "X-User-Id": str(admin.id),
        },
    )
    assert upd_resp.status_code == 403

    close_resp = client.post(
        f"/jobs/{job.id}/close",
        headers={
            "X-Org-Id": str(org2.id),
            "X-User-Id": str(admin.id),
        },
    )
    assert close_resp.status_code == 403


def test_closing_twice_returns_400(client: TestClient, db):
    org, job, make_user = _seed_job(db)
    admin = make_user("hr_admin")

    resp1 = client.post(
        f"/jobs/{job.id}/close",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(admin.id),
        },
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "closed"

    resp2 = client.post(
        f"/jobs/{job.id}/close",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(admin.id),
        },
    )
    assert resp2.status_code == 400


def test_update_closed_job_returns_400(client: TestClient, db):
    org, job, make_user = _seed_job(db)
    admin = make_user("hr_admin")

    close_resp = client.post(
        f"/jobs/{job.id}/close",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(admin.id),
        },
    )
    assert close_resp.status_code == 200

    upd_resp = client.patch(
        f"/jobs/{job.id}",
        json={"title": "New"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(admin.id),
        },
    )
    assert upd_resp.status_code == 400
