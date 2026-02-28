"""add application result

Revision ID: 9b6e6e1d7f2a
Revises: 3b2f4a1c9d8e
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "9b6e6e1d7f2a"
down_revision = "3b2f4a1c9d8e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("application", sa.Column("result", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("application", "result")
