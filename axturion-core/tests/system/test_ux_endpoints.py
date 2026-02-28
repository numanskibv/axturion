import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.domain.audit.models import AuditLog  # noqa: F401 (register model)
from app.domain.ux.models import UXConfig, PendingUXRollback  # noqa: F401 (register model)


@pytest.fixture
def client(db, monkeypatch):
    """System-level client wired to sqlite in-memory."""

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


def test_get_ux_config_returns_empty_when_missing(client: TestClient, db, org):
    recruiter = _make_user(db, org, "recruiter", "recruiter-ux@local")

    resp = client.get(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    assert resp.json() == {"module": "applications", "config": {}}


def test_get_ux_config_returns_saved_config(client: TestClient, db, org):
    recruiter = _make_user(db, org, "recruiter", "recruiter-ux2@local")

    db.add(
        UXConfig(
            organization_id=org.id,
            module="applications",
            config={
                "layout": "compact",
                "theme": "defense-dark",
                "flags": {"beta": True},
            },
        )
    )
    db.commit()

    resp = client.get(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["module"] == "applications"
    assert body["config"]["layout"] == "compact"
    assert "theme" not in body["config"]
    assert body["config"]["flags"]["beta"] is True


def test_get_ux_config_requires_scope(client: TestClient, db, org):
    # hr_admin has UX_READ, so we verify a role without defined mapping is blocked.
    user = _make_user(db, org, "unknown_role", "no-scope@local")

    resp = client.get(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(user.id),
        },
    )

    assert resp.status_code == 403


def test_put_ux_config_requires_ux_write_scope(client: TestClient, db, org):
    recruiter = _make_user(db, org, "recruiter", "recruiter-no-write@local")

    resp = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
        json={"layout": "compact"},
    )

    assert resp.status_code == 403


def test_put_ux_config_validates_and_creates_audit_log(client: TestClient, db, org):
    hr_admin = _make_user(db, org, "hr_admin", "admin-ux-write@local")

    resp = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={
            "layout": "dense",
            "theme": "defense",
            "flags": {"beta": True},
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["module"] == "applications"
    assert body["config"]["layout"] == "dense"
    assert body["config"]["theme"] == "defense"
    assert body["config"]["flags"]["beta"] is True

    audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == org.id,
            AuditLog.action == "ux_config_updated",
            AuditLog.entity_type == "ux_config",
        )
        .order_by(AuditLog.seq.desc())
        .first()
    )
    assert audit is not None
    assert audit.entity_id == f"{org.id}:applications"

    import json

    payload = json.loads(audit.payload)
    assert payload["module"] == "applications"
    assert payload["config"]["layout"] == "dense"
    assert payload["config"]["theme"] == "defense"
    assert payload["config"]["flags"]["beta"] is True


def test_put_ux_config_rejects_invalid_layout(client: TestClient, db, org):
    hr_admin = _make_user(db, org, "hr_admin", "admin-ux-invalid@local")

    resp = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={"layout": "wide"},
    )

    assert resp.status_code == 422


def test_list_versions_returns_expected_count(client: TestClient, db, org):
    hr_admin = _make_user(db, org, "hr_admin", "admin-ux-versions@local")

    r1 = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={"layout": "compact"},
    )
    assert r1.status_code == 200

    r2 = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={"layout": "dense", "theme": "defense"},
    )
    assert r2.status_code == 200

    resp = client.get(
        "/ux/applications/versions",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert body[0]["version"] == 1
    assert body[1]["version"] == 2
    assert body[0]["is_active"] is False
    assert body[1]["is_active"] is True


def test_rollback_updates_config_and_creates_audit_entry(client: TestClient, db, org):
    hr_admin = _make_user(db, org, "hr_admin", "admin-ux-rollback@local")

    r1 = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={"layout": "compact", "theme": "light"},
    )
    assert r1.status_code == 200

    r2 = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={"layout": "dense", "theme": "defense"},
    )
    assert r2.status_code == 200

    rollback = client.post(
        "/ux/applications/rollback",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={"version": 1},
    )
    assert rollback.status_code == 200
    body = rollback.json()
    assert body["config"]["layout"] == "compact"
    assert body["config"]["theme"] == "light"

    current = client.get(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
    )
    assert current.status_code == 200
    current_body = current.json()
    assert current_body["config"]["layout"] == "compact"
    assert current_body["config"]["theme"] == "light"

    audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == org.id,
            AuditLog.action == "ux_config_rollback",
            AuditLog.entity_type == "ux_config",
        )
        .order_by(AuditLog.seq.desc())
        .first()
    )
    assert audit is not None
    assert audit.entity_id == f"{org.id}:applications"

    import json

    payload = json.loads(audit.payload)
    assert payload["rolled_back_to_version"] == 1


