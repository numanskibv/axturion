from __future__ import annotations

from datetime import datetime, timedelta, timezone

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


def test_reporting_stage_aging_requires_reporting_read_scope(
    client: TestClient, db, org
):
    stage_operator = _make_user(db, org, "stage_operator", "no-reporting@local")

    resp = client.get(
        "/reporting/stage-aging",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(stage_operator.id),
        },
    )
    assert resp.status_code == 403


def test_reporting_stage_aging_org_scoped_and_exact_seconds(
    client: TestClient, db, org, monkeypatch
):
    from app.core.request_context import RequestContext
    from app.domain.application.models import Application
    from app.domain.organization.models import Organization
    from app.domain.workflow.models import Workflow
    from app.services.audit_service import append_audit_log

    recruiter = _make_user(db, org, "recruiter", "reporting-stage-aging@local")
    actor = _make_user(db, org, "hr_admin", "reporting-stage-aging-actor@local")

    other_org = Organization(name="other-org-stage-aging")
    db.add(other_org)
    db.commit()
    db.refresh(other_org)
    other_user = _make_user(db, other_org, "recruiter", "other-reporting@local")

    wf = Workflow(organization_id=org.id, name="wf")
    wf_other = Workflow(organization_id=other_org.id, name="wf2")
    db.add_all([wf, wf_other])
    db.commit()
    db.refresh(wf)
    db.refresh(wf_other)

    now = datetime(2026, 2, 28, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "app.services.lifecycle_reporting_service._now_utc", lambda: now
    )

    # App with no stage change: age from created_at.
    a1_created = now - timedelta(seconds=100)
    app1 = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="applied",
        status="active",
        created_at=a1_created,
        stage_entered_at=a1_created,
    )
    db.add(app1)

    # App with stage change at now-10s.
    a2_created = now - timedelta(seconds=1000)
    app2 = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="screening",
        status="active",
        created_at=a2_created,
        stage_entered_at=a2_created,
    )
    db.add(app2)

    # Closed app should not appear.
    app3 = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="interview",
        status="closed",
        created_at=now - timedelta(seconds=500),
        stage_entered_at=now - timedelta(seconds=500),
        closed_at=now - timedelta(seconds=10),
    )
    db.add(app3)

    # Other org app should never appear.
    app_other = Application(
        organization_id=other_org.id,
        workflow_id=wf_other.id,
        stage="applied",
        status="active",
        created_at=now - timedelta(seconds=999),
        stage_entered_at=now - timedelta(seconds=999),
    )
    db.add(app_other)

    db.commit()
    db.refresh(app1)
    db.refresh(app2)
    db.refresh(app_other)

    ctx = RequestContext(
        organization_id=org.id,
        actor_id=str(actor.id),
        role="hr_admin",
        scopes=set(),
    )

    # Stage change audit for app2 at now-10.
    monkeypatch.setattr(
        "app.services.audit_service._now_utc", lambda: now - timedelta(seconds=10)
    )
    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app2.id),
        action="stage_changed",
        payload="applied->screening",
    )
    db.commit()

    # Stage change audit for other org (should not affect org results).
    ctx_other = RequestContext(
        organization_id=other_org.id,
        actor_id=str(other_user.id),
        role="recruiter",
        scopes=set(),
    )
    monkeypatch.setattr(
        "app.services.audit_service._now_utc", lambda: now - timedelta(seconds=5)
    )
    append_audit_log(
        db,
        ctx_other,
        entity_type="application",
        entity_id=str(app_other.id),
        action="stage_changed",
        payload="x->y",
    )
    db.commit()

    resp = client.get(
        "/reporting/stage-aging",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)

    by_id = {row["application_id"]: row for row in body}
    assert str(app1.id) in by_id
    assert str(app2.id) in by_id
    assert str(app3.id) not in by_id
    assert str(app_other.id) not in by_id

    assert by_id[str(app1.id)]["current_stage"] == "applied"
    assert by_id[str(app1.id)]["age_seconds"] == 100

    assert by_id[str(app2.id)]["current_stage"] == "screening"
    assert by_id[str(app2.id)]["age_seconds"] == 10
