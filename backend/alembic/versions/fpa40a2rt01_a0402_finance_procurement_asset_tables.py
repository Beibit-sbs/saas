"""A-040.2 runtime foundation tables for Finance / Procurement / Asset."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "fpa40a2rt01"
down_revision = "hr39a2rt01"
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
        sa.Column("fake_metrics", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fake_finance_data", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("fake_payment_data", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("provider_connected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("live_bank_sync", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("live_erp_sync", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("payment_execution_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_procurement_approval_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_budget_approval_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_vendor_award_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
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
    op.create_table("fpa_readiness_profiles", *(_foundation_columns("'PROFILE_READY_NON_LIVE'") + [sa.Column("readiness_scope", sa.String(length=128), nullable=False, server_default=sa.text("'suite'"))]))
    op.create_table("fpa_dashboard_snapshots", *(_foundation_columns("'ACTIVE_METADATA_ONLY'") + [sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object())]))
    op.create_table("fpa_billing_visibility_records", *(_foundation_columns("'VISIBLE_METADATA_ONLY'") + [sa.Column("billing_state", sa.String(length=64), nullable=True)]))
    op.create_table("fpa_receivables_metadata", *(_foundation_columns("'VISIBLE_METADATA_ONLY'") + [sa.Column("aging_band", sa.String(length=64), nullable=True)]))
    op.create_table("fpa_budget_plan_metadata", *(_foundation_columns("'REVIEW_REQUIRED'") + [sa.Column("fiscal_year", sa.Integer(), nullable=True)]))
    op.create_table("fpa_budget_control_records", *(_foundation_columns("'HUMAN_REVIEW_REQUIRED'") + [sa.Column("control_state", sa.String(length=64), nullable=True)]))
    op.create_table("fpa_procurement_request_metadata", *(_foundation_columns("'SUBMITTED'") + [sa.Column("request_state", sa.String(length=64), nullable=True)]))
    op.create_table("fpa_procurement_review_records", *(_foundation_columns("'HUMAN_REVIEW_REQUIRED'") + [sa.Column("reviewer_id", sa.String(length=255), nullable=True)]))
    op.create_table("fpa_vendor_metadata", *(_foundation_columns("'REVIEW_REQUIRED'") + [sa.Column("vendor_status", sa.String(length=64), nullable=True)]))
    op.create_table("fpa_contract_evidence", *(_foundation_columns("'EVIDENCE_RECORDED'") + [sa.Column("reference_uri", sa.String(length=255), nullable=True)]))
    op.create_table("fpa_purchase_request_metadata", *(_foundation_columns("'SUBMITTED'") + [sa.Column("request_owner", sa.String(length=255), nullable=True)]))
    op.create_table("fpa_purchase_order_metadata", *(_foundation_columns("'METADATA_ONLY'") + [sa.Column("order_state", sa.String(length=64), nullable=True)]))
    op.create_table("fpa_asset_visibility_records", *(_foundation_columns("'VISIBLE_METADATA_ONLY'") + [sa.Column("asset_state", sa.String(length=64), nullable=True)]))
    op.create_table("fpa_asset_lifecycle_records", *(_foundation_columns("'HUMAN_REVIEW_REQUIRED'") + [sa.Column("lifecycle_stage", sa.String(length=64), nullable=True)]))
    op.create_table("fpa_inventory_movement_metadata", *(_foundation_columns("'METADATA_ONLY'") + [sa.Column("movement_type", sa.String(length=64), nullable=True)]))
    op.create_table("fpa_payment_readiness_profiles", *(_foundation_columns("'PROFILE_READY_NON_LIVE'") + [sa.Column("provider_name", sa.String(length=128), nullable=True)]))
    op.create_table("fpa_erp_readiness_profiles", *(_foundation_columns("'PROFILE_READY_NON_LIVE'") + [sa.Column("provider_name", sa.String(length=128), nullable=True)]))
    op.create_table("fpa_bank_readiness_profiles", *(_foundation_columns("'PROFILE_READY_NON_LIVE'") + [sa.Column("provider_name", sa.String(length=128), nullable=True)]))
    op.create_table("fpa_payment_gateway_readiness_profiles", *(_foundation_columns("'PROFILE_READY_NON_LIVE'") + [sa.Column("provider_name", sa.String(length=128), nullable=True)]))
    op.create_table("fpa_provider_readiness_evidence", *(_foundation_columns("'PROFILE_READY_NON_LIVE'") + [sa.Column("provider_name", sa.String(length=128), nullable=False, server_default=sa.text("'NON_LIVE_PROVIDER'"))]))
    op.create_table("fpa_finance_bridge_records", *(_foundation_columns("'METADATA_ONLY'") + [sa.Column("bridge_family", sa.String(length=128), nullable=False, server_default=sa.text("'executive'")), sa.Column("target_domain", sa.String(length=128), nullable=True), sa.Column("read_only_first", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("mutation_allowed", sa.Boolean(), nullable=False, server_default=sa.text("false"))]))
    op.create_table("fpa_audit_events", sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True), sa.Column("tenant_id", sa.BigInteger(), nullable=False), sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'RECORDED'")), sa.Column("entity_type", sa.String(length=128), nullable=False), sa.Column("entity_id", sa.BigInteger(), nullable=True), sa.Column("action", sa.String(length=128), nullable=False), sa.Column("actor_user_id", sa.String(length=255), nullable=True), sa.Column("before_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("after_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("hidden_score_present", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))
    op.create_table("fpa_evidence_items", sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True), sa.Column("tenant_id", sa.BigInteger(), nullable=False), sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'METADATA_ONLY'")), sa.Column("evidence_type", sa.String(length=128), nullable=False), sa.Column("title", sa.String(length=255), nullable=False), sa.Column("reference_uri", sa.String(length=255), nullable=True), sa.Column("source_module", sa.String(length=128), nullable=True), sa.Column("source_record_id", sa.BigInteger(), nullable=True), sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()), sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("fake_finance_data", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("fake_payment_data", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("provider_connected", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("created_by", sa.String(length=255), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")))
    op.create_table("fpa_limitations", sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True), sa.Column("tenant_id", sa.BigInteger(), nullable=False), sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'ACTIVE'")), sa.Column("reference_key", sa.String(length=128), nullable=False), sa.Column("title", sa.String(length=255), nullable=False), sa.Column("limitation_code", sa.String(length=128), nullable=False), sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()), sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()), sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("created_by", sa.String(length=255), nullable=True), sa.Column("updated_by", sa.String(length=255), nullable=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")), sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))

    for table_name in [
        "fpa_readiness_profiles",
        "fpa_dashboard_snapshots",
        "fpa_billing_visibility_records",
        "fpa_receivables_metadata",
        "fpa_budget_plan_metadata",
        "fpa_budget_control_records",
        "fpa_procurement_request_metadata",
        "fpa_procurement_review_records",
        "fpa_vendor_metadata",
        "fpa_contract_evidence",
        "fpa_purchase_request_metadata",
        "fpa_purchase_order_metadata",
        "fpa_asset_visibility_records",
        "fpa_asset_lifecycle_records",
        "fpa_inventory_movement_metadata",
        "fpa_payment_readiness_profiles",
        "fpa_erp_readiness_profiles",
        "fpa_bank_readiness_profiles",
        "fpa_payment_gateway_readiness_profiles",
        "fpa_provider_readiness_evidence",
        "fpa_finance_bridge_records",
        "fpa_limitations",
    ]:
        _create_standard_indexes(table_name)

    op.create_index("ix_fpa_audit_events_tenant_id", "fpa_audit_events", ["tenant_id"], unique=False)
    op.create_index("ix_fpa_audit_events_tenant_created_at", "fpa_audit_events", ["tenant_id", "created_at"], unique=False)
    op.create_index("ix_fpa_evidence_items_tenant_id", "fpa_evidence_items", ["tenant_id"], unique=False)
    op.create_index("ix_fpa_evidence_items_tenant_created_at", "fpa_evidence_items", ["tenant_id", "created_at"], unique=False)


def downgrade() -> None:
    for index_name, table_name in [
        ("ix_fpa_evidence_items_tenant_created_at", "fpa_evidence_items"),
        ("ix_fpa_evidence_items_tenant_id", "fpa_evidence_items"),
        ("ix_fpa_audit_events_tenant_created_at", "fpa_audit_events"),
        ("ix_fpa_audit_events_tenant_id", "fpa_audit_events"),
    ]:
        op.drop_index(index_name, table_name=table_name)

    for table_name in [
        "fpa_readiness_profiles",
        "fpa_dashboard_snapshots",
        "fpa_billing_visibility_records",
        "fpa_receivables_metadata",
        "fpa_budget_plan_metadata",
        "fpa_budget_control_records",
        "fpa_procurement_request_metadata",
        "fpa_procurement_review_records",
        "fpa_vendor_metadata",
        "fpa_contract_evidence",
        "fpa_purchase_request_metadata",
        "fpa_purchase_order_metadata",
        "fpa_asset_visibility_records",
        "fpa_asset_lifecycle_records",
        "fpa_inventory_movement_metadata",
        "fpa_payment_readiness_profiles",
        "fpa_erp_readiness_profiles",
        "fpa_bank_readiness_profiles",
        "fpa_payment_gateway_readiness_profiles",
        "fpa_provider_readiness_evidence",
        "fpa_finance_bridge_records",
        "fpa_limitations",
    ]:
        op.drop_index(f"ix_{table_name}_tenant_status", table_name=table_name)
        op.drop_index(f"ix_{table_name}_tenant_id", table_name=table_name)

    op.drop_table("fpa_limitations")
    op.drop_table("fpa_evidence_items")
    op.drop_table("fpa_audit_events")
    op.drop_table("fpa_finance_bridge_records")
    op.drop_table("fpa_provider_readiness_evidence")
    op.drop_table("fpa_payment_gateway_readiness_profiles")
    op.drop_table("fpa_bank_readiness_profiles")
    op.drop_table("fpa_erp_readiness_profiles")
    op.drop_table("fpa_payment_readiness_profiles")
    op.drop_table("fpa_inventory_movement_metadata")
    op.drop_table("fpa_asset_lifecycle_records")
    op.drop_table("fpa_asset_visibility_records")
    op.drop_table("fpa_purchase_order_metadata")
    op.drop_table("fpa_purchase_request_metadata")
    op.drop_table("fpa_contract_evidence")
    op.drop_table("fpa_vendor_metadata")
    op.drop_table("fpa_procurement_review_records")
    op.drop_table("fpa_procurement_request_metadata")
    op.drop_table("fpa_budget_control_records")
    op.drop_table("fpa_budget_plan_metadata")
    op.drop_table("fpa_receivables_metadata")
    op.drop_table("fpa_billing_visibility_records")
    op.drop_table("fpa_dashboard_snapshots")
    op.drop_table("fpa_readiness_profiles")