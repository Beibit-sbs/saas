"""A-042.2 runtime tables for Student Services / Welfare / Support."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "sss0422rt01"
down_revision = "ddc0412rt01"
branch_labels = None
depends_on = None


def _jsonb_default_empty_object():
    return sa.text("'{}'::jsonb")


def _jsonb_default_empty_list():
    return sa.text("'[]'::jsonb")


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
        sa.Column("source_module", sa.String(length=128), nullable=True),
        sa.Column("source_entity_id", sa.String(length=128), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("updated_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _create_standard_indexes(table_name: str) -> None:
    op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"], unique=False)
    op.create_index(f"ix_{table_name}_tenant_status", table_name, ["tenant_id", "status"], unique=False)


def upgrade() -> None:
    op.create_table(
        "sss_student_service_requests",
        *(_foundation_columns("'submitted'") + [
            sa.Column("request_type", sa.String(length=64), nullable=False),
            sa.Column("support_priority", sa.String(length=32), nullable=False, server_default=sa.text("'medium'")),
            sa.Column("student_id", sa.String(length=128), nullable=False),
            sa.Column("assigned_to_user_id", sa.String(length=255), nullable=True),
            sa.Column("subject", sa.String(length=255), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
        ]),
    )
    op.create_table(
        "sss_student_service_request_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("request_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "sss_student_support_cases",
        *(_foundation_columns("'open'") + [
            sa.Column("case_type", sa.String(length=64), nullable=False),
            sa.Column("request_id", sa.BigInteger(), nullable=True),
            sa.Column("assigned_to_user_id", sa.String(length=255), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=True),
        ]),
    )
    op.create_table(
        "sss_student_support_case_notes",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("case_id", sa.BigInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "sss_student_support_case_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("case_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "sss_student_support_evidence",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("case_id", sa.BigInteger(), nullable=False),
        sa.Column("evidence_type", sa.String(length=128), nullable=False),
        sa.Column("evidence_ref", sa.String(length=255), nullable=True),
        sa.Column("source_available", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("limitations", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_table(
        "sss_hardship_support_requests",
        *(_foundation_columns("'readiness_evaluated'") + [
            sa.Column("request_id", sa.BigInteger(), nullable=True),
            sa.Column("readiness_status", sa.String(length=64), nullable=False, server_default=sa.text("'insufficient_evidence'")),
            sa.Column("missing_evidence_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()),
            sa.Column("recommended_next_step", sa.String(length=255), nullable=True),
        ]),
    )
    op.create_table(
        "sss_disability_accommodation_requests",
        *(_foundation_columns("'readiness_evaluated'") + [
            sa.Column("request_id", sa.BigInteger(), nullable=True),
            sa.Column("readiness_status", sa.String(length=64), nullable=False, server_default=sa.text("'insufficient_evidence'")),
            sa.Column("missing_evidence_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()),
            sa.Column("recommended_next_step", sa.String(length=255), nullable=True),
        ]),
    )
    op.create_table(
        "sss_student_complaints",
        *(_foundation_columns("'submitted'") + [
            sa.Column("request_id", sa.BigInteger(), nullable=True),
            sa.Column("routed_to", sa.String(length=255), nullable=True),
            sa.Column("complaint_summary", sa.Text(), nullable=True),
        ]),
    )
    op.create_table(
        "sss_student_service_sla_policies",
        *(_foundation_columns("'active'") + [
            sa.Column("policy_code", sa.String(length=128), nullable=False),
            sa.Column("target_hours", sa.BigInteger(), nullable=False, server_default=sa.text("72")),
        ]),
    )
    op.create_table(
        "sss_student_support_escalations",
        *(_foundation_columns("'pending'") + [
            sa.Column("case_id", sa.BigInteger(), nullable=False),
            sa.Column("escalation_status", sa.String(length=64), nullable=False, server_default=sa.text("'pending'")),
            sa.Column("reason", sa.Text(), nullable=False),
        ]),
    )
    op.create_table(
        "sss_student_support_dashboard_snapshots",
        *(_foundation_columns("'active'") + [
            sa.Column("data_source", sa.String(length=128), nullable=False, server_default=sa.text("'computed_from_student_services_support_records'")),
            sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        ]),
    )

    for table_name in [
        "sss_student_service_requests",
        "sss_student_support_cases",
        "sss_hardship_support_requests",
        "sss_disability_accommodation_requests",
        "sss_student_complaints",
        "sss_student_service_sla_policies",
        "sss_student_support_escalations",
        "sss_student_support_dashboard_snapshots",
    ]:
        _create_standard_indexes(table_name)

    op.create_index("ix_sss_student_service_request_events_tenant_id", "sss_student_service_request_events", ["tenant_id"], unique=False)
    op.create_index("ix_sss_student_service_request_events_tenant_request", "sss_student_service_request_events", ["tenant_id", "request_id"], unique=False)
    op.create_index("ix_sss_student_support_case_notes_tenant_id", "sss_student_support_case_notes", ["tenant_id"], unique=False)
    op.create_index("ix_sss_student_support_case_notes_tenant_case", "sss_student_support_case_notes", ["tenant_id", "case_id"], unique=False)
    op.create_index("ix_sss_student_support_case_events_tenant_id", "sss_student_support_case_events", ["tenant_id"], unique=False)
    op.create_index("ix_sss_student_support_case_events_tenant_case", "sss_student_support_case_events", ["tenant_id", "case_id"], unique=False)
    op.create_index("ix_sss_student_support_evidence_tenant_id", "sss_student_support_evidence", ["tenant_id"], unique=False)
    op.create_index("ix_sss_student_support_evidence_tenant_case", "sss_student_support_evidence", ["tenant_id", "case_id"], unique=False)


def downgrade() -> None:
    for index_name, table_name in [
        ("ix_sss_student_support_evidence_tenant_case", "sss_student_support_evidence"),
        ("ix_sss_student_support_evidence_tenant_id", "sss_student_support_evidence"),
        ("ix_sss_student_support_case_events_tenant_case", "sss_student_support_case_events"),
        ("ix_sss_student_support_case_events_tenant_id", "sss_student_support_case_events"),
        ("ix_sss_student_support_case_notes_tenant_case", "sss_student_support_case_notes"),
        ("ix_sss_student_support_case_notes_tenant_id", "sss_student_support_case_notes"),
        ("ix_sss_student_service_request_events_tenant_request", "sss_student_service_request_events"),
        ("ix_sss_student_service_request_events_tenant_id", "sss_student_service_request_events"),
    ]:
        op.drop_index(index_name, table_name=table_name)

    for table_name in [
        "sss_student_support_dashboard_snapshots",
        "sss_student_support_escalations",
        "sss_student_service_sla_policies",
        "sss_student_complaints",
        "sss_disability_accommodation_requests",
        "sss_hardship_support_requests",
        "sss_student_support_cases",
        "sss_student_service_requests",
    ]:
        op.drop_index(f"ix_{table_name}_tenant_status", table_name=table_name)
        op.drop_index(f"ix_{table_name}_tenant_id", table_name=table_name)

    op.drop_table("sss_student_support_dashboard_snapshots")
    op.drop_table("sss_student_support_escalations")
    op.drop_table("sss_student_service_sla_policies")
    op.drop_table("sss_student_complaints")
    op.drop_table("sss_disability_accommodation_requests")
    op.drop_table("sss_hardship_support_requests")
    op.drop_table("sss_student_support_evidence")
    op.drop_table("sss_student_support_case_events")
    op.drop_table("sss_student_support_case_notes")
    op.drop_table("sss_student_support_cases")
    op.drop_table("sss_student_service_request_events")
    op.drop_table("sss_student_service_requests")
