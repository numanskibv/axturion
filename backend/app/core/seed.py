import json

from sqlalchemy.orm import Session

from app.domain.automation.models import AutomationRule
from app.domain.identity.models import OrganizationMembership, User
from app.domain.organization.models import Organization
from app.domain.workflow.models import Workflow, WorkflowStage, WorkflowTransition


def seed_identity(db: Session) -> None:
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="default")
        db.add(org)
        db.commit()
        db.refresh(org)

    # Seed user (idempotent).
    seed_email = "seed@local"
    user = db.query(User).filter(User.email == seed_email).first()
    if not user:
        user = User(email=seed_email, is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.organization_id == org.id,
            OrganizationMembership.user_id == user.id,
        )
        .first()
    )
    if membership:
        # Ensure seed membership stays active and has intended role.
        membership.is_active = True
        membership.role = "hr_admin"
        db.add(membership)
        db.commit()
        return

    db.add(
        OrganizationMembership(
            organization_id=org.id,
            user_id=user.id,
            role="hr_admin",
            is_active=True,
        )
    )
    db.commit()


def seed_workflow(db: Session) -> None:
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="default")
        db.add(org)
        db.commit()
        db.refresh(org)

    existing = db.query(Workflow).filter(Workflow.organization_id == org.id).first()
    if existing:
        return

    wf = Workflow(name="default hiring", organization_id=org.id)
    db.add(wf)
    db.flush()

    stages = ["applied", "screening", "interview", "offer", "hired"]
    for i, stage in enumerate(stages):
        db.add(
            WorkflowStage(
                organization_id=org.id,
                workflow_id=wf.id,
                name=stage,
                order=i,
            )
        )

    transitions = [
        ("applied", "screening"),
        ("screening", "interview"),
        ("interview", "offer"),
        ("offer", "hired"),
    ]
    for from_stage, to_stage in transitions:
        db.add(
            WorkflowTransition(
                organization_id=org.id,
                workflow_id=wf.id,
                from_stage=from_stage,
                to_stage=to_stage,
            )
        )

    db.commit()


def seed_automation(db: Session) -> None:
    org = db.query(Organization).first()
    if not org:
        org = Organization(name="default")
        db.add(org)
        db.commit()
        db.refresh(org)

    existing = (
        db.query(AutomationRule)
        .filter(AutomationRule.organization_id == org.id)
        .first()
    )
    if existing:
        return

    rule = AutomationRule(
        organization_id=org.id,
        name="When moved to interview -> create activity + send email",
        event_type="application.stage_changed",
        enabled="true",
        condition_key="to_stage",
        condition_value="interview",
        action_type="create_activity",
        action_payload=json.dumps(
            {
                "type": "task",
                "message": "Schedule interview with candidate",
            }
        ),
    )
    db.add(rule)
    db.commit()
