"""A-036.2 Academic Operations backend foundation tables.

Revision ID: ao36rt52uv71
Revises: uq35sl24rt80
Create Date: 2026-05-22 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "ao36rt52uv71"
down_revision = "uq35sl24rt80"
branch_labels = None
depends_on = None


def _safety_columns(status_default: str = "DRAFT") -> list[sa.Column]:
    return [
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=status_default),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("platonus_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sis_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("official_grade_publication_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automated_grading_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_sanction_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("source_capability_id", sa.String(length=64), nullable=True),
        sa.Column("source_matrix_row_id", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("updated_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _create_safety_table(name: str, extra_columns: list[sa.Column], *, unique_constraints: list[sa.UniqueConstraint] | None = None) -> None:
    op.create_table(
        name,
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        *(_safety_columns() + extra_columns),
        *(unique_constraints or []),
    )
    op.create_index(f"ix_{name}_tenant_id", name, ["tenant_id"])
    op.create_index(f"ix_{name}_tenant_status", name, ["tenant_id", "status"])
    op.create_index(f"ix_{name}_tenant_created_at", name, ["tenant_id", "created_at"])


def upgrade() -> None:
    _create_safety_table(
        "ao_academic_groups",
        [
            sa.Column("group_code", sa.String(length=64), nullable=False),
            sa.Column("group_name", sa.String(length=255), nullable=False),
            sa.Column("external_ref", sa.String(length=128), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
        ],
        unique_constraints=[sa.UniqueConstraint("tenant_id", "group_code", name="uq_ao_academic_groups_tenant_code")],
    )
    _create_safety_table(
        "ao_cohorts",
        [
            sa.Column("cohort_code", sa.String(length=64), nullable=False),
            sa.Column("cohort_name", sa.String(length=255), nullable=False),
            sa.Column("academic_group_ref", sa.String(length=128), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
        ],
        unique_constraints=[sa.UniqueConstraint("tenant_id", "cohort_code", name="uq_ao_cohorts_tenant_code")],
    )
    _create_safety_table(
        "ao_course_registration_metadata",
        [
            sa.Column("student_ref", sa.String(length=128), nullable=True),
            sa.Column("course_ref", sa.String(length=128), nullable=True),
            sa.Column("canonical_module_ref", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("notes", sa.Text(), nullable=True),
        ],
    )
    _create_safety_table(
        "ao_gradebook_metadata",
        [
            sa.Column("student_ref", sa.String(length=128), nullable=True),
            sa.Column("course_ref", sa.String(length=128), nullable=True),
            sa.Column("gradebook_key", sa.String(length=128), nullable=False),
            sa.Column("metadata_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        ],
        unique_constraints=[sa.UniqueConstraint("tenant_id", "gradebook_key", name="uq_ao_gradebook_metadata_tenant_key")],
    )
    _create_safety_table(
        "ao_retake_plans",
        [
            sa.Column("student_ref", sa.String(length=128), nullable=True),
            sa.Column("course_ref", sa.String(length=128), nullable=True),
            sa.Column("plan_code", sa.String(length=128), nullable=False),
            sa.Column("retake_window", sa.String(length=128), nullable=True),
        ],
        unique_constraints=[sa.UniqueConstraint("tenant_id", "plan_code", name="uq_ao_retake_plans_tenant_code")],
    )
    _create_safety_table(
        "ao_summer_semester_terms",
        [
            sa.Column("term_code", sa.String(length=64), nullable=False),
            sa.Column("display_name", sa.String(length=255), nullable=False),
            sa.Column("calendar_ref", sa.String(length=128), nullable=True),
        ],
        unique_constraints=[sa.UniqueConstraint("tenant_id", "term_code", name="uq_ao_summer_terms_tenant_code")],
    )
    _create_safety_table(
        "ao_advisor_tutor_assignments",
        [
            sa.Column("student_ref", sa.String(length=128), nullable=True),
            sa.Column("faculty_ref", sa.String(length=128), nullable=True),
            sa.Column("assignment_code", sa.String(length=128), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
        ],
        unique_constraints=[sa.UniqueConstraint("tenant_id", "assignment_code", name="uq_ao_advisor_tutor_assignments_tenant_code")],
    )
    _create_safety_table(
        "ao_canonical_module_bridges",
        [
            sa.Column("bridge_type", sa.String(length=64), nullable=False),
            sa.Column("canonical_module_ref", sa.String(length=128), nullable=False),
            sa.Column("external_ref", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        ],
    )
    op.create_index("ix_ao_canonical_bridges_tenant_type", "ao_canonical_module_bridges", ["tenant_id", "bridge_type"])
    _create_safety_table(
        "ao_student_lifecycle_bridge_metadata",
        [
            sa.Column("bridge_key", sa.String(length=128), nullable=False),
            sa.Column("student_ref", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        ],
    )
    _create_safety_table(
        "ao_document_workflow_bridge_metadata",
        [
            sa.Column("bridge_key", sa.String(length=128), nullable=False),
            sa.Column("external_ref", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        ],
    )
    _create_safety_table(
        "ao_executive_governance_bridge_metadata",
        [
            sa.Column("bridge_key", sa.String(length=128), nullable=False),
            sa.Column("external_ref", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        ],
    )
    _create_safety_table(
        "ao_quality_accreditation_bridge_metadata",
        [
            sa.Column("bridge_key", sa.String(length=128), nullable=False),
            sa.Column("external_ref", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        ],
    )

    op.create_table(
        "ao_academic_operations_dashboard_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default="ACTIVE"),
        sa.Column("fake_metrics", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("data_source", sa.String(length=128), nullable=False, server_default="computed_from_academic_operations_metadata"),
        sa.Column("summary_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("limitations_json", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("source_capability_id", sa.String(length=64), nullable=True),
        sa.Column("source_matrix_row_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_ao_dashboard_snapshots_tenant_id", "ao_academic_operations_dashboard_snapshots", ["tenant_id"])
    op.create_index("ix_ao_dashboard_snapshots_tenant_status", "ao_academic_operations_dashboard_snapshots", ["tenant_id", "status"])
    op.create_index("ix_ao_dashboard_snapshots_tenant_created_at", "ao_academic_operations_dashboard_snapshots", ["tenant_id", "created_at"])

    op.create_table(
        "ao_academic_operations_audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("previous_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=True),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("automated_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payload_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_ao_audit_events_tenant_id", "ao_academic_operations_audit_events", ["tenant_id"])
    op.create_index("ix_ao_audit_events_tenant_entity", "ao_academic_operations_audit_events", ["tenant_id", "entity_type"])
    op.create_index("ix_ao_audit_events_tenant_created_at", "ao_academic_operations_audit_events", ["tenant_id", "created_at"])

    _create_safety_table(
        "ao_academic_operations_evidence_metadata",
        [
            sa.Column("entity_type", sa.String(length=64), nullable=False),
            sa.Column("entity_id", sa.BigInteger(), nullable=True),
            sa.Column("evidence_kind", sa.String(length=128), nullable=False),
            sa.Column("external_ref", sa.String(length=128), nullable=True),
            sa.Column("metadata_json", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        ],
    )
    op.create_index("ix_ao_evidence_tenant_entity", "ao_academic_operations_evidence_metadata", ["tenant_id", "entity_type"])

    op.create_table(
        "ao_academic_operations_limitations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("limitation_code", sa.String(length=128), nullable=False),
        sa.Column("limitation_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_ao_limitations_tenant_id", "ao_academic_operations_limitations", ["tenant_id"])
    op.create_index("ix_ao_limitations_tenant_entity", "ao_academic_operations_limitations", ["tenant_id", "entity_type"])

    op.create_table(
        "ao_academic_operations_status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=False),
        sa.Column("previous_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_ao_status_history_tenant_id", "ao_academic_operations_status_history", ["tenant_id"])
    op.create_index("ix_ao_status_history_tenant_entity", "ao_academic_operations_status_history", ["tenant_id", "entity_type", "entity_id"])

    op.create_table(
        "ao_gradebook_status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("gradebook_metadata_id", sa.BigInteger(), sa.ForeignKey("ao_gradebook_metadata.id"), nullable=False),
        sa.Column("previous_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_ao_gradebook_status_history_tenant_id", "ao_gradebook_status_history", ["tenant_id"])
    op.create_index("ix_ao_gradebook_status_history_tenant_gradebook", "ao_gradebook_status_history", ["tenant_id", "gradebook_metadata_id"])

    op.create_table(
        "ao_retake_status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("retake_plan_id", sa.BigInteger(), sa.ForeignKey("ao_retake_plans.id"), nullable=False),
        sa.Column("previous_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_ao_retake_status_history_tenant_id", "ao_retake_status_history", ["tenant_id"])
    op.create_index("ix_ao_retake_status_history_tenant_retake", "ao_retake_status_history", ["tenant_id", "retake_plan_id"])


def downgrade() -> None:
    for index_name, table_name in [
        ("ix_ao_retake_status_history_tenant_retake", "ao_retake_status_history"),
        ("ix_ao_retake_status_history_tenant_id", "ao_retake_status_history"),
        ("ix_ao_gradebook_status_history_tenant_gradebook", "ao_gradebook_status_history"),
        ("ix_ao_gradebook_status_history_tenant_id", "ao_gradebook_status_history"),
        ("ix_ao_status_history_tenant_entity", "ao_academic_operations_status_history"),
        ("ix_ao_status_history_tenant_id", "ao_academic_operations_status_history"),
        ("ix_ao_limitations_tenant_entity", "ao_academic_operations_limitations"),
        ("ix_ao_limitations_tenant_id", "ao_academic_operations_limitations"),
        ("ix_ao_evidence_tenant_entity", "ao_academic_operations_evidence_metadata"),
        ("ix_ao_academic_operations_evidence_metadata_tenant_created_at", "ao_academic_operations_evidence_metadata"),
        ("ix_ao_academic_operations_evidence_metadata_tenant_status", "ao_academic_operations_evidence_metadata"),
        ("ix_ao_academic_operations_evidence_metadata_tenant_id", "ao_academic_operations_evidence_metadata"),
        ("ix_ao_audit_events_tenant_created_at", "ao_academic_operations_audit_events"),
        ("ix_ao_audit_events_tenant_entity", "ao_academic_operations_audit_events"),
        ("ix_ao_audit_events_tenant_id", "ao_academic_operations_audit_events"),
        ("ix_ao_dashboard_snapshots_tenant_created_at", "ao_academic_operations_dashboard_snapshots"),
        ("ix_ao_dashboard_snapshots_tenant_status", "ao_academic_operations_dashboard_snapshots"),
        ("ix_ao_dashboard_snapshots_tenant_id", "ao_academic_operations_dashboard_snapshots"),
        ("ix_ao_quality_accreditation_bridge_metadata_tenant_created_at", "ao_quality_accreditation_bridge_metadata"),
        ("ix_ao_quality_accreditation_bridge_metadata_tenant_status", "ao_quality_accreditation_bridge_metadata"),
        ("ix_ao_quality_accreditation_bridge_metadata_tenant_id", "ao_quality_accreditation_bridge_metadata"),
        ("ix_ao_executive_governance_bridge_metadata_tenant_created_at", "ao_executive_governance_bridge_metadata"),
        ("ix_ao_executive_governance_bridge_metadata_tenant_status", "ao_executive_governance_bridge_metadata"),
        ("ix_ao_executive_governance_bridge_metadata_tenant_id", "ao_executive_governance_bridge_metadata"),
        ("ix_ao_document_workflow_bridge_metadata_tenant_created_at", "ao_document_workflow_bridge_metadata"),
        ("ix_ao_document_workflow_bridge_metadata_tenant_status", "ao_document_workflow_bridge_metadata"),
        ("ix_ao_document_workflow_bridge_metadata_tenant_id", "ao_document_workflow_bridge_metadata"),
        ("ix_ao_student_lifecycle_bridge_metadata_tenant_created_at", "ao_student_lifecycle_bridge_metadata"),
        ("ix_ao_student_lifecycle_bridge_metadata_tenant_status", "ao_student_lifecycle_bridge_metadata"),
        ("ix_ao_student_lifecycle_bridge_metadata_tenant_id", "ao_student_lifecycle_bridge_metadata"),
        ("ix_ao_canonical_bridges_tenant_type", "ao_canonical_module_bridges"),
        ("ix_ao_canonical_module_bridges_tenant_created_at", "ao_canonical_module_bridges"),
        ("ix_ao_canonical_module_bridges_tenant_status", "ao_canonical_module_bridges"),
        ("ix_ao_canonical_module_bridges_tenant_id", "ao_canonical_module_bridges"),
        ("ix_ao_advisor_tutor_assignments_tenant_created_at", "ao_advisor_tutor_assignments"),
        ("ix_ao_advisor_tutor_assignments_tenant_status", "ao_advisor_tutor_assignments"),
        ("ix_ao_advisor_tutor_assignments_tenant_id", "ao_advisor_tutor_assignments"),
        ("ix_ao_summer_semester_terms_tenant_created_at", "ao_summer_semester_terms"),
        ("ix_ao_summer_semester_terms_tenant_status", "ao_summer_semester_terms"),
        ("ix_ao_summer_semester_terms_tenant_id", "ao_summer_semester_terms"),
        ("ix_ao_retake_plans_tenant_created_at", "ao_retake_plans"),
        ("ix_ao_retake_plans_tenant_status", "ao_retake_plans"),
        ("ix_ao_retake_plans_tenant_id", "ao_retake_plans"),
        ("ix_ao_gradebook_metadata_tenant_created_at", "ao_gradebook_metadata"),
        ("ix_ao_gradebook_metadata_tenant_status", "ao_gradebook_metadata"),
        ("ix_ao_gradebook_metadata_tenant_id", "ao_gradebook_metadata"),
        ("ix_ao_course_registration_metadata_tenant_created_at", "ao_course_registration_metadata"),
        ("ix_ao_course_registration_metadata_tenant_status", "ao_course_registration_metadata"),
        ("ix_ao_course_registration_metadata_tenant_id", "ao_course_registration_metadata"),
        ("ix_ao_cohorts_tenant_created_at", "ao_cohorts"),
        ("ix_ao_cohorts_tenant_status", "ao_cohorts"),
        ("ix_ao_cohorts_tenant_id", "ao_cohorts"),
        ("ix_ao_academic_groups_tenant_created_at", "ao_academic_groups"),
        ("ix_ao_academic_groups_tenant_status", "ao_academic_groups"),
        ("ix_ao_academic_groups_tenant_id", "ao_academic_groups"),
    ]:
        op.drop_index(index_name, table_name=table_name)

    for table_name in [
        "ao_retake_status_history",
        "ao_gradebook_status_history",
        "ao_academic_operations_status_history",
        "ao_academic_operations_limitations",
        "ao_academic_operations_evidence_metadata",
        "ao_academic_operations_audit_events",
        "ao_academic_operations_dashboard_snapshots",
        "ao_quality_accreditation_bridge_metadata",
        "ao_executive_governance_bridge_metadata",
        "ao_document_workflow_bridge_metadata",
        "ao_student_lifecycle_bridge_metadata",
        "ao_canonical_module_bridges",
        "ao_advisor_tutor_assignments",
        "ao_summer_semester_terms",
        "ao_retake_plans",
        "ao_gradebook_metadata",
        "ao_course_registration_metadata",
        "ao_cohorts",
        "ao_academic_groups",
    ]:
        op.drop_table(table_name)