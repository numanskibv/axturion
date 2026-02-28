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


def test_reporting_stage_duration_breakdown_requires_reporting_read_scope(
    client: TestClient, db, org
):
    stage_operator = _make_user(db, org, "stage_operator", "no-reporting-sdb@local")

    resp = client.get(
        "/reporting/stage-duration-breakdown?workflow_id=00000000-0000-0000-0000-000000000000",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(stage_operator.id),
        },
    )
    assert resp.status_code == 403


def test_reporting_stage_duration_breakdown_full_window_and_4eyes(
    client: TestClient, db, org, monkeypatch
):
    from app.core.request_context import RequestContext
    from app.domain.application.models import Application
    from app.domain.workflow.models import Workflow
    from app.services.audit_service import append_audit_log

    recruiter = _make_user(db, org, "recruiter", "reporting-sdb@local")
    actor = _make_user(db, org, "hr_admin", "reporting-sdb-actor@local")

    wf = Workflow(organization_id=org.id, name="wf")
    db.add(wf)
    db.commit()
    db.refresh(wf)

    base = datetime(2026, 2, 28, 12, 0, 0, tzinfo=timezone.utc)
    monkeypatch.setattr("app.services.stage_duration_breakdown_service._now_utc", lambda: base)

    t0 = base - timedelta(hours=6)
    t1 = base - timedelta(hours=5)
    t2 = base - timedelta(hours=3)
    t3 = base - timedelta(hours=1)

    app = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="interview",
        status="closed",
        created_at=t0,
        stage_entered_at=t0,
        closed_at=t3,
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    ctx = RequestContext(
        organization_id=org.id,
        actor_id=str(actor.id),
        role="hr_admin",
        scopes=set(),
    )

    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app.id),
        action="stage_changed",
        payload="applied->screening",
        created_at=t1,
    )
    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app.id),
        action="stage_transition_approved",
        payload={"from_stage": "screening", "to_stage": "interview"},
        created_at=t2,
    )
    db.commit()

    resp = client.get(
        f"/reporting/stage-duration-breakdown?workflow_id={wf.id}",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)

    by_stage = {row["stage"]: row for row in body}

    # applied: t0->t1 (1h)
    assert by_stage["applied"]["count"] == 1
    assert by_stage["applied"]["median_seconds"] == 3600
    assert by_stage["applied"]["p90_seconds"] == 3600

    # screening: t1->t2 (2h)
    assert by_stage["screening"]["median_seconds"] == 7200
    assert by_stage["screening"]["p90_seconds"] == 7200

    # interview: t2->t3 (2h)
    assert by_stage["interview"]["median_seconds"] == 7200
    assert by_stage["interview"]["p90_seconds"] == 7200


