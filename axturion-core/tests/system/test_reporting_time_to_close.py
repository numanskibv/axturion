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


def test_reporting_time_to_close_requires_reporting_read_scope(
    client: TestClient, db, org
):
    stage_operator = _make_user(db, org, "stage_operator", "no-reporting-ttc@local")
    resp = client.get(
        "/reporting/time-to-close",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(stage_operator.id),
        },
    )
    assert resp.status_code == 403


def test_reporting_time_to_close_stats_and_filters(client: TestClient, db, org):
    from app.domain.application.models import Application
    from app.domain.organization.models import Organization
    from app.domain.workflow.models import Workflow

    recruiter = _make_user(db, org, "recruiter", "reporting-ttc@local")

    other_org = Organization(name="other-org-ttc")
    db.add(other_org)
    db.commit()
    db.refresh(other_org)
    _make_user(db, other_org, "recruiter", "other-ttc@local")

    wf = Workflow(organization_id=org.id, name="wf")
    wf_other = Workflow(organization_id=other_org.id, name="wf2")
    db.add_all([wf, wf_other])
    db.commit()
    db.refresh(wf)
    db.refresh(wf_other)

    base = datetime(2026, 2, 28, 12, 0, 0, tzinfo=timezone.utc)

    # Closed apps in org: durations 10, 20, 90 seconds.
    a10 = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="closed",
        status="closed",
        result="hired",
        created_at=base,
        stage_entered_at=base,
        closed_at=base + timedelta(seconds=10),
    )
    a20 = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="closed",
        status="closed",
        result="rejected",
        created_at=base,
        stage_entered_at=base,
        closed_at=base + timedelta(seconds=20),
    )
    a90 = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="closed",
        status="closed",
        result="hired",
        created_at=base,
        stage_entered_at=base,
        closed_at=base + timedelta(seconds=90),
    )

    # Closed but missing closed_at should be ignored.
    a_missing = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="closed",
        status="closed",
        result="hired",
        created_at=base,
        stage_entered_at=base,
        closed_at=None,
    )

    # Open app ignored.
    a_open = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="applied",
        status="active",
        created_at=base,
        stage_entered_at=base,
    )

    # Other org closed app ignored.
    other = Application(
        organization_id=other_org.id,
        workflow_id=wf_other.id,
        stage="closed",
        status="closed",
        result="hired",
        created_at=base,
        stage_entered_at=base,
        closed_at=base + timedelta(seconds=999),
    )

    db.add_all([a10, a20, a90, a_missing, a_open, other])
    db.commit()

    resp = client.get(
        "/reporting/time-to-close",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 3
    assert body["min_seconds"] == 10
    assert body["max_seconds"] == 90
    assert body["avg_seconds"] == 40
    assert body["median_seconds"] == 20
    assert body["p90_seconds"] == 90

    resp_hired = client.get(
        "/reporting/time-to-close?result=hired",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp_hired.status_code == 200
    hired = resp_hired.json()
    assert hired["count"] == 2
    assert hired["min_seconds"] == 10
    assert hired["max_seconds"] == 90
    assert hired["avg_seconds"] == 50
    assert hired["median_seconds"] == 50
    assert hired["p90_seconds"] == 90

    resp_wf = client.get(
        f"/reporting/time-to-close?workflow_id={wf.id}",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp_wf.status_code == 200
    assert resp_wf.json()["count"] == 3
