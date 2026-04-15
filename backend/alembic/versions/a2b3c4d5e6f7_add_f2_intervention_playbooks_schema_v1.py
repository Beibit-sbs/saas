"""add f2 intervention playbooks schema v1

Revision ID: a2b3c4d5e6f7
Revises: 1b2c3d4e5f6a
Create Date: 2026-04-13 00:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a2b3c4d5e6f7"
down_revision = "1b2c3d4e5f6a"
branch_labels = None
depends_on = None


playbook_step_action_type = postgresql.ENUM(
    "consultation_scheduled",
    "notification_sent",
    "plan_updated",
    "advisor_meeting",
    "escalation",
    "resource_assigned",
    "note",
    name="playbook_step_action_type",
    create_type=False,
)

playbook_assignee_role = postgresql.ENUM(
    "advisor",
    "registrar",
    "program_manager",
    "dean",
    name="playbook_assignee_role",
    create_type=False,
)

playbook_trigger_type = postgresql.ENUM(
    "manual",
    "auto",
    name="playbook_trigger_type",
    create_type=False,
)

playbook_execution_status = postgresql.ENUM(
    "pending",
    "in_progress",
    "completed",
    "abandoned",
    name="playbook_execution_status",
    create_type=False,
)

playbook_step_execution_status = postgresql.ENUM(
    "pending",
    "completed",
    "skipped",
    name="playbook_step_execution_status",
    create_type=False,
)


def upgrade() -> None:
    # --- ENUM types ---
    playbook_step_action_type.create(op.get_bind(), checkfirst=True)
    playbook_assignee_role.create(op.get_bind(), checkfirst=True)
    playbook_trigger_type.create(op.get_bind(), checkfirst=True)
    playbook_execution_status.create(op.get_bind(), checkfirst=True)
    playbook_step_execution_status.create(op.get_bind(), checkfirst=True)

    # --- app_playbooks ---
    op.create_table(
        "app_playbooks",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_threshold_id", sa.BigInteger(), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("updated_by", sa.String(255), nullable=False),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["trigger_threshold_id"],
            ["app_risk_thresholds.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_playbooks_tenant_name"),
    )
    op.create_index("ix_playbooks_tenant_id", "app_playbooks", ["tenant_id"])
    op.create_index(
        "ix_playbooks_trigger_threshold_id",
        "app_playbooks",
        ["trigger_threshold_id"],
    )

    # --- app_playbook_steps ---
    op.create_table(
        "app_playbook_steps",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("playbook_id", sa.BigInteger(), nullable=False),
        sa.Column("step_order", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "action_type",
            playbook_step_action_type,
            nullable=False,
        ),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("is_mandatory", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("due_days_offset", sa.SmallInteger(), server_default=sa.text("3"), nullable=False),
        sa.Column(
            "assignee_role",
            playbook_assignee_role,
            server_default=sa.text("'advisor'"),
            nullable=False,
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["playbook_id"], ["app_playbooks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "playbook_id", "step_order", name="uq_playbook_steps_order"
        ),
    )
    op.create_index("ix_playbook_steps_playbook_id", "app_playbook_steps", ["playbook_id"])

    # --- app_playbook_executions ---
    op.create_table(
        "app_playbook_executions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("playbook_id", sa.BigInteger(), nullable=False),
        sa.Column("case_id", sa.BigInteger(), nullable=True),
        sa.Column("student_profile_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "triggered_by",
            playbook_trigger_type,
            server_default=sa.text("'manual'"),
            nullable=False,
        ),
        sa.Column(
            "status",
            playbook_execution_status,
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("abandoned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("abandon_reason", sa.Text(), nullable=True),
        sa.Column("outcome_delta_score", sa.Numeric(precision=6, scale=3), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(255), nullable=False),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["playbook_id"], ["app_playbooks.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["app_intervention_cases.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_playbook_executions_tenant_id", "app_playbook_executions", ["tenant_id"]
    )
    op.create_index(
        "ix_playbook_executions_playbook_id",
        "app_playbook_executions",
        ["playbook_id"],
    )
    op.create_index(
        "ix_playbook_executions_case_id", "app_playbook_executions", ["case_id"]
    )
    op.create_index(
        "ix_playbook_executions_status",
        "app_playbook_executions",
        ["tenant_id", "status"],
    )
    op.create_index(
        "ix_playbook_executions_student",
        "app_playbook_executions",
        ["tenant_id", "student_profile_id", "started_at"],
    )

    # --- app_playbook_step_executions ---
    op.create_table(
        "app_playbook_step_executions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("execution_id", sa.BigInteger(), nullable=False),
        sa.Column("step_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            playbook_step_execution_status,
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column("performed_by", sa.String(255), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome_note", sa.Text(), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["execution_id"],
            ["app_playbook_executions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["step_id"], ["app_playbook_steps.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "execution_id",
            "step_id",
            name="uq_playbook_step_executions_exec_step",
        ),
    )
    op.create_index(
        "ix_playbook_step_executions_execution_id",
        "app_playbook_step_executions",
        ["execution_id"],
    )


def downgrade() -> None:
    op.drop_table("app_playbook_step_executions")
    op.drop_index("ix_playbook_executions_student", "app_playbook_executions")
    op.drop_index("ix_playbook_executions_status", "app_playbook_executions")
    op.drop_index("ix_playbook_executions_case_id", "app_playbook_executions")
    op.drop_index("ix_playbook_executions_playbook_id", "app_playbook_executions")
    op.drop_index("ix_playbook_executions_tenant_id", "app_playbook_executions")
    op.drop_table("app_playbook_executions")
    op.drop_index("ix_playbook_steps_playbook_id", "app_playbook_steps")
    op.drop_table("app_playbook_steps")
    op.drop_index("ix_playbooks_trigger_threshold_id", "app_playbooks")
    op.drop_index("ix_playbooks_tenant_id", "app_playbooks")
    op.drop_table("app_playbooks")

    playbook_step_execution_status.drop(op.get_bind(), checkfirst=True)
    playbook_execution_status.drop(op.get_bind(), checkfirst=True)
    playbook_trigger_type.drop(op.get_bind(), checkfirst=True)
    playbook_assignee_role.drop(op.get_bind(), checkfirst=True)
    playbook_step_action_type.drop(op.get_bind(), checkfirst=True)
