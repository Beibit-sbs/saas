"""Pydantic schemas for Reporting Dashboard runtime endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class _ReportingDashboardBase(BaseModel):
    id: str
    dashboard_code: str
    dashboard_name: str
    status: str
    readiness_score: int
    risk_score: int
    workload_score: int
    signal_count: int
    owner_module: str
    generated_at: datetime
    read_only: bool = True


class ReportingDashboardSummary(_ReportingDashboardBase):
    pass


class ReportingReadinessSummary(_ReportingDashboardBase):
    pass


class ReportingRiskSummary(_ReportingDashboardBase):
    pass


class ReportingWorkloadSummary(_ReportingDashboardBase):
    pass


class ReportingSignalSummary(_ReportingDashboardBase):
    pass


class ReportingDashboardResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    dashboards: list[ReportingDashboardSummary] = Field(default_factory=list)
    signal_inventory: list[str] = Field(default_factory=list)


class ReportingReadinessResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    readiness: list[ReportingReadinessSummary] = Field(default_factory=list)


class ReportingWorkloadResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    workload: list[ReportingWorkloadSummary] = Field(default_factory=list)


class ReportingRiskResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    risks: list[ReportingRiskSummary] = Field(default_factory=list)


class ReportingSignalResponse(BaseModel):
    tenant_id: int
    generated_at: datetime
    read_only: bool = True
    signals: list[ReportingSignalSummary] = Field(default_factory=list)
