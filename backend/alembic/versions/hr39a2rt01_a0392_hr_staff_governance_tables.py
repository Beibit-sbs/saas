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


def upgrade() -> None:
    op.create_table("hr_staff_profiles", *(_foundation_columns() + [sa.Column("staff_ref", sa.String(length=128), nullable=False), sa.Column("full_name", sa.String(length=255), nullable=False), sa.Column("department_ref", sa.String(length=128), nullable=True), sa.Column("position_ref", sa.String(length=128), nullable=True), sa.UniqueConstraint("tenant_id", "staff_ref", name="uq_hr_staff_profiles_staff_ref")]))
    op.create_table("hr_employee_records", *(_foundation_columns() + [sa.Column("employee_number", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("full_name", sa.String(length=255), nullable=False), sa.Column("position_ref", sa.String(length=128), nullable=True), sa.UniqueConstraint("tenant_id", "employee_number", name="uq_hr_employee_records_employee_number")]))
    op.create_table("hr_staff_status_history", *(_foundation_columns() + [sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("previous_status", sa.String(length=64), nullable=True), sa.Column("changed_by_id", sa.String(length=255), nullable=True), sa.Column("reason", sa.Text(), nullable=True)]))
    op.create_table("hr_position_assignments", *(_foundation_columns() + [sa.Column("assignment_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("position_ref", sa.String(length=128), nullable=True), sa.UniqueConstraint("tenant_id", "assignment_ref", name="uq_hr_position_assignments_assignment_ref")]))
    op.create_table("hr_department_assignments", *(_foundation_columns() + [sa.Column("assignment_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("department_ref", sa.String(length=128), nullable=True), sa.UniqueConstraint("tenant_id", "assignment_ref", name="uq_hr_department_assignments_assignment_ref")]))
    op.create_table("hr_faculty_profiles", *(_foundation_columns() + [sa.Column("faculty_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("teaching_profile", sa.String(length=255), nullable=True), sa.UniqueConstraint("tenant_id", "faculty_ref", name="uq_hr_faculty_profiles_faculty_ref")]))
    op.create_table("hr_recruitment_requests", *(_foundation_columns() + [sa.Column("recruitment_ref", sa.String(length=128), nullable=False), sa.Column("department_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "recruitment_ref", name="uq_hr_recruitment_requests_recruitment_ref")]))
    op.create_table("hr_recruitment_pipeline_items", *(_foundation_columns() + [sa.Column("pipeline_ref", sa.String(length=128), nullable=False), sa.Column("recruitment_ref", sa.String(length=128), nullable=True), sa.Column("candidate_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "pipeline_ref", name="uq_hr_recruitment_pipeline_items_pipeline_ref")]))
    op.create_table("hr_candidate_shortlist_metadata", *(_foundation_columns("'SHORTLISTED'") + [sa.Column("shortlist_ref", sa.String(length=128), nullable=False), sa.Column("candidate_ref", sa.String(length=128), nullable=True), sa.Column("recruitment_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "shortlist_ref", name="uq_hr_candidate_shortlist_metadata_shortlist_ref")]))
    op.create_table("hr_hiring_committee_reviews", *(_foundation_columns("'COMMITTEE_REVIEW'") + [sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("recruitment_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_id", sa.String(length=255), nullable=True), sa.Column("decision", sa.String(length=64), nullable=False, server_default=sa.text("'NO_DECISION'")), sa.UniqueConstraint("tenant_id", "review_ref", name="uq_hr_hiring_committee_reviews_review_ref")]))
    op.create_table("hr_hiring_evidence_packs", *(_foundation_columns("'EVIDENCE_COMPLETE'") + [sa.Column("evidence_pack_ref", sa.String(length=128), nullable=False), sa.Column("recruitment_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.Column("reference_uri", sa.String(length=255), nullable=True), sa.UniqueConstraint("tenant_id", "evidence_pack_ref", name="uq_hr_hiring_evidence_packs_evidence_pack_ref")]))
    op.create_table("hr_onboarding_cases", *(_foundation_columns() + [sa.Column("onboarding_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "onboarding_ref", name="uq_hr_onboarding_cases_onboarding_ref")]))
    op.create_table("hr_onboarding_checklist_items", *(_foundation_columns("'DOCUMENT_COLLECTION'") + [sa.Column("checklist_ref", sa.String(length=128), nullable=False), sa.Column("onboarding_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "checklist_ref", name="uq_hr_onboarding_checklist_items_checklist_ref")]))
    op.create_table("hr_probation_reviews", *(_foundation_columns("'REVIEW_REQUIRED'") + [sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("onboarding_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_id", sa.String(length=255), nullable=True), sa.Column("decision", sa.String(length=64), nullable=False, server_default=sa.text("'NO_DECISION'")), sa.UniqueConstraint("tenant_id", "review_ref", name="uq_hr_probation_reviews_review_ref")]))
    op.create_table("hr_leave_requests", *(_foundation_columns() + [sa.Column("leave_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("leave_type", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "leave_ref", name="uq_hr_leave_requests_leave_ref")]))
    op.create_table("hr_absence_metadata", *(_foundation_columns("'SUBMITTED'") + [sa.Column("absence_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "absence_ref", name="uq_hr_absence_metadata_absence_ref")]))
    op.create_table("hr_leave_balance_snapshots", *(_foundation_columns("'SUBMITTED'") + [sa.Column("snapshot_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("balance_days", sa.Integer(), nullable=False, server_default=sa.text("0")), sa.UniqueConstraint("tenant_id", "snapshot_ref", name="uq_hr_leave_balance_snapshots_snapshot_ref")]))
    op.create_table("hr_staff_attendance_metadata", *(_foundation_columns("'SUBMITTED'") + [sa.Column("attendance_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "attendance_ref", name="uq_hr_staff_attendance_metadata_attendance_ref")]))
    op.create_table("hr_staff_requests", *(_foundation_columns() + [sa.Column("request_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("request_type", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "request_ref", name="uq_hr_staff_requests_request_ref")]))
    op.create_table("hr_staff_appeals", *(_foundation_columns() + [sa.Column("appeal_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "appeal_ref", name="uq_hr_staff_appeals_appeal_ref")]))
    op.create_table("hr_policy_exceptions", *(_foundation_columns() + [sa.Column("exception_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("policy_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "exception_ref", name="uq_hr_policy_exceptions_exception_ref")]))
    op.create_table("hr_performance_appraisal_cycles", *(_foundation_columns() + [sa.Column("appraisal_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "appraisal_ref", name="uq_hr_performance_appraisal_cycles_appraisal_ref")]))
    op.create_table("hr_appraisal_review_evidence", *(_foundation_columns("'HUMAN_REVIEW_REQUIRED'") + [sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("appraisal_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_id", sa.String(length=255), nullable=True), sa.Column("decision", sa.String(length=64), nullable=False, server_default=sa.text("'NO_DECISION'")), sa.UniqueConstraint("tenant_id", "review_ref", name="uq_hr_appraisal_review_evidence_review_ref")]))
    op.create_table("hr_training_certifications", *(_foundation_columns("'PLANNED'") + [sa.Column("certification_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "certification_ref", name="uq_hr_training_certifications_certification_ref")]))
    op.create_table("hr_certification_expiry_tracking", *(_foundation_columns("'EXPIRING'") + [sa.Column("tracking_ref", sa.String(length=128), nullable=False), sa.Column("certification_ref", sa.String(length=128), nullable=True), sa.Column("days_until_expiry", sa.Integer(), nullable=False, server_default=sa.text("0")), sa.UniqueConstraint("tenant_id", "tracking_ref", name="uq_hr_certification_expiry_tracking_tracking_ref")]))
    op.create_table("hr_staff_development_plans", *(_foundation_columns("'PLANNED'") + [sa.Column("plan_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "plan_ref", name="uq_hr_staff_development_plans_plan_ref")]))
    op.create_table("hr_disciplinary_cases", *(_foundation_columns("'INTAKE'") + [sa.Column("case_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "case_ref", name="uq_hr_disciplinary_cases_case_ref")]))
    op.create_table("hr_disciplinary_review_evidence", *(_foundation_columns("'HUMAN_REVIEW_REQUIRED'") + [sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("case_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_id", sa.String(length=255), nullable=True), sa.Column("decision", sa.String(length=64), nullable=False, server_default=sa.text("'NO_DECISION'")), sa.UniqueConstraint("tenant_id", "review_ref", name="uq_hr_disciplinary_review_evidence_review_ref")]))
    op.create_table("hr_exit_offboarding_cases", *(_foundation_columns() + [sa.Column("offboarding_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.UniqueConstraint("tenant_id", "offboarding_ref", name="uq_hr_exit_offboarding_cases_offboarding_ref")]))
    op.create_table("hr_access_lifecycle_reviews", *(_foundation_columns("'ACCESS_REVIEW_REQUIRED'") + [sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("offboarding_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_id", sa.String(length=255), nullable=True), sa.Column("decision", sa.String(length=64), nullable=False, server_default=sa.text("'NO_DECISION'")), sa.UniqueConstraint("tenant_id", "review_ref", name="uq_hr_access_lifecycle_reviews_review_ref")]))
    op.create_table("hr_workload_bridge_records", *(_foundation_columns() + [sa.Column("bridge_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("bridge_target", sa.String(length=128), nullable=False), sa.Column("read_only_first", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("mutation_allowed", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.UniqueConstraint("tenant_id", "bridge_ref", name="uq_hr_workload_bridge_records_bridge_ref")]))
    op.create_table("hr_payroll_readiness_profiles", *(_foundation_columns("'NOT_CONFIGURED'") + [sa.Column("profile_ref", sa.String(length=128), nullable=False), sa.Column("staff_ref", sa.String(length=128), nullable=True), sa.Column("provider_name", sa.String(length=128), nullable=False, server_default=sa.text("'HR_PAYROLL_PROVIDER'")), sa.Column("payroll_execution_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("live_provider_sync", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.UniqueConstraint("tenant_id", "profile_ref", name="uq_hr_payroll_readiness_profiles_profile_ref")]))
    op.create_table("hr_provider_readiness_evidence", *(_foundation_columns("'NOT_CONFIGURED'") + [sa.Column("evidence_ref", sa.String(length=128), nullable=False), sa.Column("provider_name", sa.String(length=128), nullable=False), sa.Column("readiness_status", sa.String(length=64), nullable=False, server_default=sa.text("'NOT_CONFIGURED'")), sa.Column("credentials_present", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("live_call_count", sa.Integer(), nullable=False, server_default=sa.text("0")), sa.Column("sync_count", sa.Integer(), nullable=False, server_default=sa.text("0")), sa.Column("external_submission_count", sa.Integer(), nullable=False, server_default=sa.text("0")), sa.Column("live_integration_deferred", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.UniqueConstraint("tenant_id", "evidence_ref", name="uq_hr_provider_readiness_evidence_evidence_ref")]))

    op.create_table("hr_staff_compliance_dashboard_snapshots",
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

    op.create_table("hr_audit_events",
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

    op.create_table("hr_evidence_repository",
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
    op.drop_table("hr_provider_readiness_evidence")
    op.drop_table("hr_payroll_readiness_profiles")
    op.drop_table("hr_workload_bridge_records")
    op.drop_table("hr_access_lifecycle_reviews")
    op.drop_table("hr_exit_offboarding_cases")
    op.drop_table("hr_disciplinary_review_evidence")
    op.drop_table("hr_disciplinary_cases")
    op.drop_table("hr_staff_development_plans")
    op.drop_table("hr_certification_expiry_tracking")
    op.drop_table("hr_training_certifications")
    op.drop_table("hr_appraisal_review_evidence")
    op.drop_table("hr_performance_appraisal_cycles")
    op.drop_table("hr_policy_exceptions")
    op.drop_table("hr_staff_appeals")
    op.drop_table("hr_staff_requests")
    op.drop_table("hr_staff_attendance_metadata")
    op.drop_table("hr_leave_balance_snapshots")
    op.drop_table("hr_absence_metadata")
    op.drop_table("hr_leave_requests")
    op.drop_table("hr_probation_reviews")
    op.drop_table("hr_onboarding_checklist_items")
    op.drop_table("hr_onboarding_cases")
    op.drop_table("hr_hiring_evidence_packs")
    op.drop_table("hr_hiring_committee_reviews")
    op.drop_table("hr_candidate_shortlist_metadata")
    op.drop_table("hr_recruitment_pipeline_items")
    op.drop_table("hr_recruitment_requests")
    op.drop_table("hr_faculty_profiles")
    op.drop_table("hr_department_assignments")
    op.drop_table("hr_position_assignments")
    op.drop_table("hr_staff_status_history")
    op.drop_table("hr_employee_records")
    op.drop_table("hr_staff_profiles")