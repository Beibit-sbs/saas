"""create intervention cases tables

Revision ID: 1b2c3d4e5f6a
Revises: ff01a2b3c4d5
Create Date: 2026-04-05 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "1b2c3d4e5f6a"
down_revision = "ff01a2b3c4d5"
branch_labels = None
depends_on = None


intervention_case_type = postgresql.ENUM(
    "academic_risk",
    name="intervention_case_type",
    create_type=False,
)
intervention_case_severity = postgresql.ENUM(
    "low",
    "medium",
    "high",
    name="intervention_case_severity",
    create_type=False,
)
intervention_case_status = postgresql.ENUM(
    "open",
    "in_progress",
    "resolved",
    "closed",
    name="intervention_case_status",
    create_type=False,
)
intervention_assignee_type = postgresql.ENUM(
    "user",
    "group",
    name="intervention_assignee_type",
    create_type=False,
)
intervention_action_type = postgresql.ENUM(
    "assignment",
    "status_change",
    "consultation_scheduled",
    "notification_sent",
    "plan_updated",
    "note",
    name="intervention_action_type",
    create_type=False,
)


def upgrade() -> None:
    enum_types = [
        intervention_case_type,
        intervention_case_severity,
        intervention_case_status,
        intervention_assignee_type,
        intervention_action_type,
    ]
    for enum_type in enum_types:
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "app_intervention_cases",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("case_type", intervention_case_type, nullable=False, server_default=sa.text("'academic_risk'")),
        sa.Column("student_profile_id", sa.BigInteger(), nullable=True),
        sa.Column("severity", intervention_case_severity, nullable=False, server_default=sa.text("'medium'")),
        sa.Column("status", intervention_case_status, nullable=False, server_default=sa.text("'open'")),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "risk_snapshot_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("assignee_type", intervention_assignee_type, nullable=False, server_default=sa.text("'group'")),
        sa.Column("assignee_ref", sa.String(length=255), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("version >= 1", name="ck_intervention_cases_version_positive"),
        sa.CheckConstraint("due_at >= opened_at", name="ck_intervention_cases_due_after_open"),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_profile_id"],
            ["app_students_profiles.tenant_id", "app_students_profiles.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_intervention_cases_tenant_id_id"),
    )
    op.create_index("ix_intervention_cases_tenant_status", "app_intervention_cases", ["tenant_id", "status"])
    op.create_index("ix_intervention_cases_tenant_severity", "app_intervention_cases", ["tenant_id", "severity"])
    op.create_index(
        "ix_intervention_cases_tenant_assignee",
        "app_intervention_cases",
        ["tenant_id", "assignee_type", "assignee_ref"],
    )
    op.create_index("ix_intervention_cases_tenant_due", "app_intervention_cases", ["tenant_id", "due_at"])

    op.create_table(
        "app_intervention_actions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("case_id", sa.BigInteger(), nullable=False),
        sa.Column("action_type", intervention_action_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("outcome_note", sa.Text(), nullable=True),
        sa.Column("performed_by", sa.String(length=255), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["app_tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "case_id"],
            ["app_intervention_cases.tenant_id", "app_intervention_cases.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="ux_intervention_actions_tenant_id_id"),
    )
    op.create_index(
        "ix_intervention_actions_tenant_case_performed",
        "app_intervention_actions",
        ["tenant_id", "case_id", "performed_at"],
    )
    op.create_index(
        "ix_intervention_actions_tenant_type",
        "app_intervention_actions",
        ["tenant_id", "action_type"],
    )


def downgrade() -> None:
    op.drop_index("ix_intervention_actions_tenant_type", table_name="app_intervention_actions")
    op.drop_index("ix_intervention_actions_tenant_case_performed", table_name="app_intervention_actions")
    op.drop_table("app_intervention_actions")

    op.drop_index("ix_intervention_cases_tenant_due", table_name="app_intervention_cases")
    op.drop_index("ix_intervention_cases_tenant_assignee", table_name="app_intervention_cases")
    op.drop_index("ix_intervention_cases_tenant_severity", table_name="app_intervention_cases")
    op.drop_index("ix_intervention_cases_tenant_status", table_name="app_intervention_cases")
    op.drop_table("app_intervention_cases")

    enum_types = [
        intervention_action_type,
        intervention_assignee_type,
        intervention_case_status,
        intervention_case_severity,
        intervention_case_type,
    ]
    for enum_type in enum_types:
        enum_type.drop(op.get_bind(), checkfirst=True)
