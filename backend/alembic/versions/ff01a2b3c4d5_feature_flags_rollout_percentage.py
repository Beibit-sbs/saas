"""Add rollout_percentage to app_platform_feature_flags

Revision ID: ff01a2b3c4d5
Revises: b0c1d2e3f4a5
Create Date: 2025-01-15 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "ff01a2b3c4d5"
down_revision = "b0c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_platform_feature_flags",
        sa.Column(
            "rollout_percentage",
            sa.Integer(),
            nullable=False,
            server_default="100",
        ),
    )
    op.create_check_constraint(
        "ck_platform_feature_flags_rollout_pct",
        "app_platform_feature_flags",
        "rollout_percentage >= 0 AND rollout_percentage <= 100",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_platform_feature_flags_rollout_pct",
        "app_platform_feature_flags",
        type_="check",
    )
    op.drop_column("app_platform_feature_flags", "rollout_percentage")
