from __future__ import annotations

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


def test_workflows_list_requires_workflow_read_scope(client: TestClient, db, org):
    stage_operator = _make_user(db, org, "stage_operator", "no-workflows@local")

    resp = client.get(
        "/workflows",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(stage_operator.id),
        },
    )
    assert resp.status_code == 403


def test_workflows_list_org_scoped_ordered_and_lightweight(client: TestClient, db, org):
    from app.domain.organization.models import Organization
    from app.domain.workflow.models import Workflow

    recruiter = _make_user(db, org, "recruiter", "workflow-read@local")

    other_org = Organization(name="other-org-workflows")
    db.add(other_org)
    db.commit()
    db.refresh(other_org)
    _make_user(db, other_org, "recruiter", "other-workflow-read@local")

    wf_b = Workflow(organization_id=org.id, name="b", active=False)
    wf_a = Workflow(organization_id=org.id, name="a", active=True)
    wf_other = Workflow(organization_id=other_org.id, name="c", active=True)

    db.add_all([wf_b, wf_a, wf_other])
    db.commit()
    db.refresh(wf_a)
    db.refresh(wf_b)

    resp = client.get(
        "/workflows",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )
    assert resp.status_code == 200

    body = resp.json()
    assert isinstance(body, list)

    # Org isolation.
    ids = {row["id"] for row in body}
    assert str(wf_a.id) in ids
    assert str(wf_b.id) in ids
    assert str(wf_other.id) not in ids

    # Ordered by name ASC.
    names = [row["name"] for row in body]
    assert names == sorted(names)

    # Only lightweight fields are returned.
    for row in body:
        assert set(row.keys()) == {"id", "name", "active"}

    by_id = {row["id"]: row for row in body}
    assert by_id[str(wf_a.id)]["active"] is True
    assert by_id[str(wf_b.id)]["active"] is False
