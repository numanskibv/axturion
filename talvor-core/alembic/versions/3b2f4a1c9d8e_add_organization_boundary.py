"""add organization boundary

Revision ID: 3b2f4a1c9d8e
Revises: 7c158844e78e
Create Date: 2026-02-27

"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa


revision = "3b2f4a1c9d8e"
down_revision = "7c158844e78e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.UniqueConstraint("name"),
    )

    # Add columns as nullable first, backfill, then make NOT NULL.
    for table_name in (
        "workflow",
        "workflow_stage",
        "workflow_transition",
        "application",
        "candidate",
        "job",
        "audit_log",
        "activity",
        "automation_rule",
    ):
        op.add_column(
            table_name,
            sa.Column("organization_id", sa.UUID(), nullable=True),
        )

    org_id = uuid.uuid4()
    op.execute(
        sa.text("INSERT INTO organization (id, name) VALUES (:id, :name)").bindparams(
            id=org_id, name="default"
        )
    )

    for table_name in (
        "workflow",
        "workflow_stage",
        "workflow_transition",
        "application",
        "candidate",
        "job",
        "audit_log",
        "activity",
        "automation_rule",
    ):
        op.execute(
            sa.text(
                f"UPDATE {table_name} SET organization_id = :org_id WHERE organization_id IS NULL"
            ).bindparams(org_id=org_id)
        )

    for table_name in (
        "workflow",
        "workflow_stage",
        "workflow_transition",
        "application",
        "candidate",
        "job",
        "audit_log",
        "activity",
        "automation_rule",
    ):
        op.alter_column(table_name, "organization_id", nullable=False)

    op.create_foreign_key(
        "fk_workflow_organization",
        "workflow",
        "organization",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_workflow_stage_organization",
        "workflow_stage",
        "organization",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_workflow_transition_organization",
        "workflow_transition",
        "organization",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_application_organization",
        "application",
        "organization",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_candidate_organization",
        "candidate",
        "organization",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_job_organization",
        "job",
        "organization",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_audit_log_organization",
        "audit_log",
        "organization",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_activity_organization",
        "activity",
        "organization",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_automation_rule_organization",
        "automation_rule",
        "organization",
        ["organization_id"],
        ["id"],
    )


def downgrade() -> None:
    for constraint_name, table_name in (
        ("fk_automation_rule_organization", "automation_rule"),
        ("fk_activity_organization", "activity"),
        ("fk_audit_log_organization", "audit_log"),
        ("fk_job_organization", "job"),
        ("fk_candidate_organization", "candidate"),
        ("fk_application_organization", "application"),
        ("fk_workflow_transition_organization", "workflow_transition"),
        ("fk_workflow_stage_organization", "workflow_stage"),
        ("fk_workflow_organization", "workflow"),
    ):
        op.drop_constraint(constraint_name, table_name, type_="foreignkey")

    for table_name in (
        "automation_rule",
        "activity",
        "audit_log",
        "job",
        "candidate",
        "application",
        "workflow_transition",
        "workflow_stage",
        "workflow",
    ):
        op.drop_column(table_name, "organization_id")

    op.drop_table("organization")
