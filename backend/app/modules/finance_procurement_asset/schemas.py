"""Finance / Procurement / Asset Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class FpaSafetyFlags(BaseModel):
    fake_metrics: Literal[False] = False
    fake_finance_data: Literal[False] = False
    fake_payment_data: Literal[False] = False
    provider_connected: Literal[False] = False
    live_bank_sync: Literal[False] = False
    live_erp_sync: Literal[False] = False
    payment_execution_enabled: Literal[False] = False
    automatic_procurement_approval_enabled: Literal[False] = False
    automatic_budget_approval_enabled: Literal[False] = False
    automatic_vendor_award_enabled: Literal[False] = False
    hidden_score_present: Literal[False] = False
    human_review_required: Literal[True] = True
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)


class FpaMetadataRecord(BaseModel):
    id: int
    tenant_id: int
    status: str
    reference_key: str | None = None
    title: str | None = None
    source_module: str | None = None
    source_record_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FpaAuditEventRecord(BaseModel):
    id: int
    tenant_id: int
    status: str
    entity_type: str
    entity_id: int | None = None
    action: str
    actor_user_id: str | None = None
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class FpaEvidenceItemRecord(BaseModel):
    id: int
    tenant_id: int
    status: str
    evidence_type: str
    title: str
    reference_uri: str | None = None
    source_module: str | None = None
    source_record_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class FpaResponseBase(FpaSafetyFlags):
    tenant_id: int
    module: str = "finance_procurement_asset"
    contract_version: str = "A-040.2.RUNTIME"
    source_spec_commit: str = "c9df3fa"
    runtime_mode: str = "METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY"
    data_source: str = "computed_from_finance_procurement_asset_metadata"


class FpaCollectionResponse(FpaResponseBase):
    records: list[FpaMetadataRecord] = Field(default_factory=list)


class FpaOverviewResponse(FpaResponseBase):
    target_level: str
    foundation_status: str
    selected_vertical: str
    canonical_modules: list[str]
    table_count: int
    route_count: int
    permission_count: int


class FpaReadinessResponse(FpaCollectionResponse):
    pass


class FpaDashboardResponse(FpaResponseBase):
    summary: dict[str, Any] = Field(default_factory=dict)


class FpaBillingVisibilityResponse(FpaCollectionResponse):
    pass


class FpaReceivablesMetadataResponse(FpaCollectionResponse):
    pass


class FpaBudgetPlanResponse(FpaCollectionResponse):
    pass


class FpaBudgetControlResponse(FpaCollectionResponse):
    pass


class FpaProcurementRequestResponse(FpaCollectionResponse):
    pass


class FpaProcurementReviewResponse(FpaCollectionResponse):
    pass


class FpaVendorMetadataResponse(FpaCollectionResponse):
    pass


class FpaContractEvidenceResponse(FpaCollectionResponse):
    pass


class FpaPurchaseRequestResponse(FpaCollectionResponse):
    pass


class FpaPurchaseOrderMetadataResponse(FpaCollectionResponse):
    pass


class FpaAssetVisibilityResponse(FpaCollectionResponse):
    pass


class FpaAssetLifecycleResponse(FpaCollectionResponse):
    pass


class FpaInventoryMovementMetadataResponse(FpaCollectionResponse):
    pass


class FpaPaymentReadinessResponse(FpaCollectionResponse):
    pass


class FpaErpReadinessResponse(FpaCollectionResponse):
    pass


class FpaBankReadinessResponse(FpaCollectionResponse):
    pass


class FpaPaymentGatewayReadinessResponse(FpaCollectionResponse):
    pass


class FpaProviderReadinessResponse(FpaCollectionResponse):
    pass


class FpaAuditEventResponse(FpaResponseBase):
    records: list[FpaAuditEventRecord] = Field(default_factory=list)


class FpaEvidenceItemResponse(FpaResponseBase):
    records: list[FpaEvidenceItemRecord] = Field(default_factory=list)


class FpaBridgeResponse(FpaCollectionResponse):
    pass


class FpaLimitationsResponse(FpaCollectionResponse):
    pass


class FpaMetadataContractResponse(FpaResponseBase):
    api_prefix: str
    table_prefix: str
    table_count: int
    route_count: int
    permission_count: int
    permission_namespace: str
    module_files: list[str]


class FpaMetadataCreateRequest(BaseModel):
    reference_key: str = Field(min_length=1, max_length=128)
    title: str | None = Field(default=None, max_length=255)
    status: str = Field(default="DRAFT", max_length=64)
    source_module: str | None = Field(default=None, max_length=128)
    source_record_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    incomplete_data: bool = True


class FpaReviewCreateRequest(FpaMetadataCreateRequest):
    reviewer_id: str | None = Field(default=None, max_length=255)


class FpaBridgeCreateRequest(FpaMetadataCreateRequest):
    bridge_family: str = Field(default="executive", max_length=128)
    target_domain: str | None = Field(default=None, max_length=128)


class FpaEvidenceCreateRequest(FpaMetadataCreateRequest):
    evidence_type: str = Field(default="metadata_only", max_length=128)
    reference_uri: str | None = Field(default=None, max_length=255)


class FpaAuditEventCreateRequest(BaseModel):
    entity_type: str = Field(min_length=1, max_length=128)
    entity_id: int | None = None
    action: str = Field(min_length=1, max_length=128)
    before: dict[str, Any] = Field(default_factory=dict)
    after: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
