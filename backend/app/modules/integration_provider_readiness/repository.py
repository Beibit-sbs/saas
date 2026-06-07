"""Repository helpers for Integration Provider Readiness backend foundation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import TenantResourceNotFoundError, validate_tenant_id_provided
from app.modules.integration_provider_readiness import PROVIDER_CATALOG
from app.modules.integration_provider_readiness import models


def _now() -> datetime:
    return datetime.now(UTC)


def _require(resource: object | None, tenant_id: int, resource_name: str, resource_id: int) -> object:
    if resource is None:
        raise TenantResourceNotFoundError(f"{resource_name} {resource_id} not found for tenant {tenant_id}")
    return resource


def _base_payload(actor_user_id: str, payload: dict[str, Any] | None = None, *, status: str = "draft", reason_code: str | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "payload_json": dict(payload or {}),
        "reason_code": reason_code,
        "actor_user_id": actor_user_id,
        "created_by_user_id": actor_user_id,
        "updated_by_user_id": actor_user_id,
        "readiness_only": True,
        "provider_connected": False,
        "live_provider_calls": False,
        "credentials_stored": False,
        "external_submission": False,
        "sync_execution": False,
        "fake_health_metrics": False,
        "fake_readiness_metrics": False,
        "created_at": _now(),
        "updated_at": _now(),
    }


def _next_id(db: Session, model) -> int:
    current = db.scalar(select(func.max(model.id)))
    return int(current or 0) + 1


def ensure_provider_catalog(db: Session, tenant_id: int, actor_user_id: str = "system") -> list[models.ProviderRegistry]:
    tenant_id = validate_tenant_id_provided(tenant_id)
    existing = list(
        db.execute(
            select(models.ProviderRegistry).where(models.ProviderRegistry.tenant_id == tenant_id)
        ).scalars().all()
    )
    if existing:
        return existing

    next_id = _next_id(db, models.ProviderRegistry)
    for item in PROVIDER_CATALOG:
        db.add(
            models.ProviderRegistry(
                id=next_id,
                tenant_id=tenant_id,
                provider_id=str(item["provider_id"]),
                provider_name=str(item["provider_name"]),
                provider_type=str(item["provider_type"]),
                readiness_level=str(item["readiness_level"]),
                future_scope=str(item["future_scope"]),
                business_owner_role=str(item["business_owner_role"]),
                technical_owner_role=str(item["technical_owner_role"]),
                security_owner_role=str(item["security_owner_role"]),
                auditor_visibility=bool(item["auditor_visibility"]),
                executive_visibility=bool(item["executive_visibility"]),
                payload_json={"seeded": True},
                created_by_user_id=actor_user_id,
                updated_by_user_id=actor_user_id,
                created_at=_now(),
                updated_at=_now(),
            )
        )
        next_id += 1
    db.commit()
    return list(
        db.execute(
            select(models.ProviderRegistry).where(models.ProviderRegistry.tenant_id == tenant_id)
        ).scalars().all()
    )


def list_provider_registry(db: Session, tenant_id: int, provider_type: str | None = None) -> list[models.ProviderRegistry]:
    query = select(models.ProviderRegistry).where(models.ProviderRegistry.tenant_id == validate_tenant_id_provided(tenant_id))
    if provider_type:
        query = query.where(models.ProviderRegistry.provider_type == provider_type)
    return list(db.execute(query.order_by(models.ProviderRegistry.provider_id.asc())).scalars().all())


def get_provider_registry(db: Session, tenant_id: int, record_id: int) -> models.ProviderRegistry | None:
    return db.execute(
        select(models.ProviderRegistry).where(
            models.ProviderRegistry.tenant_id == validate_tenant_id_provided(tenant_id),
            models.ProviderRegistry.id == record_id,
        )
    ).scalar_one_or_none()


def create_provider_registry(db: Session, tenant_id: int, actor_user_id: str, payload: dict[str, Any]) -> models.ProviderRegistry:
    record = models.ProviderRegistry(
        id=_next_id(db, models.ProviderRegistry),
        tenant_id=tenant_id,
        provider_id=str(payload["provider_id"]),
        provider_name=str(payload["provider_name"]),
        provider_type=str(payload["provider_type"]),
        readiness_level=str(payload.get("readiness_level", "L2_PROVIDER_READINESS_FOUNDATION")),
        future_scope=str(payload.get("future_scope", "planned")),
        business_owner_role=str(payload.get("business_owner_role", "integration_admin")),
        technical_owner_role=str(payload.get("technical_owner_role", "integration_admin")),
        security_owner_role=str(payload.get("security_owner_role", "security_admin")),
        auditor_visibility=bool(payload.get("auditor_visibility", True)),
        executive_visibility=bool(payload.get("executive_visibility", True)),
        payload_json=dict(payload),
        created_by_user_id=actor_user_id,
        updated_by_user_id=actor_user_id,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_provider_registry(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]) -> models.ProviderRegistry:
    record = _require(get_provider_registry(db, tenant_id, record_id), tenant_id, "provider_registry", record_id)
    record.provider_name = str(payload.get("provider_name", record.provider_name))
    record.provider_type = str(payload.get("provider_type", record.provider_type))
    record.readiness_level = str(payload.get("readiness_level", record.readiness_level))
    record.future_scope = str(payload.get("future_scope", record.future_scope))
    record.payload_json = {**dict(record.payload_json or {}), **dict(payload)}
    record.updated_by_user_id = actor_user_id
    record.updated_at = _now()
    db.commit()
    db.refresh(record)
    return record


def _list_by_provider(db: Session, model, tenant_id: int, provider_id: str) -> list[object]:
    return list(
        db.execute(
            select(model).where(model.tenant_id == validate_tenant_id_provided(tenant_id), model.provider_id == provider_id).order_by(model.id.asc())
        ).scalars().all()
    )


def _get_by_id(db: Session, model, tenant_id: int, record_id: int):
    return db.execute(
        select(model).where(model.tenant_id == validate_tenant_id_provided(tenant_id), model.id == record_id)
    ).scalar_one_or_none()


def _create_record(db: Session, model, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any], *, status: str = "draft"):
    record = model(id=_next_id(db, model), tenant_id=tenant_id, provider_id=provider_id, **_base_payload(actor_user_id, payload, status=status, reason_code=payload.get("reason_code")))
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _update_record(db: Session, model, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any], *, allow_create: bool = False, provider_id: str | None = None):
    record = _get_by_id(db, model, tenant_id, record_id)
    if record is None and allow_create:
        record = model(id=record_id or _next_id(db, model), tenant_id=tenant_id, provider_id=provider_id or payload.get("provider_id", "UNKNOWN"), **_base_payload(actor_user_id, payload, status=payload.get("status", "draft"), reason_code=payload.get("reason_code")))
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    record = _require(record, tenant_id, model.__tablename__, record_id)
    record.status = str(payload.get("status", record.status))
    record.reason_code = payload.get("reason_code", record.reason_code)
    record.payload_json = {**dict(record.payload_json or {}), **dict(payload)}
    record.updated_by_user_id = actor_user_id
    record.updated_at = _now()
    db.commit()
    db.refresh(record)
    return record


def _delete_record(db: Session, model, tenant_id: int, record_id: int) -> None:
    record = _require(_get_by_id(db, model, tenant_id, record_id), tenant_id, model.__tablename__, record_id)
    db.delete(record)
    db.commit()


def list_profiles(db: Session, tenant_id: int, provider_id: str):
    return _list_by_provider(db, models.ProviderProfileVersion, tenant_id, provider_id)


def get_profile(db: Session, tenant_id: int, record_id: int):
    return _get_by_id(db, models.ProviderProfileVersion, tenant_id, record_id)


def create_profile(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    return _create_record(db, models.ProviderProfileVersion, tenant_id, provider_id, actor_user_id, payload, status="profile_defined")


def update_profile(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]):
    return _update_record(db, models.ProviderProfileVersion, tenant_id, record_id, actor_user_id, payload)


def delete_profile(db: Session, tenant_id: int, record_id: int) -> None:
    _delete_record(db, models.ProviderProfileVersion, tenant_id, record_id)


def list_capabilities(db: Session, tenant_id: int, provider_id: str):
    return _list_by_provider(db, models.ProviderCapabilityMatrix, tenant_id, provider_id)


def get_capability(db: Session, tenant_id: int, record_id: int):
    return _get_by_id(db, models.ProviderCapabilityMatrix, tenant_id, record_id)


def create_capability(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    return _create_record(db, models.ProviderCapabilityMatrix, tenant_id, provider_id, actor_user_id, payload, status="capability_defined")


def update_capability(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]):
    return _update_record(db, models.ProviderCapabilityMatrix, tenant_id, record_id, actor_user_id, payload)


def list_assessments(db: Session, tenant_id: int, provider_id: str):
    return _list_by_provider(db, models.ProviderReadinessAssessment, tenant_id, provider_id)


def get_assessment(db: Session, tenant_id: int, record_id: int):
    return _get_by_id(db, models.ProviderReadinessAssessment, tenant_id, record_id)


def create_assessment(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    assessment = _create_record(db, models.ProviderReadinessAssessment, tenant_id, provider_id, actor_user_id, payload, status="assessment_recorded")
    db.add(models.ProviderReadinessAssessmentScore(id=_next_id(db, models.ProviderReadinessAssessmentScore), tenant_id=tenant_id, provider_id=provider_id, **_base_payload(actor_user_id, {"assessment_id": assessment.id, "score": payload.get("score", 0)}, status="score_recorded")))
    db.commit()
    db.refresh(assessment)
    return assessment


def update_assessment(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]):
    return _update_record(db, models.ProviderReadinessAssessment, tenant_id, record_id, actor_user_id, payload)


def list_evidence(db: Session, tenant_id: int, provider_id: str):
    return _list_by_provider(db, models.ProviderEvidenceItem, tenant_id, provider_id)


def get_evidence(db: Session, tenant_id: int, record_id: int):
    return _get_by_id(db, models.ProviderEvidenceItem, tenant_id, record_id)


def list_evidence_links(db: Session, tenant_id: int, provider_id: str):
    return _list_by_provider(db, models.ProviderEvidenceLink, tenant_id, provider_id)


def create_evidence(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    return _create_record(db, models.ProviderEvidenceItem, tenant_id, provider_id, actor_user_id, payload, status="evidence_recorded")


def create_evidence_link(db: Session, tenant_id: int, evidence_id: int, actor_user_id: str, payload: dict[str, Any]):
    evidence = _require(get_evidence(db, tenant_id, evidence_id), tenant_id, "provider_evidence_item", evidence_id)
    return _create_record(db, models.ProviderEvidenceLink, tenant_id, evidence.provider_id, actor_user_id, {**payload, "evidence_id": evidence_id}, status="link_recorded")


def update_evidence(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]):
    return _update_record(db, models.ProviderEvidenceItem, tenant_id, record_id, actor_user_id, payload)


def list_compliance_reviews(db: Session, tenant_id: int, provider_id: str):
    return _list_by_provider(db, models.ProviderComplianceReview, tenant_id, provider_id)


def list_security_reviews(db: Session, tenant_id: int, provider_id: str):
    return _list_by_provider(db, models.ProviderSecurityReview, tenant_id, provider_id)


def create_compliance_review(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    return _create_record(db, models.ProviderComplianceReview, tenant_id, provider_id, actor_user_id, payload, status="review_pending")


def update_compliance_review(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]):
    return _update_record(db, models.ProviderComplianceReview, tenant_id, record_id, actor_user_id, payload)


def upsert_security_review(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]):
    provider_id = str(payload.get("provider_id", "UNKNOWN"))
    return _update_record(db, models.ProviderSecurityReview, tenant_id, record_id, actor_user_id, payload, allow_create=True, provider_id=provider_id)


def list_risks(db: Session, tenant_id: int, provider_id: str):
    return _list_by_provider(db, models.ProviderRiskRegister, tenant_id, provider_id)


def list_exceptions(db: Session, tenant_id: int, provider_id: str):
    return _list_by_provider(db, models.ProviderExceptionCase, tenant_id, provider_id)


def create_risk(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    risk = _create_record(db, models.ProviderRiskRegister, tenant_id, provider_id, actor_user_id, payload, status="risk_open")
    db.add(models.ProviderRiskEvent(id=_next_id(db, models.ProviderRiskEvent), tenant_id=tenant_id, provider_id=provider_id, **_base_payload(actor_user_id, {"risk_id": risk.id, "event": "risk_created"}, status="risk_event")))
    db.commit()
    db.refresh(risk)
    return risk


def update_exception(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]):
    exception = _update_record(db, models.ProviderExceptionCase, tenant_id, record_id, actor_user_id, payload, allow_create=True, provider_id=str(payload.get("provider_id", "UNKNOWN")))
    db.add(models.ProviderExceptionAction(id=_next_id(db, models.ProviderExceptionAction), tenant_id=tenant_id, provider_id=exception.provider_id, **_base_payload(actor_user_id, {"exception_id": exception.id, "action": payload.get("action", "updated")}, status="exception_action")))
    db.commit()
    db.refresh(exception)
    return exception


def list_audits(db: Session, tenant_id: int, provider_id: str):
    return _list_by_provider(db, models.ProviderAuditRecord, tenant_id, provider_id)


def append_audit(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    return _create_record(db, models.ProviderAuditRecord, tenant_id, provider_id, actor_user_id, payload, status="audit_recorded")


def list_health_snapshots(db: Session, tenant_id: int, provider_id: str | None = None):
    if provider_id is None:
        return list(db.execute(select(models.ProviderHealthSnapshot).where(models.ProviderHealthSnapshot.tenant_id == validate_tenant_id_provided(tenant_id))).scalars().all())
    return _list_by_provider(db, models.ProviderHealthSnapshot, tenant_id, provider_id)


def create_health_snapshot(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    return _create_record(db, models.ProviderHealthSnapshot, tenant_id, provider_id, actor_user_id, payload, status="health_snapshot_recorded")


def list_plans(db: Session, tenant_id: int, provider_id: str):
    return _list_by_provider(db, models.ProviderIntegrationPlan, tenant_id, provider_id)


def create_plan(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    plan = _create_record(db, models.ProviderIntegrationPlan, tenant_id, provider_id, actor_user_id, payload, status="plan_defined")
    dependency = models.ProviderDependencyEdge(id=_next_id(db, models.ProviderDependencyEdge), tenant_id=tenant_id, provider_id=provider_id, **_base_payload(actor_user_id, {"plan_id": plan.id, "dependency": payload.get("dependency", "none")}, status="dependency_recorded"))
    db.add(dependency)
    db.commit()
    db.refresh(plan)
    return plan


def delete_plan(db: Session, tenant_id: int, record_id: int) -> None:
    _delete_record(db, models.ProviderIntegrationPlan, tenant_id, record_id)


def list_dashboard_snapshots(db: Session, tenant_id: int):
    return list(db.execute(select(models.ProviderDashboardSnapshot).where(models.ProviderDashboardSnapshot.tenant_id == validate_tenant_id_provided(tenant_id))).scalars().all())


def create_dashboard_snapshot(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    snapshot = _create_record(db, models.ProviderDashboardSnapshot, tenant_id, provider_id, actor_user_id, payload, status="dashboard_published")
    db.add(models.ProviderReportArtifact(id=_next_id(db, models.ProviderReportArtifact), tenant_id=tenant_id, provider_id=provider_id, **_base_payload(actor_user_id, {"snapshot_id": snapshot.id, "artifact": payload.get("artifact", "dashboard")}, status="artifact_recorded")))
    db.commit()
    db.refresh(snapshot)
    return snapshot


def create_role_assignment(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    return _create_record(db, models.ProviderRoleAssignment, tenant_id, provider_id, actor_user_id, payload, status="assignment_recorded")


def create_policy_violation(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]):
    return _create_record(db, models.ProviderPolicyViolation, tenant_id, provider_id, actor_user_id, payload, status="policy_violation_recorded")


def dashboard_counts(db: Session, tenant_id: int) -> dict[str, int]:
    tenant_id = validate_tenant_id_provided(tenant_id)
    return {
        "providers": db.scalar(select(func.count()).select_from(models.ProviderRegistry).where(models.ProviderRegistry.tenant_id == tenant_id)) or 0,
        "assessments": db.scalar(select(func.count()).select_from(models.ProviderReadinessAssessment).where(models.ProviderReadinessAssessment.tenant_id == tenant_id)) or 0,
        "evidence": db.scalar(select(func.count()).select_from(models.ProviderEvidenceItem).where(models.ProviderEvidenceItem.tenant_id == tenant_id)) or 0,
        "risks": db.scalar(select(func.count()).select_from(models.ProviderRiskRegister).where(models.ProviderRiskRegister.tenant_id == tenant_id)) or 0,
        "exceptions": db.scalar(select(func.count()).select_from(models.ProviderExceptionCase).where(models.ProviderExceptionCase.tenant_id == tenant_id)) or 0,
        "plans": db.scalar(select(func.count()).select_from(models.ProviderIntegrationPlan).where(models.ProviderIntegrationPlan.tenant_id == tenant_id)) or 0,
    }
