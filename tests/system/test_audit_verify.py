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


def _seed_org_and_users(db, *, org_name: str = "org-audit"):
    from app.domain.organization.models import Organization
    from app.domain.identity.models import OrganizationMembership, User

    org = Organization(name=org_name)
    db.add(org)
    db.commit()
    db.refresh(org)

    def make_user(role: str, email: str):
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

    return org, make_user


def test_auditor_can_verify_chain_ok(client: TestClient, db):
    org, make_user = _seed_org_and_users(db)
    recruiter = make_user("recruiter", "recruiter@local")
    auditor = make_user("auditor", "auditor@local")

    create_resp = client.post(
        "/candidates",
        json={"full_name": "Test Candidate", "email": "tc@local"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert create_resp.status_code == 200

    verify_resp = client.get(
        "/audit/verify",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )

    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert data["ok"] is True
    assert data["checked"] >= 1


def test_user_without_audit_read_cannot_verify(client: TestClient, db):
    org, make_user = _seed_org_and_users(db, org_name="org-audit-deny")
    recruiter = make_user("recruiter", "recruiter@local")

    resp = client.get(
        "/audit/verify",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 403


def test_verify_detects_tampering(client: TestClient, db):
    from app.domain.audit.models import AuditLog

    org, make_user = _seed_org_and_users(db, org_name="org-audit-tamper")
    recruiter = make_user("recruiter", "recruiter@local")
    auditor = make_user("auditor", "auditor@local")

    create_resp = client.post(
        "/candidates",
        json={"full_name": "Victim", "email": "victim@local"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert create_resp.status_code == 200

    row = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == org.id)
        .order_by(AuditLog.seq.asc())
        .first()
    )
    assert row is not None

    row.payload = '{"tampered":true}'
    db.add(row)
    db.commit()

    verify_resp = client.get(
        "/audit/verify",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )

    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert data["ok"] is False
    assert data["error"] is not None
    assert data["error"]["reason"] in ("hash_mismatch", "prev_hash_mismatch")
