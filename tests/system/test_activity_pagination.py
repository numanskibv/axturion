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


def _seed_org_and_user(db, *, org_name: str, role: str, email: str):
    from app.domain.organization.models import Organization
    from app.domain.identity.models import OrganizationMembership, User

    org = Organization(name=org_name)
    db.add(org)
    db.commit()
    db.refresh(org)

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

    return org, user


def _seed_activities(db, *, org_id, count: int, entity_type: str, entity_id: str):
    from app.domain.automation.models import Activity

    rows = [
        Activity(
            organization_id=org_id,
            entity_type=entity_type,
            entity_id=entity_id,
            type="test",
            message="",
            payload={"i": i},
        )
        for i in range(count)
    ]
    db.add_all(rows)
    db.commit()


def test_activity_endpoints_paginate_and_cap_limit(client: TestClient, db):
    org, user = _seed_org_and_user(
        db,
        org_name="org-activity-page",
        role="recruiter",
        email="recruiter@local",
    )

    _seed_activities(
        db,
        org_id=org.id,
        count=600,
        entity_type="candidate",
        entity_id="cand-1",
    )

    headers = {"X-Org-Id": str(org.id), "X-User-Id": str(user.id)}

    default_list = client.get("/activity/activities", headers=headers)
    assert default_list.status_code == 200
    assert len(default_list.json()) == 50

    limit_10_list = client.get("/activity/activities?limit=10", headers=headers)
    assert limit_10_list.status_code == 200
    assert len(limit_10_list.json()) == 10

    capped_list = client.get("/activity/activities?limit=1000", headers=headers)
    assert capped_list.status_code == 200
    assert len(capped_list.json()) == 500

    default_timeline = client.get("/activity/candidate/cand-1", headers=headers)
    assert default_timeline.status_code == 200
    assert len(default_timeline.json()) == 50

    limit_10_timeline = client.get(
        "/activity/candidate/cand-1?limit=10",
        headers=headers,
    )
    assert limit_10_timeline.status_code == 200
    assert len(limit_10_timeline.json()) == 10

    capped_timeline = client.get(
        "/activity/candidate/cand-1?limit=1000",
        headers=headers,
    )
    assert capped_timeline.status_code == 200
    assert len(capped_timeline.json()) == 500
