"""add candidate phone and notes

Revision ID: c7c61b66c9af
Revises: 8a0a6e6b8e4c
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c7c61b66c9af"
down_revision = "8a0a6e6b8e4c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidate", sa.Column("phone", sa.String(), nullable=True))
    op.add_column("candidate", sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("candidate", "notes")
    op.drop_column("candidate", "phone")
