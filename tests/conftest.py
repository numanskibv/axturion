import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base

# Import models to ensure all tables/FKs are registered on Base.metadata.
# Tests may only reference a subset, but create_all() needs the full FK graph.
from app.domain.application.models import Application  # noqa: F401
from app.domain.audit.models import AuditLog  # noqa: F401
from app.domain.automation.models import Activity, AutomationRule  # noqa: F401
from app.domain.candidate.models import Candidate  # noqa: F401
from app.domain.job.models import Job  # noqa: F401
from app.domain.workflow.models import (  # noqa: F401
    Workflow,
    WorkflowStage,
    WorkflowTransition,
)


TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db():
    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(bind=engine)

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
