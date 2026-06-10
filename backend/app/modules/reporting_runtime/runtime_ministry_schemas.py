"""Pydantic schemas for Ministry Reporting runtime endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class _MinistryReportingBase(BaseModel):
    id: str
    report_code: str
    report_name: str
    reporting_period: str
    deadline: datetime
    completion_percentage: int
    readiness_status: str
    submission_status: str
    risk_level: str
    days_remaining: int
    owner_module: str
    generated_at: datetime
    read_only: bool = True


class MinistryReportingSummary(_MinistryReportingBase):
    pass


class MinistryReportingCycle(_MinistryReportingBase):
    cycle_status: str


class MinistryReportingDeadline(_MinistryReportingBase):
    deadline_status: str
    overdue: bool


class MinistryReportingReadiness(_MinistryReportingBase):
    readiness_score: int


class MinistryReportingCompleteness(_MinistryReportingBase):
    required_data_points: int
    completed_data_points: int


class MinistryReportingRisk(_MinistryReportingBase):
    signal_name: str
    signal_owner_module: str = "brain_core"


class MinistryReportingSummaryResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    reports: list[MinistryReportingSummary] = Field(default_factory=list)
    signal_inventory: list[str] = Field(default_factory=list)


class MinistryReportingCycleResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    cycles: list[MinistryReportingCycle] = Field(default_factory=list)


class MinistryReportingDeadlineResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    deadlines: list[MinistryReportingDeadline] = Field(default_factory=list)


class MinistryReportingReadinessResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    readiness: list[MinistryReportingReadiness] = Field(default_factory=list)


class MinistryReportingCompletenessResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    completeness: list[MinistryReportingCompleteness] = Field(default_factory=list)


class MinistryReportingRiskResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    risks: list[MinistryReportingRisk] = Field(default_factory=list)
