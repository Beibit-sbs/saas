"""Router for Executive Governance runtime shell endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.module_helpers.router_errors import permission_error_to_http, tenant_not_found_to_http, validation_error_to_http
from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.core.tenant import get_current_tenant
from app.modules.executive_control_tower import permissions
from app.modules.executive_governance.runtime_shell_schemas import (
    ExecutiveAssignmentEntry,
    ExecutiveAssignmentSummary,
    ExecutiveControlTowerSummary,
    ExecutiveDecisionExecutionSummary,
    ExecutiveDecisionRegistryEntry,
    ExecutiveDecisionRegistrySummary,
    ExecutiveExecutionMetrics,
    ExecutiveGovernanceDashboardSummary,
    ExecutiveKpiOverview,
    ExecutiveMeetingEntry,
    ExecutiveMeetingSummary,
    ExecutivePerformanceMetrics,
    ExecutiveProtocolEntry,
    ExecutiveProtocolExecutionSummary,
    ExecutiveProtocolSummary,
    ExecutiveRiskOverview,
    ExecutiveGovernanceRuntimeOverview,
    ExecutiveGovernanceRuntimeSummary,
    ExecutiveGovernanceSignalSummary,
    RectorDashboardRuntimeSummary,
)
from app.modules.executive_governance.runtime_shell_service import ExecutiveGovernanceRuntimeService
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/executive-governance/runtime", tags=["executive-governance-runtime"])

_Tenant = Annotated[dict, Depends(get_current_tenant)]
_Actor = Annotated[str, Depends(get_actor)]

_service = ExecutiveGovernanceRuntimeService()


def _handle(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        raise tenant_not_found_to_http(exc)
    if isinstance(exc, (DomainValidationError, ValueError)):
        raise validation_error_to_http(exc)
    raise exc


@router.get("/overview", response_model=ExecutiveGovernanceRuntimeOverview)
def get_runtime_overview(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveGovernanceRuntimeOverview:
    try:
        return _service.get_overview(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/summary", response_model=ExecutiveGovernanceRuntimeSummary)
def get_runtime_summary(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveGovernanceRuntimeSummary:
    try:
        return _service.get_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/signals", response_model=list[ExecutiveGovernanceSignalSummary])
def get_runtime_signals(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> list[ExecutiveGovernanceSignalSummary]:
    try:
        return _service.get_signals(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/dashboard", response_model=ExecutiveGovernanceDashboardSummary)
def get_runtime_dashboard(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveGovernanceDashboardSummary:
    try:
        return _service.get_dashboard(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/decisions", response_model=list[ExecutiveDecisionRegistryEntry])
def get_runtime_decisions(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> list[ExecutiveDecisionRegistryEntry]:
    try:
        return _service.get_decisions(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/decisions/summary", response_model=ExecutiveDecisionRegistrySummary)
def get_runtime_decisions_summary(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveDecisionRegistrySummary:
    try:
        return _service.get_decisions_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/decisions/execution", response_model=ExecutiveDecisionExecutionSummary)
def get_runtime_decisions_execution(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveDecisionExecutionSummary:
    try:
        return _service.get_decision_execution_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/assignments", response_model=list[ExecutiveAssignmentEntry])
def get_runtime_assignments(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> list[ExecutiveAssignmentEntry]:
    try:
        return _service.get_assignments(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/assignments/summary", response_model=ExecutiveAssignmentSummary)
def get_runtime_assignments_summary(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveAssignmentSummary:
    try:
        return _service.get_assignments_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/assignments/execution", response_model=ExecutiveExecutionMetrics)
def get_runtime_assignments_execution(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveExecutionMetrics:
    try:
        return _service.get_assignments_execution(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/assignments/risks", response_model=ExecutiveExecutionMetrics)
def get_runtime_assignments_risks(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveExecutionMetrics:
    try:
        return _service.get_assignments_risks(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/control-tower", response_model=ExecutiveControlTowerSummary)
def get_runtime_control_tower(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveControlTowerSummary:
    try:
        return _service.get_control_tower(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/control-tower/summary", response_model=RectorDashboardRuntimeSummary)
def get_runtime_control_tower_summary(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> RectorDashboardRuntimeSummary:
    try:
        return _service.get_control_tower_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/control-tower/risks", response_model=ExecutiveRiskOverview)
def get_runtime_control_tower_risks(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveRiskOverview:
    try:
        return _service.get_control_tower_risks(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/control-tower/kpis", response_model=ExecutiveKpiOverview)
def get_runtime_control_tower_kpis(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveKpiOverview:
    try:
        return _service.get_control_tower_kpis(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/control-tower/escalations", response_model=ExecutivePerformanceMetrics)
def get_runtime_control_tower_escalations(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutivePerformanceMetrics:
    try:
        return _service.get_control_tower_escalations(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/meetings", response_model=list[ExecutiveMeetingEntry])
def get_runtime_meetings(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> list[ExecutiveMeetingEntry]:
    try:
        return _service.get_meetings(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/meetings/summary", response_model=ExecutiveMeetingSummary)
def get_runtime_meetings_summary(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveMeetingSummary:
    try:
        return _service.get_meetings_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/protocols", response_model=list[ExecutiveProtocolEntry])
def get_runtime_protocols(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> list[ExecutiveProtocolEntry]:
    try:
        return _service.get_protocols(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/protocols/summary", response_model=ExecutiveProtocolSummary)
def get_runtime_protocols_summary(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveProtocolSummary:
    try:
        return _service.get_protocols_summary(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/protocols/execution", response_model=ExecutiveProtocolExecutionSummary)
def get_runtime_protocols_execution(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ExecutiveProtocolExecutionSummary:
    try:
        return _service.get_protocols_execution(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)
