"""Router for Executive Governance runtime shell endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.module_helpers.router_errors import permission_error_to_http, tenant_not_found_to_http, validation_error_to_http
from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.core.tenant import get_current_tenant
from app.modules.executive_control_tower import permissions
from app.modules.executive_governance.runtime_shell_schemas import (
    ExecutiveGovernanceDashboardSummary,
    ExecutiveGovernanceRuntimeOverview,
    ExecutiveGovernanceRuntimeSummary,
    ExecutiveGovernanceSignalSummary,
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
