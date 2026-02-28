import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base
from app.core.request_context import RequestContext
from app.domain.organization.models import Organization

# Import models to ensure all tables/FKs are registered on Base.metadata.
# Tests may only reference a subset, but create_all() needs the full FK graph.
from app.domain.application.models import Application  # noqa: F401
from app.domain.audit.models import AuditLog  # noqa: F401
from app.domain.automation.models import Activity, AutomationRule  # noqa: F401
from app.domain.candidate.models import Candidate  # noqa: F401
from app.domain.job.models import Job  # noqa: F401
from app.domain.identity.models import OrganizationMembership, User  # noqa: F401
from app.domain.governance.models import PolicyConfig  # noqa: F401
from app.domain.ux.models import UXConfig, PendingUXRollback  # noqa: F401
from app.domain.workflow.models import PendingStageTransition  # noqa: F401
from app.domain.workflow.models import (  # noqa: F401
    Workflow,
    WorkflowStage,
    WorkflowTransition,
)


TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine)

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def org(db):
    org = Organization(name="test-org")
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@pytest.fixture
def ctx(org):
    return RequestContext(
        organization_id=org.id,
        actor_id=str(uuid.uuid4()),
        role=None,
        scopes=set(),
    )
