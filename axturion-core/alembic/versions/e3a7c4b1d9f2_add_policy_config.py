"""add policy_config

Revision ID: e3a7c4b1d9f2
Revises: d8f0f3a9a1c2
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e3a7c4b1d9f2"
down_revision = "d8f0f3a9a1c2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_config",
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column(
            "require_4eyes_on_hire",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "require_4eyes_on_ux_rollback",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("candidate_retention_days", sa.Integer(), nullable=True),
        sa.Column("audit_retention_days", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("organization_id"),
    )

    op.alter_column("policy_config", "require_4eyes_on_hire", server_default=None)
    op.alter_column(
        "policy_config", "require_4eyes_on_ux_rollback", server_default=None
    )


def downgrade() -> None:
    op.drop_table("policy_config")
