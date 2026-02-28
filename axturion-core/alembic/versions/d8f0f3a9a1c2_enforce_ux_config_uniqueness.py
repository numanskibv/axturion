"""enforce ux_config uniqueness

Revision ID: d8f0f3a9a1c2
Revises: bc3111b08e7f
Create Date: 2026-02-28 00:00:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d8f0f3a9a1c2"
down_revision = "bc3111b08e7f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Best-effort dedupe to avoid constraint failures if duplicates exist.
    # Keeps the most recently updated record per (organization_id, module).
    op.execute(
        sa.text(
            """
            WITH ranked AS (
                SELECT
                    id,
                    row_number() OVER (
                        PARTITION BY organization_id, module
                        ORDER BY updated_at DESC, created_at DESC, id DESC
                    ) AS rn
                FROM ux_config
            )
            DELETE FROM ux_config
            WHERE id IN (SELECT id FROM ranked WHERE rn > 1);
            """
        )
    )

    op.create_unique_constraint(
        "uq_ux_config_org_module",
        "ux_config",
        ["organization_id", "module"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_ux_config_org_module",
        "ux_config",
        type_="unique",
    )