def test_rollback_invalid_version_returns_404(client: TestClient, db, org):
    hr_admin = _make_user(db, org, "hr_admin", "admin-ux-rollback-404@local")

    r1 = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={"layout": "compact"},
    )
    assert r1.status_code == 200

    rollback = client.post(
        "/ux/applications/rollback",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={"version": 999},
    )
    assert rollback.status_code == 404


def test_ux_rollback_requires_second_approver_when_policy_enabled(client: TestClient, db, org):
    hr_admin1 = _make_user(db, org, "hr_admin", "admin-ux-4eyes-1@local")
    hr_admin2 = _make_user(db, org, "hr_admin", "admin-ux-4eyes-2@local")

    policy = client.put(
        "/governance/policy",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin1.id),
        },
        json={"require_4eyes_on_ux_rollback": True},
    )
    assert policy.status_code == 200
    assert policy.json()["require_4eyes_on_ux_rollback"] is True

    v1 = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin1.id),
        },
        json={"layout": "compact", "theme": "light"},
    )
    assert v1.status_code == 200

    v2 = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin1.id),
        },
        json={"layout": "dense", "theme": "defense"},
    )
    assert v2.status_code == 200

    first = client.post(
        "/ux/applications/rollback",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin1.id),
        },
        json={"version": 1},
    )
    assert first.status_code == 202
    assert first.json() == {"approval_required": True}

    pending = (
        db.query(PendingUXRollback)
        .filter(
            PendingUXRollback.organization_id == org.id,
            PendingUXRollback.module == "applications",
        )
        .one_or_none()
    )
    assert pending is not None
    assert int(pending.version) == 1
    assert str(pending.requested_by) == str(hr_admin1.id)

    pending_audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == org.id,
            AuditLog.entity_type == "ux_config",
            AuditLog.action == "ux_rollback_pending",
            AuditLog.entity_id == f"{org.id}:applications",
        )
        .order_by(AuditLog.seq.desc())
        .first()
    )
    assert pending_audit is not None

    same_user_second = client.post(
        "/ux/applications/rollback",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin1.id),
        },
        json={"version": 1},
    )
    assert same_user_second.status_code == 403

    approved = client.post(
        "/ux/applications/rollback",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin2.id),
        },
        json={"version": 1},
    )
    assert approved.status_code == 200
    body = approved.json()
    assert body["config"]["layout"] == "compact"
    assert body["config"]["theme"] == "light"

    pending_after = (
        db.query(PendingUXRollback)
        .filter(
            PendingUXRollback.organization_id == org.id,
            PendingUXRollback.module == "applications",
        )
        .one_or_none()
    )
    assert pending_after is None

    approved_audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.organization_id == org.id,
            AuditLog.entity_type == "ux_config",
            AuditLog.action == "ux_rollback_approved",
            AuditLog.entity_id == f"{org.id}:applications",
        )
        .order_by(AuditLog.seq.desc())
        .first()
    )
    assert approved_audit is not None


def test_versions_include_diff_vs_previous(client: TestClient, db, org):
    hr_admin = _make_user(db, org, "hr_admin", "admin-ux-diff@local")

    v1 = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={
            "layout": "compact",
            "theme": "light",
            "flags": {"a": True, "b": False},
        },
    )
    assert v1.status_code == 200

    v2 = client.put(
        "/ux/applications",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
        json={
            "layout": "dense",
            "theme": "light",
            "flags": {"a": False, "c": True},
        },
    )
    assert v2.status_code == 200

    resp = client.get(
        "/ux/applications/versions",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(hr_admin.id),
        },
    )
    assert resp.status_code == 200
    body = resp.json()

    assert len(body) == 2
    assert body[0]["version"] == 1
    assert body[0]["diff"] is None

    diff = body[1]["diff"]
    assert diff["layout"] == {"from": "compact", "to": "dense"}
    assert "theme" not in diff  # unchanged
    assert diff["flags_added"] == ["c"]
    assert diff["flags_removed"] == ["b"]
    assert diff["flags_changed"] == [{"key": "a", "from": True, "to": False}]
