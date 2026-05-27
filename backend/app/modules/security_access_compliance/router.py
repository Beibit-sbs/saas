"""FastAPI router for Security / Access / Compliance backend runtime."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.security_access_compliance import permissions, schemas, service
from app.modules.security_access_compliance.dependencies import (
    get_security_access_compliance_db,
    require_security_access_compliance_tenant,
)


router = APIRouter(prefix="/api/admin/security-access-compliance", tags=["security-access-compliance"])

_Actor = Annotated[str, Depends(get_actor)]
_Tenant = Annotated[int, Depends(require_security_access_compliance_tenant)]
_DB = Annotated[Session, Depends(get_security_access_compliance_db)]


def _handle(exc: Exception) -> None:
    if isinstance(exc, TenantResourceNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, DomainValidationError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise HTTPException(status_code=503, detail="fail-closed") from exc


@router.get("/overview", response_model=schemas.SacOverviewResponse)
def get_overview_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacOverviewResponse:
    try:
        del actor
        return service.get_overview(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/readiness", response_model=schemas.SacReadinessResponse)
def get_readiness_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.READINESS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacReadinessResponse:
    try:
        del actor
        return service.get_readiness(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/dashboard", response_model=schemas.SacDashboardResponse)
def get_dashboard_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacDashboardResponse:
    try:
        del actor
        return service.get_dashboard(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/limitations", response_model=schemas.SacLimitationsResponse)
def get_limitations_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.LIMITATIONS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacLimitationsResponse:
    try:
        del actor
        return service.get_limitations(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/roles", response_model=schemas.SacRoleResponse)
def get_roles_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ROLES_READ))],
    tenant_id: _Tenant,
) -> schemas.SacRoleResponse:
    try:
        del actor
        return service.get_roles(tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/permissions", response_model=schemas.SacPermissionResponse)
def get_permissions_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.PERMISSIONS_READ))],
    tenant_id: _Tenant,
) -> schemas.SacPermissionResponse:
    try:
        del actor
        return service.get_permissions(tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/access-governance", response_model=schemas.SacAccessGovernanceResponse)
def get_access_governance_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ACCESS_GOVERNANCE_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacAccessGovernanceResponse:
    try:
        del actor
        return service.get_access_governance(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/rbac-evidence", response_model=schemas.SacRbacEvidenceResponse)
def get_rbac_evidence_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.RBAC_EVIDENCE_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacRbacEvidenceResponse:
    try:
        del actor
        return service.get_rbac_evidence(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/abac-evidence", response_model=schemas.SacAbacEvidenceResponse)
def get_abac_evidence_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ABAC_EVIDENCE_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacAbacEvidenceResponse:
    try:
        del actor
        return service.get_abac_evidence(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/sessions", response_model=schemas.SacSessionVisibilityResponse)
def get_sessions_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SESSIONS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacSessionVisibilityResponse:
    try:
        del actor
        return service.get_sessions(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/login-events", response_model=schemas.SacLoginEventReviewResponse)
def get_login_events_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.LOGIN_EVENTS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacLoginEventReviewResponse:
    try:
        del actor
        return service.get_login_events(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/mfa-readiness", response_model=schemas.SacMfaReadinessResponse)
def get_mfa_readiness_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.MFA_READINESS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMfaReadinessResponse:
    try:
        del actor
        return service.get_mfa_readiness(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/tenant-isolation", response_model=schemas.SacTenantIsolationEvidenceResponse)
def get_tenant_isolation_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.TENANT_ISOLATION_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacTenantIsolationEvidenceResponse:
    try:
        del actor
        return service.get_tenant_isolation(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/incidents", response_model=schemas.SacSecurityIncidentResponse)
def get_incidents_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.INCIDENTS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacSecurityIncidentResponse:
    try:
        del actor
        return service.get_incidents(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/incident-review", response_model=schemas.SacIncidentReviewResponse)
def get_incident_review_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.INCIDENT_REVIEW_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacIncidentReviewResponse:
    try:
        del actor
        return service.get_incident_review(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/remediation", response_model=schemas.SacRemediationTrackingResponse)
def get_remediation_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.REMEDIATION_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacRemediationTrackingResponse:
    try:
        del actor
        return service.get_remediation(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/risks", response_model=schemas.SacRiskRegisterResponse)
def get_risks_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.RISKS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacRiskRegisterResponse:
    try:
        del actor
        return service.get_risks(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/compliance-controls", response_model=schemas.SacComplianceControlResponse)
def get_compliance_controls_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.COMPLIANCE_CONTROLS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacComplianceControlResponse:
    try:
        del actor
        return service.get_compliance_controls(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/policy-controls", response_model=schemas.SacPolicyControlBridgeResponse)
def get_policy_controls_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.POLICY_CONTROLS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacPolicyControlBridgeResponse:
    try:
        del actor
        return service.get_policy_controls(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/audit-events", response_model=schemas.SacAuditEventReviewResponse)
def get_audit_events_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_EVENTS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacAuditEventReviewResponse:
    try:
        del actor
        return service.get_audit_events(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/sensitive-actions", response_model=schemas.SacSensitiveActionReviewResponse)
def get_sensitive_actions_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SENSITIVE_ACTIONS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacSensitiveActionReviewResponse:
    try:
        del actor
        return service.get_sensitive_actions(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/data-protection", response_model=schemas.SacDataProtectionReadinessResponse)
def get_data_protection_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DATA_PROTECTION_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacDataProtectionReadinessResponse:
    try:
        del actor
        return service.get_data_protection(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/privacy-readiness", response_model=schemas.SacPrivacyReadinessResponse)
def get_privacy_readiness_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.PRIVACY_READINESS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacPrivacyReadinessResponse:
    try:
        del actor
        return service.get_privacy_readiness(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/exceptions", response_model=schemas.SacSecurityExceptionResponse)
def get_exceptions_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.EXCEPTIONS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacSecurityExceptionResponse:
    try:
        del actor
        return service.get_exceptions(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/visitor-access", response_model=schemas.SacVisitorAccessBridgeResponse)
def get_visitor_access_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.VISITOR_ACCESS_READ))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacVisitorAccessBridgeResponse:
    try:
        del actor
        return service.get_visitor_access(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/bridges/hr", response_model=schemas.SacCrossVerticalBridgeResponse)
def get_bridge_hr_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.BRIDGES_HR))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacCrossVerticalBridgeResponse:
    try:
        del actor
        return service.get_bridge_hr(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/bridges/finance", response_model=schemas.SacCrossVerticalBridgeResponse)
def get_bridge_finance_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.BRIDGES_FINANCE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacCrossVerticalBridgeResponse:
    try:
        del actor
        return service.get_bridge_finance(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/bridges/documents", response_model=schemas.SacCrossVerticalBridgeResponse)
def get_bridge_documents_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.BRIDGES_DOCUMENTS))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacCrossVerticalBridgeResponse:
    try:
        del actor
        return service.get_bridge_documents(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/bridges/student-services", response_model=schemas.SacCrossVerticalBridgeResponse)
def get_bridge_student_services_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.BRIDGES_STUDENT_SERVICES))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacCrossVerticalBridgeResponse:
    try:
        del actor
        return service.get_bridge_student_services(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/metadata-contract", response_model=schemas.SacMetadataContractResponse)
def get_metadata_contract_endpoint(
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))],
    tenant_id: _Tenant,
) -> schemas.SacMetadataContractResponse:
    try:
        del actor
        return service.get_metadata_contract(tenant_id)
    except Exception as exc:
        _handle(exc)


@router.post("/incidents/metadata", response_model=schemas.SacMutationResponse, status_code=201)
def create_incident_metadata_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.INCIDENTS_METADATA))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_incident_metadata(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/incident-review/metadata", response_model=schemas.SacMutationResponse, status_code=201)
def create_incident_review_metadata_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.INCIDENT_REVIEW_METADATA))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_incident_review_metadata(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/remediation/metadata", response_model=schemas.SacMutationResponse, status_code=201)
def create_remediation_metadata_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.REMEDIATION_METADATA))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_remediation_metadata(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/risks/metadata", response_model=schemas.SacMutationResponse, status_code=201)
def create_risk_metadata_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.RISKS_METADATA))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_risk_metadata(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/compliance-controls/metadata", response_model=schemas.SacMutationResponse, status_code=201)
def create_compliance_control_metadata_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.COMPLIANCE_CONTROLS_METADATA))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_compliance_control_metadata(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/policy-controls/metadata", response_model=schemas.SacMutationResponse, status_code=201)
def create_policy_control_metadata_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.POLICY_CONTROLS_METADATA))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_policy_control_metadata(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/audit-events/metadata", response_model=schemas.SacMutationResponse, status_code=201)
def create_audit_event_metadata_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_EVENTS_METADATA))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_audit_event_metadata(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/sensitive-actions/review", response_model=schemas.SacMutationResponse, status_code=201)
def create_sensitive_action_review_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.SENSITIVE_ACTIONS_REVIEW))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_sensitive_action_review(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/data-protection/evidence", response_model=schemas.SacMutationResponse, status_code=201)
def create_data_protection_evidence_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.DATA_PROTECTION_EVIDENCE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_data_protection_evidence(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/privacy-readiness/evidence", response_model=schemas.SacMutationResponse, status_code=201)
def create_privacy_readiness_evidence_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.PRIVACY_READINESS_EVIDENCE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_privacy_readiness_evidence(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/exceptions/metadata", response_model=schemas.SacMutationResponse, status_code=201)
def create_exception_metadata_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.EXCEPTIONS_METADATA))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_exception_metadata(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/visitor-access/metadata", response_model=schemas.SacMutationResponse, status_code=201)
def create_visitor_access_metadata_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.VISITOR_ACCESS_METADATA))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_visitor_access_metadata(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/bridges/hr", response_model=schemas.SacMutationResponse, status_code=201)
def create_bridge_hr_endpoint(
    payload: schemas.SacBridgeWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.BRIDGES_HR))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_bridge_hr(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/bridges/finance", response_model=schemas.SacMutationResponse, status_code=201)
def create_bridge_finance_endpoint(
    payload: schemas.SacBridgeWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.BRIDGES_FINANCE))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_bridge_finance(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/bridges/documents", response_model=schemas.SacMutationResponse, status_code=201)
def create_bridge_documents_endpoint(
    payload: schemas.SacBridgeWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.BRIDGES_DOCUMENTS))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_bridge_documents(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/bridges/student-services", response_model=schemas.SacMutationResponse, status_code=201)
def create_bridge_student_services_endpoint(
    payload: schemas.SacBridgeWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.BRIDGES_STUDENT_SERVICES))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_bridge_student_services(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)


@router.post("/limitations", response_model=schemas.SacMutationResponse, status_code=201)
def create_limitation_endpoint(
    payload: schemas.SacMetadataWriteRequest,
    actor: _Actor,
    _: Annotated[None, Depends(permission_dependency(permissions.ACCESS_GOVERNANCE_METADATA))],
    tenant_id: _Tenant,
    db: _DB,
) -> schemas.SacMutationResponse:
    try:
        return service.create_limitation_record(db, tenant_id, actor, payload)
    except Exception as exc:
        _handle(exc)
