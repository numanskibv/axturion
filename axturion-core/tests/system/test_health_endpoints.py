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


def test_live_returns_alive(client: TestClient):
    resp = client.get("/live")
    assert resp.status_code == 200
    assert resp.json() == {"status": "alive"}

    assert "x-correlation-id" in {k.lower() for k in resp.headers.keys()}
    import uuid

    uuid.UUID(resp.headers["X-Correlation-Id"])


def test_ready_returns_keys(client: TestClient):
    resp = client.get("/ready")
    assert resp.status_code == 200

    data = resp.json()
    assert "status" in data
    assert "database" in data
    assert "migrations" in data


def test_health_returns_keys(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200

    data = resp.json()
    for key in (
        "status",
        "database",
        "migrations",
        "version",
        "build_hash",
        "uptime_seconds",
        "timestamp",
    ):
        assert key in data


def test_ready_not_ready_on_db_failure(client: TestClient, monkeypatch):
    """Optional: simulate DB failure via monkeypatch and ensure /ready reports not_ready."""

    # app.main imports the functions into its module namespace, so patch there.
    monkeypatch.setattr("app.main.check_database", lambda _db: False)

    resp = client.get("/ready")
    assert resp.status_code == 200

    data = resp.json()
    assert data["status"] == "not_ready"