def test_reporting_stage_duration_breakdown_pre_window_stage_resolution(
    client: TestClient, db, org
):
    from app.core.request_context import RequestContext
    from app.domain.application.models import Application
    from app.domain.workflow.models import Workflow
    from app.services.audit_service import append_audit_log

    recruiter = _make_user(db, org, "recruiter", "reporting-sdb-window@local")
    actor = _make_user(db, org, "hr_admin", "reporting-sdb-window-actor@local")

    wf = Workflow(organization_id=org.id, name="wf")
    db.add(wf)
    db.commit()
    db.refresh(wf)

    base = datetime(2026, 2, 28, 12, 0, 0, tzinfo=timezone.utc)

    t0 = base - timedelta(hours=6)
    t1 = base - timedelta(hours=5)
    t2 = base - timedelta(hours=3)
    t3 = base - timedelta(hours=1)

    app = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="interview",
        status="closed",
        created_at=t0,
        stage_entered_at=t0,
        closed_at=t3,
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    ctx = RequestContext(
        organization_id=org.id,
        actor_id=str(actor.id),
        role="hr_admin",
        scopes=set(),
    )

    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app.id),
        action="stage_changed",
        payload="applied->screening",
        created_at=t1,
    )
    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app.id),
        action="stage_transition_approved",
        payload={"from_stage": "screening", "to_stage": "interview"},
        created_at=t2,
    )
    db.commit()

    window_from = (t1 + timedelta(hours=1)).isoformat().replace("+00:00", "Z")

    resp = client.get(
        f"/reporting/stage-duration-breakdown?workflow_id={wf.id}&from={window_from}",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    by_stage = {row["stage"]: row for row in body}

    # From t1+1h to t2: 1h of screening.
    assert by_stage["screening"]["median_seconds"] == 3600
    # From t2 to t3: 2h of interview.
    assert by_stage["interview"]["median_seconds"] == 7200
    # No applied contribution after window_from.
    assert "applied" not in by_stage


def test_reporting_stage_duration_breakdown_to_capping(
    client: TestClient, db, org
):
    from app.core.request_context import RequestContext
    from app.domain.application.models import Application
    from app.domain.workflow.models import Workflow
    from app.services.audit_service import append_audit_log

    recruiter = _make_user(db, org, "recruiter", "reporting-sdb-to@local")
    actor = _make_user(db, org, "hr_admin", "reporting-sdb-to-actor@local")

    wf = Workflow(organization_id=org.id, name="wf")
    db.add(wf)
    db.commit()
    db.refresh(wf)

    base = datetime(2026, 2, 28, 12, 0, 0, tzinfo=timezone.utc)

    t0 = base - timedelta(hours=6)
    t1 = base - timedelta(hours=5)
    t2 = base - timedelta(hours=3)
    t3 = base - timedelta(hours=1)

    app = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="interview",
        status="closed",
        created_at=t0,
        stage_entered_at=t0,
        closed_at=t3,
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    ctx = RequestContext(
        organization_id=org.id,
        actor_id=str(actor.id),
        role="hr_admin",
        scopes=set(),
    )

    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app.id),
        action="stage_changed",
        payload="applied->screening",
        created_at=t1,
    )
    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app.id),
        action="stage_transition_approved",
        payload={"from_stage": "screening", "to_stage": "interview"},
        created_at=t2,
    )
    db.commit()

    window_to = (t2 + timedelta(hours=1)).isoformat().replace("+00:00", "Z")

    resp = client.get(
        f"/reporting/stage-duration-breakdown?workflow_id={wf.id}&to={window_to}",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    by_stage = {row["stage"]: row for row in body}

    # interview should be capped to 1h (t2 -> t2+1h)
    assert by_stage["interview"]["median_seconds"] == 3600


def test_reporting_stage_duration_breakdown_org_isolation(
    client: TestClient, db, org
):
    from app.core.request_context import RequestContext
    from app.domain.application.models import Application
    from app.domain.organization.models import Organization
    from app.domain.workflow.models import Workflow
    from app.services.audit_service import append_audit_log

    recruiter = _make_user(db, org, "recruiter", "reporting-sdb-org@local")
    actor = _make_user(db, org, "hr_admin", "reporting-sdb-org-actor@local")

    other_org = Organization(name="other-org-sdb")
    db.add(other_org)
    db.commit()
    db.refresh(other_org)
    other_user = _make_user(db, other_org, "hr_admin", "reporting-sdb-other@local")

    wf = Workflow(organization_id=org.id, name="wf")
    wf_other = Workflow(organization_id=other_org.id, name="wf")
    db.add_all([wf, wf_other])
    db.commit()
    db.refresh(wf)
    db.refresh(wf_other)

    base = datetime(2026, 2, 28, 12, 0, 0, tzinfo=timezone.utc)
    t0 = base - timedelta(hours=2)
    t1 = base - timedelta(hours=1)

    app = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="screening",
        status="active",
        created_at=t0,
        stage_entered_at=t0,
    )
    app_other = Application(
        organization_id=other_org.id,
        workflow_id=wf_other.id,
        stage="screening",
        status="active",
        created_at=t0,
        stage_entered_at=t0,
    )
    db.add_all([app, app_other])
    db.commit()
    db.refresh(app)
    db.refresh(app_other)

    ctx = RequestContext(
        organization_id=org.id,
        actor_id=str(actor.id),
        role="hr_admin",
        scopes=set(),
    )
    ctx_other = RequestContext(
        organization_id=other_org.id,
        actor_id=str(other_user.id),
        role="hr_admin",
        scopes=set(),
    )

    append_audit_log(
        db,
        ctx,
        entity_type="application",
        entity_id=str(app.id),
        action="stage_changed",
        payload="x->y",
        created_at=t1,
    )
    append_audit_log(
        db,
        ctx_other,
        entity_type="application",
        entity_id=str(app_other.id),
        action="stage_changed",
        payload="x->leak",
        created_at=t1,
    )
    db.commit()

    resp = client.get(
        f"/reporting/stage-duration-breakdown?workflow_id={wf.id}",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert all(row["stage"] != "leak" for row in body)
