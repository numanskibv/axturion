import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.domain.audit.models import AuditLog  # noqa: F401 (register model)
from app.domain.governance.models import PolicyConfig  # noqa: F401 (register model)


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


def _make_user(db, org, role: str, email: str):
    from app.domain.identity.models import OrganizationMembership, User

    user = User(email=email, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    membership = OrganizationMembership(
        organization_id=org.id,
        user_id=user.id,
        role=role,
        is_active=True,
    )
    db.add(membership)
    db.commit()

    return user


def test_get_policy_autocreates_defaults(client: TestClient, db, org):
    recruiter = _make_user(db, org, "recruiter", "recruiter-policy@local")

    resp = client.get(
        "/governance/policy",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["organization_id"] == str(org.id)
    assert body["require_4eyes_on_hire"] is False
    assert body["require_4eyes_on_ux_rollback"] is False
    assert body["stage_aging_sla_days"] == 7
    assert body["default_language"] == "en"
    assert body.get("candidate_retention_days") is None
    assert body.get("audit_retention_days") is None
    assert "created_at" in body
    assert "updated_at" in body

    row = (
        db.query(PolicyConfig)
        .filter(PolicyConfig.organization_id == org.id)
        .one_or_none()
    )
    assert row is not None


def test_put_policy_requires_workflow_write_scope(client: TestClient, db, org):
    recruiter = _make_user(db, org, "recruiter", "recruiter-policy-write@local")

    resp = client.put(
        "/governance/policy",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
        json={"require_4eyes_on_hire": True},
    )

    assert resp.status_code == 403


def test_put_policy_strict_write_and_audited(client: TestClient, db, org):
    hr_admin = _make_user(db, org, "hr_admin", "hr-admin-policy@local")

    bad = client.put(
        "/governance/policy",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={"unknown": 123},
    )
    assert bad.status_code == 422

    empty = client.put(
        "/governance/policy",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={},
    )
    assert empty.status_code == 422

    resp = client.put(
        "/governance/policy",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={
            "require_4eyes_on_hire": True,
            "require_4eyes_on_ux_rollback": True,
            "stage_aging_sla_days": 14,
            "default_language": "nl",
            "candidate_retention_days": 365,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["require_4eyes_on_hire"] is True
    assert body["require_4eyes_on_ux_rollback"] is True
    assert body["stage_aging_sla_days"] == 14
    assert body["default_language"] == "nl"
    assert body["candidate_retention_days"] == 365
    assert body.get("audit_retention_days") is None

    audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == org.id,
            AuditLog.entity_type == "policy",
            AuditLog.action == "policy_updated",
            AuditLog.entity_id == str(org.id),
        )
        .order_by(AuditLog.seq.desc())
        .first()
    )
    assert audit is not None

    payload = json.loads(audit.payload)
    assert payload["organization_id"] == str(org.id)
    assert payload["require_4eyes_on_hire"] is True
    assert payload["require_4eyes_on_ux_rollback"] is True
    assert payload["stage_aging_sla_days"] == 14
    assert payload["default_language"] == "nl"
    assert payload["candidate_retention_days"] == 365
    assert payload["audit_retention_days"] is None


def test_put_policy_rejects_invalid_language(client: TestClient, db, org):
    hr_admin = _make_user(db, org, "hr_admin", "hr-admin-policy-lang@local")

    resp = client.put(
        "/governance/policy",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={"default_language": "de"},
    )

    assert resp.status_code == 422
