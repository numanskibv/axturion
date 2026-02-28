"""add policy default language

Revision ID: 91b7c2d4e5f6
Revises: 6a9c1f4b2d3e
Create Date: 2026-02-28

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "91b7c2d4e5f6"
down_revision = "6a9c1f4b2d3e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "policy_config",
        sa.Column(
            "default_language",
            sa.String(length=2),
            nullable=False,
            server_default=sa.text("'en'"),
        ),
    )
    op.create_check_constraint(
        "ck_policy_config_default_language",
        "policy_config",
        "default_language in ('en','nl')",
    )
    op.alter_column("policy_config", "default_language", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "ck_policy_config_default_language",
        "policy_config",
        type_="check",
    )
    op.drop_column("policy_config", "default_language")
