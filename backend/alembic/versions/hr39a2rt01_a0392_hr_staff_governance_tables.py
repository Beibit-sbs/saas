"""A-039.2 runtime foundation tables for HR / Staff Governance."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "hr39a2rt01"
down_revision = "qa38a2rt01"
branch_labels = None
depends_on = None


def _jsonb_default_empty_object():
    return sa.text("'{}'::jsonb")


def _jsonb_default_empty_list():
    return sa.text("'[]'::jsonb")


def _foundation_columns(status_default: str = "'DRAFT'") -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text(status_default)),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column("evidence_status", sa.String(length=64), nullable=True),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("fake_data", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_connected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(length=255), nullable=True),
        sa.Column("updated_by_id", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    ]


def _create_reviewable_table(
    table_name: str,
    *extra_columns: sa.Column,
    status_default: str = "'DRAFT'",
    unique_fields: tuple[str, ...] = (),
) -> None:
    constraints: list[sa.Constraint] = []
    for field_name in unique_fields:
        constraints.append(sa.UniqueConstraint("tenant_id", field_name, name=f"uq_{table_name}_{field_name}"))
    op.create_table(table_name, *(_foundation_columns(status_default) + list(extra_columns) + constraints))
    op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"], unique=False)
    op.create_index(f"ix_{table_name}_tenant_status", table_name, ["tenant_id", "status"], unique=False)


def upgrade() -> None:
    _create_reviewable_table("hr_staff_profiles", sa.Column("staff_ref", sa.String(length=128), nullable=False), sa.Column("full_name", sa.String(length=255), nullable=False), sa.Column("department_ref", sa.String(length=128), nullable=True), sa.Column("position_ref", sa.String(length=128), nullable=True), unique_fields=("staff_ref",))
    _create_reviewable_table("hr_employee_records", sa.Column("employee_number", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("full_name", sa.String(length=255), nullable=False), sa.Column("position_ref", sa.String(length=128), nullable=True), unique_fields=("employee_number",))
    _create_reviewable_table("hr_staff_status_history", sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("previous_status", sa.String(length=64), nullable=True), sa.Column("changed_by_id", sa.String(length=255), nullable=True), sa.Column("reason", sa.Text(), nullable=True))
    _create_reviewable_table("hr_position_assignments", sa.Column("assignment_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("position_ref", sa.String(length=128), nullable=True), unique_fields=("assignment_ref",))
    _create_reviewable_table("hr_department_assignments", sa.Column("assignment_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("department_ref", sa.String(length=128), nullable=True), unique_fields=("assignment_ref",))
    _create_reviewable_table("hr_faculty_profiles", sa.Column("faculty_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("teaching_profile", sa.String(length=255), nullable=True), unique_fields=("faculty_ref",))
    _create_reviewable_table("hr_recruitment_requests", sa.Column("recruitment_ref", sa.String(length=128), nullable=False), sa.Column("department_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), unique_fields=("recruitment_ref",))
    _create_reviewable_table("hr_recruitment_pipeline_items", sa.Column("pipeline_ref", sa.String(length=128), nullable=False), sa.Column("recruitment_ref", sa.String(length=128), nullable=True), sa.Column("candidate_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), unique_fields=("pipeline_ref",))
    _create_reviewable_table("hr_candidate_shortlist_metadata", sa.Column("shortlist_ref", sa.String(length=128), nullable=False), sa.Column("candidate_ref", sa.String(length=128), nullable=True), sa.Column("recruitment_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), status_default="'SHORTLISTED'", unique_fields=("shortlist_ref",))
    _create_reviewable_table("hr_hiring_committee_reviews", sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("recruitment_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_id", sa.String(length=255), nullable=True), sa.Column("decision", sa.String(length=64), nullable=False, server_default=sa.text("'NO_DECISION'")), status_default="'COMMITTEE_REVIEW'", unique_fields=("review_ref",))
    _create_reviewable_table("hr_hiring_evidence_packs", sa.Column("evidence_pack_ref", sa.String(length=128), nullable=False), sa.Column("recruitment_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.Column("reference_uri", sa.String(length=255), nullable=True), status_default="'EVIDENCE_COMPLETE'", unique_fields=("evidence_pack_ref",))
    _create_reviewable_table("hr_onboarding_cases", sa.Column("onboarding_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), unique_fields=("onboarding_ref",))
    _create_reviewable_table("hr_onboarding_checklist_items", sa.Column("checklist_ref", sa.String(length=128), nullable=False), sa.Column("onboarding_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), status_default="'DOCUMENT_COLLECTION'", unique_fields=("checklist_ref",))
    _create_reviewable_table("hr_probation_reviews", sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("onboarding_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_id", sa.String(length=255), nullable=True), sa.Column("decision", sa.String(length=64), nullable=False, server_default=sa.text("'NO_DECISION'")), status_default="'REVIEW_REQUIRED'", unique_fields=("review_ref",))
    _create_reviewable_table("hr_leave_requests", sa.Column("leave_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("leave_type", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), unique_fields=("leave_ref",))
    _create_reviewable_table("hr_absence_metadata", sa.Column("absence_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), status_default="'SUBMITTED'", unique_fields=("absence_ref",))
    _create_reviewable_table("hr_leave_balance_snapshots", sa.Column("snapshot_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("balance_days", sa.Integer(), nullable=False, server_default=sa.text("0")), status_default="'SUBMITTED'", unique_fields=("snapshot_ref",))
    _create_reviewable_table("hr_staff_attendance_metadata", sa.Column("attendance_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), status_default="'SUBMITTED'", unique_fields=("attendance_ref",))
    _create_reviewable_table("hr_staff_requests", sa.Column("request_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("request_type", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), unique_fields=("request_ref",))
    _create_reviewable_table("hr_staff_appeals", sa.Column("appeal_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), unique_fields=("appeal_ref",))
    _create_reviewable_table("hr_policy_exceptions", sa.Column("exception_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("policy_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), unique_fields=("exception_ref",))
    _create_reviewable_table("hr_performance_appraisal_cycles", sa.Column("appraisal_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), unique_fields=("appraisal_ref",))
    _create_reviewable_table("hr_appraisal_review_evidence", sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("appraisal_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_id", sa.String(length=255), nullable=True), sa.Column("decision", sa.String(length=64), nullable=False, server_default=sa.text("'NO_DECISION'")), status_default="'HUMAN_REVIEW_REQUIRED'", unique_fields=("review_ref",))
    _create_reviewable_table("hr_training_certifications", sa.Column("certification_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), status_default="'PLANNED'", unique_fields=("certification_ref",))
    _create_reviewable_table("hr_certification_expiry_tracking", sa.Column("tracking_ref", sa.String(length=128), nullable=False), sa.Column("certification_ref", sa.String(length=128), nullable=True), sa.Column("days_until_expiry", sa.Integer(), nullable=False, server_default=sa.text("0")), status_default="'EXPIRING'", unique_fields=("tracking_ref",))
    _create_reviewable_table("hr_staff_development_plans", sa.Column("plan_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), status_default="'PLANNED'", unique_fields=("plan_ref",))
    _create_reviewable_table("hr_disciplinary_cases", sa.Column("case_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), status_default="'INTAKE'", unique_fields=("case_ref",))
    _create_reviewable_table("hr_disciplinary_review_evidence", sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("case_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_id", sa.String(length=255), nullable=True), sa.Column("decision", sa.String(length=64), nullable=False, server_default=sa.text("'NO_DECISION'")), status_default="'HUMAN_REVIEW_REQUIRED'", unique_fields=("review_ref",))
    _create_reviewable_table("hr_exit_offboarding_cases", sa.Column("offboarding_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), unique_fields=("offboarding_ref",))
    _create_reviewable_table("hr_access_lifecycle_reviews", sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("offboarding_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_id", sa.String(length=255), nullable=True), sa.Column("decision", sa.String(length=64), nullable=False, server_default=sa.text("'NO_DECISION'")), status_default="'ACCESS_REVIEW_REQUIRED'", unique_fields=("review_ref",))
    _create_reviewable_table("hr_workload_bridge_records", sa.Column("bridge_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("bridge_target", sa.String(length=128), nullable=False), sa.Column("read_only_first", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("mutation_allowed", sa.Boolean(), nullable=False, server_default=sa.text("false")), unique_fields=("bridge_ref",))
    _create_reviewable_table("hr_payroll_readiness_profiles", sa.Column("profile_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("provider_name", sa.String(length=128), nullable=False, server_default=sa.text("'HR_PAYROLL_PROVIDER'")), sa.Column("payroll_execution_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("live_provider_sync", sa.Boolean(), nullable=False, server_default=sa.text("false")), status_default="'NOT_CONFIGURED'", unique_fields=("profile_ref",))
    _create_reviewable_table("hr_provider_readiness_evidence", sa.Column("evidence_ref", sa.String(length=128), nullable=False), sa.Column("provider_name", sa.String(length=128), nullable=False), sa.Column("readiness_status", sa.String(length=64), nullable=False, server_default=sa.text("'NOT_CONFIGURED'")), sa.Column("credentials_present", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("live_call_count", sa.Integer(), nullable=False, server_default=sa.text("0")), sa.Column("sync_count", sa.Integer(), nullable=False, server_default=sa.text("0")), sa.Column("external_submission_count", sa.Integer(), nullable=False, server_default=sa.text("0")), sa.Column("live_integration_deferred", sa.Boolean(), nullable=False, server_default=sa.text("true")), status_default="'NOT_CONFIGURED'", unique_fields=("evidence_ref",))

    op.create_table(
        "hr_staff_compliance_dashboard_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'ACTIVE_METADATA_ONLY'")),
        sa.Column("fake_metrics", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fake_hr_data", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_connected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("live_provider_sync", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payroll_execution_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_decision_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("data_source", sa.String(length=128), nullable=False, server_default=sa.text("'computed_from_hr_staff_governance_metadata'")),
        sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("limitation_flags_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_hr_staff_compliance_dashboard_snapshots_tenant_id", "hr_staff_compliance_dashboard_snapshots", ["tenant_id"], unique=False)
    op.create_index("ix_hr_staff_compliance_dashboard_snapshots_tenant_created_at", "hr_staff_compliance_dashboard_snapshots", ["tenant_id", "created_at"], unique=False)

    op.create_table(
        "hr_audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("source_entity_type", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("previous_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("provider_connected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_hr_audit_events_tenant_id", "hr_audit_events", ["tenant_id"], unique=False)
    op.create_index("ix_hr_audit_events_tenant_created_at", "hr_audit_events", ["tenant_id", "created_at"], unique=False)

    op.create_table(
        "hr_evidence_repository",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'METADATA_ONLY'")),
        sa.Column("source_entity_type", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.BigInteger(), nullable=True),
        sa.Column("evidence_type", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("reference_uri", sa.String(length=255), nullable=True),
        sa.Column("storage_ref", sa.String(length=255), nullable=True),
        sa.Column("source_reference", sa.String(length=255), nullable=True),
        sa.Column("evidence_status", sa.String(length=64), nullable=True),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("fake_data", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_connected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.String(length=255), nullable=True),
        sa.Column("updated_by_id", sa.String(length=255), nullable=True),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_hr_evidence_repository_tenant_id", "hr_evidence_repository", ["tenant_id"], unique=False)
    op.create_index("ix_hr_evidence_repository_tenant_created_at", "hr_evidence_repository", ["tenant_id", "created_at"], unique=False)
    op.create_index("ix_hr_evidence_repository_tenant_entity", "hr_evidence_repository", ["tenant_id", "source_entity_type", "source_entity_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_hr_evidence_repository_tenant_entity", table_name="hr_evidence_repository")
    op.drop_index("ix_hr_evidence_repository_tenant_created_at", table_name="hr_evidence_repository")
    op.drop_index("ix_hr_evidence_repository_tenant_id", table_name="hr_evidence_repository")
    op.drop_table("hr_evidence_repository")

    op.drop_index("ix_hr_audit_events_tenant_created_at", table_name="hr_audit_events")
    op.drop_index("ix_hr_audit_events_tenant_id", table_name="hr_audit_events")
    op.drop_table("hr_audit_events")

    op.drop_index("ix_hr_staff_compliance_dashboard_snapshots_tenant_created_at", table_name="hr_staff_compliance_dashboard_snapshots")
    op.drop_index("ix_hr_staff_compliance_dashboard_snapshots_tenant_id", table_name="hr_staff_compliance_dashboard_snapshots")
    op.drop_table("hr_staff_compliance_dashboard_snapshots")

    for table_name in [
        "hr_provider_readiness_evidence",
        "hr_payroll_readiness_profiles",
        "hr_workload_bridge_records",
        "hr_access_lifecycle_reviews",
        "hr_exit_offboarding_cases",
        "hr_disciplinary_review_evidence",
        "hr_disciplinary_cases",
        "hr_staff_development_plans",
        "hr_certification_expiry_tracking",
        "hr_training_certifications",
        "hr_appraisal_review_evidence",
        "hr_performance_appraisal_cycles",
        "hr_policy_exceptions",
        "hr_staff_appeals",
        "hr_staff_requests",
        "hr_staff_attendance_metadata",
        "hr_leave_balance_snapshots",
        "hr_absence_metadata",
        "hr_leave_requests",
        "hr_probation_reviews",
        "hr_onboarding_checklist_items",
        "hr_onboarding_cases",
        "hr_hiring_evidence_packs",
        "hr_hiring_committee_reviews",
        "hr_candidate_shortlist_metadata",
        "hr_recruitment_pipeline_items",
        "hr_recruitment_requests",
        "hr_faculty_profiles",
        "hr_department_assignments",
        "hr_position_assignments",
        "hr_staff_status_history",
        "hr_employee_records",
        "hr_staff_profiles",
    ]:
        op.drop_index(f"ix_{table_name}_tenant_status", table_name=table_name)
        op.drop_index(f"ix_{table_name}_tenant_id", table_name=table_name)
        op.drop_table(table_name)