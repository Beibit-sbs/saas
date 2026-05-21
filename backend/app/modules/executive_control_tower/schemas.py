"""Pydantic schemas for the Executive Control Tower backend foundation."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


DataSourceValue = Literal["computed_from_governance_workflows"]
FailureModeValue = Literal["INCOMPLETE_DATA", "UNAVAILABLE", "PERMISSION_DENIED"]
RuntimeStatusValue = Literal["FOUNDATION_CONTRACT_ONLY", "DEFERRED_UNTIL_STRATEGY_MODULE"]
ReadinessValue = Literal["CONTRACT_DEFINED", "FUTURE_CONTRACT"]


class EvidenceLink(BaseModel):
    label: str
    source_module: str
    source_entity: str | None = None
    source_table: str | None = None
    reference_field: str | None = None
    reference_value: str | int | None = None
    url: str | None = None
    available: bool = True
    limitations: list[str] = Field(default_factory=list)


class ExecutiveControlTowerMetric(BaseModel):
    metric_id: str
    metric_group: str
    label: str
    description: str
    value: int | float | str | None = None
    unit: str | None = None
    source_module: str
    source_entities: list[str] = Field(default_factory=list)
    source_tables: list[str] = Field(default_factory=list)
    source_fields: list[str] = Field(default_factory=list)
    calculation_method: str
    formula: str
    tenant_scope: str
    permission_required: str
    freshness_timestamp: datetime | None = None
    staleness_threshold_minutes: int | None = None
    evidence_links: list[EvidenceLink] = Field(default_factory=list)
    data_source: DataSourceValue = "computed_from_governance_workflows"
    fake_metrics: bool = False
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)
    failure_mode: FailureModeValue = "INCOMPLETE_DATA"
    runtime_status: RuntimeStatusValue = "FOUNDATION_CONTRACT_ONLY"
    readiness: ReadinessValue = "CONTRACT_DEFINED"


class ExecutiveControlTowerMetricGroup(BaseModel):
    group_id: str
    label: str
    description: str
    metrics: list[ExecutiveControlTowerMetric] = Field(default_factory=list)
    fake_metrics: bool = False
    data_source: DataSourceValue = "computed_from_governance_workflows"
    incomplete_data: bool
    limitations: list[str] = Field(default_factory=list)


class _FoundationResponse(BaseModel):
    fake_metrics: bool = False
    data_source: DataSourceValue = "computed_from_governance_workflows"
    incomplete_data: bool
    generated_at: datetime
    limitations: list[str] = Field(default_factory=list)


class MetricRegistryResponse(_FoundationResponse):
    groups: list[ExecutiveControlTowerMetricGroup] = Field(default_factory=list)
    total_metrics: int


class MetricDetailResponse(_FoundationResponse):
    metric: ExecutiveControlTowerMetric


class ExecutiveControlTowerSummaryResponse(_FoundationResponse):
    groups: list[ExecutiveControlTowerMetricGroup] = Field(default_factory=list)


class AssignmentExecutionSummaryResponse(_FoundationResponse):
    metric_group: str
    group_label: str
    metrics: list[ExecutiveControlTowerMetric] = Field(default_factory=list)


class DocumentWorkflowSummaryResponse(_FoundationResponse):
    metric_group: str
    group_label: str
    metrics: list[ExecutiveControlTowerMetric] = Field(default_factory=list)


class DecreeWorkflowSummaryResponse(_FoundationResponse):
    metric_group: str
    group_label: str
    metrics: list[ExecutiveControlTowerMetric] = Field(default_factory=list)


class CorrespondenceWorkflowSummaryResponse(_FoundationResponse):
    metric_group: str
    group_label: str
    metrics: list[ExecutiveControlTowerMetric] = Field(default_factory=list)


class SlaRiskBottleneckSummaryResponse(_FoundationResponse):
    metric_group: str
    group_label: str
    metrics: list[ExecutiveControlTowerMetric] = Field(default_factory=list)


class StrategyKpiSummaryResponse(_FoundationResponse):
    metric_group: str
    group_label: str
    metrics: list[ExecutiveControlTowerMetric] = Field(default_factory=list)


class AuditComplianceSummaryResponse(_FoundationResponse):
    metric_group: str
    group_label: str
    metrics: list[ExecutiveControlTowerMetric] = Field(default_factory=list)


class DepartmentPerformanceSummaryResponse(_FoundationResponse):
    metric_group: str
    group_label: str
    metrics: list[ExecutiveControlTowerMetric] = Field(default_factory=list)


class ExecutiveControlTowerHealthResponse(_FoundationResponse):
    total_groups: int
    total_metrics: int
    registry_valid: bool
    validation_errors: list[str] = Field(default_factory=list)
    read_only_foundation: bool = True
    runtime_status: str = "FOUNDATION_CONTRACT_ONLY"