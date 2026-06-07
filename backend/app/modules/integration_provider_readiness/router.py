"""FastAPI router for Integration Provider Readiness backend foundation."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.modules.integration_provider_readiness import API_PREFIX, permissions, schemas, service
from app.modules.integration_provider_readiness.dependencies import get_integration_provider_readiness_db, require_integration_provider_readiness_tenant
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix=API_PREFIX, tags=["integration-provider-readiness"])

_Actor = Annotated[str, Depends(get_actor)]
_Tenant = Annotated[int, Depends(require_integration_provider_readiness_tenant)]
_DB = Annotated[Session, Depends(get_integration_provider_readiness_db)]


def _handle(exc: Exception) -> None:
    if isinstance(exc, TenantResourceNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, DomainValidationError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


@router.get("/providers", response_model=schemas.GovernanceListRead)
def list_provider_registry_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.REGISTRY_LIST))], tenant_id: _Tenant, db: _DB, provider_type: str | None = None):
    try:
        del actor
        return service.list_provider_registry(db, tenant_id, provider_type)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{record_id}", response_model=schemas.GovernanceRecordRead)
def get_provider_registry_endpoint(record_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.REGISTRY_READ))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.get_provider_registry(db, tenant_id, record_id)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/by-type/{provider_type}", response_model=schemas.GovernanceListRead)
def list_provider_registry_by_type_endpoint(provider_type: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.REGISTRY_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_provider_registry(db, tenant_id, provider_type)
    except Exception as exc:
        _handle(exc)


@router.post("/providers", response_model=schemas.GovernanceRecordRead, status_code=201)
def create_provider_registry_endpoint(payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.REGISTRY_CREATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.create_provider_registry(db, tenant_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.put("/providers/{record_id}", response_model=schemas.GovernanceRecordRead)
def update_provider_registry_endpoint(record_id: int, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.REGISTRY_UPDATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.update_provider_registry(db, tenant_id, record_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/profiles", response_model=schemas.GovernanceListRead)
def list_profiles_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PROFILE_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_profiles(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.get("/profiles/{profile_id}", response_model=schemas.GovernanceRecordRead)
def get_profile_endpoint(profile_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PROFILE_READ))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.get_profile(db, tenant_id, profile_id)
    except Exception as exc:
        _handle(exc)


@router.post("/providers/{provider_id}/profiles", response_model=schemas.GovernanceRecordRead, status_code=201)
def create_profile_endpoint(provider_id: str, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PROFILE_CREATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.create_provider_profile(db, tenant_id, provider_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.put("/profiles/{profile_id}", response_model=schemas.GovernanceRecordRead)
def update_profile_endpoint(profile_id: int, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PROFILE_UPDATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.update_provider_profile(db, tenant_id, profile_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.delete("/profiles/{profile_id}", status_code=204)
def delete_profile_endpoint(profile_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PROFILE_UPDATE))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        service.delete_provider_profile(db, tenant_id, profile_id)
        return None
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/capabilities", response_model=schemas.GovernanceListRead)
def list_capabilities_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.CAPABILITY_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_capabilities(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.get("/capabilities/{capability_id}", response_model=schemas.GovernanceRecordRead)
def get_capability_endpoint(capability_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.CAPABILITY_READ))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.get_capability(db, tenant_id, capability_id)
    except Exception as exc:
        _handle(exc)


@router.post("/providers/{provider_id}/capabilities", response_model=schemas.GovernanceRecordRead, status_code=201)
def create_capability_endpoint(provider_id: str, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.CAPABILITY_CREATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.upsert_capability_matrix(db, tenant_id, provider_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.put("/capabilities/{capability_id}", response_model=schemas.GovernanceRecordRead)
def update_capability_endpoint(capability_id: int, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.CAPABILITY_UPDATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.update_capability_matrix(db, tenant_id, capability_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/assessments", response_model=schemas.GovernanceListRead)
def list_assessments_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.READINESS_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_readiness_assessments(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.get("/assessments/{assessment_id}", response_model=schemas.GovernanceRecordRead)
def get_assessment_endpoint(assessment_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.READINESS_READ))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.get_readiness_assessment(db, tenant_id, assessment_id)
    except Exception as exc:
        _handle(exc)


@router.post("/providers/{provider_id}/assessments", response_model=schemas.GovernanceRecordRead, status_code=201)
def create_assessment_endpoint(provider_id: str, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.READINESS_CREATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.create_readiness_assessment(db, tenant_id, provider_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.put("/assessments/{assessment_id}", response_model=schemas.GovernanceRecordRead)
def update_assessment_endpoint(assessment_id: int, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.READINESS_UPDATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.update_readiness_assessment(db, tenant_id, assessment_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/evidence", response_model=schemas.GovernanceListRead)
def list_evidence_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_evidence(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.get("/evidence/{evidence_id}", response_model=schemas.GovernanceRecordRead)
def get_evidence_endpoint(evidence_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_READ))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.get_evidence(db, tenant_id, evidence_id)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/evidence-links", response_model=schemas.GovernanceListRead)
def list_evidence_links_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_evidence_links(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.post("/providers/{provider_id}/evidence", response_model=schemas.GovernanceRecordRead, status_code=201)
def create_evidence_endpoint(provider_id: str, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_CREATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.collect_evidence(db, tenant_id, provider_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.post("/evidence/{evidence_id}/links", response_model=schemas.GovernanceRecordRead, status_code=201)
def create_evidence_link_endpoint(evidence_id: int, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_CREATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.link_evidence(db, tenant_id, evidence_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.put("/evidence/{evidence_id}", response_model=schemas.GovernanceRecordRead)
def update_evidence_endpoint(evidence_id: int, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_UPDATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.update_evidence(db, tenant_id, evidence_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/compliance-reviews", response_model=schemas.GovernanceListRead)
def list_compliance_reviews_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.COMPLIANCE_READ))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_compliance_reviews(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/security-reviews", response_model=schemas.GovernanceListRead)
def list_security_reviews_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.SECURITY_READ))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_security_reviews(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.post("/providers/{provider_id}/compliance-reviews", response_model=schemas.GovernanceRecordRead, status_code=201)
def create_compliance_review_endpoint(provider_id: str, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.COMPLIANCE_REVIEW))], tenant_id: _Tenant, db: _DB):
    try:
        return service.review_compliance(db, tenant_id, provider_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.put("/compliance-reviews/{review_id}", response_model=schemas.GovernanceRecordRead)
def update_compliance_review_endpoint(review_id: int, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.COMPLIANCE_APPROVE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.approve_compliance(db, tenant_id, review_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.put("/security-reviews/{review_id}", response_model=schemas.GovernanceRecordRead)
def update_security_review_endpoint(review_id: int, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.SECURITY_APPROVE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.review_security(db, tenant_id, review_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/risks", response_model=schemas.GovernanceListRead)
def list_risks_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.RISK_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_risks(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/exceptions", response_model=schemas.GovernanceListRead)
def list_exceptions_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.RISK_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_exceptions(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.post("/providers/{provider_id}/risks", response_model=schemas.GovernanceRecordRead, status_code=201)
def create_risk_endpoint(provider_id: str, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.RISK_CREATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.escalate_risk_exception(db, tenant_id, provider_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.put("/exceptions/{exception_id}", response_model=schemas.GovernanceRecordRead)
def update_exception_endpoint(exception_id: int, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.RISK_UPDATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.update_exception_case(db, tenant_id, exception_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/audits", response_model=schemas.GovernanceListRead)
def list_audits_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_audit_records(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.post("/providers/{provider_id}/audits", response_model=schemas.GovernanceRecordRead, status_code=201)
def create_audit_endpoint(provider_id: str, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_APPEND))], tenant_id: _Tenant, db: _DB):
    try:
        return service.record_provider_audit_review(db, tenant_id, provider_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/health", response_model=schemas.GovernanceListRead)
def get_provider_health_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.READINESS_READ))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.generate_provider_health_visibility(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.get("/health-snapshots", response_model=schemas.GovernanceListRead)
def list_health_snapshots_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.READINESS_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_health_snapshots(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/health-summary", response_model=schemas.HealthSummaryRead)
def get_health_summary_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.READINESS_READ))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.get_health_summary(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/providers/{provider_id}/plans", response_model=schemas.GovernanceListRead)
def list_plans_endpoint(provider_id: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PLAN_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.list_integration_plans(db, tenant_id, provider_id)
    except Exception as exc:
        _handle(exc)


@router.get("/roadmap", response_model=schemas.DashboardContractListRead)
def get_roadmap_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PLAN_LIST))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.get_roadmap_summary(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.post("/providers/{provider_id}/plans", response_model=schemas.GovernanceRecordRead, status_code=201)
def create_plan_endpoint(provider_id: str, payload: schemas.GovernanceMutationRequest, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PLAN_CREATE))], tenant_id: _Tenant, db: _DB):
    try:
        return service.plan_integration_roadmap(db, tenant_id, provider_id, actor, payload.payload)
    except Exception as exc:
        _handle(exc)


@router.delete("/plans/{plan_id}", status_code=204)
def delete_plan_endpoint(plan_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PLAN_UPDATE))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        service.delete_integration_plan(db, tenant_id, plan_id)
        return None
    except Exception as exc:
        _handle(exc)


@router.get("/dashboards", response_model=schemas.DashboardContractListRead)
def list_dashboards_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_OVERVIEW_READ))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.publish_dashboard_bundle(db, tenant_id)
    except Exception as exc:
        _handle(exc)


@router.get("/dashboards/{dashboard_name}", response_model=schemas.DashboardContractRead)
def get_dashboard_endpoint(dashboard_name: str, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_OVERVIEW_READ))], tenant_id: _Tenant, db: _DB):
    try:
        del actor
        return service.get_dashboard_contract(db, tenant_id, dashboard_name)
    except Exception as exc:
        _handle(exc)
