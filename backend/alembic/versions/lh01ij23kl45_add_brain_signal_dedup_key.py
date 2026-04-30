"""Add dedup_key column to app_brain_signals for signal deduplication.

Revision ID: lh01ij23kl45
Revises: kg78hi90jk12
Create Date: 2026-04-26 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "lh01ij23kl45"
down_revision = "kg78hi90jk12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "app_brain_signals",
        sa.Column("dedup_key", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_app_brain_signals_tenant_dedup_key",
        "app_brain_signals",
        ["tenant_id", "dedup_key"],
    )


def downgrade() -> None:
    op.drop_index("ix_app_brain_signals_tenant_dedup_key", table_name="app_brain_signals")
    op.drop_column("app_brain_signals", "dedup_key")
