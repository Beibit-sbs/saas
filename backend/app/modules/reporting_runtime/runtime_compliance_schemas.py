"""Pydantic schemas for Compliance Monitoring runtime endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class _ComplianceMonitoringBase(BaseModel):
    id: str
    control_code: str
    control_name: str
    compliance_status: str
    readiness_score: int
    risk_level: str
    gap_count: int
    owner_module: str
    generated_at: datetime
    read_only: bool = True


class ComplianceMonitoringSummary(_ComplianceMonitoringBase):
    pass


class ComplianceControlSummary(_ComplianceMonitoringBase):
    control_type: str


class ComplianceRiskSummary(_ComplianceMonitoringBase):
    signal_name: str
    signal_owner_module: str = "brain_core"


class ComplianceGapSummary(_ComplianceMonitoringBase):
    gap_severity: str


class ComplianceReadinessSummary(_ComplianceMonitoringBase):
    readiness_level: str


class ComplianceMonitoringResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    reports: list[ComplianceMonitoringSummary] = Field(default_factory=list)
    signal_inventory: list[str] = Field(default_factory=list)


class ComplianceControlResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    controls: list[ComplianceControlSummary] = Field(default_factory=list)


class ComplianceReadinessResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    readiness: list[ComplianceReadinessSummary] = Field(default_factory=list)


class ComplianceGapResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    gaps: list[ComplianceGapSummary] = Field(default_factory=list)


class ComplianceRiskResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    risks: list[ComplianceRiskSummary] = Field(default_factory=list)