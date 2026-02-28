import pytest

from app.core.request_context import RequestContext
from app.domain.organization.models import Organization
from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition
from app.domain.application.models import Application
from app.workflow.service import move_application_stage, OrganizationAccessError
from app.services.workflow_query_service import (
    get_allowed_transitions,
    OrganizationAccessError as QueryOrgAccessError,
)


def test_move_stage_cannot_cross_organization_boundary(db):
    org_a = Organization(name="org-a")
    org_b = Organization(name="org-b")
    db.add_all([org_a, org_b])
    db.commit()
    db.refresh(org_a)
    db.refresh(org_b)

    ctx_a = RequestContext(organization_id=org_a.id, actor_id="actor-a", scopes=())

    workflow_b = Workflow(name="Workflow B", organization_id=org_b.id)
    db.add(workflow_b)
    db.commit()
    db.refresh(workflow_b)

    db.add_all(
        [
            WorkflowStage(
                organization_id=org_b.id,
                workflow_id=workflow_b.id,
                name="applied",
                order=1,
            ),
            WorkflowStage(
                organization_id=org_b.id,
                workflow_id=workflow_b.id,
                name="screening",
                order=2,
            ),
        ]
    )
    db.add(
        WorkflowTransition(
            organization_id=org_b.id,
            workflow_id=workflow_b.id,
            from_stage="applied",
            to_stage="screening",
        )
    )
    db.commit()

    app_b = Application(
        organization_id=org_b.id, workflow_id=workflow_b.id, stage="applied"
    )
    db.add(app_b)
    db.commit()
    db.refresh(app_b)

    with pytest.raises(OrganizationAccessError):
        move_application_stage(db, ctx_a, app_b.id, "screening")


def test_allowed_transitions_cannot_cross_organization_boundary(db):
    org_a = Organization(name="org-a")
    org_b = Organization(name="org-b")
    db.add_all([org_a, org_b])
    db.commit()
    db.refresh(org_a)
    db.refresh(org_b)

    ctx_a = RequestContext(organization_id=org_a.id, actor_id="actor-a", scopes=())

    workflow_b = Workflow(name="Workflow B", organization_id=org_b.id)
    db.add(workflow_b)
    db.commit()
    db.refresh(workflow_b)

    db.add_all(
        [
            WorkflowStage(
                organization_id=org_b.id,
                workflow_id=workflow_b.id,
                name="applied",
                order=1,
            ),
            WorkflowStage(
                organization_id=org_b.id,
                workflow_id=workflow_b.id,
                name="screening",
                order=2,
            ),
        ]
    )
    db.add(
        WorkflowTransition(
            organization_id=org_b.id,
            workflow_id=workflow_b.id,
            from_stage="applied",
            to_stage="screening",
        )
    )
    db.commit()

    app_b = Application(
        organization_id=org_b.id, workflow_id=workflow_b.id, stage="applied"
    )
    db.add(app_b)
    db.commit()
    db.refresh(app_b)

    with pytest.raises(QueryOrgAccessError):
        get_allowed_transitions(db, ctx_a, str(app_b.id))
