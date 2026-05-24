"""A-038.2 runtime foundation tables for Quality / Accreditation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "qa38a2rt01"
down_revision = "rs37a2rt01"
branch_labels = None
depends_on = None


def _jsonb_default_empty_object():
    return sa.text("'{}'::jsonb")


def _jsonb_default_empty_list():
    return sa.text("'[]'::jsonb")


def _common_columns(*, include_status: bool = True):
    columns = [
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("updated_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("source_capability_id", sa.String(length=64), nullable=True),
        sa.Column("source_family_id", sa.String(length=64), nullable=True),
        sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("official_accreditation_approval_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("official_ministry_submission_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("official_ranking_claim_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_accreditation_decision_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("external_database_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("autonomous_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    ]
    if include_status:
        columns.insert(2, sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'DRAFT'")))
    return columns


def upgrade() -> None:
    op.create_table("qa_quality_frameworks", *(_common_columns() + [sa.Column("framework_ref", sa.String(length=128), nullable=False), sa.Column("title", sa.String(length=255), nullable=False), sa.Column("description", sa.Text(), nullable=True)]))
    op.create_table("qa_quality_policy_registry", *(_common_columns() + [sa.Column("policy_ref", sa.String(length=128), nullable=False), sa.Column("owner_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_accreditation_standards", *(_common_columns() + [sa.Column("framework_ref", sa.String(length=128), nullable=True), sa.Column("standard_ref", sa.String(length=128), nullable=False), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_standard_criteria", *(_common_columns() + [sa.Column("standard_ref", sa.String(length=128), nullable=True), sa.Column("criterion_ref", sa.String(length=128), nullable=False), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_standards_evidence_requirements", *(_common_columns() + [sa.Column("standard_ref", sa.String(length=128), nullable=True), sa.Column("criterion_ref", sa.String(length=128), nullable=True), sa.Column("requirement_ref", sa.String(length=128), nullable=False), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_quality_evidence_registry", *(_common_columns() + [sa.Column("standard_ref", sa.String(length=128), nullable=True), sa.Column("criterion_ref", sa.String(length=128), nullable=True), sa.Column("evidence_ref", sa.String(length=128), nullable=False), sa.Column("source_entity_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False), sa.Column("reference_uri", sa.String(length=255), nullable=True), sa.Column("fake_evidence", sa.Boolean(), nullable=False, server_default=sa.text("false"))]))
    op.create_table("qa_evidence_review", *(_common_columns() + [sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("evidence_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_ref", sa.String(length=128), nullable=True), sa.Column("notes", sa.Text(), nullable=True)]))
    op.create_table("qa_evidence_limitations", *(_common_columns() + [sa.Column("standard_ref", sa.String(length=128), nullable=True), sa.Column("criterion_ref", sa.String(length=128), nullable=True), sa.Column("limitation_ref", sa.String(length=128), nullable=False), sa.Column("evidence_ref", sa.String(length=128), nullable=True), sa.Column("limitation_code", sa.String(length=128), nullable=False), sa.Column("limitation_text", sa.Text(), nullable=False)]))
    op.create_table("qa_program_accreditation_readiness", *(_common_columns() + [sa.Column("readiness_ref", sa.String(length=128), nullable=False), sa.Column("program_ref", sa.String(length=128), nullable=True), sa.Column("framework_ref", sa.String(length=128), nullable=True), sa.Column("completion_percent", sa.Integer(), nullable=False, server_default=sa.text("0"))]))
    op.create_table("qa_institutional_accreditation_readiness", *(_common_columns() + [sa.Column("readiness_ref", sa.String(length=128), nullable=False), sa.Column("framework_ref", sa.String(length=128), nullable=True), sa.Column("completion_percent", sa.Integer(), nullable=False, server_default=sa.text("0"))]))
    op.create_table("qa_self_assessment_reports", *(_common_columns() + [sa.Column("report_ref", sa.String(length=128), nullable=False), sa.Column("framework_ref", sa.String(length=128), nullable=True), sa.Column("program_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_self_assessment_sections", *(_common_columns() + [sa.Column("standard_ref", sa.String(length=128), nullable=True), sa.Column("criterion_ref", sa.String(length=128), nullable=True), sa.Column("section_ref", sa.String(length=128), nullable=False), sa.Column("report_ref", sa.String(length=128), nullable=True), sa.Column("owner_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_quality_improvement_plans", *(_common_columns() + [sa.Column("plan_ref", sa.String(length=128), nullable=False), sa.Column("report_ref", sa.String(length=128), nullable=True), sa.Column("owner_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_quality_improvement_actions", *(_common_columns() + [sa.Column("action_ref", sa.String(length=128), nullable=False), sa.Column("plan_ref", sa.String(length=128), nullable=True), sa.Column("owner_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_internal_quality_audits", *(_common_columns() + [sa.Column("audit_ref", sa.String(length=128), nullable=False), sa.Column("framework_ref", sa.String(length=128), nullable=True), sa.Column("committee_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_quality_audit_findings", *(_common_columns() + [sa.Column("standard_ref", sa.String(length=128), nullable=True), sa.Column("criterion_ref", sa.String(length=128), nullable=True), sa.Column("finding_ref", sa.String(length=128), nullable=False), sa.Column("audit_ref", sa.String(length=128), nullable=True), sa.Column("risk_band", sa.String(length=32), nullable=False, server_default=sa.text("'UNKNOWN'")), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_program_review_cycles", *(_common_columns() + [sa.Column("cycle_ref", sa.String(length=128), nullable=False), sa.Column("program_ref", sa.String(length=128), nullable=True), sa.Column("framework_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_learning_outcomes_assessment", *(_common_columns() + [sa.Column("assessment_ref", sa.String(length=128), nullable=False), sa.Column("program_ref", sa.String(length=128), nullable=True), sa.Column("criterion_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_stakeholder_feedback_metadata", *(_common_columns() + [sa.Column("feedback_ref", sa.String(length=128), nullable=False), sa.Column("program_ref", sa.String(length=128), nullable=True), sa.Column("student_group_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_survey_quality_metadata", *(_common_columns() + [sa.Column("survey_ref", sa.String(length=128), nullable=False), sa.Column("program_ref", sa.String(length=128), nullable=True), sa.Column("owner_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_external_expert_reviews", *(_common_columns() + [sa.Column("review_ref", sa.String(length=128), nullable=False), sa.Column("program_ref", sa.String(length=128), nullable=True), sa.Column("reviewer_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_expert_recommendation_response_plans", *(_common_columns() + [sa.Column("response_plan_ref", sa.String(length=128), nullable=False), sa.Column("review_ref", sa.String(length=128), nullable=True), sa.Column("owner_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_accreditation_committee_workflow", *(_common_columns() + [sa.Column("workflow_ref", sa.String(length=128), nullable=False), sa.Column("report_ref", sa.String(length=128), nullable=True), sa.Column("committee_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_compliance_gap_analysis", *(_common_columns() + [sa.Column("standard_ref", sa.String(length=128), nullable=True), sa.Column("criterion_ref", sa.String(length=128), nullable=True), sa.Column("gap_ref", sa.String(length=128), nullable=False), sa.Column("risk_ref", sa.String(length=128), nullable=True), sa.Column("risk_band", sa.String(length=32), nullable=False, server_default=sa.text("'UNKNOWN'")), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_accreditation_calendar", *(_common_columns() + [sa.Column("calendar_ref", sa.String(length=128), nullable=False), sa.Column("owner_ref", sa.String(length=128), nullable=True), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_quality_risk_register", *(_common_columns() + [sa.Column("risk_ref", sa.String(length=128), nullable=False), sa.Column("program_ref", sa.String(length=128), nullable=True), sa.Column("standard_ref", sa.String(length=128), nullable=True), sa.Column("risk_band", sa.String(length=32), nullable=False, server_default=sa.text("'UNKNOWN'")), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_quality_bridge_metadata", *(_common_columns() + [sa.Column("bridge_ref", sa.String(length=128), nullable=False), sa.Column("source_vertical_ref", sa.String(length=128), nullable=True), sa.Column("source_entity_ref", sa.String(length=128), nullable=True), sa.Column("target_reference", sa.String(length=255), nullable=True), sa.Column("read_only_first", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("mutation_allowed", sa.Boolean(), nullable=False, server_default=sa.text("false"))]))
    op.create_table("qa_quality_dashboard_snapshots", sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True), sa.Column("tenant_id", sa.BigInteger(), nullable=False), sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'ACTIVE_METADATA_ONLY'")), sa.Column("fake_metrics", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("data_source", sa.String(length=128), nullable=False, server_default=sa.text("'computed_from_quality_accreditation_metadata'")), sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))
    op.create_table("qa_quality_brain_signals", *(_common_columns() + [sa.Column("signal_ref", sa.String(length=128), nullable=False), sa.Column("source_entity_ref", sa.String(length=128), nullable=True), sa.Column("signal_type", sa.String(length=128), nullable=False), sa.Column("title", sa.String(length=255), nullable=False)]))
    op.create_table("qa_quality_audit_events", sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True), sa.Column("tenant_id", sa.BigInteger(), nullable=False), sa.Column("event_type", sa.String(length=128), nullable=False), sa.Column("source_entity_type", sa.String(length=64), nullable=False), sa.Column("source_entity_id", sa.BigInteger(), nullable=True), sa.Column("actor_user_id", sa.String(length=255), nullable=True), sa.Column("previous_status", sa.String(length=64), nullable=True), sa.Column("new_status", sa.String(length=64), nullable=True), sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")), sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_table("qa_quality_status_history", sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True), sa.Column("tenant_id", sa.BigInteger(), nullable=False), sa.Column("source_entity_type", sa.String(length=64), nullable=False), sa.Column("source_entity_id", sa.BigInteger(), nullable=True), sa.Column("previous_status", sa.String(length=64), nullable=True), sa.Column("new_status", sa.String(length=64), nullable=False), sa.Column("changed_by_user_id", sa.String(length=255), nullable=True), sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))
    op.create_table("qa_quality_limitations", sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True), sa.Column("tenant_id", sa.BigInteger(), nullable=False), sa.Column("source_entity_type", sa.String(length=64), nullable=False), sa.Column("source_entity_id", sa.BigInteger(), nullable=True), sa.Column("limitation_code", sa.String(length=128), nullable=False), sa.Column("limitation_text", sa.Text(), nullable=False), sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))

    for table_name in [
        "qa_quality_frameworks",
        "qa_quality_policy_registry",
        "qa_accreditation_standards",
        "qa_standard_criteria",
        "qa_standards_evidence_requirements",
        "qa_quality_evidence_registry",
        "qa_evidence_review",
        "qa_evidence_limitations",
        "qa_program_accreditation_readiness",
        "qa_institutional_accreditation_readiness",
        "qa_self_assessment_reports",
        "qa_self_assessment_sections",
        "qa_quality_improvement_plans",
        "qa_quality_improvement_actions",
        "qa_internal_quality_audits",
        "qa_quality_audit_findings",
        "qa_program_review_cycles",
        "qa_learning_outcomes_assessment",
        "qa_stakeholder_feedback_metadata",
        "qa_survey_quality_metadata",
        "qa_external_expert_reviews",
        "qa_expert_recommendation_response_plans",
        "qa_accreditation_committee_workflow",
        "qa_compliance_gap_analysis",
        "qa_accreditation_calendar",
        "qa_quality_risk_register",
        "qa_quality_bridge_metadata",
        "qa_quality_brain_signals",
    ]:
        op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"], unique=False)

    for table_name in [
        "qa_quality_frameworks",
        "qa_quality_policy_registry",
        "qa_accreditation_standards",
        "qa_standard_criteria",
        "qa_standards_evidence_requirements",
        "qa_quality_evidence_registry",
        "qa_evidence_review",
        "qa_evidence_limitations",
        "qa_program_accreditation_readiness",
        "qa_institutional_accreditation_readiness",
        "qa_self_assessment_reports",
        "qa_self_assessment_sections",
        "qa_quality_improvement_plans",
        "qa_quality_improvement_actions",
        "qa_internal_quality_audits",
        "qa_quality_audit_findings",
        "qa_program_review_cycles",
        "qa_learning_outcomes_assessment",
        "qa_stakeholder_feedback_metadata",
        "qa_survey_quality_metadata",
        "qa_external_expert_reviews",
        "qa_expert_recommendation_response_plans",
        "qa_accreditation_committee_workflow",
        "qa_compliance_gap_analysis",
        "qa_accreditation_calendar",
        "qa_quality_risk_register",
        "qa_quality_bridge_metadata",
        "qa_quality_brain_signals",
    ]:
        op.create_index(f"ix_{table_name}_tenant_status", table_name, ["tenant_id", "status"], unique=False)

    for table_name in [
        "qa_accreditation_standards",
        "qa_standard_criteria",
        "qa_standards_evidence_requirements",
        "qa_quality_evidence_registry",
        "qa_evidence_limitations",
        "qa_self_assessment_sections",
        "qa_quality_audit_findings",
        "qa_compliance_gap_analysis",
    ]:
        columns = ["tenant_id", "standard_ref"]
        if table_name != "qa_accreditation_standards":
            columns.append("criterion_ref")
        op.create_index(f"ix_{table_name}_tenant_standard_criterion", table_name, columns, unique=False)

    op.create_index("ix_qa_quality_bridge_metadata_tenant_source", "qa_quality_bridge_metadata", ["tenant_id", "source_vertical_ref", "source_entity_ref"], unique=False)
    op.create_index("ix_qa_quality_dashboard_snapshots_tenant_created", "qa_quality_dashboard_snapshots", ["tenant_id", "created_at"], unique=False)
    op.create_index("ix_qa_quality_audit_events_tenant_created", "qa_quality_audit_events", ["tenant_id", "created_at"], unique=False)
    op.create_index("ix_qa_quality_status_history_tenant_created", "qa_quality_status_history", ["tenant_id", "created_at"], unique=False)


def downgrade() -> None:
    for index_name in [
        "ix_qa_quality_status_history_tenant_created",
        "ix_qa_quality_audit_events_tenant_created",
        "ix_qa_quality_dashboard_snapshots_tenant_created",
        "ix_qa_quality_bridge_metadata_tenant_source",
    ]:
        op.drop_index(index_name, table_name=index_name.replace("ix_", "", 1).rsplit("_", 2)[0])

    for table_name in [
        "qa_quality_frameworks",
        "qa_quality_policy_registry",
        "qa_accreditation_standards",
        "qa_standard_criteria",
        "qa_standards_evidence_requirements",
        "qa_quality_evidence_registry",
        "qa_evidence_review",
        "qa_evidence_limitations",
        "qa_program_accreditation_readiness",
        "qa_institutional_accreditation_readiness",
        "qa_self_assessment_reports",
        "qa_self_assessment_sections",
        "qa_quality_improvement_plans",
        "qa_quality_improvement_actions",
        "qa_internal_quality_audits",
        "qa_quality_audit_findings",
        "qa_program_review_cycles",
        "qa_learning_outcomes_assessment",
        "qa_stakeholder_feedback_metadata",
        "qa_survey_quality_metadata",
        "qa_external_expert_reviews",
        "qa_expert_recommendation_response_plans",
        "qa_accreditation_committee_workflow",
        "qa_compliance_gap_analysis",
        "qa_accreditation_calendar",
        "qa_quality_risk_register",
        "qa_quality_bridge_metadata",
        "qa_quality_brain_signals",
    ]:
        op.drop_index(f"ix_{table_name}_tenant_standard_criterion", table_name=table_name, if_exists=True)
        op.drop_index(f"ix_{table_name}_tenant_status", table_name=table_name, if_exists=True)
        op.drop_index(f"ix_{table_name}_tenant_id", table_name=table_name, if_exists=True)

    for table_name in [
        "qa_quality_limitations",
        "qa_quality_status_history",
        "qa_quality_audit_events",
        "qa_quality_brain_signals",
        "qa_quality_dashboard_snapshots",
        "qa_quality_bridge_metadata",
        "qa_quality_risk_register",
        "qa_accreditation_calendar",
        "qa_compliance_gap_analysis",
        "qa_accreditation_committee_workflow",
        "qa_expert_recommendation_response_plans",
        "qa_external_expert_reviews",
        "qa_survey_quality_metadata",
        "qa_stakeholder_feedback_metadata",
        "qa_learning_outcomes_assessment",
        "qa_program_review_cycles",
        "qa_quality_audit_findings",
        "qa_internal_quality_audits",
        "qa_quality_improvement_actions",
        "qa_quality_improvement_plans",
        "qa_self_assessment_sections",
        "qa_self_assessment_reports",
        "qa_institutional_accreditation_readiness",
        "qa_program_accreditation_readiness",
        "qa_evidence_limitations",
        "qa_evidence_review",
        "qa_quality_evidence_registry",
        "qa_standards_evidence_requirements",
        "qa_standard_criteria",
        "qa_accreditation_standards",
        "qa_quality_policy_registry",
        "qa_quality_frameworks",
    ]:
        op.drop_table(table_name)