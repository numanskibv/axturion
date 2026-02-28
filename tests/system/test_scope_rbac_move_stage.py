import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def client(db, monkeypatch):
    """System-level client wired to sqlite in-memory.

    Notes:
    - Uses the existing `db` fixture (sqlite in-memory) for an engine.
    - Overrides DB dependency to create per-request sessions.
    - Neutralizes startup side effects that would require Postgres/migrations.
    """

    # Import inside the fixture so monkeypatching can happen before TestClient
    # triggers FastAPI lifespan events.
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

    # Ensure startup doesn't try to talk to Postgres or seed workflow tables.
    monkeypatch.setattr("app.main.core_db.wait_for_db", lambda: None)
    monkeypatch.setattr("app.main.core_db.init_db", lambda _settings: None)
    monkeypatch.setattr("app.main.verify_startup", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.main.seed_identity", lambda _db: None)
    monkeypatch.setattr("app.main.seed_workflow", lambda _db: None)
    monkeypatch.setattr("app.main.seed_automation", lambda _db: None)

    # Ensure settings load doesn't require env in tests.
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: Settings(DATABASE_URL=str(engine.url), ENV="test", LOG_LEVEL="INFO"),
    )

    # Patch SessionLocal used by lifespan to use sqlite.
    monkeypatch.setattr(core_db, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.main.core_db", core_db)

    # Override FastAPI dependency for DB sessions.
    app.dependency_overrides[core_db.get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def _seed_move_stage_data(db):
    from app.domain.organization.models import Organization
    from app.domain.identity.models import OrganizationMembership, User
    from app.domain.workflow.models import Workflow, WorkflowTransition
    from app.domain.application.models import Application

    org = Organization(name="org")
    db.add(org)
    db.commit()
    db.refresh(org)

    wf = Workflow(organization_id=org.id, name="wf")
    db.add(wf)
    db.commit()
    db.refresh(wf)

    transition = WorkflowTransition(
        organization_id=org.id,
        workflow_id=wf.id,
        from_stage="applied",
        to_stage="screening",
    )
    db.add(transition)

    app = Application(
        organization_id=org.id,
        workflow_id=wf.id,
        stage="applied",
        status="active",
    )
    db.add(app)

    db.commit()
    db.refresh(app)

    def make_user(role: str):
        user = User(email=f"{role}@local", is_active=True)
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

    return org, app, make_user


def test_move_stage_denied_missing_user_id_header(client: TestClient, db):
    org, app, _make_user = _seed_move_stage_data(db)

    resp = client.post(
        f"/applications/{app.id}/move-stage",
        json={"new_stage": "screening"},
        headers={
            "X-Org-Id": str(org.id),
        },
    )

    assert resp.status_code == 401


def test_move_stage_denied_for_auditor_membership(client: TestClient, db):
    org, app, make_user = _seed_move_stage_data(db)
    auditor = make_user("auditor")

    resp = client.post(
        f"/applications/{app.id}/move-stage",
        json={"new_stage": "screening"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )

    assert resp.status_code == 403


def test_move_stage_denied_for_unknown_role_membership(client: TestClient, db):
    org, app, make_user = _seed_move_stage_data(db)
    unknown = make_user("does_not_exist")

    resp = client.post(
        f"/applications/{app.id}/move-stage",
        json={"new_stage": "screening"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(unknown.id),
        },
    )

    assert resp.status_code == 403


def test_move_stage_allowed_for_recruiter_membership(client: TestClient, db):
    org, app, make_user = _seed_move_stage_data(db)
    recruiter = make_user("recruiter")

    resp = client.post(
        f"/applications/{app.id}/move-stage",
        json={"new_stage": "screening"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    assert resp.json() == {"id": str(app.id), "new_stage": "screening"}
