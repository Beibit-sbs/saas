"""Schemas for Quality / Accreditation accreditation registry runtime."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AccreditationRegistryItem(BaseModel):
    accreditation_id: str
    accreditation_name: str
    accreditation_type: str
    accreditation_scope: str
    provider: str
    status: str
    issued_date: datetime
    expiry_date: datetime
    readiness_score: int = 0
    risk_level: str = "UNKNOWN"
    read_only: bool = True
    aggregator_only: bool = True


class AccreditationProviderSummary(BaseModel):
    provider: str
    accreditation_count: int = 0
    active_count: int = 0
    expiring_count: int = 0
    read_only: bool = True
    aggregator_only: bool = True


class AccreditationStatusSummary(BaseModel):
    status: str
    accreditation_count: int = 0
    read_only: bool = True
    aggregator_only: bool = True


class AccreditationReadinessSummary(BaseModel):
    readiness_band: str
    accreditation_count: int = 0
    average_readiness_score: float = 0.0
    read_only: bool = True
    aggregator_only: bool = True


class AccreditationRiskSummary(BaseModel):
    risk_level: str
    accreditation_count: int = 0
    read_only: bool = True
    aggregator_only: bool = True


class AccreditationRegistryRuntimeResponse(BaseModel):
    tenant_id: int
    owner_module: str = "quality_accreditation"
    runtime_registry: str = "ACCREDITATION_REGISTRY_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    active_accreditations: list[AccreditationRegistryItem] = Field(default_factory=list)
    expiring_accreditations: list[AccreditationRegistryItem] = Field(default_factory=list)
    accreditation_provider: list[AccreditationProviderSummary] = Field(default_factory=list)
    accreditation_status: list[AccreditationStatusSummary] = Field(default_factory=list)
    accreditation_readiness: list[AccreditationReadinessSummary] = Field(default_factory=list)
    accreditation_risk: list[AccreditationRiskSummary] = Field(default_factory=list)