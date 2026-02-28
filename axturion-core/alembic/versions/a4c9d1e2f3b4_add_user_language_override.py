"""add user language override

Revision ID: a4c9d1e2f3b4
Revises: 91b7c2d4e5f6
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a4c9d1e2f3b4"
down_revision = "91b7c2d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "language",
            sa.String(length=2),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_user_language",
        "user",
        "language is null or language in ('en','nl')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_user_language",
        "user",
        type_="check",
    )
    op.drop_column("user", "language")
