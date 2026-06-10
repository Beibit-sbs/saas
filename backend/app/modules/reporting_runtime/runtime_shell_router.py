"""Router for Reporting Runtime shell endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.module_helpers.router_errors import permission_error_to_http, tenant_not_found_to_http, validation_error_to_http
from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.reporting_runtime import permissions
from app.modules.reporting_runtime.runtime_accreditation_schemas import (
    AccreditationComplianceResponse,
    AccreditationCycleResponse,
    AccreditationDeadlineResponse,
    AccreditationEvidenceReadinessResponse,
    AccreditationReportingResponse,
    AccreditationRiskResponse,
)
from app.modules.reporting_runtime.runtime_accreditation_service import AccreditationReportingRuntimeService
from app.modules.reporting_runtime.runtime_regulatory_schemas import (
    RegulatoryComplianceResponse,
    RegulatoryDeadlineResponse,
    RegulatoryDocumentResponse,
    RegulatoryReportingResponse,
    RegulatoryRequirementResponse,
    RegulatoryRiskResponse,
)
from app.modules.reporting_runtime.runtime_regulatory_service import RegulatoryReportingRuntimeService
from app.modules.reporting_runtime.runtime_ministry_schemas import (
    MinistryReportingCompletenessResponse,
    MinistryReportingCycleResponse,
    MinistryReportingDeadlineResponse,
    MinistryReportingReadinessResponse,
    MinistryReportingRiskResponse,
    MinistryReportingSummaryResponse,
)
from app.modules.reporting_runtime.runtime_ministry_service import MinistryReportingRuntimeService
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
_ministry_service = MinistryReportingRuntimeService()
_accreditation_service = AccreditationReportingRuntimeService()
_regulatory_service = RegulatoryReportingRuntimeService()


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


@router.get("/runtime/ministry", response_model=MinistryReportingSummaryResponse)
def get_ministry_reporting_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> MinistryReportingSummaryResponse:
    try:
        return _ministry_service.get_ministry(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/ministry/cycles", response_model=MinistryReportingCycleResponse)
def get_ministry_reporting_cycles_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> MinistryReportingCycleResponse:
    try:
        return _ministry_service.get_cycles(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/ministry/deadlines", response_model=MinistryReportingDeadlineResponse)
def get_ministry_reporting_deadlines_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> MinistryReportingDeadlineResponse:
    try:
        return _ministry_service.get_deadlines(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/ministry/readiness", response_model=MinistryReportingReadinessResponse)
def get_ministry_reporting_readiness_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> MinistryReportingReadinessResponse:
    try:
        return _ministry_service.get_readiness(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/ministry/risks", response_model=MinistryReportingRiskResponse)
def get_ministry_reporting_risks_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> MinistryReportingRiskResponse:
    try:
        return _ministry_service.get_risks(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/ministry/completeness", response_model=MinistryReportingCompletenessResponse)
def get_ministry_reporting_completeness_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> MinistryReportingCompletenessResponse:
    try:
        return _ministry_service.get_completeness(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/accreditation", response_model=AccreditationReportingResponse)
def get_accreditation_reporting_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> AccreditationReportingResponse:
    try:
        return _accreditation_service.get_accreditation(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/accreditation/cycles", response_model=AccreditationCycleResponse)
def get_accreditation_reporting_cycles_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> AccreditationCycleResponse:
    try:
        return _accreditation_service.get_cycles(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/accreditation/readiness", response_model=AccreditationEvidenceReadinessResponse)
def get_accreditation_reporting_readiness_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> AccreditationEvidenceReadinessResponse:
    try:
        return _accreditation_service.get_readiness(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/accreditation/compliance", response_model=AccreditationComplianceResponse)
def get_accreditation_reporting_compliance_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> AccreditationComplianceResponse:
    try:
        return _accreditation_service.get_compliance(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/accreditation/deadlines", response_model=AccreditationDeadlineResponse)
def get_accreditation_reporting_deadlines_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> AccreditationDeadlineResponse:
    try:
        return _accreditation_service.get_deadlines(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/accreditation/risks", response_model=AccreditationRiskResponse)
def get_accreditation_reporting_risks_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> AccreditationRiskResponse:
    try:
        return _accreditation_service.get_risks(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/regulatory", response_model=RegulatoryReportingResponse)
def get_regulatory_reporting_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> RegulatoryReportingResponse:
    try:
        return _regulatory_service.get_regulatory(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/regulatory/requirements", response_model=RegulatoryRequirementResponse)
def get_regulatory_reporting_requirements_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> RegulatoryRequirementResponse:
    try:
        return _regulatory_service.get_requirements(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/regulatory/compliance", response_model=RegulatoryComplianceResponse)
def get_regulatory_reporting_compliance_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> RegulatoryComplianceResponse:
    try:
        return _regulatory_service.get_compliance(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/regulatory/deadlines", response_model=RegulatoryDeadlineResponse)
def get_regulatory_reporting_deadlines_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> RegulatoryDeadlineResponse:
    try:
        return _regulatory_service.get_deadlines(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/regulatory/documents", response_model=RegulatoryDocumentResponse)
def get_regulatory_reporting_documents_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> RegulatoryDocumentResponse:
    try:
        return _regulatory_service.get_documents(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)


@router.get("/runtime/regulatory/risks", response_model=RegulatoryRiskResponse)
def get_regulatory_reporting_risks_runtime(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SUMMARY_READ))],
    tenant: _Tenant,
) -> RegulatoryRiskResponse:
    try:
        return _regulatory_service.get_risks(int(tenant["id"]))
    except Exception as exc:
        _handle(exc)
