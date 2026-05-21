"""A-035.2 Student Lifecycle backend foundation tables.

Revision ID: uq35sl24rt80
Revises: 7c2e9a4b1d0f, a7c9e1d2f3b4, a9b8c7d6e5f4, b3c5d7e9f1a2, bs57uv69wx70, e8b4c2d1f7a9, f6a2d1e9b3c4, f9d0e1a2b3c4, lh01ij23kl45, pg45qr67st89, sj78tu90wx12
Create Date: 2026-05-22 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "uq35sl24rt80"
down_revision = (
    "7c2e9a4b1d0f",
    "a7c9e1d2f3b4",
    "a9b8c7d6e5f4",
    "b3c5d7e9f1a2",
    "bs57uv69wx70",
    "e8b4c2d1f7a9",
    "f6a2d1e9b3c4",
    "f9d0e1a2b3c4",
    "lh01ij23kl45",
    "pg45qr67st89",
    "sj78tu90wx12",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sl_applicants",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("applicant_code", sa.String(length=64), nullable=False),
        sa.Column("program_interest", sa.String(length=128), nullable=True),
        sa.Column("entry_term", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="DRAFT"),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("source_available", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default="'[]'::jsonb"),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "applicant_code", name="uq_sl_applicants_tenant_code"),
    )
    op.create_index("ix_sl_applicants_tenant_id", "sl_applicants", ["tenant_id"])
    op.create_index("ix_sl_applicants_tenant_status", "sl_applicants", ["tenant_id", "status"])

    op.create_table(
        "sl_student_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_code", sa.String(length=64), nullable=False),
        sa.Column("source_applicant_id", sa.BigInteger(), sa.ForeignKey("sl_applicants.id"), nullable=True),
        sa.Column("program_code", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="PROFILE_CREATED"),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default="'[]'::jsonb"),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("tenant_id", "student_code", name="uq_sl_student_profiles_tenant_code"),
    )
    op.create_index("ix_sl_student_profiles_tenant_id", "sl_student_profiles", ["tenant_id"])
    op.create_index("ix_sl_student_profiles_tenant_status", "sl_student_profiles", ["tenant_id", "status"])

    op.create_table(
        "sl_applicant_status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("applicant_id", sa.BigInteger(), sa.ForeignKey("sl_applicants.id"), nullable=False),
        sa.Column("previous_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_sl_applicant_status_history_tenant_id", "sl_applicant_status_history", ["tenant_id"])
    op.create_index("ix_sl_applicant_status_history_tenant_applicant", "sl_applicant_status_history", ["tenant_id", "applicant_id"])

    op.create_table(
        "sl_student_status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("sl_student_profiles.id"), nullable=False),
        sa.Column("previous_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_sl_student_status_history_tenant_id", "sl_student_status_history", ["tenant_id"])
    op.create_index("ix_sl_student_status_history_tenant_student", "sl_student_status_history", ["tenant_id", "student_id"])

    op.create_table(
        "sl_student_enrollments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("sl_student_profiles.id"), nullable=False),
        sa.Column("term_code", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="DRAFT"),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default="'[]'::jsonb"),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sl_student_enrollments_tenant_id", "sl_student_enrollments", ["tenant_id"])
    op.create_index("ix_sl_student_enrollments_tenant_status", "sl_student_enrollments", ["tenant_id", "status"])

    op.create_table(
        "sl_enrollment_status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("enrollment_id", sa.BigInteger(), sa.ForeignKey("sl_student_enrollments.id"), nullable=False),
        sa.Column("previous_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_sl_enrollment_status_history_tenant_id", "sl_enrollment_status_history", ["tenant_id"])
    op.create_index("ix_sl_enrollment_status_history_tenant_enrollment", "sl_enrollment_status_history", ["tenant_id", "enrollment_id"])

    op.create_table(
        "sl_academic_records",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("sl_student_profiles.id"), nullable=False),
        sa.Column("record_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="OPENED"),
        sa.Column("source_available", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("result_metadata_json", JSONB(), nullable=False, server_default="'{}'::jsonb"),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default="'[]'::jsonb"),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sl_academic_records_tenant_id", "sl_academic_records", ["tenant_id"])
    op.create_index("ix_sl_academic_records_tenant_status", "sl_academic_records", ["tenant_id", "status"])

    op.create_table(
        "sl_transcript_previews",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("sl_student_profiles.id"), nullable=False),
        sa.Column("academic_record_id", sa.BigInteger(), sa.ForeignKey("sl_academic_records.id"), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="GENERATED_UNOFFICIAL_PREVIEW"),
        sa.Column("official_document", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("preview_payload_json", JSONB(), nullable=False, server_default="'{}'::jsonb"),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default="'[]'::jsonb"),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_sl_transcript_previews_tenant_id", "sl_transcript_previews", ["tenant_id"])
    op.create_index("ix_sl_transcript_previews_tenant_status", "sl_transcript_previews", ["tenant_id", "status"])

    op.create_table(
        "sl_degree_progress_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("sl_student_profiles.id"), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="PENDING"),
        sa.Column("data_source", sa.String(length=128), nullable=False, server_default="computed_from_student_lifecycle_metadata"),
        sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("completion_summary_json", JSONB(), nullable=False, server_default="'{}'::jsonb"),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default="'[]'::jsonb"),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_sl_degree_progress_snapshots_tenant_id", "sl_degree_progress_snapshots", ["tenant_id"])
    op.create_index("ix_sl_degree_progress_snapshots_tenant_status", "sl_degree_progress_snapshots", ["tenant_id", "status"])

    op.create_table(
        "sl_student_requests",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("sl_student_profiles.id"), nullable=False),
        sa.Column("request_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="DRAFT"),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default="'[]'::jsonb"),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sl_student_requests_tenant_id", "sl_student_requests", ["tenant_id"])
    op.create_index("ix_sl_student_requests_tenant_status", "sl_student_requests", ["tenant_id", "status"])

    op.create_table(
        "sl_student_appeals",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("sl_student_profiles.id"), nullable=False),
        sa.Column("appeal_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="DRAFT"),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("decision_note", sa.Text(), nullable=True),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default="'[]'::jsonb"),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sl_student_appeals_tenant_id", "sl_student_appeals", ["tenant_id"])
    op.create_index("ix_sl_student_appeals_tenant_status", "sl_student_appeals", ["tenant_id", "status"])

    op.create_table(
        "sl_intervention_plans",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("sl_student_profiles.id"), nullable=False),
        sa.Column("signal_type", sa.String(length=64), nullable=False),
        sa.Column("plan_summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="SIGNAL_REGISTERED"),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("followups_json", JSONB(), nullable=False, server_default="'[]'::jsonb"),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default="'[]'::jsonb"),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_sl_intervention_plans_tenant_id", "sl_intervention_plans", ["tenant_id"])
    op.create_index("ix_sl_intervention_plans_tenant_status", "sl_intervention_plans", ["tenant_id", "status"])

    op.create_table(
        "sl_student_lifecycle_audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=False),
        sa.Column("previous_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=True),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("action", sa.String(length=256), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=False, server_default="'{}'::jsonb"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_sl_student_lifecycle_audit_events_tenant_id", "sl_student_lifecycle_audit_events", ["tenant_id"])
    op.create_index("ix_sl_audit_events_tenant_entity", "sl_student_lifecycle_audit_events", ["tenant_id", "entity_type", "entity_id"])

    op.create_table(
        "sl_student_lifecycle_evidence_metadata",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("audit_event_id", sa.BigInteger(), sa.ForeignKey("sl_student_lifecycle_audit_events.id"), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("evidence_ref", sa.String(length=255), nullable=False),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default="'[]'::jsonb"),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_sl_student_lifecycle_evidence_metadata_tenant_id", "sl_student_lifecycle_evidence_metadata", ["tenant_id"])
    op.create_index("ix_sl_evidence_metadata_tenant_entity", "sl_student_lifecycle_evidence_metadata", ["tenant_id", "entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_index("ix_sl_evidence_metadata_tenant_entity", table_name="sl_student_lifecycle_evidence_metadata")
    op.drop_index("ix_sl_student_lifecycle_evidence_metadata_tenant_id", table_name="sl_student_lifecycle_evidence_metadata")
    op.drop_table("sl_student_lifecycle_evidence_metadata")
    op.drop_index("ix_sl_audit_events_tenant_entity", table_name="sl_student_lifecycle_audit_events")
    op.drop_index("ix_sl_student_lifecycle_audit_events_tenant_id", table_name="sl_student_lifecycle_audit_events")
    op.drop_table("sl_student_lifecycle_audit_events")
    op.drop_index("ix_sl_intervention_plans_tenant_status", table_name="sl_intervention_plans")
    op.drop_index("ix_sl_intervention_plans_tenant_id", table_name="sl_intervention_plans")
    op.drop_table("sl_intervention_plans")
    op.drop_index("ix_sl_student_appeals_tenant_status", table_name="sl_student_appeals")
    op.drop_index("ix_sl_student_appeals_tenant_id", table_name="sl_student_appeals")
    op.drop_table("sl_student_appeals")
    op.drop_index("ix_sl_student_requests_tenant_status", table_name="sl_student_requests")
    op.drop_index("ix_sl_student_requests_tenant_id", table_name="sl_student_requests")
    op.drop_table("sl_student_requests")
    op.drop_index("ix_sl_degree_progress_snapshots_tenant_status", table_name="sl_degree_progress_snapshots")
    op.drop_index("ix_sl_degree_progress_snapshots_tenant_id", table_name="sl_degree_progress_snapshots")
    op.drop_table("sl_degree_progress_snapshots")
    op.drop_index("ix_sl_transcript_previews_tenant_status", table_name="sl_transcript_previews")
    op.drop_index("ix_sl_transcript_previews_tenant_id", table_name="sl_transcript_previews")
    op.drop_table("sl_transcript_previews")
    op.drop_index("ix_sl_academic_records_tenant_status", table_name="sl_academic_records")
    op.drop_index("ix_sl_academic_records_tenant_id", table_name="sl_academic_records")
    op.drop_table("sl_academic_records")
    op.drop_index("ix_sl_enrollment_status_history_tenant_enrollment", table_name="sl_enrollment_status_history")
    op.drop_index("ix_sl_enrollment_status_history_tenant_id", table_name="sl_enrollment_status_history")
    op.drop_table("sl_enrollment_status_history")
    op.drop_index("ix_sl_student_enrollments_tenant_status", table_name="sl_student_enrollments")
    op.drop_index("ix_sl_student_enrollments_tenant_id", table_name="sl_student_enrollments")
    op.drop_table("sl_student_enrollments")
    op.drop_index("ix_sl_student_status_history_tenant_student", table_name="sl_student_status_history")
    op.drop_index("ix_sl_student_status_history_tenant_id", table_name="sl_student_status_history")
    op.drop_table("sl_student_status_history")
    op.drop_index("ix_sl_applicant_status_history_tenant_applicant", table_name="sl_applicant_status_history")
    op.drop_index("ix_sl_applicant_status_history_tenant_id", table_name="sl_applicant_status_history")
    op.drop_table("sl_applicant_status_history")
    op.drop_index("ix_sl_student_profiles_tenant_status", table_name="sl_student_profiles")
    op.drop_index("ix_sl_student_profiles_tenant_id", table_name="sl_student_profiles")
    op.drop_table("sl_student_profiles")
    op.drop_index("ix_sl_applicants_tenant_status", table_name="sl_applicants")
    op.drop_index("ix_sl_applicants_tenant_id", table_name="sl_applicants")
    op.drop_table("sl_applicants")