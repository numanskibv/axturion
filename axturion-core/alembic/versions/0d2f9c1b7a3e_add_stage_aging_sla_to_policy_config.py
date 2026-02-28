"""add stage_aging_sla_days to policy_config

Revision ID: 0d2f9c1b7a3e
Revises: f1c2d3e4a5b6
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0d2f9c1b7a3e"
down_revision = "f1c2d3e4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "policy_config",
        sa.Column(
            "stage_aging_sla_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("7"),
        ),
    )
    op.alter_column("policy_config", "stage_aging_sla_days", server_default=None)


def downgrade() -> None:
    op.drop_column("policy_config", "stage_aging_sla_days")
