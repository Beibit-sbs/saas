"""A-031.5 rector assignment outbox, SLA policy, escalation policy tables.

Revision ID: ar46st58uv69
Revises: zq35rs47tu58
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "ar46st58uv69"
down_revision = "zq35rs47tu58"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 11. rector_assignment_outbox_events
    op.create_table(
        "rector_assignment_outbox_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), sa.ForeignKey("rector_assignments.id"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("recipient_user_id", sa.BigInteger(), nullable=True),
        sa.Column("recipient_role", sa.String(100), nullable=True),
        sa.Column("channel", sa.String(20), nullable=False, server_default="IN_APP"),
        sa.Column("payload_json", JSONB(), nullable=False, server_default="'{}'::jsonb"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rao_outbox_tenant_id", "rector_assignment_outbox_events", ["tenant_id"])
    op.create_index("ix_rao_outbox_tenant_assignment", "rector_assignment_outbox_events", ["tenant_id", "assignment_id"])
    op.create_index("ix_rao_outbox_tenant_status", "rector_assignment_outbox_events", ["tenant_id", "status"])
    op.create_index("ix_rao_outbox_tenant_event_type", "rector_assignment_outbox_events", ["tenant_id", "event_type"])

    # 12. rector_assignment_sla_policies
    op.create_table(
        "rector_assignment_sla_policies",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("priority", sa.String(20), nullable=True),
        sa.Column("due_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("warning_before_hours", sa.Integer(), nullable=False, server_default="48"),
        sa.Column("overdue_after_hours", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("escalation_after_hours", sa.Integer(), nullable=False, server_default="72"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rao_sla_tenant_id", "rector_assignment_sla_policies", ["tenant_id"])
    op.create_index("ix_rao_sla_tenant_active", "rector_assignment_sla_policies", ["tenant_id", "is_active"])
    op.create_index("ix_rao_sla_tenant_priority", "rector_assignment_sla_policies", ["tenant_id", "priority"])

    # 13. rector_assignment_escalation_policies
    op.create_table(
        "rector_assignment_escalation_policies",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_priority", sa.String(20), nullable=False),
        sa.Column("escalation_level", sa.Integer(), nullable=False),
        sa.Column("escalate_to_role", sa.String(100), nullable=False),
        sa.Column("escalate_after_hours", sa.Integer(), nullable=False, server_default="72"),
        sa.Column("require_manual_confirmation", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rao_esc_policy_tenant_id", "rector_assignment_escalation_policies", ["tenant_id"])
    op.create_index("ix_rao_esc_policy_tenant_active", "rector_assignment_escalation_policies", ["tenant_id", "is_active"])
    op.create_index("ix_rao_esc_policy_tenant_level", "rector_assignment_escalation_policies", ["tenant_id", "escalation_level"])
    op.create_index("ix_rao_esc_policy_tenant_priority", "rector_assignment_escalation_policies", ["tenant_id", "assignment_priority"])


def downgrade() -> None:
    op.drop_table("rector_assignment_escalation_policies")
    op.drop_table("rector_assignment_sla_policies")
    op.drop_table("rector_assignment_outbox_events")
