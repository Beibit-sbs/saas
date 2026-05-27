"""Service layer for Security / Access / Compliance."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, validate_tenant_id_provided
from app.modules.security_access_compliance import models, permissions, repository, schemas


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _actor(value: str | int | None) -> str:
    actor = str(value or "").strip()
    if not actor:
        raise DomainValidationError("actor is required")
    return actor


def _safety(*, incomplete_data: bool = False, limitations: list[str] | None = None) -> schemas.SacSafetyFlags:
    return schemas.SacSafetyFlags(
        fake_security_certification=False,
        fake_compliance_certification=False,
        legal_regulatory_compliance_claimed=False,
        soc_siem_replacement_claimed=False,
        fake_incident_resolution=False,
        fake_audit_proof=False,
        fake_penetration_test_result=False,
        fake_vulnerability_scan_result=False,
        fake_risk_score=False,
        hidden_user_risk_score_present=False,
        discriminatory_ranking_present=False,
        autonomous_enforcement_enabled=False,
        automatic_user_blocking_enabled=False,
        automatic_user_sanction_enabled=False,
        automatic_data_deletion_enabled=False,
        external_regulator_submission_enabled=False,
        production_security_claimed=False,
        human_review_required=True,
        incomplete_data=bool(incomplete_data),
        limitations=list(limitations or []),
    )


def _base(tenant_id: int, *, incomplete_data: bool = False, limitations: list[str] | None = None) -> dict:
    return {
        "module": models.MODULE_NAME,
        "contract_version": models.CONTRACT_VERSION,
        "runtime_mode": models.RUNTIME_MODE,
        "tenant_id": tenant_id,
        "safety_flags": _safety(incomplete_data=incomplete_data, limitations=limitations),
    }


def _collection_response(response_type, tenant_id: int, items: list[dict], *, limitations: list[str] | None = None):
    incomplete = any(bool(row.get("incomplete_data", False)) for row in items)
    return response_type.model_validate(_base(tenant_id, incomplete_data=incomplete, limitations=limitations) | {"items": items})


def _metadata_contract(tenant_id: int) -> schemas.SacMetadataContractResponse:
    return schemas.SacMetadataContractResponse.model_validate(
        _base(tenant_id, limitations=get_safety_boundaries())
        | {
            "expected_table_count": models.EXPECTED_TABLE_COUNT,
            "expected_route_count": models.EXPECTED_ROUTE_COUNT,
            "expected_permission_count": models.EXPECTED_PERMISSION_COUNT,
            "permission_namespace": "security_access_compliance.*",
        }
    )


def get_safety_boundaries() -> list[str]:
    return [
        "no fake security certification",
        "no fake compliance certification",
        "no fake legal/regulatory compliance claim",
        "no fake soc/siem claim",
        "no fake incident resolution",
        "no fake audit proof",
        "no fake penetration-test result",
        "no fake vulnerability-scan result",
        "no fake risk score",
        "no hidden user risk score",
        "no discriminatory ranking",
        "no automatic user blocking",
        "no automatic user sanction",
        "no automatic data deletion",
        "no autonomous enforcement",
        "no external regulator submission",
        "no production-ready security claim",
    ]


def get_health(tenant_id: int) -> schemas.SacMetadataContractResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    return _metadata_contract(tenant_id)


def get_metadata_contract(tenant_id: int) -> schemas.SacMetadataContractResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    return _metadata_contract(tenant_id)


def get_overview(db: Session, tenant_id: int) -> schemas.SacOverviewResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    return _collection_response(schemas.SacOverviewResponse, tenant_id, repository.list_family_records(db, tenant_id, "overview"), limitations=get_safety_boundaries())


def get_readiness(db: Session, tenant_id: int) -> schemas.SacReadinessResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    return _collection_response(schemas.SacReadinessResponse, tenant_id, repository.list_family_records(db, tenant_id, "readiness"), limitations=get_safety_boundaries())


def get_dashboard(db: Session, tenant_id: int) -> schemas.SacDashboardResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    dashboard = repository.get_dashboard_inputs(db, tenant_id)
    flat = [
        {"family": family, "items": items}
        for family, items in dashboard.items()
    ]
    return _collection_response(schemas.SacDashboardResponse, tenant_id, flat, limitations=get_safety_boundaries())


def get_limitations(db: Session, tenant_id: int) -> schemas.SacLimitationsResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    return _collection_response(schemas.SacLimitationsResponse, tenant_id, repository.list_family_records(db, tenant_id, "limitations"), limitations=get_safety_boundaries())


def get_roles(tenant_id: int) -> schemas.SacRoleResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    items = [
        {"role": "superadmin", "scope": "platform"},
        {"role": "admin", "scope": "tenant"},
        {"role": "auditor", "scope": "read_only"},
    ]
    return _collection_response(schemas.SacRoleResponse, tenant_id, items, limitations=get_safety_boundaries())


def get_permissions(tenant_id: int) -> schemas.SacPermissionResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    items = [{"permission": name} for name in permissions.SECURITY_ACCESS_COMPLIANCE_PERMISSIONS]
    return _collection_response(schemas.SacPermissionResponse, tenant_id, items, limitations=get_safety_boundaries())


def get_access_governance(db: Session, tenant_id: int) -> schemas.SacAccessGovernanceResponse:
    return _collection_response(schemas.SacAccessGovernanceResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "access_governance"), limitations=get_safety_boundaries())


def get_rbac_evidence(db: Session, tenant_id: int) -> schemas.SacRbacEvidenceResponse:
    return _collection_response(schemas.SacRbacEvidenceResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "rbac_evidence"), limitations=get_safety_boundaries())


def get_abac_evidence(db: Session, tenant_id: int) -> schemas.SacAbacEvidenceResponse:
    return _collection_response(schemas.SacAbacEvidenceResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "abac_evidence"), limitations=get_safety_boundaries())


def get_sessions(db: Session, tenant_id: int) -> schemas.SacSessionVisibilityResponse:
    return _collection_response(schemas.SacSessionVisibilityResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "sessions"), limitations=get_safety_boundaries())


def get_login_events(db: Session, tenant_id: int) -> schemas.SacLoginEventReviewResponse:
    return _collection_response(schemas.SacLoginEventReviewResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "login_events"), limitations=get_safety_boundaries())


def get_mfa_readiness(db: Session, tenant_id: int) -> schemas.SacMfaReadinessResponse:
    return _collection_response(schemas.SacMfaReadinessResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "mfa_readiness"), limitations=get_safety_boundaries())


def get_tenant_isolation(db: Session, tenant_id: int) -> schemas.SacTenantIsolationEvidenceResponse:
    return _collection_response(schemas.SacTenantIsolationEvidenceResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "tenant_isolation"), limitations=get_safety_boundaries())


def get_incidents(db: Session, tenant_id: int) -> schemas.SacSecurityIncidentResponse:
    return _collection_response(schemas.SacSecurityIncidentResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "incidents"), limitations=get_safety_boundaries())


def get_incident_review(db: Session, tenant_id: int) -> schemas.SacIncidentReviewResponse:
    return _collection_response(schemas.SacIncidentReviewResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "incident_review"), limitations=get_safety_boundaries())


def get_remediation(db: Session, tenant_id: int) -> schemas.SacRemediationTrackingResponse:
    return _collection_response(schemas.SacRemediationTrackingResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "remediation"), limitations=get_safety_boundaries())


def get_risks(db: Session, tenant_id: int) -> schemas.SacRiskRegisterResponse:
    return _collection_response(schemas.SacRiskRegisterResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "risks"), limitations=get_safety_boundaries())


def get_compliance_controls(db: Session, tenant_id: int) -> schemas.SacComplianceControlResponse:
    return _collection_response(schemas.SacComplianceControlResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "compliance_controls"), limitations=get_safety_boundaries())


def get_policy_controls(db: Session, tenant_id: int) -> schemas.SacPolicyControlBridgeResponse:
    return _collection_response(schemas.SacPolicyControlBridgeResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "policy_controls"), limitations=get_safety_boundaries())


def get_audit_events(db: Session, tenant_id: int) -> schemas.SacAuditEventReviewResponse:
    return _collection_response(schemas.SacAuditEventReviewResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "audit_events"), limitations=get_safety_boundaries())


def get_sensitive_actions(db: Session, tenant_id: int) -> schemas.SacSensitiveActionReviewResponse:
    return _collection_response(schemas.SacSensitiveActionReviewResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "sensitive_actions"), limitations=get_safety_boundaries())


def get_data_protection(db: Session, tenant_id: int) -> schemas.SacDataProtectionReadinessResponse:
    return _collection_response(schemas.SacDataProtectionReadinessResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "data_protection"), limitations=get_safety_boundaries())


def get_privacy_readiness(db: Session, tenant_id: int) -> schemas.SacPrivacyReadinessResponse:
    return _collection_response(schemas.SacPrivacyReadinessResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "privacy_readiness"), limitations=get_safety_boundaries())


def get_exceptions(db: Session, tenant_id: int) -> schemas.SacSecurityExceptionResponse:
    return _collection_response(schemas.SacSecurityExceptionResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "exceptions"), limitations=get_safety_boundaries())


def get_visitor_access(db: Session, tenant_id: int) -> schemas.SacVisitorAccessBridgeResponse:
    return _collection_response(schemas.SacVisitorAccessBridgeResponse, validate_tenant_id_provided(tenant_id), repository.list_family_records(db, tenant_id, "visitor_access"), limitations=get_safety_boundaries())


def get_bridge_hr(db: Session, tenant_id: int) -> schemas.SacCrossVerticalBridgeResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    return _collection_response(schemas.SacCrossVerticalBridgeResponse, tenant_id, repository.get_bridge_inputs(db, tenant_id)["hr"], limitations=get_safety_boundaries())


def get_bridge_finance(db: Session, tenant_id: int) -> schemas.SacCrossVerticalBridgeResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    return _collection_response(schemas.SacCrossVerticalBridgeResponse, tenant_id, repository.get_bridge_inputs(db, tenant_id)["finance"], limitations=get_safety_boundaries())


def get_bridge_documents(db: Session, tenant_id: int) -> schemas.SacCrossVerticalBridgeResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    return _collection_response(schemas.SacCrossVerticalBridgeResponse, tenant_id, repository.get_bridge_inputs(db, tenant_id)["documents"], limitations=get_safety_boundaries())


def get_bridge_student_services(db: Session, tenant_id: int) -> schemas.SacCrossVerticalBridgeResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    return _collection_response(schemas.SacCrossVerticalBridgeResponse, tenant_id, repository.get_bridge_inputs(db, tenant_id)["student_services"], limitations=get_safety_boundaries())


def _write(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest | schemas.SacBridgeWriteRequest, writer):
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _actor(actor)
    item = writer(db, tenant_id, actor, payload.model_dump())
    _commit(db)
    return schemas.SacMutationResponse.model_validate(_base(tenant_id, incomplete_data=item.get("incomplete_data", False), limitations=item.get("limitations", [])) | {"item": item})


def create_incident_metadata(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_incident_metadata)


def create_incident_review_metadata(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_incident_review_metadata)


def create_remediation_metadata(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_remediation_metadata)


def create_risk_metadata(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_risk_metadata)


def create_compliance_control_metadata(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_compliance_control_metadata)


def create_policy_control_metadata(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_policy_control_metadata)


def create_audit_event_metadata(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_audit_event_metadata)


def create_sensitive_action_review(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_sensitive_action_review)


def create_data_protection_evidence(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_data_protection_evidence)


def create_privacy_readiness_evidence(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_privacy_readiness_evidence)


def create_exception_metadata(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_exception_metadata)


def create_visitor_access_metadata(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_visitor_access_metadata)


def create_bridge_hr(db: Session, tenant_id: int, actor: str, payload: schemas.SacBridgeWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_bridge_hr)


def create_bridge_finance(db: Session, tenant_id: int, actor: str, payload: schemas.SacBridgeWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_bridge_finance)


def create_bridge_documents(db: Session, tenant_id: int, actor: str, payload: schemas.SacBridgeWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_bridge_documents)


def create_bridge_student_services(db: Session, tenant_id: int, actor: str, payload: schemas.SacBridgeWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_bridge_student_services)


def create_limitation_record(db: Session, tenant_id: int, actor: str, payload: schemas.SacMetadataWriteRequest) -> schemas.SacMutationResponse:
    return _write(db, tenant_id, actor, payload, repository.create_limitation_record)
