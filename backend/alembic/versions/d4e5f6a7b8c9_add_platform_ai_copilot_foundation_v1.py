"""add platform ai copilot foundation v1 query logs

Revision ID: d4e5f6a7b8c9
Revises: c1d2e3f4a5b6
Create Date: 2026-03-24 12:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "d4e5f6a7b8c9"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_platform_ai_copilot_query_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), sa.ForeignKey("app_tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("query_type", sa.String(length=64), nullable=False),
        sa.Column(
            "retrieved_sources_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "answer_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "ix_platform_ai_copilot_logs_tenant",
        "app_platform_ai_copilot_query_logs",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "ix_platform_ai_copilot_logs_created_at",
        "app_platform_ai_copilot_query_logs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_platform_ai_copilot_logs_created_at", table_name="app_platform_ai_copilot_query_logs")
    op.drop_index("ix_platform_ai_copilot_logs_tenant", table_name="app_platform_ai_copilot_query_logs")
    op.drop_table("app_platform_ai_copilot_query_logs")
