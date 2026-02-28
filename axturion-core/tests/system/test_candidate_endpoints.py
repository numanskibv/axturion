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


def _make_org(db, name: str):
    from app.domain.organization.models import Organization

    org = Organization(name=name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


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


def _make_candidate(db, org, full_name: str, email: str | None = None):
    from app.domain.candidate.models import Candidate

    candidate = Candidate(organization_id=org.id, name=full_name, email=email)
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def test_recruiter_can_create_candidate(client: TestClient, db):
    org = _make_org(db, "org")
    recruiter = _make_user(db, org, "recruiter", "recruiter@local")

    resp = client.post(
        "/candidates",
        json={
            "full_name": "Ada Lovelace",
            "email": "ada@local",
            "phone": "123",
            "notes": "note",
        },
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Ada Lovelace"
    assert data["email"] == "ada@local"
    assert data["phone"] == "123"
    assert data["notes"] == "note"


def test_auditor_cannot_create_candidate(client: TestClient, db):
    org = _make_org(db, "org")
    auditor = _make_user(db, org, "auditor", "auditor@local")

    resp = client.post(
        "/candidates",
        json={"full_name": "Ada Lovelace"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )

    assert resp.status_code == 403


def test_auditor_can_read_candidate(client: TestClient, db):
    org = _make_org(db, "org")
    candidate = _make_candidate(db, org, "Ada Lovelace")
    auditor = _make_user(db, org, "auditor", "auditor@local")

    resp = client.get(
        f"/candidates/{candidate.id}",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )

    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Ada Lovelace"


def test_wrong_org_read_returns_404(client: TestClient, db):
    org1 = _make_org(db, "org1")
    candidate = _make_candidate(db, org1, "Ada Lovelace")

    org2 = _make_org(db, "org2")
    auditor = _make_user(db, org2, "auditor", "auditor@local")

    resp = client.get(
        f"/candidates/{candidate.id}",
        headers={
            "X-Org-Id": str(org2.id),
            "X-User-Id": str(auditor.id),
        },
    )

    assert resp.status_code == 404


def test_recruiter_can_update_candidate(client: TestClient, db):
    org = _make_org(db, "org")
    candidate = _make_candidate(db, org, "Ada Lovelace")
    recruiter = _make_user(db, org, "recruiter", "recruiter@local")

    resp = client.patch(
        f"/candidates/{candidate.id}",
        json={"notes": "updated"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    assert resp.json()["notes"] == "updated"


def test_auditor_cannot_update_candidate(client: TestClient, db):
    org = _make_org(db, "org")
    candidate = _make_candidate(db, org, "Ada Lovelace")
    auditor = _make_user(db, org, "auditor", "auditor@local")

    resp = client.patch(
        f"/candidates/{candidate.id}",
        json={"notes": "updated"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )

    assert resp.status_code == 403


def test_duplicate_email_same_org_returns_400(client: TestClient, db):
    org = _make_org(db, "org")
    recruiter = _make_user(db, org, "recruiter", "recruiter@local")

    resp1 = client.post(
        "/candidates",
        json={"full_name": "Ada", "email": "dup@local"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp1.status_code == 200

    resp2 = client.post(
        "/candidates",
        json={"full_name": "Ada2", "email": "dup@local"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp2.status_code == 400


def test_same_email_different_org_allowed(client: TestClient, db):
    org1 = _make_org(db, "org1")
    recruiter1 = _make_user(db, org1, "recruiter", "recruiter1@local")

    resp1 = client.post(
        "/candidates",
        json={"full_name": "Ada", "email": "same@local"},
        headers={
            "X-Org-Id": str(org1.id),
            "X-User-Id": str(recruiter1.id),
        },
    )
    assert resp1.status_code == 200

    org2 = _make_org(db, "org2")
    recruiter2 = _make_user(db, org2, "recruiter", "recruiter2@local")

    resp2 = client.post(
        "/candidates",
        json={"full_name": "Ada2", "email": "same@local"},
        headers={
            "X-Org-Id": str(org2.id),
            "X-User-Id": str(recruiter2.id),
        },
    )
    assert resp2.status_code == 200
