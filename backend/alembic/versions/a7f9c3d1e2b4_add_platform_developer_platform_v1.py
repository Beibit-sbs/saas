"""add platform developer platform v1

Revision ID: a7f9c3d1e2b4
Revises: f6a7b8c9d0e2
Create Date: 2026-03-24 16:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a7f9c3d1e2b4"
down_revision = "f6a7b8c9d0e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_platform_developer_apps",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("app_key", sa.Text(), nullable=False),
        sa.Column("app_secret_hash", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("owner_email", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("webhook_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("app_key"),
    )

    op.create_table(
        "app_platform_developer_app_scopes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("app_id", sa.BigInteger(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["app_id"], ["app_platform_developer_apps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("app_id", "scope"),
    )

    op.create_table(
        "app_platform_developer_app_installations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("app_id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("installed_by", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["app_id"], ["app_platform_developer_apps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("app_id", "tenant_id"),
    )

    op.create_table(
        "app_platform_developer_api_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("app_id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["app_id"], ["app_platform_developer_apps.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "app_platform_app_event_subscriptions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("app_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["app_id"], ["app_platform_developer_apps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_platform_developer_apps_status",
        "app_platform_developer_apps",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_platform_developer_installations_tenant",
        "app_platform_developer_app_installations",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_platform_developer_api_logs_app_created",
        "app_platform_developer_api_logs",
        ["app_id", "created_at"],
    )
    op.create_index(
        "ix_platform_developer_event_subscriptions_event",
        "app_platform_app_event_subscriptions",
        ["event_type", "app_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_platform_developer_event_subscriptions_event", table_name="app_platform_app_event_subscriptions")
    op.drop_index("ix_platform_developer_api_logs_app_created", table_name="app_platform_developer_api_logs")
    op.drop_index("ix_platform_developer_installations_tenant", table_name="app_platform_developer_app_installations")
    op.drop_index("ix_platform_developer_apps_status", table_name="app_platform_developer_apps")

    op.drop_table("app_platform_app_event_subscriptions")
    op.drop_table("app_platform_developer_api_logs")
    op.drop_table("app_platform_developer_app_installations")
    op.drop_table("app_platform_developer_app_scopes")
    op.drop_table("app_platform_developer_apps")