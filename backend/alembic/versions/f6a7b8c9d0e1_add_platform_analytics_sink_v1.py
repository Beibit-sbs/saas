"""add platform analytics sink v1

Revision ID: f6a7b8c9d0e1
Revises: f5a6b7c8d9e0
Create Date: 2026-03-24 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f6a7b8c9d0e1"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_platform_analytics_events",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("outbox_event_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("aggregate_type", sa.Text(), nullable=False),
        sa.Column("aggregate_id", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["outbox_event_id"],
            ["app_platform_outbox_events.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "outbox_event_id", name="uq_analytics_events_outbox_event_id"
        ),
    )

    op.create_table(
        "app_platform_tenant_kpi_snapshots",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column(
            "event_counts_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("total_events", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "snapshot_date", name="uq_kpi_snapshots_tenant_date"
        ),
    )

    op.create_index(
        "ix_platform_analytics_events_tenant_type",
        "app_platform_analytics_events",
        ["tenant_id", "event_type", "id"],
    )
    op.create_index(
        "ix_platform_analytics_events_tenant_created",
        "app_platform_analytics_events",
        ["tenant_id", "created_at"],
    )
    op.create_index(
        "ix_platform_kpi_snapshots_tenant_date",
        "app_platform_tenant_kpi_snapshots",
        ["tenant_id", sa.text("snapshot_date DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_platform_kpi_snapshots_tenant_date", table_name="app_platform_tenant_kpi_snapshots")
    op.drop_index("ix_platform_analytics_events_tenant_created", table_name="app_platform_analytics_events")
    op.drop_index("ix_platform_analytics_events_tenant_type", table_name="app_platform_analytics_events")
    op.drop_table("app_platform_tenant_kpi_snapshots")
    op.drop_table("app_platform_analytics_events")
