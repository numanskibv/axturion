"""add pending_ux_rollback

Revision ID: f1c2d3e4a5b6
Revises: e3a7c4b1d9f2
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f1c2d3e4a5b6"
down_revision = "e3a7c4b1d9f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_ux_rollback",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("module", sa.String(), nullable=False),
        sa.Column("requested_by", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "module",
            name="uq_pending_ux_rollback_org_module",
        ),
    )

    op.create_index(
        "ix_pending_ux_rollback_org",
        "pending_ux_rollback",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_pending_ux_rollback_org", table_name="pending_ux_rollback")
    op.drop_table("pending_ux_rollback")
