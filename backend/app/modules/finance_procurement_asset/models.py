"""Finance / Procurement / Asset SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.core.db import Base


MODULE_NAME = "finance_procurement_asset"
API_PREFIX = "/api/admin/finance-procurement-asset"
RUNTIME_MODE = "METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY"
EXPECTED_TABLE_COUNT = 24
EXPECTED_ROUTE_COUNT = 56
EXPECTED_PERMISSION_COUNT = 50
TABLE_PREFIX = "fpa_"
TARGET_LEVEL = "L3"
CONTRACT_VERSION = "A-040.2.RUNTIME"
FOUNDATION_STATUS = "FINANCE_PROCUREMENT_ASSET_METADATA_EVIDENCE_BACKEND_FOUNDATION"
SOURCE_SPEC_COMMIT = "c9df3fa"
SOURCE_PRODUCT_MAP_COMMIT = "ef32c5c"
SOURCE_VERTICAL_SELECTION_COMMIT = "4a11b71,f2037c9"
PRODUCT_VERTICAL = "Finance / Procurement / Asset Suite"
DATA_SOURCE = "computed_from_finance_procurement_asset_metadata"

FAKE_METRICS = False
FAKE_FINANCE_DATA = False
FAKE_PAYMENT_DATA = False
PROVIDER_CONNECTED = False
LIVE_BANK_SYNC = False
LIVE_ERP_SYNC = False
PAYMENT_EXECUTION_ENABLED = False
AUTOMATIC_PROCUREMENT_APPROVAL_ENABLED = False
AUTOMATIC_BUDGET_APPROVAL_ENABLED = False
AUTOMATIC_VENDOR_AWARD_ENABLED = False
HIDDEN_SCORE_PRESENT = False
HUMAN_REVIEW_REQUIRED = True

TABLE_NAMES = {
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
    "fpa_audit_events",
    "fpa_evidence_items",
    "fpa_limitations",
}


def _table_args(table_name: str):
    return (
        Index(f"ix_{table_name}_tenant_id", "tenant_id"),
        Index(f"ix_{table_name}_tenant_status", "tenant_id", "status"),
    )


@declarative_mixin
class FpaMetadataMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'DRAFT'"))
    reference_key: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_module: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_record_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    fake_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_finance_data: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_payment_data: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    provider_connected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    live_bank_sync: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    live_erp_sync: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    payment_execution_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_procurement_approval_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_budget_approval_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_vendor_award_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReadinessProfile(FpaMetadataMixin, Base):
    __tablename__ = "fpa_readiness_profiles"
    __table_args__ = _table_args(__tablename__)
    readiness_scope: Mapped[str] = mapped_column(String(128), nullable=False, server_default=sa_text("'suite'"))


class DashboardSnapshot(FpaMetadataMixin, Base):
    __tablename__ = "fpa_dashboard_snapshots"
    __table_args__ = _table_args(__tablename__)
    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))


class BillingVisibilityRecord(FpaMetadataMixin, Base):
    __tablename__ = "fpa_billing_visibility_records"
    __table_args__ = _table_args(__tablename__)
    billing_state: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ReceivablesMetadata(FpaMetadataMixin, Base):
    __tablename__ = "fpa_receivables_metadata"
    __table_args__ = _table_args(__tablename__)
    aging_band: Mapped[str | None] = mapped_column(String(64), nullable=True)


class BudgetPlanMetadata(FpaMetadataMixin, Base):
    __tablename__ = "fpa_budget_plan_metadata"
    __table_args__ = _table_args(__tablename__)
    fiscal_year: Mapped[int | None] = mapped_column(Integer, nullable=True)


class BudgetControlRecord(FpaMetadataMixin, Base):
    __tablename__ = "fpa_budget_control_records"
    __table_args__ = _table_args(__tablename__)
    control_state: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ProcurementRequestMetadata(FpaMetadataMixin, Base):
    __tablename__ = "fpa_procurement_request_metadata"
    __table_args__ = _table_args(__tablename__)
    request_state: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ProcurementReviewRecord(FpaMetadataMixin, Base):
    __tablename__ = "fpa_procurement_review_records"
    __table_args__ = _table_args(__tablename__)
    reviewer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)


class VendorMetadata(FpaMetadataMixin, Base):
    __tablename__ = "fpa_vendor_metadata"
    __table_args__ = _table_args(__tablename__)
    vendor_status: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ContractEvidence(FpaMetadataMixin, Base):
    __tablename__ = "fpa_contract_evidence"
    __table_args__ = _table_args(__tablename__)
    reference_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)


class PurchaseRequestMetadata(FpaMetadataMixin, Base):
    __tablename__ = "fpa_purchase_request_metadata"
    __table_args__ = _table_args(__tablename__)
    request_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)


class PurchaseOrderMetadata(FpaMetadataMixin, Base):
    __tablename__ = "fpa_purchase_order_metadata"
    __table_args__ = _table_args(__tablename__)
    order_state: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AssetVisibilityRecord(FpaMetadataMixin, Base):
    __tablename__ = "fpa_asset_visibility_records"
    __table_args__ = _table_args(__tablename__)
    asset_state: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AssetLifecycleRecord(FpaMetadataMixin, Base):
    __tablename__ = "fpa_asset_lifecycle_records"
    __table_args__ = _table_args(__tablename__)
    lifecycle_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)


class InventoryMovementMetadata(FpaMetadataMixin, Base):
    __tablename__ = "fpa_inventory_movement_metadata"
    __table_args__ = _table_args(__tablename__)
    movement_type: Mapped[str | None] = mapped_column(String(64), nullable=True)


class PaymentReadinessProfile(FpaMetadataMixin, Base):
    __tablename__ = "fpa_payment_readiness_profiles"
    __table_args__ = _table_args(__tablename__)
    provider_name: Mapped[str | None] = mapped_column(String(128), nullable=True)


class ErpReadinessProfile(FpaMetadataMixin, Base):
    __tablename__ = "fpa_erp_readiness_profiles"
    __table_args__ = _table_args(__tablename__)
    provider_name: Mapped[str | None] = mapped_column(String(128), nullable=True)


class BankReadinessProfile(FpaMetadataMixin, Base):
    __tablename__ = "fpa_bank_readiness_profiles"
    __table_args__ = _table_args(__tablename__)
    provider_name: Mapped[str | None] = mapped_column(String(128), nullable=True)


class PaymentGatewayReadinessProfile(FpaMetadataMixin, Base):
    __tablename__ = "fpa_payment_gateway_readiness_profiles"
    __table_args__ = _table_args(__tablename__)
    provider_name: Mapped[str | None] = mapped_column(String(128), nullable=True)


class ProviderReadinessEvidence(FpaMetadataMixin, Base):
    __tablename__ = "fpa_provider_readiness_evidence"
    __table_args__ = _table_args(__tablename__)
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False, server_default=sa_text("'NON_LIVE_PROVIDER'"))


class FinanceBridgeRecord(FpaMetadataMixin, Base):
    __tablename__ = "fpa_finance_bridge_records"
    __table_args__ = _table_args(__tablename__)
    bridge_family: Mapped[str] = mapped_column(String(128), nullable=False, server_default=sa_text("'executive'"))
    target_domain: Mapped[str | None] = mapped_column(String(128), nullable=True)
    read_only_first: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    mutation_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))


class AuditEvent(Base):
    __tablename__ = "fpa_audit_events"
    __table_args__ = (
        Index("ix_fpa_audit_events_tenant_id", "tenant_id"),
        Index("ix_fpa_audit_events_tenant_created_at", "tenant_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'RECORDED'"))
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    before_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    after_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class EvidenceItem(Base):
    __tablename__ = "fpa_evidence_items"
    __table_args__ = (
        Index("ix_fpa_evidence_items_tenant_id", "tenant_id"),
        Index("ix_fpa_evidence_items_tenant_created_at", "tenant_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'METADATA_ONLY'"))
    evidence_type: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_module: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_record_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    fake_finance_data: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    fake_payment_data: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    provider_connected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


class Limitation(Base):
    __tablename__ = "fpa_limitations"
    __table_args__ = (
        Index("ix_fpa_limitations_tenant_id", "tenant_id"),
        Index("ix_fpa_limitations_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'ACTIVE'"))
    reference_key: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    limitation_code: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


MODEL_BY_FAMILY = {
    "readiness": ReadinessProfile,
    "dashboard": DashboardSnapshot,
    "billing": BillingVisibilityRecord,
    "receivables": ReceivablesMetadata,
    "budget_plans": BudgetPlanMetadata,
    "budget_controls": BudgetControlRecord,
    "procurement_requests": ProcurementRequestMetadata,
    "procurement_reviews": ProcurementReviewRecord,
    "vendors": VendorMetadata,
    "contracts": ContractEvidence,
    "purchase_requests": PurchaseRequestMetadata,
    "purchase_orders": PurchaseOrderMetadata,
    "assets": AssetVisibilityRecord,
    "asset_lifecycle": AssetLifecycleRecord,
    "inventory_movements": InventoryMovementMetadata,
    "payment_readiness": PaymentReadinessProfile,
    "erp_readiness": ErpReadinessProfile,
    "bank_readiness": BankReadinessProfile,
    "payment_gateway_readiness": PaymentGatewayReadinessProfile,
    "provider_readiness": ProviderReadinessEvidence,
    "bridges": FinanceBridgeRecord,
    "audit": AuditEvent,
    "evidence": EvidenceItem,
    "limitations": Limitation,
}
