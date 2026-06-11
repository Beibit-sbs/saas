"""Schemas for Quality / Accreditation audit findings runtime."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NonConformityDTO(BaseModel):
    non_conformity_id: str
    category: str
    severity: str
    affected_area: str
    status: str
    read_only: bool = True
    aggregator_only: bool = True


class AuditObservationDTO(BaseModel):
    observation_id: str
    observation_type: str
    summary: str
    impact_level: str
    read_only: bool = True
    aggregator_only: bool = True


class AuditRecommendationDTO(BaseModel):
    recommendation_id: str
    recommendation_title: str
    priority: str
    owner_unit: str
    target_date: datetime
    status: str
    read_only: bool = True
    aggregator_only: bool = True


class AuditRiskAnalysisDTO(BaseModel):
    risk_band: str
    findings_count: int
    non_conformities_count: int
    recommendations_open: int
    read_only: bool = True
    aggregator_only: bool = True


class AuditRemediationStatusDTO(BaseModel):
    remediation_state: str
    findings_count: int
    average_completion_percentage: int
    read_only: bool = True
    aggregator_only: bool = True


class AuditReadinessDTO(BaseModel):
    indicator_name: str
    indicator_value: int
    threshold: int
    status: str
    read_only: bool = True
    aggregator_only: bool = True


class AuditFindingDTO(BaseModel):
    finding_id: str
    finding_source: str
    finding_type: str
    finding_title: str
    severity: str
    impacted_standard: str
    remediation_status: str
    closure_tracking_status: str
    opened_at: datetime
    due_date: datetime
    read_only: bool = True
    aggregator_only: bool = True


class AuditFindingsRuntimeResponseDTO(BaseModel):
    tenant_id: int
    owner_module: str = "quality_accreditation"
    runtime_registry: str = "AUDIT_FINDINGS_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    findings: list[AuditFindingDTO] = Field(default_factory=list)
    non_conformities: list[NonConformityDTO] = Field(default_factory=list)
    observations: list[AuditObservationDTO] = Field(default_factory=list)
    recommendations: list[AuditRecommendationDTO] = Field(default_factory=list)
    risk_severity_analysis: list[AuditRiskAnalysisDTO] = Field(default_factory=list)
    remediation_status: list[AuditRemediationStatusDTO] = Field(default_factory=list)
    audit_readiness_indicators: list[AuditReadinessDTO] = Field(default_factory=list)
