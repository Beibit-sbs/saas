"""platform core sprint b constraints

Revision ID: f2a3b4c5d6e7
Revises: f1a2b3c4d5e6
Create Date: 2026-03-23 19:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ux_platform_usage_tenant_metric_period",
        "app_platform_usage_counters",
        ["tenant_id", "metric", "period_key"],
        unique=True,
    )
    op.create_index(
        "ux_platform_subscriptions_active_per_tenant",
        "app_platform_subscriptions",
        ["tenant_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )
    op.create_index(
        "ux_platform_feature_flags_scope_tenant_module_key",
        "app_platform_feature_flags",
        ["scope", "tenant_id", "module", "key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_platform_feature_flags_scope_tenant_module_key", table_name="app_platform_feature_flags")
    op.drop_index("ux_platform_subscriptions_active_per_tenant", table_name="app_platform_subscriptions")
    op.drop_index("ux_platform_usage_tenant_metric_period", table_name="app_platform_usage_counters")
