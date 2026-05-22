"""A-037.2 research science backend foundation tables."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "rs37a2rt01"
down_revision = "ao36rt52uv71"
branch_labels = None
depends_on = None


def _safety_columns(status_default: str = "DRAFT") -> list[sa.Column]:
    return [
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text(f"'{status_default}'")),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("autonomous_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("external_database_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("official_verification_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("source_capability_id", sa.String(length=64), nullable=True),
        sa.Column("source_matrix_row_id", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("updated_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "rs_research_projects",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        *_safety_columns(),
        sa.Column("project_ref", sa.String(length=128), nullable=False),
        sa.Column("department_ref", sa.String(length=128), nullable=True),
        sa.Column("program_ref", sa.String(length=128), nullable=True),
        sa.Column("external_ref", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("tenant_id", "project_ref", name="uq_rs_research_projects_tenant_ref"),
    )
    op.create_index("ix_rs_research_projects_tenant_status", "rs_research_projects", ["tenant_id", "status"])

    op.create_table(
        "rs_student_research_work",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        *_safety_columns(),
        sa.Column("student_ref", sa.String(length=128), nullable=True),
        sa.Column("faculty_ref", sa.String(length=128), nullable=True),
        sa.Column("project_ref", sa.String(length=128), nullable=True),
        sa.Column("publication_ref", sa.String(length=128), nullable=True),
        sa.Column("conference_ref", sa.String(length=128), nullable=True),
        sa.Column("topic_title", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_rs_student_research_work_tenant_status", "rs_student_research_work", ["tenant_id", "status"])

    op.create_table(
        "rs_scientific_supervision",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        *_safety_columns(),
        sa.Column("student_ref", sa.String(length=128), nullable=True),
        sa.Column("faculty_ref", sa.String(length=128), nullable=True),
        sa.Column("project_ref", sa.String(length=128), nullable=True),
        sa.Column("supervision_ref", sa.String(length=128), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("tenant_id", "supervision_ref", name="uq_rs_scientific_supervision_tenant_ref"),
    )
    op.create_index("ix_rs_scientific_supervision_tenant_status", "rs_scientific_supervision", ["tenant_id", "status"])

    op.create_table(
        "rs_publication_registry",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        *_safety_columns(),
        sa.Column("publication_ref", sa.String(length=128), nullable=False),
        sa.Column("faculty_ref", sa.String(length=128), nullable=True),
        sa.Column("student_ref", sa.String(length=128), nullable=True),
        sa.Column("project_ref", sa.String(length=128), nullable=True),
        sa.Column("external_ref", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("fake_publication", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("autonomous_publication_verification_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("tenant_id", "publication_ref", name="uq_rs_publication_registry_tenant_ref"),
    )
    op.create_index("ix_rs_publication_registry_tenant_status", "rs_publication_registry", ["tenant_id", "status"])

    op.create_table(
        "rs_conference_participation",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        *_safety_columns(),
        sa.Column("conference_ref", sa.String(length=128), nullable=False),
        sa.Column("faculty_ref", sa.String(length=128), nullable=True),
        sa.Column("student_ref", sa.String(length=128), nullable=True),
        sa.Column("project_ref", sa.String(length=128), nullable=True),
        sa.Column("external_ref", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("fake_certificate", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("tenant_id", "conference_ref", name="uq_rs_conference_participation_tenant_ref"),
    )
    op.create_index("ix_rs_conference_participation_tenant_status", "rs_conference_participation", ["tenant_id", "status"])

    op.create_table(
        "rs_grant_applications",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        *_safety_columns(),
        sa.Column("grant_ref", sa.String(length=128), nullable=False),
        sa.Column("project_ref", sa.String(length=128), nullable=True),
        sa.Column("department_ref", sa.String(length=128), nullable=True),
        sa.Column("faculty_ref", sa.String(length=128), nullable=True),
        sa.Column("external_ref", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("fake_grant_evidence", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("autonomous_grant_submission_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("tenant_id", "grant_ref", name="uq_rs_grant_applications_tenant_ref"),
    )
    op.create_index("ix_rs_grant_applications_tenant_status", "rs_grant_applications", ["tenant_id", "status"])

    op.create_table(
        "rs_grant_deliverables",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        *_safety_columns(),
        sa.Column("grant_ref", sa.String(length=128), nullable=True),
        sa.Column("project_ref", sa.String(length=128), nullable=True),
        sa.Column("external_ref", sa.String(length=128), nullable=True),
        sa.Column("deliverable_ref", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("fake_grant_evidence", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("tenant_id", "deliverable_ref", name="uq_rs_grant_deliverables_tenant_ref"),
    )
    op.create_index("ix_rs_grant_deliverables_tenant_status", "rs_grant_deliverables", ["tenant_id", "status"])

    op.create_table(
        "rs_research_ethics_requests",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        *_safety_columns(),
        sa.Column("ethics_ref", sa.String(length=128), nullable=False),
        sa.Column("project_ref", sa.String(length=128), nullable=True),
        sa.Column("faculty_ref", sa.String(length=128), nullable=True),
        sa.Column("student_ref", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("autonomous_ethics_approval_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("tenant_id", "ethics_ref", name="uq_rs_research_ethics_requests_tenant_ref"),
    )
    op.create_index("ix_rs_research_ethics_requests_tenant_status", "rs_research_ethics_requests", ["tenant_id", "status"])

    op.create_table(
        "rs_research_ethics_amendments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        *_safety_columns(),
        sa.Column("ethics_ref", sa.String(length=128), nullable=True),
        sa.Column("project_ref", sa.String(length=128), nullable=True),
        sa.Column("external_ref", sa.String(length=128), nullable=True),
        sa.Column("amendment_ref", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("tenant_id", "amendment_ref", name="uq_rs_research_ethics_amendments_tenant_ref"),
    )
    op.create_index("ix_rs_research_ethics_amendments_tenant_status", "rs_research_ethics_amendments", ["tenant_id", "status"])

    op.create_table(
        "rs_research_evidence_metadata",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        *_safety_columns(),
        sa.Column("source_entity_type", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.BigInteger(), nullable=True),
        sa.Column("evidence_type", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference_uri", sa.String(length=255), nullable=True),
        sa.Column("storage_ref", sa.String(length=255), nullable=True),
        sa.Column("submitted_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_status", sa.String(length=64), nullable=False, server_default=sa.text("'METADATA_ONLY'")),
        sa.Column("verified_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fake_evidence", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_rs_research_evidence_tenant_entity", "rs_research_evidence_metadata", ["tenant_id", "source_entity_type", "source_entity_id"])

    op.create_table(
        "rs_research_bridge_metadata",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        *_safety_columns(),
        sa.Column("bridge_target", sa.String(length=64), nullable=False),
        sa.Column("source_entity_type", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.BigInteger(), nullable=True),
        sa.Column("target_reference", sa.String(length=255), nullable=True),
        sa.Column("bridge_status", sa.String(length=64), nullable=False, server_default=sa.text("'DRAFT'")),
        sa.Column("bridge_ref", sa.String(length=128), nullable=True),
        sa.Column("read_only_first", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("mutation_allowed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("external_submission_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_rs_research_bridge_tenant_target", "rs_research_bridge_metadata", ["tenant_id", "bridge_target"])

    op.create_table(
        "rs_research_dashboard_snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'ACTIVE'")),
        sa.Column("fake_metrics", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("data_source", sa.String(length=128), nullable=False, server_default=sa.text("'computed_from_research_science_metadata'")),
        sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("source_capability_id", sa.String(length=64), nullable=True),
        sa.Column("source_matrix_row_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_rs_dashboard_snapshots_tenant_status", "rs_research_dashboard_snapshots", ["tenant_id", "status"])

    op.create_table(
        "rs_research_audit_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("source_entity_type", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.BigInteger(), nullable=True),
        sa.Column("actor_user_id", sa.String(length=255), nullable=True),
        sa.Column("previous_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=True),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("request_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("autonomous_decision", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_integration_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_rs_audit_events_tenant_entity", "rs_research_audit_events", ["tenant_id", "source_entity_type", "source_entity_id"])

    op.create_table(
        "rs_research_status_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("source_entity_type", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.BigInteger(), nullable=True),
        sa.Column("previous_status", sa.String(length=64), nullable=True),
        sa.Column("new_status", sa.String(length=64), nullable=False),
        sa.Column("changed_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_rs_status_history_tenant_entity", "rs_research_status_history", ["tenant_id", "source_entity_type", "source_entity_id"])

    op.create_table(
        "rs_research_limitations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("source_entity_type", sa.String(length=64), nullable=False),
        sa.Column("source_entity_id", sa.BigInteger(), nullable=True),
        sa.Column("limitation_code", sa.String(length=128), nullable=False),
        sa.Column("limitation_text", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_rs_limitations_tenant_entity", "rs_research_limitations", ["tenant_id", "source_entity_type", "source_entity_id"])


def downgrade() -> None:
    op.drop_index("ix_rs_limitations_tenant_entity", table_name="rs_research_limitations")
    op.drop_table("rs_research_limitations")
    op.drop_index("ix_rs_status_history_tenant_entity", table_name="rs_research_status_history")
    op.drop_table("rs_research_status_history")
    op.drop_index("ix_rs_audit_events_tenant_entity", table_name="rs_research_audit_events")
    op.drop_table("rs_research_audit_events")
    op.drop_index("ix_rs_dashboard_snapshots_tenant_status", table_name="rs_research_dashboard_snapshots")
    op.drop_table("rs_research_dashboard_snapshots")
    op.drop_index("ix_rs_research_bridge_tenant_target", table_name="rs_research_bridge_metadata")
    op.drop_table("rs_research_bridge_metadata")
    op.drop_index("ix_rs_research_evidence_tenant_entity", table_name="rs_research_evidence_metadata")
    op.drop_table("rs_research_evidence_metadata")
    op.drop_index("ix_rs_research_ethics_amendments_tenant_status", table_name="rs_research_ethics_amendments")
    op.drop_table("rs_research_ethics_amendments")
    op.drop_index("ix_rs_research_ethics_requests_tenant_status", table_name="rs_research_ethics_requests")
    op.drop_table("rs_research_ethics_requests")
    op.drop_index("ix_rs_grant_deliverables_tenant_status", table_name="rs_grant_deliverables")
    op.drop_table("rs_grant_deliverables")
    op.drop_index("ix_rs_grant_applications_tenant_status", table_name="rs_grant_applications")
    op.drop_table("rs_grant_applications")
    op.drop_index("ix_rs_conference_participation_tenant_status", table_name="rs_conference_participation")
    op.drop_table("rs_conference_participation")
    op.drop_index("ix_rs_publication_registry_tenant_status", table_name="rs_publication_registry")
    op.drop_table("rs_publication_registry")
    op.drop_index("ix_rs_scientific_supervision_tenant_status", table_name="rs_scientific_supervision")
    op.drop_table("rs_scientific_supervision")
    op.drop_index("ix_rs_student_research_work_tenant_status", table_name="rs_student_research_work")
    op.drop_table("rs_student_research_work")
    op.drop_index("ix_rs_research_projects_tenant_status", table_name="rs_research_projects")
    op.drop_table("rs_research_projects")