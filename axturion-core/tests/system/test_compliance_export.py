import json
import zipfile
from io import BytesIO

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


def _seed_org(db, *, name: str):
    from app.domain.organization.models import Organization

    org = Organization(name=name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def _seed_user(db, *, org_id, role: str, email: str):
    from app.domain.identity.models import OrganizationMembership, User

    user = User(email=email, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(
        OrganizationMembership(
            organization_id=org_id,
            user_id=user.id,
            role=role,
            is_active=True,
        )
    )
    db.commit()
    return user


def _download_zip(client: TestClient, *, org_id, user_id):
    resp = client.get(
        "/compliance/export",
        headers={
            "X-Org-Id": str(org_id),
            "X-User-Id": str(user_id),
        },
    )
    return resp


def _zip_names(resp) -> list[str]:
    zf = zipfile.ZipFile(BytesIO(resp.content))
    return sorted(zf.namelist())


def _read_zip_json(resp, name: str):
    zf = zipfile.ZipFile(BytesIO(resp.content))
    with zf.open(name) as f:
        return json.loads(f.read().decode("utf-8"))


def test_hr_admin_can_download_export(client: TestClient, db):
    org = _seed_org(db, name="org-export-hr")
    hr_admin = _seed_user(db, org_id=org.id, role="hr_admin", email="hr@local")

    # Generate at least one audit row
    create_resp = client.post(
        "/candidates",
        json={"full_name": "A", "email": "a@local"},
        headers={"X-Org-Id": str(org.id), "X-User-Id": str(hr_admin.id)},
    )
    assert create_resp.status_code == 200

    resp = _download_zip(client, org_id=org.id, user_id=hr_admin.id)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/zip")
    assert "attachment" in resp.headers.get("content-disposition", "")

    names = _zip_names(resp)
    assert names == [
        "approvals_snapshot.json",
        "audit_chain.json",
        "audit_verification.json",
        "lifecycle_summary.json",
    ]


def test_auditor_can_download_export(client: TestClient, db):
    org = _seed_org(db, name="org-export-aud")
    recruiter = _seed_user(db, org_id=org.id, role="recruiter", email="r@local")
    auditor = _seed_user(db, org_id=org.id, role="auditor", email="aud@local")

    create_resp = client.post(
        "/candidates",
        json={"full_name": "B", "email": "b@local"},
        headers={"X-Org-Id": str(org.id), "X-User-Id": str(recruiter.id)},
    )
    assert create_resp.status_code == 200

    resp = _download_zip(client, org_id=org.id, user_id=auditor.id)
    assert resp.status_code == 200


def test_recruiter_denied_export(client: TestClient, db):
    org = _seed_org(db, name="org-export-deny")
    recruiter = _seed_user(db, org_id=org.id, role="recruiter", email="r2@local")

    resp = _download_zip(client, org_id=org.id, user_id=recruiter.id)
    assert resp.status_code == 403


def test_export_is_org_scoped_no_cross_org_leak(client: TestClient, db):
    org1 = _seed_org(db, name="org-export-1")
    org2 = _seed_org(db, name="org-export-2")

    org1_hr = _seed_user(db, org_id=org1.id, role="hr_admin", email="hr1@local")
    org2_hr = _seed_user(db, org_id=org2.id, role="hr_admin", email="hr2@local")

    # Create one candidate in each org to generate distinct audit chains.
    resp1 = client.post(
        "/candidates",
        json={"full_name": "Org1", "email": "org1@local"},
        headers={"X-Org-Id": str(org1.id), "X-User-Id": str(org1_hr.id)},
    )
    assert resp1.status_code == 200

    resp2 = client.post(
        "/candidates",
        json={"full_name": "Org2", "email": "org2@local"},
        headers={"X-Org-Id": str(org2.id), "X-User-Id": str(org2_hr.id)},
    )
    assert resp2.status_code == 200

    export2 = _download_zip(client, org_id=org2.id, user_id=org2_hr.id)
    assert export2.status_code == 200

    audit_chain = _read_zip_json(export2, "audit_chain.json")
    assert isinstance(audit_chain, list)
    assert len(audit_chain) >= 1
    assert all(item["organization_id"] == str(org2.id) for item in audit_chain)

    lifecycle = _read_zip_json(export2, "lifecycle_summary.json")
    assert lifecycle["total_candidates"] == 1


def test_export_truncates_audit_chain_when_over_cap(
    client: TestClient, db, monkeypatch
):
    monkeypatch.setattr("app.services.compliance_service.MAX_AUDIT_ENTRIES", 2)

    org = _seed_org(db, name="org-export-truncate")
    hr_admin = _seed_user(db, org_id=org.id, role="hr_admin", email="hr@local")

    for i in range(3):
        create_resp = client.post(
            "/candidates",
            json={"full_name": f"C{i}", "email": f"c{i}@local"},
            headers={"X-Org-Id": str(org.id), "X-User-Id": str(hr_admin.id)},
        )
        assert create_resp.status_code == 200

    export = _download_zip(client, org_id=org.id, user_id=hr_admin.id)
    assert export.status_code == 200

    audit_chain = _read_zip_json(export, "audit_chain.json")
    assert isinstance(audit_chain, list)
    assert len(audit_chain) == 2
    assert [item["seq"] for item in audit_chain] == sorted(
        item["seq"] for item in audit_chain
    )

    verification = _read_zip_json(export, "audit_verification.json")
    assert verification["export_truncated"] is True
    assert verification["exported_count"] == 2
    assert verification["total_count"] == 3
