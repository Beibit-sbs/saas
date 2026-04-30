"""Phase VII-VII1: IP management schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class IpAssetCreatePayload(BaseModel):
    asset_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=256)
    inventor_ids: str | None = Field(default=None, max_length=512)
    ip_type: str = Field(default="patent", min_length=1, max_length=64)
    status: str = Field(default="draft", min_length=1, max_length=32)
    filing_date: str | None = Field(default=None, max_length=64)
    grant_date: str | None = Field(default=None, max_length=64)
    commercialization_status: str = Field(default="none", min_length=1, max_length=64)
    licensing_revenue: float | None = Field(default=None, ge=0.0)
    notes: str | None = Field(default=None, max_length=2000)
    integration_source: str | None = Field(default=None, max_length=64)
    department: str | None = Field(default=None, max_length=128)


class IpAssetResponse(IpAssetCreatePayload):
    id: int
    tenant_id: int


class IpAssetItemResponse(BaseModel):
    record: IpAssetResponse


class IpAssetListResponse(BaseModel):
    records: list[IpAssetResponse]


class IpManagementBrainContextResponse(BaseModel):
    module: str
    tenant_id: int
    total_assets: int
    active_patents: int
    commercialized_assets: int
    total_licensing_revenue: float
    commercialization_rate: float
    portfolio_health: str
