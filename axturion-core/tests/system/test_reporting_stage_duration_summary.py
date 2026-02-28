from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def client(db, monkeypatch):
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


def test_reporting_stage_duration_summary_requires_reporting_read_scope(client: TestClient, db, org):
    stage_operator = _make_user(db, org, "stage_operator", "no-reporting-sds@local")

    resp = client.get(
        "/reporting/stage-duration-summary?workflow_id=00000000-0000-0000-0000-000000000000",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(stage_operator.id),
        },
    )
    assert resp.status_code == 403


def test_reporting_stage_duration_summary_workflow_not_found(client: TestClient, db, org):
    recruiter = _make_user(db, org, "recruiter", "reporting-sds-404@local")

    resp = client.get(
        "/reporting/stage-duration-summary?workflow_id=00000000-0000-0000-0000-000000000000",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp.status_code == 404


def test_reporting_stage_duration_summary_deterministic_stats(client: TestClient, db, org, monkeypatch):
    from app.core.request_context import RequestContext
    from app.domain.application.models import Application
    from app.domain.workflow.models import Workflow
    from app.services.audit_service import append_audit_log

    recruiter = _make_user(db, org, "recruiter", "reporting-sds@local")
    actor = _make_user(db, org, "hr_admin", "reporting-sds-actor@local")

    wf = Workflow(organization_id=org.id, name="wf")
    db.add(wf)
    db.commit()
    db.refresh(wf)

    base = datetime(2026, 2, 28, 12, 0, 0, tzinfo=timezone.utc)

    # App1: stage changes at t=10 and t=40, closed at t=100.
    app1 = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="closed",
        status="closed",
        created_at=base,
        stage_entered_at=base,
        closed_at=base + timedelta(seconds=100),
    )

    # App2: stage change at t=20, closed at t=80.
    app2 = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="closed",
        status="closed",
        created_at=base,
        stage_entered_at=base,
        closed_at=base + timedelta(seconds=80),
    )

    # Open app ignored.
    open_app = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="screening",
        status="active",
        created_at=base,
        stage_entered_at=base,
    )

    db.add_all([app1, app2, open_app])
    db.commit()
    db.refresh(app1)
    db.refresh(app2)
    db.refresh(open_app)

    ctx = RequestContext(
        organization_id=org.id,
        actor_id=str(actor.id),
        role="hr_admin",
        scopes=set(),
    )

    # app1: applied->screening at t=10
    monkeypatch.setattr("app.services.audit_service._now_utc", lambda: base + timedelta(seconds=10))
    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app1.id),
        action="stage_changed",
        payload="applied->screening",
    )

    # app1: screening->interview at t=40
    monkeypatch.setattr("app.services.audit_service._now_utc", lambda: base + timedelta(seconds=40))
    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app1.id),
        action="stage_changed",
        payload="screening->interview",
    )

    # app2: applied->screening at t=20
    monkeypatch.setattr("app.services.audit_service._now_utc", lambda: base + timedelta(seconds=20))
    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app2.id),
        action="stage_changed",
        payload="applied->screening",
    )

    # open_app stage change should not affect closed-only summary.
    monkeypatch.setattr("app.services.audit_service._now_utc", lambda: base + timedelta(seconds=30))
    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(open_app.id),
        action="stage_changed",
        payload="applied->screening",
    )
    db.commit()

    resp = client.get(
        f"/reporting/stage-duration-summary?workflow_id={wf.id}",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)

    by_stage = {row["stage"]: row for row in body}
    # screening durations: app1 (40-10=30), app2 (80-20=60)
    assert by_stage["screening"]["count"] == 2
    assert by_stage["screening"]["avg_duration_seconds"] == 45.0
    assert by_stage["screening"]["median_duration_seconds"] == 45.0
    assert by_stage["screening"]["p90_duration_seconds"] == 60.0

    # interview duration: app1 (100-40=60)
    assert by_stage["interview"]["count"] == 1
    assert by_stage["interview"]["avg_duration_seconds"] == 60.0
    assert by_stage["interview"]["median_duration_seconds"] == 60.0
    assert by_stage["interview"]["p90_duration_seconds"] == 60.0
