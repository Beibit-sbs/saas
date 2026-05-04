from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


VendorStatus = Literal["active", "under_review", "inactive"]
ContractStatus = Literal[
    "draft",
    "active",
    "expiring",
    "expired",
    "DRAFT",
    "SUBMITTED",
    "APPROVED",
    "REJECTED",
    "PO_ISSUED",
    "DELIVERED",
]
PurchaseOrderStatus = Literal["DRAFT", "SUBMITTED", "APPROVED", "REJECTED", "PO_ISSUED", "DELIVERED"]
AssetStatus = Literal["available", "allocated", "maintenance", "retired"]
InventoryItemStatus = Literal["healthy", "watch", "critical", "inactive"]


class VendorCreateSchema(BaseModel):
    vendor_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=120)
    sla_breach_rate: float = Field(default=0, ge=0, le=1)
    on_time_delivery_rate: float = Field(default=1, ge=0, le=1)
    status: VendorStatus = "active"
    contact_name: str | None = Field(default=None, max_length=128)


class VendorSchema(VendorCreateSchema):
    id: int
    tenant_id: str | None = None


class ContractCreateSchema(BaseModel):
    contract_code: str = Field(min_length=1, max_length=64)
    vendor_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=220)
    risk_score: float = Field(default=0, ge=0, le=1)
    sla_target_met: bool = True
    status: ContractStatus = "draft"


class ContractSchema(ContractCreateSchema):
    id: int
    tenant_id: str | None = None


class AssetCreateSchema(BaseModel):
    asset_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=220)
    asset_category: str = Field(min_length=1, max_length=120)
    status: AssetStatus = "available"


class AssetSchema(AssetCreateSchema):
    id: int
    tenant_id: str | None = None


class InventoryItemCreateSchema(BaseModel):
    item_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=220)
    current_stock: float = Field(ge=0)
    reorder_point: float = Field(ge=0)
    daily_usage_rate: float = Field(ge=0)
    lead_time_days: int = Field(ge=0)
    auto_reorder_enabled: bool = True
    status: InventoryItemStatus = "healthy"


class InventoryItemSchema(InventoryItemCreateSchema):
    id: int
    tenant_id: str | None = None

    @property
    def projected_days_remaining(self) -> float | None:
        if self.daily_usage_rate <= 0:
            return None
        return self.current_stock / self.daily_usage_rate


class VendorListResponseSchema(BaseModel):
    items: list[VendorSchema]


class ContractListResponseSchema(BaseModel):
    items: list[ContractSchema]


class AssetListResponseSchema(BaseModel):
    items: list[AssetSchema]


class InventoryItemListResponseSchema(BaseModel):
    items: list[InventoryItemSchema]


class VendorItemResponseSchema(BaseModel):
    item: VendorSchema


class ContractItemResponseSchema(BaseModel):
    item: ContractSchema


class ContractStatusUpdateSchema(BaseModel):
    status: PurchaseOrderStatus


class AssetItemResponseSchema(BaseModel):
    item: AssetSchema


class InventoryItemItemResponseSchema(BaseModel):
    item: InventoryItemSchema


class ProcurementHealthSnapshotSchema(BaseModel):
    tenant_id: int = Field(..., ge=1)
    vendors_total: int = Field(..., ge=0)
    active_vendors: int = Field(..., ge=0)
    vendors_sla_breached: int = Field(..., ge=0)
    contracts_total: int = Field(..., ge=0)
    at_risk_contracts: int = Field(..., ge=0)
    contracts_high_risk: int = Field(..., ge=0)
    assets_total: int = Field(..., ge=0)
    constrained_assets: int = Field(..., ge=0)
    inventory_items_total: int = Field(..., ge=0)
    low_stock_items: int = Field(..., ge=0)
    projected_stockouts_7d: int = Field(..., ge=0)
    auto_reorder_candidates: int = Field(..., ge=0)


class ProcurementHealthResponseSchema(BaseModel):
    item: ProcurementHealthSnapshotSchema


# ─── Request Lifecycle Schemas (A-009 Phase 2.3: Missing frontend contract endpoints) ────


ProcurementRequestStatus = Literal[
    "draft", "submitted", "under_review", "approved", "rejected", "ordered", "fulfilled", "cancelled"
]
ProcurementPriority = Literal["low", "medium", "high", "critical"]
ProcurementCategory = Literal["equipment", "software", "services", "facilities", "supplies", "other"]
ProcurementOrderStatus = Literal["issued", "partially_received", "received", "cancelled"]
ApprovalStepStatus = Literal["pending", "approved", "rejected", "skipped"]


class RequestItemCreateSchema(BaseModel):
    description: str = Field(min_length=1, max_length=512)
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    category: ProcurementCategory = "supplies"
    sku: str | None = None


class RequestItemSchema(BaseModel):
    item_id: str
    request_id: str
    sku: str | None = None
    description: str
    quantity: int
    unit_price: float
    total_price: float
    category: ProcurementCategory


class ProcurementRequestCreateSchema(BaseModel):
    department_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=220)
    description: str | None = None
    priority: ProcurementPriority = "medium"
    needed_by_date: str | None = None
    items: list[RequestItemCreateSchema] = Field(default_factory=list)


class ProcurementRequestUpdateSchema(BaseModel):
    title: str | None = Field(default=None, max_length=220)
    description: str | None = None
    priority: ProcurementPriority | None = None
    needed_by_date: str | None = None


class ProcurementStatusUpdateSchema(BaseModel):
    status: ProcurementRequestStatus
    comment: str | None = None


class ProcurementRequestSchema(BaseModel):
    request_id: str
    request_number: str
    requester_id: str
    requester_name: str
    department_id: str
    department_name: str
    title: str
    description: str | None = None
    status: ProcurementRequestStatus
    priority: ProcurementPriority
    estimated_total: float
    currency: str = "KZT"
    needed_by_date: str | None = None
    created_at: str
    updated_at: str
    submitted_at: str | None = None


class ProcurementListItemSchema(BaseModel):
    request_id: str
    request_number: str
    title: str
    requester_name: str
    department_name: str
    status: ProcurementRequestStatus
    priority: ProcurementPriority
    estimated_total: float
    created_at: str
    updated_at: str


class ApprovalStepSchema(BaseModel):
    step_id: str
    request_id: str
    sequence: int
    approver_id: str
    approver_name: str
    status: ApprovalStepStatus
    decision_at: str | None = None
    comment: str | None = None


class ProcurementAuditEntrySchema(BaseModel):
    audit_id: str
    request_id: str
    action: str
    actor_id: str
    actor_name: str
    from_status: ProcurementRequestStatus | None = None
    to_status: ProcurementRequestStatus | None = None
    timestamp: str
    metadata: dict | None = None


class ProcurementOrderCreateSchema(BaseModel):
    request_id: str = Field(min_length=1)
    vendor_id: str = Field(min_length=1)
    order_number: str = Field(min_length=1, max_length=64)
    expected_delivery_date: str | None = None


class ProcurementOrderSchema(BaseModel):
    order_id: str
    request_id: str
    vendor_id: str
    vendor_name: str
    order_number: str
    order_date: str
    expected_delivery_date: str | None = None
    total_amount: float
    currency: str = "KZT"
    status: ProcurementOrderStatus


class ProcurementDashboardSummarySchema(BaseModel):
    total_requests: int
    status_breakdown: dict[str, int]
    total_pending_approvals: int
    total_ordered_value: float
    overdue_requests: int
    last_updated: str