"""Pydantic schemas for NOBD Reporting runtime endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class _NobdReportingBase(BaseModel):
    id: str
    dataset_code: str
    dataset_name: str
    records_total: int
    records_complete: int
    completeness_percentage: int
    quality_score: int
    sync_status: str
    risk_level: str
    owner_module: str
    generated_at: datetime
    read_only: bool = True


class NobdReportingSummary(_NobdReportingBase):
    pass


class NobdDatasetSummary(_NobdReportingBase):
    dataset_priority: str


class NobdCompletenessSummary(_NobdReportingBase):
    completeness_gap: int


class NobdQualitySummary(_NobdReportingBase):
    quality_band: str


class NobdSyncStatusSummary(_NobdReportingBase):
    sync_lag_hours: int


class NobdRiskSummary(_NobdReportingBase):
    signal_name: str
    signal_owner_module: str = "brain_core"


class NobdReportingResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    reports: list[NobdReportingSummary] = Field(default_factory=list)
    signal_inventory: list[str] = Field(default_factory=list)


class NobdDatasetResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    datasets: list[NobdDatasetSummary] = Field(default_factory=list)


class NobdCompletenessResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    completeness: list[NobdCompletenessSummary] = Field(default_factory=list)


class NobdQualityResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    quality: list[NobdQualitySummary] = Field(default_factory=list)


class NobdSyncStatusResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    sync_status: list[NobdSyncStatusSummary] = Field(default_factory=list)


class NobdRiskResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    risks: list[NobdRiskSummary] = Field(default_factory=list)