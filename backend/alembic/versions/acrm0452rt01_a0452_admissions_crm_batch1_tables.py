"""A-045.2 runtime Batch 1 tables for Admissions CRM."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "acrm0452rt01"
down_revision = "cfht0442rt01"
branch_labels = None
depends_on = None


def _jsonb_default_empty_object():
    return sa.text("'{}'::jsonb")


def _foundation_columns(status_default: str = "'draft'") -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text(status_default)),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("fake_metrics", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_live_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("autonomous_decision_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("updated_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    ]


def _create_standard_indexes(table_name: str) -> None:
    op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"], unique=False)
    op.create_index(f"ix_{table_name}_tenant_status", table_name, ["tenant_id", "status"], unique=False)


def upgrade() -> None:
    op.create_table(
        "acrm_leads",
        *(_foundation_columns("'lead_created'") + [
            sa.Column("lead_ref", sa.String(length=64), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("phone", sa.String(length=64), nullable=True),
            sa.Column("source_channel", sa.String(length=64), nullable=False, server_default=sa.text("'direct'")),
        ]),
    )
    op.create_table(
        "acrm_lead_status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("lead_id", sa.BigInteger(), nullable=False),
        sa.Column("from_status", sa.String(length=64), nullable=True),
        sa.Column("to_status", sa.String(length=64), nullable=False),
        sa.Column("changed_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "acrm_lead_notes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("lead_id", sa.BigInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "acrm_lead_tags",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("lead_id", sa.BigInteger(), nullable=False),
        sa.Column("tag", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "acrm_applicants",
        *(_foundation_columns("'applicant_created'") + [
            sa.Column("lead_id", sa.BigInteger(), nullable=False),
            sa.Column("applicant_ref", sa.String(length=64), nullable=False),
            sa.Column("full_name", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
        ]),
    )
    op.create_table(
        "acrm_applicant_notes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("applicant_id", sa.BigInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "acrm_applications",
        *(_foundation_columns("'application_started'") + [
            sa.Column("applicant_id", sa.BigInteger(), nullable=False),
            sa.Column("application_ref", sa.String(length=64), nullable=False),
            sa.Column("program_code", sa.String(length=64), nullable=False),
            sa.Column("intake_term", sa.String(length=64), nullable=False),
        ]),
    )
    op.create_table(
        "acrm_application_status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("application_id", sa.BigInteger(), nullable=False),
        sa.Column("from_status", sa.String(length=64), nullable=True),
        sa.Column("to_status", sa.String(length=64), nullable=False),
        sa.Column("changed_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "acrm_workflow_transition_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("from_status", sa.String(length=64), nullable=True),
        sa.Column("to_status", sa.String(length=64), nullable=True),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "acrm_audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "acrm_counselor_assignments",
        *(_foundation_columns("'active'") + [
            sa.Column("lead_id", sa.BigInteger(), nullable=True),
            sa.Column("applicant_id", sa.BigInteger(), nullable=True),
            sa.Column("counselor_user_id", sa.String(length=255), nullable=False),
        ]),
    )
    op.create_table(
        "acrm_assignment_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("assignment_id", sa.BigInteger(), nullable=False),
        sa.Column("previous_counselor_user_id", sa.String(length=255), nullable=True),
        sa.Column("new_counselor_user_id", sa.String(length=255), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    for table_name in [
        "acrm_leads",
        "acrm_applicants",
        "acrm_applications",
        "acrm_counselor_assignments",
    ]:
        _create_standard_indexes(table_name)

    op.create_index("ix_acrm_lead_status_history_tenant_id", "acrm_lead_status_history", ["tenant_id"], unique=False)
    op.create_index("ix_acrm_lead_status_history_tenant_lead", "acrm_lead_status_history", ["tenant_id", "lead_id"], unique=False)
    op.create_index("ix_acrm_lead_notes_tenant_id", "acrm_lead_notes", ["tenant_id"], unique=False)
    op.create_index("ix_acrm_lead_notes_tenant_lead", "acrm_lead_notes", ["tenant_id", "lead_id"], unique=False)
    op.create_index("ix_acrm_lead_tags_tenant_id", "acrm_lead_tags", ["tenant_id"], unique=False)
    op.create_index("ix_acrm_lead_tags_tenant_lead", "acrm_lead_tags", ["tenant_id", "lead_id"], unique=False)
    op.create_index("ix_acrm_applicant_notes_tenant_id", "acrm_applicant_notes", ["tenant_id"], unique=False)
    op.create_index("ix_acrm_applicant_notes_tenant_applicant", "acrm_applicant_notes", ["tenant_id", "applicant_id"], unique=False)
    op.create_index("ix_acrm_application_status_history_tenant_id", "acrm_application_status_history", ["tenant_id"], unique=False)
    op.create_index(
        "ix_acrm_application_status_history_tenant_app",
        "acrm_application_status_history",
        ["tenant_id", "application_id"],
        unique=False,
    )
    op.create_index("ix_acrm_workflow_transition_events_tenant_id", "acrm_workflow_transition_events", ["tenant_id"], unique=False)
    op.create_index(
        "ix_acrm_workflow_transition_events_tenant_entity",
        "acrm_workflow_transition_events",
        ["tenant_id", "entity_type", "entity_id"],
        unique=False,
    )
    op.create_index("ix_acrm_audit_events_tenant_id", "acrm_audit_events", ["tenant_id"], unique=False)
    op.create_index("ix_acrm_audit_events_tenant_action", "acrm_audit_events", ["tenant_id", "action"], unique=False)
    op.create_index("ix_acrm_assignment_history_tenant_id", "acrm_assignment_history", ["tenant_id"], unique=False)
    op.create_index(
        "ix_acrm_assignment_history_tenant_assignment",
        "acrm_assignment_history",
        ["tenant_id", "assignment_id"],
        unique=False,
    )


def downgrade() -> None:
    for index_name, table_name in [
        ("ix_acrm_assignment_history_tenant_assignment", "acrm_assignment_history"),
        ("ix_acrm_assignment_history_tenant_id", "acrm_assignment_history"),
        ("ix_acrm_audit_events_tenant_action", "acrm_audit_events"),
        ("ix_acrm_audit_events_tenant_id", "acrm_audit_events"),
        ("ix_acrm_workflow_transition_events_tenant_entity", "acrm_workflow_transition_events"),
        ("ix_acrm_workflow_transition_events_tenant_id", "acrm_workflow_transition_events"),
        ("ix_acrm_application_status_history_tenant_app", "acrm_application_status_history"),
        ("ix_acrm_application_status_history_tenant_id", "acrm_application_status_history"),
        ("ix_acrm_applicant_notes_tenant_applicant", "acrm_applicant_notes"),
        ("ix_acrm_applicant_notes_tenant_id", "acrm_applicant_notes"),
        ("ix_acrm_lead_tags_tenant_lead", "acrm_lead_tags"),
        ("ix_acrm_lead_tags_tenant_id", "acrm_lead_tags"),
        ("ix_acrm_lead_notes_tenant_lead", "acrm_lead_notes"),
        ("ix_acrm_lead_notes_tenant_id", "acrm_lead_notes"),
        ("ix_acrm_lead_status_history_tenant_lead", "acrm_lead_status_history"),
        ("ix_acrm_lead_status_history_tenant_id", "acrm_lead_status_history"),
    ]:
        op.drop_index(index_name, table_name=table_name)

    for table_name in [
        "acrm_counselor_assignments",
        "acrm_applications",
        "acrm_applicants",
        "acrm_leads",
    ]:
        op.drop_index(f"ix_{table_name}_tenant_status", table_name=table_name)
        op.drop_index(f"ix_{table_name}_tenant_id", table_name=table_name)

    op.drop_table("acrm_assignment_history")
    op.drop_table("acrm_counselor_assignments")
    op.drop_table("acrm_audit_events")
    op.drop_table("acrm_workflow_transition_events")
    op.drop_table("acrm_application_status_history")
    op.drop_table("acrm_applications")
    op.drop_table("acrm_applicant_notes")
    op.drop_table("acrm_applicants")
    op.drop_table("acrm_lead_tags")
    op.drop_table("acrm_lead_notes")
    op.drop_table("acrm_lead_status_history")
    op.drop_table("acrm_leads")
