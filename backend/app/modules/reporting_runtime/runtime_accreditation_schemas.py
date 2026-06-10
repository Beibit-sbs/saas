"""Pydantic schemas for Accreditation Reporting runtime endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class _AccreditationReportingBase(BaseModel):
    id: str
    accreditation_code: str
    accreditation_name: str
    accreditation_type: str
    agency_name: str
    deadline: datetime
    completion_percentage: int
    evidence_readiness: str
    compliance_status: str
    risk_level: str
    days_remaining: int
    owner_module: str
    generated_at: datetime
    read_only: bool = True


class AccreditationReportingSummary(_AccreditationReportingBase):
    pass


class AccreditationCycle(_AccreditationReportingBase):
    cycle_status: str


class AccreditationEvidenceReadiness(_AccreditationReportingBase):
    readiness_score: int


class AccreditationComplianceSummary(_AccreditationReportingBase):
    compliance_score: int


class AccreditationDeadlineSummary(_AccreditationReportingBase):
    deadline_status: str
    overdue: bool


class AccreditationRiskSummary(_AccreditationReportingBase):
    signal_name: str
    signal_owner_module: str = "brain_core"


class AccreditationReportingResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    reports: list[AccreditationReportingSummary] = Field(default_factory=list)
    signal_inventory: list[str] = Field(default_factory=list)


class AccreditationCycleResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    cycles: list[AccreditationCycle] = Field(default_factory=list)


class AccreditationEvidenceReadinessResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    readiness: list[AccreditationEvidenceReadiness] = Field(default_factory=list)


class AccreditationComplianceResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    compliance: list[AccreditationComplianceSummary] = Field(default_factory=list)


class AccreditationDeadlineResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    deadlines: list[AccreditationDeadlineSummary] = Field(default_factory=list)


class AccreditationRiskResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    risks: list[AccreditationRiskSummary] = Field(default_factory=list)
