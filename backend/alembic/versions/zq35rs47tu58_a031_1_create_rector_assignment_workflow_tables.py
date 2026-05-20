"""A-031.1 create rector assignment workflow tables.

Revision ID: zq35rs47tu58
Revises: yp24qr56st78
Create Date: 2025-01-01 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "zq35rs47tu58"
down_revision = "yp24qr56st78"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. rector_assignments
    op.create_table(
        "rector_assignments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assignment_number", sa.String(64), nullable=True),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("priority", sa.String(16), nullable=False, server_default="NORMAL"),
        sa.Column("status", sa.String(32), nullable=False, server_default="DRAFT"),
        sa.Column("originator_user_id", sa.BigInteger(), nullable=False),
        sa.Column("originator_role", sa.String(64), nullable=True),
        sa.Column("owner_user_id", sa.BigInteger(), nullable=True),
        sa.Column("responsible_unit_id", sa.BigInteger(), nullable=True),
        sa.Column("source_decree_id", sa.BigInteger(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("recurrence_type", sa.String(16), nullable=False, server_default="NONE"),
        sa.Column("recurrence_config", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rector_assignments_tenant_id", "rector_assignments", ["tenant_id"])
    op.create_index("ix_rector_assignments_tenant_status", "rector_assignments", ["tenant_id", "status"])
    op.create_index("ix_rector_assignments_tenant_due_date", "rector_assignments", ["tenant_id", "due_date"])
    op.create_index("ix_rector_assignments_tenant_priority", "rector_assignments", ["tenant_id", "priority"])
    op.create_index("ix_rector_assignments_tenant_originator", "rector_assignments", ["tenant_id", "originator_user_id"])
    op.create_index("ix_rector_assignments_tenant_created", "rector_assignments", ["tenant_id", "created_at"])

    # 2. rector_assignment_tasks
    op.create_table(
        "rector_assignment_tasks",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assignee_user_id", sa.BigInteger(), nullable=True),
        sa.Column("assignee_unit_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rector_assignment_tasks_tenant_id", "rector_assignment_tasks", ["tenant_id"])
    op.create_index("ix_rector_assignment_tasks_tenant_assignment", "rector_assignment_tasks", ["tenant_id", "assignment_id"])

    # 3. rector_assignment_assignees
    op.create_table(
        "rector_assignment_assignees",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("unit_id", sa.BigInteger(), nullable=True),
        sa.Column("role_on_assignment", sa.String(32), nullable=False, server_default="RESPONSIBLE"),
        sa.Column("assigned_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rector_assignment_assignees_tenant_id", "rector_assignment_assignees", ["tenant_id"])
    op.create_index("ix_rector_assignment_assignees_tenant_assignment", "rector_assignment_assignees", ["tenant_id", "assignment_id"])
    op.create_index("ix_rector_assignment_assignees_tenant_user", "rector_assignment_assignees", ["tenant_id", "user_id"])

    # 4. rector_assignment_reports
    op.create_table(
        "rector_assignment_reports",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=False),
        sa.Column("submitted_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("reporting_period_start", sa.Date(), nullable=False),
        sa.Column("reporting_period_end", sa.Date(), nullable=False),
        sa.Column("progress_percent", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("blockers", sa.Text(), nullable=True),
        sa.Column("next_steps", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="SUBMITTED"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("reviewed_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rector_assignment_reports_tenant_id", "rector_assignment_reports", ["tenant_id"])
    op.create_index("ix_rector_assignment_reports_tenant_assignment", "rector_assignment_reports", ["tenant_id", "assignment_id"])
    op.create_index("ix_rector_assignment_reports_tenant_submitted_by", "rector_assignment_reports", ["tenant_id", "submitted_by_user_id"])

    # 5. rector_assignment_evidence
    op.create_table(
        "rector_assignment_evidence",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=False),
        sa.Column("report_id", sa.BigInteger(), nullable=True),
        sa.Column("evidence_type", sa.String(32), nullable=False),
        sa.Column("file_id", sa.BigInteger(), nullable=True),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("uploaded_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by_user_id", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rector_assignment_evidence_tenant_id", "rector_assignment_evidence", ["tenant_id"])
    op.create_index("ix_rector_assignment_evidence_tenant_assignment", "rector_assignment_evidence", ["tenant_id", "assignment_id"])

    # 6. rector_assignment_comments
    op.create_table(
        "rector_assignment_comments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=False),
        sa.Column("parent_comment_id", sa.BigInteger(), nullable=True),
        sa.Column("author_user_id", sa.BigInteger(), nullable=False),
        sa.Column("author_role", sa.String(64), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("visibility", sa.String(32), nullable=False, server_default="ASSIGNEES"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rector_assignment_comments_tenant_id", "rector_assignment_comments", ["tenant_id"])
    op.create_index("ix_rector_assignment_comments_tenant_assignment", "rector_assignment_comments", ["tenant_id", "assignment_id"])

    # 7. rector_assignment_status_history (INSERT-ONLY)
    op.create_table(
        "rector_assignment_status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=False),
        sa.Column("old_status", sa.String(32), nullable=True),
        sa.Column("new_status", sa.String(32), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=False),
        sa.Column("actor_role", sa.String(64), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rector_assignment_status_history_tenant_id", "rector_assignment_status_history", ["tenant_id"])
    op.create_index("ix_rector_assignment_status_history_tenant_assignment", "rector_assignment_status_history", ["tenant_id", "assignment_id"])

    # 8. rector_assignment_escalations
    op.create_table(
        "rector_assignment_escalations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=False),
        sa.Column("trigger_type", sa.String(32), nullable=False),
        sa.Column("escalation_level", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("escalated_to_user_id", sa.BigInteger(), nullable=True),
        sa.Column("escalated_to_role", sa.String(64), nullable=False),
        sa.Column("triggered_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="OPEN"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rector_assignment_escalations_tenant_id", "rector_assignment_escalations", ["tenant_id"])
    op.create_index("ix_rector_assignment_escalations_tenant_assignment", "rector_assignment_escalations", ["tenant_id", "assignment_id"])
    op.create_index("ix_rector_assignment_escalations_tenant_status", "rector_assignment_escalations", ["tenant_id", "status"])

    # 9. rector_assignment_templates
    op.create_table(
        "rector_assignment_templates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(64), nullable=True),
        sa.Column("default_priority", sa.String(16), nullable=False, server_default="NORMAL"),
        sa.Column("default_due_days", sa.Integer(), nullable=True),
        sa.Column("default_recurrence_type", sa.String(16), nullable=False, server_default="NONE"),
        sa.Column("template_body", JSONB(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rector_assignment_templates_tenant_id", "rector_assignment_templates", ["tenant_id"])
    op.create_index("ix_rector_assignment_templates_tenant_active", "rector_assignment_templates", ["tenant_id", "is_active"])

    # 10. rector_assignment_audit_events (INSERT-ONLY)
    op.create_table(
        "rector_assignment_audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_role", sa.String(64), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("action", sa.String(256), nullable=False),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rector_assignment_audit_events_tenant_id", "rector_assignment_audit_events", ["tenant_id"])
    op.create_index("ix_rector_assignment_audit_events_tenant_assignment", "rector_assignment_audit_events", ["tenant_id", "assignment_id"])
    op.create_index("ix_rector_assignment_audit_events_tenant_event_type", "rector_assignment_audit_events", ["tenant_id", "event_type"])
    op.create_index("ix_rector_assignment_audit_events_tenant_created", "rector_assignment_audit_events", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_table("rector_assignment_audit_events")
    op.drop_table("rector_assignment_templates")
    op.drop_table("rector_assignment_escalations")
    op.drop_table("rector_assignment_status_history")
    op.drop_table("rector_assignment_comments")
    op.drop_table("rector_assignment_evidence")
    op.drop_table("rector_assignment_reports")
    op.drop_table("rector_assignment_assignees")
    op.drop_table("rector_assignment_tasks")
    op.drop_table("rector_assignments")
