"""Repository helpers for Security / Access / Compliance."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError, validate_tenant_id_provided
from app.modules.security_access_compliance import models


MODEL_BY_FAMILY = {
    "overview": models.SacReadinessProfile,
    "readiness": models.SacReadinessProfile,
    "dashboard": models.SacDashboardSnapshot,
    "limitations": models.SacLimitation,
    "access_governance": models.SacAccessGovernanceRecord,
    "role_permission_inventory": models.SacRolePermissionInventorySnapshot,
    "rbac_evidence": models.SacRbacEvidenceRecord,
    "abac_evidence": models.SacAbacEvidenceRecord,
    "sessions": models.SacSessionVisibilityRecord,
    "login_events": models.SacLoginEventReviewRecord,
    "mfa_readiness": models.SacMfaReadinessRecord,
    "tenant_isolation": models.SacTenantIsolationEvidenceRecord,
    "incidents": models.SacSecurityIncidentRecord,
    "incident_review": models.SacIncidentReviewRecord,
    "remediation": models.SacRemediationTrackingRecord,
    "risks": models.SacRiskRegisterRecord,
    "compliance_controls": models.SacComplianceControlRecord,
    "policy_controls": models.SacPolicyControlBridgeRecord,
    "audit_events": models.SacAuditEventReviewRecord,
    "sensitive_actions": models.SacSensitiveActionReviewRecord,
    "data_protection": models.SacDataProtectionReadinessRecord,
    "privacy_readiness": models.SacPrivacyReadinessRecord,
    "exceptions": models.SacSecurityExceptionRecord,
    "visitor_access": models.SacVisitorAccessBridgeRecord,
    "bridges": models.SacCrossVerticalBridgeRecord,
}


def _now() -> datetime:
    return datetime.now(UTC)


def verify_tenant_scope(tenant_id: int) -> int:
    return validate_tenant_id_provided(tenant_id)


def _as_dict(record) -> dict:
    return {
        "id": record.id,
        "tenant_id": record.tenant_id,
        "status": record.status,
        "metadata": dict(record.metadata_json or {}),
        "limitations": list(record.limitations_json or []),
        "incomplete_data": bool(getattr(record, "incomplete_data", False)),
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        "archived_at": record.archived_at,
    }


def list_family_records(db: Session, tenant_id: int, family: str) -> list[dict]:
    tenant_id = verify_tenant_scope(tenant_id)
    model = MODEL_BY_FAMILY.get(family)
    if model is None:
        raise DomainValidationError(f"unsupported family: {family}")
    rows = list(
        db.execute(
            select(model)
            .where(and_(model.tenant_id == tenant_id, model.archived_at.is_(None)))
            .order_by(model.created_at.desc())
        ).scalars()
    )
    return [_as_dict(row) for row in rows]


def create_family_record(
    db: Session,
    tenant_id: int,
    family: str,
    *,
    actor: str,
    record_key: str,
    status: str,
    metadata: dict,
    limitations: list[str],
    incomplete_data: bool,
    bridge_key: str | None = None,
) -> dict:
    tenant_id = verify_tenant_scope(tenant_id)
    model = MODEL_BY_FAMILY.get(family)
    if model is None:
        raise DomainValidationError(f"unsupported family: {family}")

    payload = {
        "tenant_id": tenant_id,
        "status": status,
        "source_module": models.MODULE_NAME,
        "source_entity_id": record_key,
        "metadata_json": metadata,
        "limitations_json": limitations,
        "created_by": actor,
        "updated_by": actor,
        "created_at": _now(),
        "updated_at": _now(),
        "incomplete_data": bool(incomplete_data),
        "human_review_required": True,
        "certification_claimed": False,
        "compliance_certified": False,
        "soc_siem_replacement": False,
        "autonomous_enforcement_enabled": False,
        "external_submission_enabled": False,
        "hidden_user_risk_score_present": False,
    }
    if bridge_key and model is models.SacCrossVerticalBridgeRecord:
        payload["bridge_key"] = bridge_key
    if model is models.SacLimitation:
        payload["limitation_text"] = str(record_key)

    obj = model(**payload)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return _as_dict(obj)


def get_dashboard_inputs(db: Session, tenant_id: int) -> dict[str, list[dict]]:
    tenant_id = verify_tenant_scope(tenant_id)
    return {
        "readiness": list_family_records(db, tenant_id, "readiness"),
        "incidents": list_family_records(db, tenant_id, "incidents"),
        "risks": list_family_records(db, tenant_id, "risks"),
        "compliance_controls": list_family_records(db, tenant_id, "compliance_controls"),
    }


def get_bridge_inputs(db: Session, tenant_id: int) -> dict[str, list[dict]]:
    tenant_id = verify_tenant_scope(tenant_id)
    bridges = list_family_records(db, tenant_id, "bridges")
    return {
        "hr": [row for row in bridges if row.get("metadata", {}).get("bridge_key") == "hr"],
        "finance": [row for row in bridges if row.get("metadata", {}).get("bridge_key") == "finance"],
        "documents": [row for row in bridges if row.get("metadata", {}).get("bridge_key") == "documents"],
        "student_services": [row for row in bridges if row.get("metadata", {}).get("bridge_key") == "student_services"],
    }


def _create_metadata(db: Session, tenant_id: int, family: str, *, actor: str, payload: dict, bridge_key: str | None = None) -> dict:
    return create_family_record(
        db,
        tenant_id,
        family,
        actor=actor,
        record_key=str(payload.get("record_key") or "metadata"),
        status=str(payload.get("status") or "active"),
        metadata=dict(payload.get("metadata") or {}),
        limitations=list(payload.get("limitations") or []),
        incomplete_data=bool(payload.get("incomplete_data", False)),
        bridge_key=bridge_key,
    )


def create_incident_metadata(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "incidents", actor=actor, payload=payload)


def create_incident_review_metadata(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "incident_review", actor=actor, payload=payload)


def create_remediation_metadata(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "remediation", actor=actor, payload=payload)


def create_risk_metadata(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "risks", actor=actor, payload=payload)


def create_compliance_control_metadata(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "compliance_controls", actor=actor, payload=payload)


def create_policy_control_metadata(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "policy_controls", actor=actor, payload=payload)


def create_audit_event_metadata(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "audit_events", actor=actor, payload=payload)


def create_sensitive_action_review(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "sensitive_actions", actor=actor, payload=payload)


def create_data_protection_evidence(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "data_protection", actor=actor, payload=payload)


def create_privacy_readiness_evidence(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "privacy_readiness", actor=actor, payload=payload)


def create_exception_metadata(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "exceptions", actor=actor, payload=payload)


def create_visitor_access_metadata(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "visitor_access", actor=actor, payload=payload)


def create_bridge_hr(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    payload = dict(payload)
    payload.setdefault("metadata", {})
    payload["metadata"]["bridge_key"] = "hr"
    return _create_metadata(db, tenant_id, "bridges", actor=actor, payload=payload, bridge_key="hr")


def create_bridge_finance(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    payload = dict(payload)
    payload.setdefault("metadata", {})
    payload["metadata"]["bridge_key"] = "finance"
    return _create_metadata(db, tenant_id, "bridges", actor=actor, payload=payload, bridge_key="finance")


def create_bridge_documents(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    payload = dict(payload)
    payload.setdefault("metadata", {})
    payload["metadata"]["bridge_key"] = "documents"
    return _create_metadata(db, tenant_id, "bridges", actor=actor, payload=payload, bridge_key="documents")


def create_bridge_student_services(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    payload = dict(payload)
    payload.setdefault("metadata", {})
    payload["metadata"]["bridge_key"] = "student_services"
    return _create_metadata(db, tenant_id, "bridges", actor=actor, payload=payload, bridge_key="student_services")


def create_limitation_record(db: Session, tenant_id: int, actor: str, payload: dict) -> dict:
    return _create_metadata(db, tenant_id, "limitations", actor=actor, payload=payload)


def get_record_or_raise(db: Session, tenant_id: int, family: str, record_id: int) -> dict:
    model = MODEL_BY_FAMILY.get(family)
    if model is None:
        raise DomainValidationError(f"unsupported family: {family}")
    row = db.execute(select(model).where(and_(model.tenant_id == verify_tenant_scope(tenant_id), model.id == record_id))).scalar_one_or_none()
    if row is None:
        raise TenantResourceNotFoundError(f"{family} record {record_id} not found for tenant {tenant_id}")
    return _as_dict(row)
