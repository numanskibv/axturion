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


def _seed_move_stage_data(db, *, requires_approval: bool):
    from app.domain.organization.models import Organization
    from app.domain.identity.models import OrganizationMembership, User
    from app.domain.workflow.models import Workflow, WorkflowTransition
    from app.domain.application.models import Application

    org = Organization(name=f"org-{'approval' if requires_approval else 'direct'}")
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
        requires_approval=requires_approval,
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

    return org, app, make_user


def test_transition_without_approval_works_as_before(client: TestClient, db):
    org, app, make_user = _seed_move_stage_data(db, requires_approval=False)
    recruiter = make_user("recruiter", "recruiter@local")

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


def test_transition_with_approval_requires_second_user(client: TestClient, db):
    org, app, make_user = _seed_move_stage_data(db, requires_approval=True)
    user1 = make_user("recruiter", "user1@local")
    user2 = make_user("recruiter", "user2@local")

    first = client.post(
        f"/applications/{app.id}/move-stage",
        json={"new_stage": "screening"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(user1.id),
        },
    )
    assert first.status_code == 202
    assert first.json()["detail"] == "approval_required"

    self_approve = client.post(
        f"/applications/{app.id}/move-stage",
        json={"new_stage": "screening"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(user1.id),
        },
    )
    assert self_approve.status_code == 403

    approved = client.post(
        f"/applications/{app.id}/move-stage",
        json={"new_stage": "screening"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(user2.id),
        },
    )
    assert approved.status_code == 200
    assert approved.json() == {"id": str(app.id), "new_stage": "screening"}


def test_cross_org_is_forbidden_even_with_pending(client: TestClient, db):
    org, app, make_user = _seed_move_stage_data(db, requires_approval=True)
    user1 = make_user("recruiter", "user1@local")

    pending = client.post(
        f"/applications/{app.id}/move-stage",
        json={"new_stage": "screening"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(user1.id),
        },
    )
    assert pending.status_code == 202

    from app.domain.organization.models import Organization
    from app.domain.identity.models import OrganizationMembership, User

    other_org = Organization(name="other-org")
    db.add(other_org)
    db.commit()
    db.refresh(other_org)

    other_user = User(email="other@local", is_active=True)
    db.add(other_user)
    db.commit()
    db.refresh(other_user)

    db.add(
        OrganizationMembership(
            organization_id=other_org.id,
            user_id=other_user.id,
            role="recruiter",
            is_active=True,
        )
    )
    db.commit()

    denied = client.post(
        f"/applications/{app.id}/move-stage",
        json={"new_stage": "screening"},
        headers={
            "X-Org-Id": str(other_org.id),
            "X-User-Id": str(other_user.id),
        },
    )

    assert denied.status_code == 403
