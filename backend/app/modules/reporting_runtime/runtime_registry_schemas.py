"""Pydantic schemas for Reporting Registry runtime endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class _ReportingRegistryBase(BaseModel):
    id: str
    report_code: str
    report_name: str
    report_type: str
    owner_module: str
    reporting_period: str
    submission_deadline: datetime
    submission_status: str
    compliance_status: str
    provider_status: str
    generated_at: datetime
    read_only: bool = True


class ReportingRegistryEntry(_ReportingRegistryBase):
    pass


class ReportingTemplateSummary(_ReportingRegistryBase):
    template_version: str
    section_count: int


class ReportingCycleSummary(_ReportingRegistryBase):
    cycle_stage: str
    active_days_remaining: int


class ReportingSubmissionSummary(_ReportingRegistryBase):
    submission_id: str
    reviewer_required: bool = True


class ReportingRequirementSummary(_ReportingRegistryBase):
    requirement_code: str
    requirement_status: str


class ReportingEvidenceSummary(_ReportingRegistryBase):
    evidence_count: int
    evidence_completeness: int


class ReportingProviderSummary(_ReportingRegistryBase):
    provider_key: str
    live_integrations_enabled: bool = False
    submission_execution_enabled: bool = False


class ReportingStatusSummary(_ReportingRegistryBase):
    risk_signal: str


class ReportingRegistryResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    entries: list[ReportingRegistryEntry] = Field(default_factory=list)
    requirements: list[ReportingRequirementSummary] = Field(default_factory=list)
    statuses: list[ReportingStatusSummary] = Field(default_factory=list)


class ReportingTemplateResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    templates: list[ReportingTemplateSummary] = Field(default_factory=list)


class ReportingCycleResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    cycles: list[ReportingCycleSummary] = Field(default_factory=list)


class ReportingSubmissionResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    submissions: list[ReportingSubmissionSummary] = Field(default_factory=list)


class ReportingEvidenceResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    evidence: list[ReportingEvidenceSummary] = Field(default_factory=list)


class ReportingProviderResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    providers: list[ReportingProviderSummary] = Field(default_factory=list)
