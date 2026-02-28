from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.domain.audit.models import AuditLog  # noqa: F401 (register model)
from app.domain.candidate.models import Candidate  # noqa: F401 (register model)
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


def test_retention_preview_defaults_are_safe(client: TestClient, db, org):
    recruiter = _make_user(db, org, "recruiter", "recruiter-retention@local")

    resp = client.get(
        "/governance/retention/preview",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["candidate_retention_days"] is None
    assert body["audit_retention_days"] is None
    assert body["candidates_eligible_for_deletion"] == 0
    assert body["audit_entries_eligible_for_deletion"] == 0


def test_retention_preview_counts_are_org_scoped(
    client: TestClient, db, org, monkeypatch
):
    from app.core.request_context import RequestContext
    from app.domain.organization.models import Organization
    from app.services.audit_service import append_audit_log

    hr_admin = _make_user(db, org, "hr_admin", "hr-admin-retention@local")
    recruiter = _make_user(db, org, "recruiter", "recruiter-retention2@local")

    # Configure retention policy (read-only preview, but config comes from PolicyConfig).
    put = client.put(
        "/governance/policy",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={
            "candidate_retention_days": 10,
            "audit_retention_days": 7,
        },
    )
    assert put.status_code == 200

    now = datetime.now(timezone.utc)
    very_old = now - timedelta(days=100)
    recent = now - timedelta(days=1)

    # Candidates (two in org, one in other org)
    db.add(
        Candidate(
            organization_id=org.id,
            name="Eligible",
            email="eligible@local",
            created_at=very_old,
        )
    )
    db.add(
        Candidate(
            organization_id=org.id,
            name="Recent",
            email="recent@local",
            created_at=recent,
        )
    )

    other_org = Organization(name="other-org")
    db.add(other_org)
    db.commit()
    db.refresh(other_org)

    db.add(
        Candidate(
            organization_id=other_org.id,
            name="OtherEligible",
            email="other@local",
            created_at=very_old,
        )
    )
    db.commit()

    # Audit logs (two in org, one in other org)
    ctx_org = RequestContext(
        organization_id=org.id,
        actor_id=str(hr_admin.id),
        role="hr_admin",
        scopes=set(),
    )
    ctx_other = RequestContext(
        organization_id=other_org.id,
        actor_id=str(hr_admin.id),
        role="hr_admin",
        scopes=set(),
    )

    monkeypatch.setattr("app.services.audit_service._now_utc", lambda: very_old)
    append_audit_log(
        db,
        ctx_org,
        entity_type="retention_test",
        entity_id="1",
        action="created",
        payload={"kind": "old"},
    )
    db.commit()

    monkeypatch.setattr("app.services.audit_service._now_utc", lambda: recent)
    append_audit_log(
        db,
        ctx_org,
        entity_type="retention_test",
        entity_id="2",
        action="created",
        payload={"kind": "recent"},
    )
    db.commit()

    monkeypatch.setattr("app.services.audit_service._now_utc", lambda: very_old)
    append_audit_log(
        db,
        ctx_other,
        entity_type="retention_test",
        entity_id="3",
        action="created",
        payload={"kind": "other-old"},
    )
    db.commit()

    resp = client.get(
        "/governance/retention/preview",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["candidate_retention_days"] == 10
    assert body["audit_retention_days"] == 7
    assert body["candidates_eligible_for_deletion"] == 1
    assert body["audit_entries_eligible_for_deletion"] == 1
