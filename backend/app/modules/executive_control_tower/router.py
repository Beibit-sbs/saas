"""FastAPI router for the Executive Control Tower read-only foundation."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.module_helpers.router_errors import permission_error_to_http, tenant_not_found_to_http, validation_error_to_http
from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.core.tenant import get_current_tenant
from app.modules.executive_control_tower import permissions, service
from app.modules.executive_control_tower.schemas import (
    AssignmentExecutionSummaryResponse,
    AuditComplianceSummaryResponse,
    CorrespondenceWorkflowSummaryResponse,
    DecreeWorkflowSummaryResponse,
    DepartmentPerformanceSummaryResponse,
    DocumentWorkflowSummaryResponse,
    ExecutiveControlTowerHealthResponse,
    ExecutiveControlTowerSummaryResponse,
    MetricDetailResponse,
    MetricRegistryResponse,
    SlaRiskBottleneckSummaryResponse,
    StrategyKpiSummaryResponse,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/executive-control-tower", tags=["executive-control-tower"])

_Tenant = Annotated[dict, Depends(get_current_tenant)]
_Actor = Annotated[str, Depends(get_actor)]


def _handle(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        raise tenant_not_found_to_http(exc)
    if isinstance(exc, (DomainValidationError, ValueError)):
        raise validation_error_to_http(exc)
    raise exc


@router.get("/summary", response_model=ExecutiveControlTowerSummaryResponse)
def get_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveControlTowerSummaryResponse:
    try:
        return service.get_executive_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/assignments", response_model=AssignmentExecutionSummaryResponse)
def get_assignments_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ASSIGNMENTS_READ))],
    tenant: _Tenant,
) -> AssignmentExecutionSummaryResponse:
    try:
        return service.get_assignment_execution_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/documents", response_model=DocumentWorkflowSummaryResponse)
def get_documents_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DOCUMENTS_READ))],
    tenant: _Tenant,
) -> DocumentWorkflowSummaryResponse:
    try:
        return service.get_document_workflow_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/decrees", response_model=DecreeWorkflowSummaryResponse)
def get_decrees_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DOCUMENTS_READ))],
    tenant: _Tenant,
) -> DecreeWorkflowSummaryResponse:
    try:
        return service.get_decree_workflow_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/correspondence", response_model=CorrespondenceWorkflowSummaryResponse)
def get_correspondence_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DOCUMENTS_READ))],
    tenant: _Tenant,
) -> CorrespondenceWorkflowSummaryResponse:
    try:
        return service.get_correspondence_workflow_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/sla-risk", response_model=SlaRiskBottleneckSummaryResponse)
def get_sla_risk_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SLA_RISK_READ))],
    tenant: _Tenant,
) -> SlaRiskBottleneckSummaryResponse:
    try:
        return service.get_sla_risk_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/strategy-kpis", response_model=StrategyKpiSummaryResponse)
def get_strategy_kpi_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.STRATEGY_READ))],
    tenant: _Tenant,
) -> StrategyKpiSummaryResponse:
    try:
        return service.get_strategy_kpi_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/audit-compliance", response_model=AuditComplianceSummaryResponse)
def get_audit_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_READ))],
    tenant: _Tenant,
) -> AuditComplianceSummaryResponse:
    try:
        return service.get_audit_compliance_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/department-performance", response_model=DepartmentPerformanceSummaryResponse)
def get_department_summary_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DEPARTMENT_READ))],
    tenant: _Tenant,
) -> DepartmentPerformanceSummaryResponse:
    try:
        return service.get_department_performance_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/metric-registry", response_model=MetricRegistryResponse)
def get_metric_registry_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.METRIC_REGISTRY_READ))],
    tenant: _Tenant,
) -> MetricRegistryResponse:
    try:
        return service.get_metric_registry_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/metrics/{metric_id}", response_model=MetricDetailResponse)
def get_metric_detail_endpoint(
    metric_id: str,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.METRIC_REGISTRY_READ))],
    tenant: _Tenant,
) -> MetricDetailResponse:
    try:
        return service.get_metric_detail(int(tenant["id"]), metric_id)
    except Exception as exc:
        _handle(exc)


@router.get("/health", response_model=ExecutiveControlTowerHealthResponse)
def get_health_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READ))],
    tenant: _Tenant,
) -> ExecutiveControlTowerHealthResponse:
    try:
        return service.get_health(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)