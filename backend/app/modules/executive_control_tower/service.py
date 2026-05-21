"""Read-only service layer for the Executive Control Tower foundation."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.module_helpers.service_validation import (
    TenantResourceNotFoundError,
    validate_tenant_id_provided,
)
from app.modules.executive_control_tower.metric_registry import (
    ASSIGNMENT_EXECUTION,
    AUDIT_COMPLIANCE,
    CORRESPONDENCE_WORKFLOW,
    DATA_SOURCE,
    DEPARTMENT_PERFORMANCE,
    DECREE_WORKFLOW,
    DOCUMENT_WORKFLOW,
    FAKE_METRICS,
    SLA_RISK_BOTTLENECK,
    STRATEGY_KPI,
    get_metric_by_id,
    get_metric_group,
    get_registry_summary,
    list_metric_groups,
)
from app.modules.executive_control_tower.schemas import (
    AssignmentExecutionSummaryResponse,
    AuditComplianceSummaryResponse,
    CorrespondenceWorkflowSummaryResponse,
    DecreeWorkflowSummaryResponse,
    DepartmentPerformanceSummaryResponse,
    DocumentWorkflowSummaryResponse,
    ExecutiveControlTowerHealthResponse,
    ExecutiveControlTowerMetricGroup,
    ExecutiveControlTowerSummaryResponse,
    MetricDetailResponse,
    MetricRegistryResponse,
    SlaRiskBottleneckSummaryResponse,
    StrategyKpiSummaryResponse,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _foundation_limitations() -> list[str]:
    return [
        "Read-only backend foundation only; no workflow mutation routes are exposed.",
        "Metrics remain null until live aggregation is implemented in a later runtime slice.",
    ]


def _validate_tenant(tenant_id: int) -> int:
    return validate_tenant_id_provided(tenant_id)


def _build_group_response(group_id: str) -> ExecutiveControlTowerMetricGroup:
    group = get_metric_group(group_id)
    if group is None:
        raise TenantResourceNotFoundError(f"metric group '{group_id}' not found")
    return group


def get_metric_registry_summary(tenant_id: int) -> MetricRegistryResponse:
    _validate_tenant(tenant_id)
    groups = list_metric_groups()
    return MetricRegistryResponse(
        groups=groups,
        total_metrics=get_registry_summary()["total_metrics"],
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=True,
        generated_at=_now_utc(),
        limitations=_foundation_limitations(),
    )


def get_metric_detail(tenant_id: int, metric_id: str) -> MetricDetailResponse:
    _validate_tenant(tenant_id)
    metric = get_metric_by_id(metric_id)
    if metric is None:
        raise TenantResourceNotFoundError(f"metric '{metric_id}' not found")
    return MetricDetailResponse(
        metric=metric,
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=metric.incomplete_data,
        generated_at=_now_utc(),
        limitations=_foundation_limitations(),
    )


def get_executive_summary(tenant_id: int) -> ExecutiveControlTowerSummaryResponse:
    _validate_tenant(tenant_id)
    return ExecutiveControlTowerSummaryResponse(
        groups=list_metric_groups(),
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=True,
        generated_at=_now_utc(),
        limitations=_foundation_limitations(),
    )


def get_assignment_execution_summary(tenant_id: int) -> AssignmentExecutionSummaryResponse:
    _validate_tenant(tenant_id)
    group = _build_group_response(ASSIGNMENT_EXECUTION)
    return AssignmentExecutionSummaryResponse(
        metric_group=group.group_id,
        group_label=group.label,
        metrics=group.metrics,
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=group.incomplete_data,
        generated_at=_now_utc(),
        limitations=_foundation_limitations(),
    )


def get_document_workflow_summary(tenant_id: int) -> DocumentWorkflowSummaryResponse:
    _validate_tenant(tenant_id)
    group = _build_group_response(DOCUMENT_WORKFLOW)
    return DocumentWorkflowSummaryResponse(
        metric_group=group.group_id,
        group_label=group.label,
        metrics=group.metrics,
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=group.incomplete_data,
        generated_at=_now_utc(),
        limitations=_foundation_limitations(),
    )


def get_decree_workflow_summary(tenant_id: int) -> DecreeWorkflowSummaryResponse:
    _validate_tenant(tenant_id)
    group = _build_group_response(DECREE_WORKFLOW)
    return DecreeWorkflowSummaryResponse(
        metric_group=group.group_id,
        group_label=group.label,
        metrics=group.metrics,
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=group.incomplete_data,
        generated_at=_now_utc(),
        limitations=_foundation_limitations(),
    )


def get_correspondence_workflow_summary(tenant_id: int) -> CorrespondenceWorkflowSummaryResponse:
    _validate_tenant(tenant_id)
    group = _build_group_response(CORRESPONDENCE_WORKFLOW)
    return CorrespondenceWorkflowSummaryResponse(
        metric_group=group.group_id,
        group_label=group.label,
        metrics=group.metrics,
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=group.incomplete_data,
        generated_at=_now_utc(),
        limitations=_foundation_limitations(),
    )


def get_sla_risk_summary(tenant_id: int) -> SlaRiskBottleneckSummaryResponse:
    _validate_tenant(tenant_id)
    group = _build_group_response(SLA_RISK_BOTTLENECK)
    return SlaRiskBottleneckSummaryResponse(
        metric_group=group.group_id,
        group_label=group.label,
        metrics=group.metrics,
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=group.incomplete_data,
        generated_at=_now_utc(),
        limitations=_foundation_limitations(),
    )


def get_strategy_kpi_summary(tenant_id: int) -> StrategyKpiSummaryResponse:
    _validate_tenant(tenant_id)
    group = _build_group_response(STRATEGY_KPI)
    return StrategyKpiSummaryResponse(
        metric_group=group.group_id,
        group_label=group.label,
        metrics=group.metrics,
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=True,
        generated_at=_now_utc(),
        limitations=_foundation_limitations() + ["Strategy metrics remain deferred until a real strategy source exists."],
    )


def get_audit_compliance_summary(tenant_id: int) -> AuditComplianceSummaryResponse:
    _validate_tenant(tenant_id)
    group = _build_group_response(AUDIT_COMPLIANCE)
    return AuditComplianceSummaryResponse(
        metric_group=group.group_id,
        group_label=group.label,
        metrics=group.metrics,
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=group.incomplete_data,
        generated_at=_now_utc(),
        limitations=_foundation_limitations(),
    )


def get_department_performance_summary(tenant_id: int) -> DepartmentPerformanceSummaryResponse:
    _validate_tenant(tenant_id)
    group = _build_group_response(DEPARTMENT_PERFORMANCE)
    return DepartmentPerformanceSummaryResponse(
        metric_group=group.group_id,
        group_label=group.label,
        metrics=group.metrics,
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=group.incomplete_data,
        generated_at=_now_utc(),
        limitations=_foundation_limitations() + ["Department metrics remain operational visibility only."],
    )


def get_health(tenant_id: int) -> ExecutiveControlTowerHealthResponse:
    _validate_tenant(tenant_id)
    summary = get_registry_summary()
    return ExecutiveControlTowerHealthResponse(
        total_groups=summary["total_groups"],
        total_metrics=summary["total_metrics"],
        registry_valid=summary["valid"],
        validation_errors=summary["errors"],
        read_only_foundation=True,
        runtime_status="FOUNDATION_CONTRACT_ONLY",
        fake_metrics=FAKE_METRICS,
        data_source=DATA_SOURCE,
        incomplete_data=True,
        generated_at=_now_utc(),
        limitations=_foundation_limitations(),
    )