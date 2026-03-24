"""add platform ai copilot recommendation logs v1

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-24 10:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_platform_ai_copilot_recommendation_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("actor_id", sa.String(length=255), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("recommendation_type", sa.String(length=128), nullable=False),
        sa.Column(
            "context_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "recommendation_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["app_tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_platform_ai_rec_logs_tenant",
        "app_platform_ai_copilot_recommendation_logs",
        ["tenant_id"],
    )
    op.create_index(
        "ix_platform_ai_rec_logs_type",
        "app_platform_ai_copilot_recommendation_logs",
        ["recommendation_type"],
    )
    op.create_index(
        "ix_platform_ai_rec_logs_created_at",
        "app_platform_ai_copilot_recommendation_logs",
        ["created_at"],
        postgresql_ops={"created_at": "DESC"},
    )


def downgrade() -> None:
    op.drop_index("ix_platform_ai_rec_logs_created_at", "app_platform_ai_copilot_recommendation_logs")
    op.drop_index("ix_platform_ai_rec_logs_type", "app_platform_ai_copilot_recommendation_logs")
    op.drop_index("ix_platform_ai_rec_logs_tenant", "app_platform_ai_copilot_recommendation_logs")
    op.drop_table("app_platform_ai_copilot_recommendation_logs")
