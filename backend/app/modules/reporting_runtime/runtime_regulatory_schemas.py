"""Pydantic schemas for Regulatory Reporting runtime endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class _RegulatoryReportingBase(BaseModel):
    id: str
    requirement_code: str
    requirement_name: str
    regulator_name: str
    compliance_status: str
    deadline: datetime
    days_remaining: int
    risk_level: str
    document_status: str
    owner_module: str
    generated_at: datetime
    read_only: bool = True


class RegulatoryReportingSummary(_RegulatoryReportingBase):
    pass


class RegulatoryRequirementSummary(_RegulatoryReportingBase):
    requirement_status: str


class RegulatoryComplianceSummary(_RegulatoryReportingBase):
    compliance_score: int


class RegulatoryDeadlineSummary(_RegulatoryReportingBase):
    deadline_status: str
    overdue: bool


class RegulatoryDocumentStatus(_RegulatoryReportingBase):
    document_name: str
    document_completeness: int


class RegulatoryRiskSummary(_RegulatoryReportingBase):
    signal_name: str
    signal_owner_module: str = "brain_core"


class RegulatoryReportingResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    reports: list[RegulatoryReportingSummary] = Field(default_factory=list)
    signal_inventory: list[str] = Field(default_factory=list)


class RegulatoryRequirementResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    requirements: list[RegulatoryRequirementSummary] = Field(default_factory=list)


class RegulatoryComplianceResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    compliance: list[RegulatoryComplianceSummary] = Field(default_factory=list)


class RegulatoryDeadlineResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    deadlines: list[RegulatoryDeadlineSummary] = Field(default_factory=list)


class RegulatoryDocumentResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    documents: list[RegulatoryDocumentStatus] = Field(default_factory=list)


class RegulatoryRiskResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    risks: list[RegulatoryRiskSummary] = Field(default_factory=list)
