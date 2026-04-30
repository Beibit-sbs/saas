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
]
PurchaseOrderStatus = Literal["DRAFT", "SUBMITTED", "APPROVED", "REJECTED", "PO_ISSUED"]
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