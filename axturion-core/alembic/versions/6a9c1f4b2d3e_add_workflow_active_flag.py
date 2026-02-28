"""add workflow active flag

Revision ID: 6a9c1f4b2d3e
Revises: 0d2f9c1b7a3e
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "6a9c1f4b2d3e"
down_revision = "0d2f9c1b7a3e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workflow",
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.alter_column("workflow", "active", server_default=None)


def downgrade() -> None:
    op.drop_column("workflow", "active")
