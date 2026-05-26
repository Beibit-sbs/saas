"""A-041.2 runtime tables for Document / Decree / Correspondence."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "ddc0412rt01"
down_revision = "fpa40a2rt01"
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
        sa.Column("reference_key", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("source_module", sa.String(length=128), nullable=True),
        sa.Column("source_record_id", sa.BigInteger(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("fake_documents", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fake_decrees", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fake_signatures", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fake_delivery_confirmations", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fake_archive_legal_record", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("official_legal_effect", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("external_submission_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_rector_decision_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_decree_approval_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_document_signing_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _create_standard_indexes(table_name: str) -> None:
    op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"], unique=False)
    op.create_index(f"ix_{table_name}_tenant_status", table_name, ["tenant_id", "status"], unique=False)


def upgrade() -> None:
    op.create_table("ddc_readiness_profiles", *(_foundation_columns("'PROFILE_READY_NON_LIVE'") + [sa.Column("readiness_scope", sa.String(length=128), nullable=False, server_default=sa.text("'suite'"))]))
    op.create_table("ddc_dashboard_snapshots", *(_foundation_columns("'ACTIVE_METADATA_ONLY'") + [sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object())]))
    op.create_table("ddc_document_intake_records", *(_foundation_columns("'INTAKE_RECORDED'") + [sa.Column("intake_channel", sa.String(length=64), nullable=True)]))
    op.create_table("ddc_document_registration_records", *(_foundation_columns("'REGISTRATION_METADATA_RECORDED'") + [sa.Column("registry_number", sa.String(length=128), nullable=True)]))
    op.create_table("ddc_document_routing_records", *(_foundation_columns("'ROUTING_METADATA_RECORDED'") + [sa.Column("routed_to", sa.String(length=255), nullable=True)]))
    op.create_table("ddc_document_workflow_metadata", *(_foundation_columns("'WORKFLOW_METADATA_RECORDED'") + [sa.Column("workflow_stage", sa.String(length=64), nullable=True)]))
    op.create_table("ddc_rector_resolution_records", *(_foundation_columns("'RESOLUTION_METADATA_RECORDED'") + [sa.Column("resolution_state", sa.String(length=64), nullable=True)]))
    op.create_table("ddc_decree_registry_records", *(_foundation_columns("'DECREE_METADATA_RECORDED'") + [sa.Column("decree_type", sa.String(length=64), nullable=True)]))
    op.create_table("ddc_decree_draft_metadata", *(_foundation_columns("'DECREE_DRAFT_METADATA_RECORDED'") + [sa.Column("draft_version", sa.Integer(), nullable=True)]))
    op.create_table("ddc_incoming_correspondence_records", *(_foundation_columns("'INCOMING_METADATA_RECORDED'") + [sa.Column("sender_name", sa.String(length=255), nullable=True)]))
    op.create_table("ddc_outgoing_correspondence_records", *(_foundation_columns("'OUTGOING_METADATA_RECORDED'") + [sa.Column("recipient_name", sa.String(length=255), nullable=True)]))
    op.create_table("ddc_template_metadata", *(_foundation_columns("'TEMPLATE_METADATA_RECORDED'") + [sa.Column("template_type", sa.String(length=64), nullable=True)]))
    op.create_table("ddc_committee_decision_bridge_records", *(_foundation_columns("'BRIDGE_METADATA_RECORDED'") + [sa.Column("committee_reference", sa.String(length=255), nullable=True)]))
    op.create_table("ddc_assignment_bridge_records", *(_foundation_columns("'BRIDGE_METADATA_RECORDED'") + [sa.Column("assignment_reference", sa.String(length=255), nullable=True)]))
    op.create_table("ddc_execution_control_records", *(_foundation_columns("'EXECUTION_METADATA_RECORDED'") + [sa.Column("control_state", sa.String(length=64), nullable=True)]))
    op.create_table("ddc_sla_deadline_records", *(_foundation_columns("'SLA_METADATA_RECORDED'") + [sa.Column("deadline_label", sa.String(length=128), nullable=True)]))
    op.create_table("ddc_overdue_visibility_records", *(_foundation_columns("'OVERDUE_METADATA_RECORDED'") + [sa.Column("overdue_reason", sa.String(length=255), nullable=True)]))
    op.create_table("ddc_attachment_metadata", *(_foundation_columns("'ATTACHMENT_METADATA_RECORDED'") + [sa.Column("attachment_uri", sa.String(length=255), nullable=True)]))
    op.create_table("ddc_archive_readiness_records", *(_foundation_columns("'ARCHIVE_READINESS_RECORDED'") + [sa.Column("archive_scope", sa.String(length=128), nullable=True)]))
    op.create_table("ddc_retention_metadata", *(_foundation_columns("'RETENTION_METADATA_RECORDED'") + [sa.Column("retention_rule", sa.String(length=128), nullable=True)]))
    op.create_table("ddc_signature_readiness_profiles", *(_foundation_columns("'SIGNATURE_READINESS_RECORDED'") + [sa.Column("provider_name", sa.String(length=128), nullable=True)]))
    op.create_table("ddc_delivery_readiness_profiles", *(_foundation_columns("'DELIVERY_READINESS_RECORDED'") + [sa.Column("provider_name", sa.String(length=128), nullable=True)]))
    op.create_table("ddc_bridge_records", *(_foundation_columns("'BRIDGE_METADATA_RECORDED'") + [sa.Column("bridge_family", sa.String(length=128), nullable=False, server_default=sa.text("'executive'")), sa.Column("target_domain", sa.String(length=128), nullable=True), sa.Column("read_only_first", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("mutation_allowed", sa.Boolean(), nullable=False, server_default=sa.text("false"))]))
    op.create_table("ddc_limitations", *(_foundation_columns("'ACTIVE'") + [sa.Column("limitation_code", sa.String(length=128), nullable=True)]))
    op.create_table("ddc_evidence_items", sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True), sa.Column("tenant_id", sa.BigInteger(), nullable=False), sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'RECORDED'")), sa.Column("evidence_type", sa.String(length=128), nullable=False), sa.Column("title", sa.String(length=255), nullable=False), sa.Column("reference_uri", sa.String(length=255), nullable=True), sa.Column("source_module", sa.String(length=128), nullable=True), sa.Column("source_record_id", sa.BigInteger(), nullable=True), sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()), sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("fake_documents", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("fake_decrees", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("fake_signatures", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("fake_delivery_confirmations", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("fake_archive_legal_record", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("official_legal_effect", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("external_submission_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("automatic_rector_decision_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("automatic_decree_approval_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("automatic_document_signing_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("created_by", sa.String(length=255), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))
    op.create_table("ddc_audit_events", sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True), sa.Column("tenant_id", sa.BigInteger(), nullable=False), sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'RECORDED'")), sa.Column("entity_type", sa.String(length=128), nullable=False), sa.Column("entity_id", sa.BigInteger(), nullable=True), sa.Column("action", sa.String(length=128), nullable=False), sa.Column("actor_user_id", sa.String(length=255), nullable=True), sa.Column("before_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("after_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))

    for table_name in [
        "ddc_readiness_profiles",
        "ddc_dashboard_snapshots",
        "ddc_document_intake_records",
        "ddc_document_registration_records",
        "ddc_document_routing_records",
        "ddc_document_workflow_metadata",
        "ddc_rector_resolution_records",
        "ddc_decree_registry_records",
        "ddc_decree_draft_metadata",
        "ddc_incoming_correspondence_records",
        "ddc_outgoing_correspondence_records",
        "ddc_template_metadata",
        "ddc_committee_decision_bridge_records",
        "ddc_assignment_bridge_records",
        "ddc_execution_control_records",
        "ddc_sla_deadline_records",
        "ddc_overdue_visibility_records",
        "ddc_attachment_metadata",
        "ddc_archive_readiness_records",
        "ddc_retention_metadata",
        "ddc_signature_readiness_profiles",
        "ddc_delivery_readiness_profiles",
        "ddc_bridge_records",
        "ddc_limitations",
    ]:
        _create_standard_indexes(table_name)

    op.create_index("ix_ddc_audit_events_tenant_id", "ddc_audit_events", ["tenant_id"], unique=False)
    op.create_index("ix_ddc_audit_events_tenant_created_at", "ddc_audit_events", ["tenant_id", "created_at"], unique=False)
    op.create_index("ix_ddc_evidence_items_tenant_id", "ddc_evidence_items", ["tenant_id"], unique=False)
    op.create_index("ix_ddc_evidence_items_tenant_created_at", "ddc_evidence_items", ["tenant_id", "created_at"], unique=False)


def downgrade() -> None:
    for index_name, table_name in [
        ("ix_ddc_evidence_items_tenant_created_at", "ddc_evidence_items"),
        ("ix_ddc_evidence_items_tenant_id", "ddc_evidence_items"),
        ("ix_ddc_audit_events_tenant_created_at", "ddc_audit_events"),
        ("ix_ddc_audit_events_tenant_id", "ddc_audit_events"),
    ]:
        op.drop_index(index_name, table_name=table_name)

    for table_name in [
        "ddc_readiness_profiles",
        "ddc_dashboard_snapshots",
        "ddc_document_intake_records",
        "ddc_document_registration_records",
        "ddc_document_routing_records",
        "ddc_document_workflow_metadata",
        "ddc_rector_resolution_records",
        "ddc_decree_registry_records",
        "ddc_decree_draft_metadata",
        "ddc_incoming_correspondence_records",
        "ddc_outgoing_correspondence_records",
        "ddc_template_metadata",
        "ddc_committee_decision_bridge_records",
        "ddc_assignment_bridge_records",
        "ddc_execution_control_records",
        "ddc_sla_deadline_records",
        "ddc_overdue_visibility_records",
        "ddc_attachment_metadata",
        "ddc_archive_readiness_records",
        "ddc_retention_metadata",
        "ddc_signature_readiness_profiles",
        "ddc_delivery_readiness_profiles",
        "ddc_bridge_records",
        "ddc_limitations",
    ]:
        op.drop_index(f"ix_{table_name}_tenant_status", table_name=table_name)
        op.drop_index(f"ix_{table_name}_tenant_id", table_name=table_name)

    op.drop_table("ddc_audit_events")
    op.drop_table("ddc_evidence_items")
    op.drop_table("ddc_limitations")
    op.drop_table("ddc_bridge_records")
    op.drop_table("ddc_delivery_readiness_profiles")
    op.drop_table("ddc_signature_readiness_profiles")
    op.drop_table("ddc_retention_metadata")
    op.drop_table("ddc_archive_readiness_records")
    op.drop_table("ddc_attachment_metadata")
    op.drop_table("ddc_overdue_visibility_records")
    op.drop_table("ddc_sla_deadline_records")
    op.drop_table("ddc_execution_control_records")
    op.drop_table("ddc_assignment_bridge_records")
    op.drop_table("ddc_committee_decision_bridge_records")
    op.drop_table("ddc_template_metadata")
    op.drop_table("ddc_outgoing_correspondence_records")
    op.drop_table("ddc_incoming_correspondence_records")
    op.drop_table("ddc_decree_draft_metadata")
    op.drop_table("ddc_decree_registry_records")
    op.drop_table("ddc_rector_resolution_records")
    op.drop_table("ddc_document_workflow_metadata")
    op.drop_table("ddc_document_routing_records")
    op.drop_table("ddc_document_registration_records")
    op.drop_table("ddc_document_intake_records")
    op.drop_table("ddc_dashboard_snapshots")
    op.drop_table("ddc_readiness_profiles")
