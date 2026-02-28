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


def _make_user(db, org, role: str, email: str, *, language: str | None = None):
    from app.domain.identity.models import OrganizationMembership, User

    user = User(email=email, is_active=True, language=language)
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


def test_me_requires_headers(client: TestClient):
    resp = client.get("/me")
    assert resp.status_code in {401, 403}


def test_me_returns_effective_language_defaults_when_user_language_null(
    client: TestClient, db, org
):
    recruiter = _make_user(db, org, "recruiter", "me-default-lang@local")

    resp = client.get(
        "/me",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200

    correlation_header = resp.headers.get("X-Correlation-Id")
    assert correlation_header

    body = resp.json()

    assert body["organization_id"] == str(org.id)
    assert body["user_id"] == str(recruiter.id)
    assert isinstance(body["role"], str)

    assert isinstance(body["scopes"], list)
    assert body["scopes"] == sorted(body["scopes"])

    assert body["language"] is None
    assert body["default_language"] == "en"
    assert body["effective_language"] == body["default_language"]

    assert isinstance(body.get("ux"), dict)
    assert isinstance(body.get("features"), dict)

    assert body.get("correlation_id")
    assert body["correlation_id"] == correlation_header


def test_me_user_language_override_wins_over_policy_default(
    client: TestClient, db, org
):
    recruiter = _make_user(
        db,
        org,
        "recruiter",
        "me-user-lang@local",
        language="nl",
    )

    resp = client.get(
        "/me",
        headers={
            "X-Org-Id": str(org.id),
            "X-User-Id": str(recruiter.id),
        },
    )

    assert resp.status_code == 200
    body = resp.json()

    assert body["default_language"] == "en"
    assert body["language"] == "nl"
    assert body["effective_language"] == "nl"
