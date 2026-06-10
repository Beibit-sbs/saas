"""Router for Reporting Runtime shell endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.module_helpers.router_errors import permission_error_to_http, tenant_not_found_to_http, validation_error_to_http
from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.reporting_runtime import permissions
from app.modules.reporting_runtime.runtime_shell_schemas import ReportingRuntimeShellResponse
from app.modules.reporting_runtime.runtime_shell_service import ReportingRuntimeShellService


router = APIRouter(prefix="/api/admin/reporting-brain", tags=["reporting-runtime"])

_Tenant = Annotated[dict, Depends(get_current_tenant)]
_Actor = Annotated[str, Depends(get_actor)]

_service = ReportingRuntimeShellService()


def _handle(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        raise tenant_not_found_to_http(exc)
    if isinstance(exc, (DomainValidationError, ValueError)):
        raise validation_error_to_http(exc)
    raise exc


@router.get("/runtime", response_model=ReportingRuntimeShellResponse)
def get_reporting_runtime_shell(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ReportingRuntimeShellResponse:
    try:
        return _service.get_runtime_shell(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)
