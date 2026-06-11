"""Schemas for Quality / Accreditation dashboard runtime."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DashboardSummaryCardDTO(BaseModel):
    metric_key: str
    label: str
    value: int
    status: str
    read_only: bool = True
    aggregator_only: bool = True


class DashboardKpiRollupDTO(BaseModel):
    kpi_group: str
    score: int
    threshold: int
    trend: str
    read_only: bool = True
    aggregator_only: bool = True


class DashboardComplianceIndicatorDTO(BaseModel):
    indicator_name: str
    indicator_value: int
    threshold: int
    status: str
    read_only: bool = True
    aggregator_only: bool = True


class DashboardRiskIndicatorDTO(BaseModel):
    risk_name: str
    risk_level: str
    impacted_area: str
    mitigation_status: str
    read_only: bool = True
    aggregator_only: bool = True


class DashboardRuntimeResponseDTO(BaseModel):
    tenant_id: int
    owner_module: str = "quality_accreditation"
    runtime_registry: str = "DASHBOARD_RUNTIME"
    runtime_mode: str = "READ_ONLY_AGGREGATOR"
    generated_at: datetime
    read_only: bool = True
    aggregator_only: bool = True
    accreditation_summary: list[DashboardSummaryCardDTO] = Field(default_factory=list)
    evidence_coverage_summary: list[DashboardSummaryCardDTO] = Field(default_factory=list)
    self_assessment_status: list[DashboardSummaryCardDTO] = Field(default_factory=list)
    corrective_action_status: list[DashboardSummaryCardDTO] = Field(default_factory=list)
    improvement_plan_status: list[DashboardSummaryCardDTO] = Field(default_factory=list)
    readiness_monitoring_summary: list[DashboardSummaryCardDTO] = Field(default_factory=list)
    audit_findings_summary: list[DashboardSummaryCardDTO] = Field(default_factory=list)
    executive_kpi_rollup: list[DashboardKpiRollupDTO] = Field(default_factory=list)
    compliance_indicators: list[DashboardComplianceIndicatorDTO] = Field(default_factory=list)
    accreditation_risk_indicators: list[DashboardRiskIndicatorDTO] = Field(default_factory=list)
