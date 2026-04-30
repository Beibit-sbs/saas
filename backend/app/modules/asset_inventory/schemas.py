"""Phase XI-XI2: Asset Inventory schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AssetCategory = Literal["equipment", "furniture", "it_hardware", "vehicle", "other"]
AssetCondition = Literal["new", "good", "fair", "poor", "condemned"]
AssetStatus = Literal["active", "in_maintenance", "decommissioned"]

DepreciationMethod = Literal["straight_line", "declining_balance"]
DepreciationStatus = Literal["active", "closed"]


class AssetItemCreateSchema(BaseModel):
    asset_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    category: AssetCategory = "equipment"
    location: str = Field(min_length=1, max_length=200)
    condition: AssetCondition = "good"
    purchase_year: int = Field(ge=2000, le=2100)
    vendor: str | None = Field(default=None, max_length=128)
    status: AssetStatus = "active"
    reviewer_notes: str | None = Field(default=None, max_length=500)


class AssetItemSchema(AssetItemCreateSchema):
    id: int
    tenant_id: str | None = None


class AssetItemStatusUpdateSchema(BaseModel):
    status: AssetStatus


class AssetItemResponseSchema(BaseModel):
    item: AssetItemSchema


class AssetListResponseSchema(BaseModel):
    items: list[AssetItemSchema]


class DepreciationRecordCreateSchema(BaseModel):
    asset_code: str = Field(min_length=1, max_length=64)
    depreciation_method: DepreciationMethod = "straight_line"
    original_value: float = Field(ge=0.0)
    current_value: float = Field(ge=0.0)
    depreciation_rate: float = Field(ge=0.0, le=1.0)
    status: DepreciationStatus = "active"
    notes: str | None = Field(default=None, max_length=500)


class DepreciationRecordSchema(DepreciationRecordCreateSchema):
    id: int
    tenant_id: str | None = None


class DepreciationRecordItemResponseSchema(BaseModel):
    item: DepreciationRecordSchema


class DepreciationRecordListResponseSchema(BaseModel):
    items: list[DepreciationRecordSchema]
