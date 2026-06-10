"""Router for Reporting Runtime shell endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.module_helpers.router_errors import permission_error_to_http, tenant_not_found_to_http, validation_error_to_http
from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.reporting_runtime import permissions
from app.modules.reporting_runtime.runtime_registry_schemas import (
    ReportingCycleResponse,
    ReportingEvidenceResponse,
    ReportingProviderResponse,
    ReportingRegistryResponse,
    ReportingSubmissionResponse,
    ReportingTemplateResponse,
)
from app.modules.reporting_runtime.runtime_registry_service import ReportingRegistryRuntimeService
from app.modules.reporting_runtime.runtime_shell_schemas import ReportingRuntimeShellResponse
from app.modules.reporting_runtime.runtime_shell_service import ReportingRuntimeShellService


router = APIRouter(prefix="/api/admin/reporting-brain", tags=["reporting-runtime"])

_Tenant = Annotated[dict, Depends(get_current_tenant)]
_Actor = Annotated[str, Depends(get_actor)]

_service = ReportingRuntimeShellService()
_registry_service = ReportingRegistryRuntimeService()


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


@router.get("/runtime/registry", response_model=ReportingRegistryResponse)
def get_reporting_registry_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ReportingRegistryResponse:
    try:
        return _registry_service.get_registry(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/templates", response_model=ReportingTemplateResponse)
def get_reporting_templates_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ReportingTemplateResponse:
    try:
        return _registry_service.get_templates(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/cycles", response_model=ReportingCycleResponse)
def get_reporting_cycles_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ReportingCycleResponse:
    try:
        return _registry_service.get_cycles(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/submissions", response_model=ReportingSubmissionResponse)
def get_reporting_submissions_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ReportingSubmissionResponse:
    try:
        return _registry_service.get_submissions(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/evidence", response_model=ReportingEvidenceResponse)
def get_reporting_evidence_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ReportingEvidenceResponse:
    try:
        return _registry_service.get_evidence(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/providers", response_model=ReportingProviderResponse)
def get_reporting_providers_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> ReportingProviderResponse:
    try:
        return _registry_service.get_providers(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)
