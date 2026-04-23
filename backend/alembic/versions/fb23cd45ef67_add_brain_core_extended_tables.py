"""add brain core extended tables (context snapshots, action executions, learning observations)

Revision ID: fb23cd45ef67
Revises: fa12bc34de56
Create Date: 2026-04-22 14:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "fb23cd45ef67"
down_revision: Union[str, None] = "fa12bc34de56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_brain_signal_context_snapshots",
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("signal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("context_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("context_sources", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["signal_id"], ["app_brain_signals.signal_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("snapshot_id"),
    )
    op.create_index("ix_brain_ctx_snapshots_signal_id", "app_brain_signal_context_snapshots", ["signal_id"])
    op.create_index("ix_brain_ctx_snapshots_tenant_id", "app_brain_signal_context_snapshots", ["tenant_id"])

    op.create_table(
        "app_brain_action_executions",
        sa.Column("execution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("action_type", sa.String(length=128), nullable=False),
        sa.Column("action_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decision_id"], ["app_brain_decisions.decision_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("execution_id"),
    )
    op.create_index("ix_brain_action_executions_decision_id", "app_brain_action_executions", ["decision_id"])
    op.create_index("ix_brain_action_executions_tenant_id", "app_brain_action_executions", ["tenant_id"])
    op.create_index("ix_brain_action_executions_status", "app_brain_action_executions", ["status"])

    op.create_table(
        "app_brain_learning_observations",
        sa.Column("observation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("outcome_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("signal_class", sa.String(length=128), nullable=False),
        sa.Column("decision_type", sa.String(length=64), nullable=False),
        sa.Column("effectiveness", sa.String(length=32), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("autonomy_level", sa.String(length=32), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decision_id"], ["app_brain_decisions.decision_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("observation_id"),
    )
    op.create_index("ix_brain_learning_observations_tenant_id", "app_brain_learning_observations", ["tenant_id"])
    op.create_index("ix_brain_learning_observations_decision_id", "app_brain_learning_observations", ["decision_id"])
    op.create_index("ix_brain_learning_observations_signal_class", "app_brain_learning_observations", ["signal_class"])


def downgrade() -> None:
    op.drop_index("ix_brain_learning_observations_signal_class", table_name="app_brain_learning_observations")
    op.drop_index("ix_brain_learning_observations_decision_id", table_name="app_brain_learning_observations")
    op.drop_index("ix_brain_learning_observations_tenant_id", table_name="app_brain_learning_observations")
    op.drop_table("app_brain_learning_observations")

    op.drop_index("ix_brain_action_executions_status", table_name="app_brain_action_executions")
    op.drop_index("ix_brain_action_executions_tenant_id", table_name="app_brain_action_executions")
    op.drop_index("ix_brain_action_executions_decision_id", table_name="app_brain_action_executions")
    op.drop_table("app_brain_action_executions")

    op.drop_index("ix_brain_ctx_snapshots_tenant_id", table_name="app_brain_signal_context_snapshots")
    op.drop_index("ix_brain_ctx_snapshots_signal_id", table_name="app_brain_signal_context_snapshots")
    op.drop_table("app_brain_signal_context_snapshots")
