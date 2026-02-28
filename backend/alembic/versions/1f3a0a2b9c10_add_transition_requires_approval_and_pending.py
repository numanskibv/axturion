"""add transition requires_approval and pending stage transitions

Revision ID: 1f3a0a2b9c10
Revises: c7c61b66c9af
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "1f3a0a2b9c10"
down_revision = "c7c61b66c9af"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow_transition",
        sa.Column(
            "requires_approval",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.alter_column("workflow_transition", "requires_approval", server_default=None)

    op.create_table(
        "pending_stage_transition",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("application_id", sa.UUID(), nullable=False),
        sa.Column("target_stage", sa.String(), nullable=False),
        sa.Column("initiated_by_user_id", sa.UUID(), nullable=False),
        sa.Column(
            "initiated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("approved_by_user_id", sa.UUID(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["application_id"], ["application.id"]),
    )


def downgrade() -> None:
    op.drop_table("pending_stage_transition")
    op.drop_column("workflow_transition", "requires_approval")
