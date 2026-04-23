"""create brain core tables

Revision ID: fa12bc34de56
Revises: f9d0e1a2b3c4
Create Date: 2026-04-22 12:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "fa12bc34de56"
down_revision: Union[str, None] = "f9d0e1a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_brain_signals",
        sa.Column("signal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("signal_class", sa.String(length=128), nullable=False),
        sa.Column("source_module", sa.String(length=128), nullable=False),
        sa.Column("source_entity_type", sa.String(length=128), nullable=False),
        sa.Column("source_entity_id", sa.String(length=255), nullable=False),
        sa.Column("subject_student_id", sa.String(length=255), nullable=True),
        sa.Column("subject_faculty_id", sa.String(length=255), nullable=True),
        sa.Column("subject_course_id", sa.String(length=255), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'received'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("signal_id"),
    )
    op.create_index("ix_brain_signals_tenant_id", "app_brain_signals", ["tenant_id"])
    op.create_index("ix_brain_signals_correlation_id", "app_brain_signals", ["correlation_id"])
    op.create_index("ix_brain_signals_event_type", "app_brain_signals", ["event_type"])
    op.create_index("ix_brain_signals_signal_class", "app_brain_signals", ["signal_class"])

    op.create_table(
        "app_brain_decisions",
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("signal_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("correlation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_type", sa.String(length=64), nullable=False),
        sa.Column("situation_type", sa.String(length=128), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("severity_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("urgency_score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_by", sa.String(length=255), nullable=False, server_default=sa.text("'brain_core'")),
        sa.Column("policy_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["signal_id"], ["app_brain_signals.signal_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("decision_id"),
    )
    op.create_index("ix_brain_decisions_tenant_id", "app_brain_decisions", ["tenant_id"])
    op.create_index("ix_brain_decisions_correlation_id", "app_brain_decisions", ["correlation_id"])
    op.create_index("ix_brain_decisions_status", "app_brain_decisions", ["status"])

    op.create_table(
        "app_brain_action_plans",
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'planned'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decision_id"], ["app_brain_decisions.decision_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("plan_id"),
    )
    op.create_index("ix_brain_action_plans_tenant_id", "app_brain_action_plans", ["tenant_id"])

    op.create_table(
        "app_brain_outcomes",
        sa.Column("outcome_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("outcome_type", sa.String(length=64), nullable=False),
        sa.Column("outcome_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("effectiveness", sa.String(length=32), nullable=False, server_default=sa.text("'neutral'")),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["decision_id"], ["app_brain_decisions.decision_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("outcome_id"),
    )
    op.create_index("ix_brain_outcomes_tenant_id", "app_brain_outcomes", ["tenant_id"])

    op.create_table(
        "app_brain_explanations",
        sa.Column("explanation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("factors", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("policy_notes", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("expected_outcome", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["decision_id"], ["app_brain_decisions.decision_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("explanation_id"),
    )
    op.create_index("ix_brain_explanations_decision_id", "app_brain_explanations", ["decision_id"])

    op.create_table(
        "app_brain_policy_profiles",
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("autonomy_level", sa.String(length=32), nullable=False, server_default=sa.text("'level_1'")),
        sa.Column("decision_type", sa.String(length=64), nullable=False),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("approval_role", sa.String(length=255), nullable=True),
        sa.Column("requires_notification", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notification_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("profile_id"),
    )
    op.create_index("ix_brain_policy_profiles_tenant_id", "app_brain_policy_profiles", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_brain_policy_profiles_tenant_id", table_name="app_brain_policy_profiles")
    op.drop_table("app_brain_policy_profiles")

    op.drop_index("ix_brain_explanations_decision_id", table_name="app_brain_explanations")
    op.drop_table("app_brain_explanations")

    op.drop_index("ix_brain_outcomes_tenant_id", table_name="app_brain_outcomes")
    op.drop_table("app_brain_outcomes")

    op.drop_index("ix_brain_action_plans_tenant_id", table_name="app_brain_action_plans")
    op.drop_table("app_brain_action_plans")

    op.drop_index("ix_brain_decisions_status", table_name="app_brain_decisions")
    op.drop_index("ix_brain_decisions_correlation_id", table_name="app_brain_decisions")
    op.drop_index("ix_brain_decisions_tenant_id", table_name="app_brain_decisions")
    op.drop_table("app_brain_decisions")

    op.drop_index("ix_brain_signals_signal_class", table_name="app_brain_signals")
    op.drop_index("ix_brain_signals_event_type", table_name="app_brain_signals")
    op.drop_index("ix_brain_signals_correlation_id", table_name="app_brain_signals")
    op.drop_index("ix_brain_signals_tenant_id", table_name="app_brain_signals")
    op.drop_table("app_brain_signals")
