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


def _seed_pending_approval(db, org_name: str = "org"):
    from app.domain.organization.models import Organization
    from app.domain.identity.models import OrganizationMembership, User
    from app.domain.workflow.models import Workflow, WorkflowTransition
    from app.domain.application.models import Application

    org = Organization(name=org_name)
    db.add(org)
    db.commit()
    db.refresh(org)

    wf = Workflow(organization_id=org.id, name="wf")
    db.add(wf)
    db.commit()
    db.refresh(wf)

    # applied -> screening requires approval
    transition = WorkflowTransition(
        organization_id=org.id,
        workflow_id=wf.id,
        from_stage="applied",
        to_stage="screening",
        requires_approval=True,
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


def _create_pending_via_move_stage(client: TestClient, org, app, user):
    resp = client.post(
        f"/applications/{app.id}/move-stage",
        json={"new_stage": "screening"},
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(user.id),
        },
    )
    assert resp.status_code == 202


def test_recruiter_can_list_pending_approvals(client: TestClient, db):
    org, app, make_user = _seed_pending_approval(db)
    recruiter = make_user("recruiter", "recruiter@local")

    _create_pending_via_move_stage(client, org, app, recruiter)

    resp = client.get(
        "/approvals/pending",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    item = data[0]

    assert item["application_id"] == str(app.id)
    assert item["target_stage"] == "screening"
    assert item["initiated_by_user_id"] == str(recruiter.id)
    assert "initiated_at" in item
    assert isinstance(item["age_seconds"], int)
    assert item["age_seconds"] >= 0


def test_auditor_can_list_pending_approvals(client: TestClient, db):
    org, app, make_user = _seed_pending_approval(db, org_name="org-a")
    recruiter = make_user("recruiter", "recruiter@local")
    auditor = make_user("auditor", "auditor@local")

    _create_pending_via_move_stage(client, org, app, recruiter)

    resp = client.get(
        "/approvals/pending",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(auditor.id),
        },
    )

    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_user_without_reporting_read_cannot_list(client: TestClient, db):
    org, app, make_user = _seed_pending_approval(db, org_name="org-noreport")
    recruiter = make_user("recruiter", "recruiter@local")
    operator = make_user("stage_operator", "operator@local")

    _create_pending_via_move_stage(client, org, app, recruiter)

    resp = client.get(
        "/approvals/pending",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(operator.id),
        },
    )

    assert resp.status_code == 403


def test_cross_org_cannot_see_pending_list_or_detail(client: TestClient, db):
    org1, app1, make_user1 = _seed_pending_approval(db, org_name="org1")
    recruiter1 = make_user1("recruiter", "recruiter1@local")
    _create_pending_via_move_stage(client, org1, app1, recruiter1)

    org2, _app2, make_user2 = _seed_pending_approval(db, org_name="org2")
    auditor2 = make_user2("auditor", "auditor2@local")

    list_resp = client.get(
        "/approvals/pending",
        headers={
            "X-Org-Id": str(org2.id),
            "X-User-Id": str(auditor2.id),
        },
    )
    assert list_resp.status_code == 200
    assert list_resp.json() == []

    detail_resp = client.get(
        f"/approvals/pending/{app1.id}",
        headers={
            "X-Org-Id": str(org2.id),
            "X-User-Id": str(auditor2.id),
        },
    )
    assert detail_resp.status_code == 404


def test_reporting_summary_endpoint_returns_metrics(client: TestClient, db):
    org, app, make_user = _seed_pending_approval(db, org_name="org-summary")
    recruiter = make_user("recruiter", "recruiter@local")

    _create_pending_via_move_stage(client, org, app, recruiter)

    resp = client.get(
        "/reporting/approvals/summary",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_pending"] == 1
    assert data["oldest_pending_age_seconds"] >= 0
    assert data["avg_pending_age_seconds"] >= 0
