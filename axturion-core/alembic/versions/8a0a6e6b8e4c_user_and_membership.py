"""user and organization membership

Revision ID: 8a0a6e6b8e4c
Revises: 2cf2b24f0b0b
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "8a0a6e6b8e4c"
down_revision = "2cf2b24f0b0b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "organization_membership",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_user"),
    )

    op.alter_column("user", "is_active", server_default=None)
    op.alter_column("organization_membership", "is_active", server_default=None)


def downgrade() -> None:
    op.drop_table("organization_membership")
    op.drop_table("user")
