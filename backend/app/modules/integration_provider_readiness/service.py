"""Service layer for Integration Provider Readiness backend foundation."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError, validate_tenant_id_provided
from app.modules.integration_provider_readiness import CONTRACT_VERSION, DASHBOARD_NAMES, EXPECTED_PROVIDER_COUNT, MODULE_NAME, PROVIDER_CONNECTED, PROVIDER_CATALOG, READINESS_ONLY
from app.modules.integration_provider_readiness import permissions, repository


def _validate_actor(actor_user_id: str | None) -> str:
    actor = str(actor_user_id or "").strip()
    if not actor:
        raise DomainValidationError("actor_user_id is required")
    return actor


def _record_payload(record: object, record_type: str) -> dict[str, Any]:
    base = {
        "id": int(getattr(record, "id")),
        "tenant_id": int(getattr(record, "tenant_id")),
        "provider_id": str(getattr(record, "provider_id")),
        "record_type": record_type,
        "status": str(getattr(record, "status")),
        "payload": dict(getattr(record, "payload_json", {}) or {}),
        "readiness_only": bool(getattr(record, "readiness_only", True)),
        "provider_connected": bool(getattr(record, "provider_connected", False)),
        "live_provider_calls": bool(getattr(record, "live_provider_calls", False)),
        "credentials_stored": bool(getattr(record, "credentials_stored", False)),
        "external_submission": bool(getattr(record, "external_submission", False)),
        "sync_execution": bool(getattr(record, "sync_execution", False)),
        "fake_health_metrics": bool(getattr(record, "fake_health_metrics", False)),
        "fake_readiness_metrics": bool(getattr(record, "fake_readiness_metrics", False)),
    }
    if hasattr(record, "provider_name"):
        base["payload"].update(
            {
                "provider_name": getattr(record, "provider_name"),
                "provider_type": getattr(record, "provider_type"),
                "readiness_level": getattr(record, "readiness_level"),
                "future_scope": getattr(record, "future_scope"),
                "business_owner_role": getattr(record, "business_owner_role"),
                "technical_owner_role": getattr(record, "technical_owner_role"),
                "security_owner_role": getattr(record, "security_owner_role"),
            }
        )
    return base


def _list_payload(items: list[object], record_type: str) -> dict[str, Any]:
    return {"items": [_record_payload(item, record_type) for item in items], "total": len(items)}


def ensure_provider_foundation(db: Session, tenant_id: int) -> None:
    repository.ensure_provider_catalog(db, validate_tenant_id_provided(tenant_id))


def list_provider_registry(db: Session, tenant_id: int, provider_type: str | None = None) -> dict[str, Any]:
    ensure_provider_foundation(db, tenant_id)
    return _list_payload(repository.list_provider_registry(db, tenant_id, provider_type), "provider_registry")


def get_provider_registry(db: Session, tenant_id: int, record_id: int) -> dict[str, Any]:
    ensure_provider_foundation(db, tenant_id)
    record = repository.get_provider_registry(db, tenant_id, record_id)
    if record is None:
        raise TenantResourceNotFoundError(f"provider_registry {record_id} not found for tenant {tenant_id}")
    return _record_payload(record, "provider_registry")


def create_provider_registry(db: Session, tenant_id: int, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    record = repository.create_provider_registry(db, validate_tenant_id_provided(tenant_id), _validate_actor(actor_user_id), payload)
    repository.create_role_assignment(db, tenant_id, record.provider_id, actor_user_id, {"business_owner_role": record.business_owner_role})
    return _record_payload(record, "provider_registry")


def update_provider_registry(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    record = repository.update_provider_registry(db, validate_tenant_id_provided(tenant_id), record_id, _validate_actor(actor_user_id), payload)
    return _record_payload(record, "provider_registry")


def list_profiles(db: Session, tenant_id: int, provider_id: str) -> dict[str, Any]:
    ensure_provider_foundation(db, tenant_id)
    return _list_payload(repository.list_profiles(db, tenant_id, provider_id), "provider_profile")


def get_profile(db: Session, tenant_id: int, record_id: int) -> dict[str, Any]:
    record = repository.get_profile(db, tenant_id, record_id)
    if record is None:
        raise TenantResourceNotFoundError(f"provider_profile {record_id} not found for tenant {tenant_id}")
    return _record_payload(record, "provider_profile")


def create_provider_profile(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    record = repository.create_profile(db, validate_tenant_id_provided(tenant_id), provider_id, _validate_actor(actor_user_id), payload)
    return _record_payload(record, "provider_profile")


def update_provider_profile(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.update_profile(db, tenant_id, record_id, _validate_actor(actor_user_id), payload), "provider_profile")


def delete_provider_profile(db: Session, tenant_id: int, record_id: int) -> None:
    repository.delete_profile(db, validate_tenant_id_provided(tenant_id), record_id)


def list_capabilities(db: Session, tenant_id: int, provider_id: str) -> dict[str, Any]:
    return _list_payload(repository.list_capabilities(db, tenant_id, provider_id), "provider_capability")


def get_capability(db: Session, tenant_id: int, record_id: int) -> dict[str, Any]:
    record = repository.get_capability(db, tenant_id, record_id)
    if record is None:
        raise TenantResourceNotFoundError(f"provider_capability {record_id} not found for tenant {tenant_id}")
    return _record_payload(record, "provider_capability")


def upsert_capability_matrix(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.create_capability(db, validate_tenant_id_provided(tenant_id), provider_id, _validate_actor(actor_user_id), payload), "provider_capability")


def update_capability_matrix(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.update_capability(db, tenant_id, record_id, _validate_actor(actor_user_id), payload), "provider_capability")


def list_readiness_assessments(db: Session, tenant_id: int, provider_id: str) -> dict[str, Any]:
    return _list_payload(repository.list_assessments(db, tenant_id, provider_id), "provider_assessment")


def get_readiness_assessment(db: Session, tenant_id: int, record_id: int) -> dict[str, Any]:
    record = repository.get_assessment(db, tenant_id, record_id)
    if record is None:
        raise TenantResourceNotFoundError(f"provider_assessment {record_id} not found for tenant {tenant_id}")
    return _record_payload(record, "provider_assessment")


def create_readiness_assessment(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.create_assessment(db, validate_tenant_id_provided(tenant_id), provider_id, _validate_actor(actor_user_id), payload), "provider_assessment")


def update_readiness_assessment(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.update_assessment(db, tenant_id, record_id, _validate_actor(actor_user_id), payload), "provider_assessment")


def list_evidence(db: Session, tenant_id: int, provider_id: str) -> dict[str, Any]:
    return _list_payload(repository.list_evidence(db, tenant_id, provider_id), "provider_evidence")


def get_evidence(db: Session, tenant_id: int, record_id: int) -> dict[str, Any]:
    record = repository.get_evidence(db, tenant_id, record_id)
    if record is None:
        raise TenantResourceNotFoundError(f"provider_evidence {record_id} not found for tenant {tenant_id}")
    return _record_payload(record, "provider_evidence")


def list_evidence_links(db: Session, tenant_id: int, provider_id: str) -> dict[str, Any]:
    return _list_payload(repository.list_evidence_links(db, tenant_id, provider_id), "provider_evidence_link")


def collect_evidence(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.create_evidence(db, validate_tenant_id_provided(tenant_id), provider_id, _validate_actor(actor_user_id), payload), "provider_evidence")


def link_evidence(db: Session, tenant_id: int, evidence_id: int, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.create_evidence_link(db, validate_tenant_id_provided(tenant_id), evidence_id, _validate_actor(actor_user_id), payload), "provider_evidence_link")


def update_evidence(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.update_evidence(db, tenant_id, record_id, _validate_actor(actor_user_id), payload), "provider_evidence")


def list_compliance_reviews(db: Session, tenant_id: int, provider_id: str) -> dict[str, Any]:
    return _list_payload(repository.list_compliance_reviews(db, tenant_id, provider_id), "provider_compliance_review")


def list_security_reviews(db: Session, tenant_id: int, provider_id: str) -> dict[str, Any]:
    return _list_payload(repository.list_security_reviews(db, tenant_id, provider_id), "provider_security_review")


def review_compliance(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.create_compliance_review(db, validate_tenant_id_provided(tenant_id), provider_id, _validate_actor(actor_user_id), payload), "provider_compliance_review")


def approve_compliance(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.update_compliance_review(db, tenant_id, record_id, _validate_actor(actor_user_id), payload), "provider_compliance_review")


def review_security(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.upsert_security_review(db, validate_tenant_id_provided(tenant_id), record_id, _validate_actor(actor_user_id), payload), "provider_security_review")


def list_risks(db: Session, tenant_id: int, provider_id: str) -> dict[str, Any]:
    return _list_payload(repository.list_risks(db, tenant_id, provider_id), "provider_risk")


def list_exceptions(db: Session, tenant_id: int, provider_id: str) -> dict[str, Any]:
    return _list_payload(repository.list_exceptions(db, tenant_id, provider_id), "provider_exception")


def escalate_risk_exception(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.create_risk(db, validate_tenant_id_provided(tenant_id), provider_id, _validate_actor(actor_user_id), payload), "provider_risk")


def update_exception_case(db: Session, tenant_id: int, record_id: int, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.update_exception(db, validate_tenant_id_provided(tenant_id), record_id, _validate_actor(actor_user_id), payload), "provider_exception")


def list_audit_records(db: Session, tenant_id: int, provider_id: str) -> dict[str, Any]:
    return _list_payload(repository.list_audits(db, tenant_id, provider_id), "provider_audit")


def record_provider_audit_review(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.append_audit(db, validate_tenant_id_provided(tenant_id), provider_id, _validate_actor(actor_user_id), payload), "provider_audit")


def generate_provider_health_visibility(db: Session, tenant_id: int, provider_id: str, actor_user_id: str = "system") -> dict[str, Any]:
    snapshots = repository.list_health_snapshots(db, validate_tenant_id_provided(tenant_id), provider_id)
    if not snapshots:
        repository.create_health_snapshot(db, tenant_id, provider_id, actor_user_id, {"source": "generated", "readiness_only": True})
        snapshots = repository.list_health_snapshots(db, tenant_id, provider_id)
    return _list_payload(snapshots, "provider_health_snapshot")


def list_health_snapshots(db: Session, tenant_id: int) -> dict[str, Any]:
    ensure_provider_foundation(db, tenant_id)
    if not repository.list_health_snapshots(db, tenant_id):
        for item in PROVIDER_CATALOG:
            repository.create_health_snapshot(db, tenant_id, str(item["provider_id"]), "system", {"dashboard_ready": True})
    return _list_payload(repository.list_health_snapshots(db, tenant_id), "provider_health_snapshot")


def get_health_summary(db: Session, tenant_id: int) -> dict[str, Any]:
    ensure_provider_foundation(db, tenant_id)
    counts = repository.dashboard_counts(db, tenant_id)
    return {
        "tenant_id": validate_tenant_id_provided(tenant_id),
        "total_providers": EXPECTED_PROVIDER_COUNT,
        "readiness_only": READINESS_ONLY,
        "fake_metrics": False,
        "provider_connected": PROVIDER_CONNECTED,
        "live_provider_calls": False,
        "external_submission": False,
        "data": counts,
    }


def list_integration_plans(db: Session, tenant_id: int, provider_id: str) -> dict[str, Any]:
    return _list_payload(repository.list_plans(db, tenant_id, provider_id), "provider_integration_plan")


def plan_integration_roadmap(db: Session, tenant_id: int, provider_id: str, actor_user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _record_payload(repository.create_plan(db, validate_tenant_id_provided(tenant_id), provider_id, _validate_actor(actor_user_id), payload), "provider_integration_plan")


def get_roadmap_summary(db: Session, tenant_id: int) -> dict[str, Any]:
    counts = repository.dashboard_counts(db, tenant_id)
    return {
        "items": [
            {
                "dashboard_name": "Integration Roadmap",
                "required_permission": permissions.DASHBOARD_ROADMAP_READ,
                "tenant_scope": "tenant-scoped",
                "readiness_only": True,
                "fake_metrics": False,
                "provider_connected": False,
                "live_provider_calls": False,
                "external_submission": False,
                "data": {"plans": counts["plans"], "exceptions": counts["exceptions"]},
            }
        ],
        "total": 1,
    }


def delete_integration_plan(db: Session, tenant_id: int, record_id: int) -> None:
    repository.delete_plan(db, validate_tenant_id_provided(tenant_id), record_id)


def _dashboard_payload(name: str, permission_slug: str, counts: dict[str, int]) -> dict[str, Any]:
    data = {
        "Provider Overview": {"providers": counts["providers"], "assessments": counts["assessments"]},
        "Provider Readiness": {"providers": counts["providers"], "assessments": counts["assessments"]},
        "Capability Matrix": {"providers": counts["providers"], "evidence": counts["evidence"]},
        "Risk Dashboard": {"risks": counts["risks"], "exceptions": counts["exceptions"]},
        "Evidence Dashboard": {"evidence": counts["evidence"], "assessments": counts["assessments"]},
        "Integration Roadmap": {"plans": counts["plans"], "exceptions": counts["exceptions"]},
    }[name]
    return {
        "dashboard_name": name,
        "required_permission": permission_slug,
        "tenant_scope": "tenant-scoped",
        "readiness_only": True,
        "fake_metrics": False,
        "provider_connected": False,
        "live_provider_calls": False,
        "external_submission": False,
        "data": data,
    }


def publish_dashboard_bundle(db: Session, tenant_id: int, actor_user_id: str = "system") -> dict[str, Any]:
    ensure_provider_foundation(db, tenant_id)
    counts = repository.dashboard_counts(db, tenant_id)
    if counts["providers"] == 0:
        counts = repository.dashboard_counts(db, tenant_id)
    permission_map = {
        "Provider Overview": permissions.DASHBOARD_OVERVIEW_READ,
        "Provider Readiness": permissions.DASHBOARD_READINESS_READ,
        "Capability Matrix": permissions.DASHBOARD_READINESS_READ,
        "Risk Dashboard": permissions.DASHBOARD_RISK_READ,
        "Evidence Dashboard": permissions.DASHBOARD_RISK_READ,
        "Integration Roadmap": permissions.DASHBOARD_ROADMAP_READ,
    }
    snapshots = []
    for item in PROVIDER_CATALOG[:1]:
        snapshots.append(repository.create_dashboard_snapshot(db, tenant_id, str(item["provider_id"]), actor_user_id, {"bundle": True, "dashboard_count": len(DASHBOARD_NAMES)}))
    del snapshots
    return {
        "items": [_dashboard_payload(name, permission_map[name], counts) for name in DASHBOARD_NAMES],
        "total": len(DASHBOARD_NAMES),
    }


def get_dashboard_contract(db: Session, tenant_id: int, dashboard_name: str) -> dict[str, Any]:
    dashboards = publish_dashboard_bundle(db, tenant_id)
    for item in dashboards["items"]:
        if item["dashboard_name"].lower() == dashboard_name.lower().replace("-", " "):
            return item
    raise TenantResourceNotFoundError(f"dashboard {dashboard_name} not found for tenant {tenant_id}")
