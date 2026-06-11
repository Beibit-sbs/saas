"""Schemas for Quality / Accreditation readiness monitoring runtime."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReadinessDomainDTO(BaseModel):
    domain_id: str
    domain_name: str
    readiness_score: int
    threshold: int
    status: str
    trend: str
    read_only: bool = True
    aggregator_only: bool = True


class ReadinessRiskDTO(BaseModel):
    risk_id: str
    risk_title: str
    risk_level: str
    impacted_domain: str
    mitigation_status: str
    read_only: bool = True
    aggregator_only: bool = True


class ReadinessRemediationDTO(BaseModel):
    remediation_id: str
    remediation_title: str
    owner_unit: str
    completion_percentage: int
    status: str
    due_date: datetime
    read_only: bool = True
    aggregator_only: bool = True


class ReadinessIndicatorDTO(BaseModel):
    indicator_name: str
    indicator_value: int
    threshold: int
    status: str
    read_only: bool = True
    aggregator_only: bool = True


class ReadinessSummaryDTO(BaseModel):
    monitored_domains_total: int
    domains_on_track: int
    domains_at_risk: int
    average_readiness_score: int
    read_only: bool = True
    aggregator_only: bool = True


class ReadinessMonitoringRuntimeResponseDTO(BaseModel):
    tenant_id: int
    owner_module: str = "quality_accreditation"
    runtime_registry: str = "READINESS_MONITORING_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    readiness_summary: ReadinessSummaryDTO
    readiness_domains: list[ReadinessDomainDTO] = Field(default_factory=list)
    readiness_risks: list[ReadinessRiskDTO] = Field(default_factory=list)
    remediation_tracking: list[ReadinessRemediationDTO] = Field(default_factory=list)
    readiness_indicators: list[ReadinessIndicatorDTO] = Field(default_factory=list)
