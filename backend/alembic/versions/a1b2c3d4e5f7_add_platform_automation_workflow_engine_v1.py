"""add platform automation workflow engine v1

Revision ID: a1b2c3d4e5f7
Revises: f7b8c9d0e1f2
Create Date: 2026-03-24 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f7"
down_revision = "f7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_platform_automation_rules",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column(
            "condition_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "actions_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "app_platform_automation_executions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("rule_id", sa.BigInteger(), nullable=False),
        sa.Column("event_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(32), server_default="pending", nullable=False),
        sa.Column(
            "result_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_platform_automation_rules_tenant",
        "app_platform_automation_rules",
        ["tenant_id"],
    )
    op.create_index(
        "ix_platform_automation_rules_event_type",
        "app_platform_automation_rules",
        ["tenant_id", "event_type"],
    )
    op.create_index(
        "ix_platform_automation_executions_tenant",
        "app_platform_automation_executions",
        ["tenant_id"],
    )
    op.create_index(
        "ix_platform_automation_executions_rule",
        "app_platform_automation_executions",
        ["rule_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_platform_automation_executions_rule", table_name="app_platform_automation_executions")
    op.drop_index("ix_platform_automation_executions_tenant", table_name="app_platform_automation_executions")
    op.drop_index("ix_platform_automation_rules_event_type", table_name="app_platform_automation_rules")
    op.drop_index("ix_platform_automation_rules_tenant", table_name="app_platform_automation_rules")
    op.drop_table("app_platform_automation_executions")
    op.drop_table("app_platform_automation_rules")
