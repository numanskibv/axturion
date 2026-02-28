"""job lifecycle fields

Revision ID: 2cf2b24f0b0b
Revises: 9b6e6e1d7f2a
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "2cf2b24f0b0b"
down_revision = "9b6e6e1d7f2a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job", sa.Column("description", sa.String(), nullable=True))
    op.add_column(
        "job",
        sa.Column("status", sa.String(), nullable=False, server_default="open"),
    )
    op.add_column(
        "job", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True)
    )

    # Remove the server default after backfill.
    op.alter_column("job", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("job", "closed_at")
    op.drop_column("job", "status")
    op.drop_column("job", "description")
