"""add platform kpi metrics engine v1

Revision ID: f7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-03-24 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_platform_tenant_metric_snapshots",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("metric_key", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "metric_key", "snapshot_date", name="uq_metric_snapshots_tenant_metric_date"),
    )

    op.create_table(
        "app_platform_tenant_dashboard_snapshots",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column(
            "snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "snapshot_date", name="uq_dashboard_snapshots_tenant_date"),
    )

    op.create_index(
        "ix_platform_metric_snapshots_tenant_date",
        "app_platform_tenant_metric_snapshots",
        ["tenant_id", sa.text("snapshot_date DESC")],
    )
    op.create_index(
        "ix_platform_metric_snapshots_tenant_key_date",
        "app_platform_tenant_metric_snapshots",
        ["tenant_id", "metric_key", sa.text("snapshot_date DESC")],
    )
    op.create_index(
        "ix_platform_dashboard_snapshots_tenant_date",
        "app_platform_tenant_dashboard_snapshots",
        ["tenant_id", sa.text("snapshot_date DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_platform_dashboard_snapshots_tenant_date", table_name="app_platform_tenant_dashboard_snapshots")
    op.drop_index("ix_platform_metric_snapshots_tenant_key_date", table_name="app_platform_tenant_metric_snapshots")
    op.drop_index("ix_platform_metric_snapshots_tenant_date", table_name="app_platform_tenant_metric_snapshots")
    op.drop_table("app_platform_tenant_dashboard_snapshots")
    op.drop_table("app_platform_tenant_metric_snapshots")
