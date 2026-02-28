"""add ux_config table

Revision ID: bc3111b08e7f
Revises: 4d6b1a8c2f41
Create Date: 2026-02-28 13:15:14.047132

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bc3111b08e7f"
down_revision = "4d6b1a8c2f41"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ux_config",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("module", sa.String(), nullable=False),
        sa.Column("config", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ux_config")
