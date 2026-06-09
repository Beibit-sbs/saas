"""Research / Science service layer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.publication_registry.service import get_publication_registry_foundation_contract
from app.modules.research.service import get_research_health_snapshot
from app.modules.research_ethics.service import list_ethics_reviews
from app.modules.research_grants.service import evaluate_research_grants_readiness
from app.modules.research_projects.service import get_research_projects_foundation_contract
from app.modules.research_science import permissions, repository
from app.modules.research_science.dependencies import validate_tenant_id
from app.modules.research_science.models import (
    AUTONOMY_MODE,
    CONTRACT_VERSION,
    DATA_SOURCE,
    FOUNDATION_STATUS,
    MASTER_MATRIX_COMMIT,
    MASTER_MATRIX_ROW_COUNT,
    MODULE_NAME,
    PRODUCT_VERTICAL,
    RESEARCH_SCIENCE_CAPABILITY_COUNT,
    RUNTIME_MODE,
    SOURCE_PRODUCT_MAP_COMMIT,
    SOURCE_SPEC_COMMIT,
    TARGET_LEVEL,
    ResearchAuditEventType,
)
from app.modules.research_science.schemas import (
    ResearchBrainContextResponse,
    ResearchBrainContextSourceResponse,
    ResearchBrainKpiSurfaceResponse,
    ResearchBrainOrchestrationItemResponse,
    ResearchBrainOrchestrationResponse,
    ResearchBrainRbacValidationResponse,
    ResearchBrainRoleValidationResponse,
    ResearchBrainShellResponse,
    ResearchBrainSignalItemResponse,
    ResearchBrainSignalSurfaceResponse,
    ResearchScienceDashboardResponse,
    ResearchScienceHealthResponse,
    ResearchScienceLimitationsResponse,
    ResearchScienceMatrixSummaryResponse,
)


MASTER_MATRIX_COMMIT = MASTER_MATRIX_COMMIT
MASTER_MATRIX_ROW_COUNT = MASTER_MATRIX_ROW_COUNT
SOURCE_SPEC_COMMIT = SOURCE_SPEC_COMMIT
SOURCE_PRODUCT_MAP_COMMIT = SOURCE_PRODUCT_MAP_COMMIT
RESEARCH_SCIENCE_CAPABILITY_COUNT = RESEARCH_SCIENCE_CAPABILITY_COUNT
RUNTIME_MODE = RUNTIME_MODE
DATA_SOURCE = DATA_SOURCE
PROVIDER_INTEGRATION_ENABLED = False
EXTERNAL_DATABASE_SYNC_ENABLED = False
OFFICIAL_VERIFICATION_ENABLED = False
AUTONOMOUS_DECISION_ENABLED = False
HIDDEN_SCORE_PRESENT = False
FAKE_METRICS = False
HUMAN_REVIEW_REQUIRED = True
EXPECTED_ROUTE_COUNT = 43
EXPECTED_TABLE_COUNT = 15
READ_ONLY_FIRST = True
MUTATION_ALLOWED = False

BRIDGE_TARGETS = {
    "EXECUTIVE_GOVERNANCE",
    "QUALITY_ACCREDITATION",
    "STUDENT_LIFECYCLE",
    "ACADEMIC_OPERATIONS",
    "LIBRARY_REPOSITORY",
    "DOCUMENT_WORKFLOW",
    "FINANCE_PROCUREMENT",
    "INTEGRATION_PROVIDER",
}

FORBIDDEN_RUNTIME_CLAIMS = [
    "researcher_score",
    "citation_score",
    "official_ranking",
    "provider_sync",
    "external_database_sync",
    "autonomous_ethics_approval",
    "autonomous_grant_submission",
    "autonomous_publication_verification",
]

REQUIRED_LIMITATIONS = [
    "metadata_only_foundation",
    "evidence_metadata_only",
    "no_provider_integration",
    "no_external_database_sync",
    "no_official_verification",
    "human_review_required",
]


def _now() -> datetime:
    return datetime.now(UTC)


def _validate_actor(actor_user_id: str | int | None) -> str:
    actor = str(actor_user_id or "").strip()
    if not actor:
        raise DomainValidationError("actor_user_id is required")
    return actor


def _commit(db: Session):
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _merge_limitations(values: list[str] | None) -> list[str]:
    merged = list(values or [])
    for item in REQUIRED_LIMITATIONS:
        if item not in merged:
            merged.append(item)
    return merged


def _base_safety_defaults(actor: str | None = None, source_capability_id: str | None = None, source_matrix_row_id: str | None = None) -> dict[str, Any]:
    return {
        "human_review_required": True,
        "autonomous_decision": False,
        "provider_integration_enabled": False,
        "external_database_sync_enabled": False,
        "official_verification_enabled": False,
        "hidden_score_present": False,
        "incomplete_data": True,
        "created_by_user_id": actor,
        "updated_by_user_id": actor,
        "source_capability_id": source_capability_id,
        "source_matrix_row_id": source_matrix_row_id,
    }


def _publication_safety() -> dict[str, Any]:
    return {
        "fake_publication": False,
        "autonomous_publication_verification_enabled": False,
    }


def _conference_safety() -> dict[str, Any]:
    return {"fake_certificate": False}


def _grant_safety() -> dict[str, Any]:
    return {
        "fake_grant_evidence": False,
        "autonomous_grant_submission_enabled": False,
    }


def _ethics_safety() -> dict[str, Any]:
    return {"autonomous_ethics_approval_enabled": False}


def _evidence_safety() -> dict[str, Any]:
    return {
        "fake_evidence": False,
        "provider_verified": False,
    }


def _bridge_safety() -> dict[str, Any]:
    return {
        "read_only_first": True,
        "mutation_allowed": False,
        "provider_sync_enabled": False,
        "external_submission_enabled": False,
    }


def _create_payload(request, actor: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = request.model_dump(exclude_none=True)
    payload["limitations_json"] = _merge_limitations(payload.pop("limitations", None))
    payload["metadata_json"] = payload.pop("metadata", {})
    return payload | _base_safety_defaults(actor, payload.get("source_capability_id"), payload.get("source_matrix_row_id")) | (extra or {})


def _update_payload(request, actor: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = request.model_dump(exclude_none=True)
    payload["limitations_json"] = _merge_limitations(payload.pop("limitations", None))
    if "metadata" in payload:
        payload["metadata_json"] = payload.pop("metadata")
    payload["updated_by_user_id"] = actor
    payload["autonomous_decision"] = False
    payload["provider_integration_enabled"] = False
    payload["external_database_sync_enabled"] = False
    payload["official_verification_enabled"] = False
    payload["hidden_score_present"] = False
    payload["incomplete_data"] = True
    return payload | (extra or {})


def _audit(
    db: Session,
    tenant_id: int,
    *,
    source_entity_type: str,
    source_entity_id: int | None,
    event_type: str,
    actor_user_id: str,
    previous_status: str | None = None,
    new_status: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    repository.create_research_audit_event(
        db,
        tenant_id,
        event_type=event_type,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        actor_user_id=actor_user_id,
        previous_status=previous_status,
        new_status=new_status,
        payload_json=payload or {},
        human_review_required=True,
        autonomous_decision=False,
        provider_integration_enabled=False,
        hidden_score_present=False,
    )


def _status_history(db: Session, tenant_id: int, *, source_entity_type: str, source_entity_id: int | None, previous_status: str | None, new_status: str, actor_user_id: str, reason: str | None = None) -> None:
    repository.create_status_history(
        db,
        tenant_id,
        source_entity_type=source_entity_type,
        source_entity_id=source_entity_id,
        previous_status=previous_status,
        new_status=new_status,
        changed_by_user_id=actor_user_id,
        reason=reason,
        metadata_json={},
        human_review_required=True,
    )


def _after_create(db: Session, tenant_id: int, actor: str, *, source_entity_type: str, entity, event_type: str) -> None:
    _audit(db, tenant_id, source_entity_type=source_entity_type, source_entity_id=entity.id, event_type=event_type, actor_user_id=actor, previous_status=None, new_status=entity.status)
    _status_history(db, tenant_id, source_entity_type=source_entity_type, source_entity_id=entity.id, previous_status=None, new_status=entity.status, actor_user_id=actor, reason="created")
    _commit(db)


def _after_update(db: Session, tenant_id: int, actor: str, *, source_entity_type: str, current, entity, event_type: str) -> None:
    _audit(db, tenant_id, source_entity_type=source_entity_type, source_entity_id=entity.id, event_type=event_type, actor_user_id=actor, previous_status=current.status, new_status=entity.status)
    if current.status != entity.status:
        _status_history(db, tenant_id, source_entity_type=source_entity_type, source_entity_id=entity.id, previous_status=current.status, new_status=entity.status, actor_user_id=actor, reason="status_changed")
    _commit(db)


def create_research_project_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_research_project(db, tenant_id, **_create_payload(request, actor))
    _after_create(db, tenant_id, actor, source_entity_type="research_project", entity=entity, event_type=ResearchAuditEventType.PROJECT_CREATED)
    return entity


def list_research_projects_service(db: Session, tenant_id: int):
    return repository.list_research_projects(db, validate_tenant_id(tenant_id))


def get_research_project_service(db: Session, tenant_id: int, project_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_research_project(db, tenant_id, project_id)
    if entity is None:
        raise DomainValidationError(f"research_project {project_id} not found in tenant scope")
    return entity


def update_research_project_service(db: Session, tenant_id: int, actor_user_id: str, project_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_research_project_service(db, tenant_id, project_id)
    entity = repository.update_research_project(db, tenant_id, project_id, **_update_payload(request, actor))
    _after_update(db, tenant_id, actor, source_entity_type="research_project", current=current, entity=entity, event_type=ResearchAuditEventType.PROJECT_UPDATED)
    return entity


def create_student_research_work_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_student_research_work(db, tenant_id, **_create_payload(request, actor))
    _after_create(db, tenant_id, actor, source_entity_type="student_research_work", entity=entity, event_type=ResearchAuditEventType.STUDENT_RESEARCH_CREATED)
    return entity


def list_student_research_work_service(db: Session, tenant_id: int):
    return repository.list_student_research_work(db, validate_tenant_id(tenant_id))


def get_student_research_work_service(db: Session, tenant_id: int, student_research_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_student_research_work(db, tenant_id, student_research_id)
    if entity is None:
        raise DomainValidationError(f"student_research_work {student_research_id} not found in tenant scope")
    return entity


def update_student_research_work_service(db: Session, tenant_id: int, actor_user_id: str, student_research_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_student_research_work_service(db, tenant_id, student_research_id)
    entity = repository.update_student_research_work(db, tenant_id, student_research_id, **_update_payload(request, actor))
    _after_update(db, tenant_id, actor, source_entity_type="student_research_work", current=current, entity=entity, event_type=ResearchAuditEventType.STUDENT_RESEARCH_UPDATED)
    return entity


def create_scientific_supervision_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_scientific_supervision(db, tenant_id, **_create_payload(request, actor))
    _after_create(db, tenant_id, actor, source_entity_type="scientific_supervision", entity=entity, event_type=ResearchAuditEventType.SUPERVISION_ASSIGNED)
    return entity


def list_scientific_supervisions_service(db: Session, tenant_id: int):
    return repository.list_scientific_supervisions(db, validate_tenant_id(tenant_id))


def get_scientific_supervision_service(db: Session, tenant_id: int, supervision_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_scientific_supervision(db, tenant_id, supervision_id)
    if entity is None:
        raise DomainValidationError(f"scientific_supervision {supervision_id} not found in tenant scope")
    return entity


def update_scientific_supervision_service(db: Session, tenant_id: int, actor_user_id: str, supervision_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_scientific_supervision_service(db, tenant_id, supervision_id)
    entity = repository.update_scientific_supervision(db, tenant_id, supervision_id, **_update_payload(request, actor))
    _after_update(db, tenant_id, actor, source_entity_type="scientific_supervision", current=current, entity=entity, event_type=ResearchAuditEventType.SUPERVISION_UPDATED)
    return entity


def create_publication_metadata_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_publication_metadata(db, tenant_id, **_create_payload(request, actor, extra=_publication_safety()))
    _after_create(db, tenant_id, actor, source_entity_type="publication_metadata", entity=entity, event_type=ResearchAuditEventType.PUBLICATION_METADATA_ADDED)
    return entity


def list_publication_metadata_service(db: Session, tenant_id: int):
    return repository.list_publication_metadata(db, validate_tenant_id(tenant_id))


def get_publication_metadata_service(db: Session, tenant_id: int, publication_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_publication_metadata(db, tenant_id, publication_id)
    if entity is None:
        raise DomainValidationError(f"publication_metadata {publication_id} not found in tenant scope")
    return entity


def update_publication_metadata_service(db: Session, tenant_id: int, actor_user_id: str, publication_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_publication_metadata_service(db, tenant_id, publication_id)
    entity = repository.update_publication_metadata(db, tenant_id, publication_id, **_update_payload(request, actor, extra=_publication_safety()))
    _after_update(db, tenant_id, actor, source_entity_type="publication_metadata", current=current, entity=entity, event_type=ResearchAuditEventType.PUBLICATION_METADATA_UPDATED)
    return entity


def create_conference_participation_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_conference_participation(db, tenant_id, **_create_payload(request, actor, extra=_conference_safety()))
    _after_create(db, tenant_id, actor, source_entity_type="conference_participation", entity=entity, event_type=ResearchAuditEventType.CONFERENCE_METADATA_ADDED)
    return entity


def list_conference_participation_service(db: Session, tenant_id: int):
    return repository.list_conference_participation(db, validate_tenant_id(tenant_id))


def get_conference_participation_service(db: Session, tenant_id: int, conference_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_conference_participation(db, tenant_id, conference_id)
    if entity is None:
        raise DomainValidationError(f"conference_participation {conference_id} not found in tenant scope")
    return entity


def update_conference_participation_service(db: Session, tenant_id: int, actor_user_id: str, conference_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_conference_participation_service(db, tenant_id, conference_id)
    entity = repository.update_conference_participation(db, tenant_id, conference_id, **_update_payload(request, actor, extra=_conference_safety()))
    _after_update(db, tenant_id, actor, source_entity_type="conference_participation", current=current, entity=entity, event_type=ResearchAuditEventType.CONFERENCE_METADATA_UPDATED)
    return entity


def create_grant_application_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_grant_application(db, tenant_id, **_create_payload(request, actor, extra=_grant_safety()))
    _after_create(db, tenant_id, actor, source_entity_type="grant_application", entity=entity, event_type=ResearchAuditEventType.GRANT_APPLICATION_ADDED)
    return entity


def list_grant_applications_service(db: Session, tenant_id: int):
    return repository.list_grant_applications(db, validate_tenant_id(tenant_id))


def get_grant_application_service(db: Session, tenant_id: int, grant_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_grant_application(db, tenant_id, grant_id)
    if entity is None:
        raise DomainValidationError(f"grant_application {grant_id} not found in tenant scope")
    return entity


def update_grant_application_service(db: Session, tenant_id: int, actor_user_id: str, grant_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_grant_application_service(db, tenant_id, grant_id)
    entity = repository.update_grant_application(db, tenant_id, grant_id, **_update_payload(request, actor, extra=_grant_safety()))
    _after_update(db, tenant_id, actor, source_entity_type="grant_application", current=current, entity=entity, event_type=ResearchAuditEventType.GRANT_APPLICATION_UPDATED)
    return entity


def create_grant_deliverable_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_grant_deliverable(db, tenant_id, **_create_payload(request, actor, extra=_grant_safety()))
    _after_create(db, tenant_id, actor, source_entity_type="grant_deliverable", entity=entity, event_type=ResearchAuditEventType.GRANT_DELIVERABLE_ADDED)
    return entity


def list_grant_deliverables_service(db: Session, tenant_id: int):
    return repository.list_grant_deliverables(db, validate_tenant_id(tenant_id))


def get_grant_deliverable_service(db: Session, tenant_id: int, deliverable_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_grant_deliverable(db, tenant_id, deliverable_id)
    if entity is None:
        raise DomainValidationError(f"grant_deliverable {deliverable_id} not found in tenant scope")
    return entity


def update_grant_deliverable_service(db: Session, tenant_id: int, actor_user_id: str, deliverable_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_grant_deliverable_service(db, tenant_id, deliverable_id)
    entity = repository.update_grant_deliverable(db, tenant_id, deliverable_id, **_update_payload(request, actor, extra=_grant_safety()))
    _after_update(db, tenant_id, actor, source_entity_type="grant_deliverable", current=current, entity=entity, event_type=ResearchAuditEventType.GRANT_APPLICATION_UPDATED)
    return entity


def create_ethics_request_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_ethics_request(db, tenant_id, **_create_payload(request, actor, extra=_ethics_safety()))
    _after_create(db, tenant_id, actor, source_entity_type="ethics_request", entity=entity, event_type=ResearchAuditEventType.ETHICS_REQUEST_CREATED)
    return entity


def list_ethics_requests_service(db: Session, tenant_id: int):
    return repository.list_ethics_requests(db, validate_tenant_id(tenant_id))


def get_ethics_request_service(db: Session, tenant_id: int, ethics_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_ethics_request(db, tenant_id, ethics_id)
    if entity is None:
        raise DomainValidationError(f"ethics_request {ethics_id} not found in tenant scope")
    return entity


def update_ethics_request_service(db: Session, tenant_id: int, actor_user_id: str, ethics_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_ethics_request_service(db, tenant_id, ethics_id)
    entity = repository.update_ethics_request(db, tenant_id, ethics_id, **_update_payload(request, actor, extra=_ethics_safety()))
    _after_update(db, tenant_id, actor, source_entity_type="ethics_request", current=current, entity=entity, event_type=ResearchAuditEventType.ETHICS_REVIEW_STATUS_UPDATED)
    return entity


def create_ethics_amendment_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_ethics_amendment(db, tenant_id, **_create_payload(request, actor))
    _after_create(db, tenant_id, actor, source_entity_type="ethics_amendment", entity=entity, event_type=ResearchAuditEventType.ETHICS_AMENDMENT_CREATED)
    return entity


def list_ethics_amendments_service(db: Session, tenant_id: int):
    return repository.list_ethics_amendments(db, validate_tenant_id(tenant_id))


def attach_research_evidence_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    payload = _create_payload(request, actor, extra=_evidence_safety())
    payload["submitted_by_user_id"] = actor
    payload["submitted_at"] = _now()
    payload["official_verification_enabled"] = False
    entity = repository.attach_research_evidence(db, tenant_id, **payload)
    _audit(db, tenant_id, source_entity_type="research_evidence", source_entity_id=entity.id, event_type=ResearchAuditEventType.EVIDENCE_ATTACHED, actor_user_id=actor, previous_status=None, new_status=entity.status)
    _commit(db)
    return entity


def get_research_evidence_service(db: Session, tenant_id: int, evidence_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_research_evidence(db, tenant_id, evidence_id)
    if entity is None:
        raise DomainValidationError(f"research_evidence {evidence_id} not found in tenant scope")
    return entity


def list_research_evidence_service(db: Session, tenant_id: int):
    return repository.list_research_evidence(db, validate_tenant_id(tenant_id))


def list_research_audit_events_service(db: Session, tenant_id: int):
    return repository.list_research_audit_events(db, validate_tenant_id(tenant_id))


def list_status_history_service(db: Session, tenant_id: int):
    return repository.list_status_history(db, validate_tenant_id(tenant_id))


def create_research_bridge_metadata_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    bridge_target = request.bridge_target
    if bridge_target not in BRIDGE_TARGETS:
        raise DomainValidationError(f"unsupported bridge_target {bridge_target}")
    entity = repository.create_research_bridge_metadata(db, tenant_id, **_create_payload(request, actor, extra=_bridge_safety()))
    _audit(db, tenant_id, source_entity_type="research_bridge", source_entity_id=entity.id, event_type=ResearchAuditEventType.BRIDGE_METADATA_ADDED, actor_user_id=actor, previous_status=None, new_status=entity.status)
    _commit(db)
    return entity


def list_research_bridge_metadata_service(db: Session, tenant_id: int):
    return repository.list_research_bridge_metadata(db, validate_tenant_id(tenant_id))


def get_research_dashboard_service(db: Session, tenant_id: int) -> ResearchScienceDashboardResponse:
    tenant_id = validate_tenant_id(tenant_id)
    summary = repository.compute_research_dashboard_summary(db, tenant_id)
    bridge_counts = repository.get_research_bridge_summary(db, tenant_id)
    incomplete = not all(summary[key] for key in [
        "projects_summary",
        "student_research_summary",
        "supervision_summary",
        "publications_summary",
        "conferences_summary",
        "grants_summary",
        "ethics_summary",
    ])
    response = ResearchScienceDashboardResponse(
        tenant_id=tenant_id,
        generated_at=_now(),
        contract_version=CONTRACT_VERSION,
        source_spec_commit=SOURCE_SPEC_COMMIT,
        master_matrix_commit=MASTER_MATRIX_COMMIT,
        master_matrix_rows=MASTER_MATRIX_ROW_COUNT,
        capability_count=RESEARCH_SCIENCE_CAPABILITY_COUNT,
        fake_metrics=False,
        data_source=DATA_SOURCE,
        incomplete_data=incomplete,
        limitations=_merge_limitations([]),
        projects_summary=summary["projects_summary"],
        student_research_summary=summary["student_research_summary"],
        supervision_summary=summary["supervision_summary"],
        publications_summary=summary["publications_summary"],
        conferences_summary=summary["conferences_summary"],
        grants_summary=summary["grants_summary"],
        ethics_summary=summary["ethics_summary"],
        evidence_summary=summary["evidence_summary"],
        bridge_summary=bridge_counts,
        brain_readiness_summary={"signal_families": 7, "safe_agents": 5},
        boundary_summary={
            "provider_integration_enabled": False,
            "external_database_sync_enabled": False,
            "official_verification_enabled": False,
            "hidden_score_present": False,
            "autonomous_decision": False,
            "human_review_required": True,
            "fake_publications": False,
            "fake_grant_evidence": False,
            "fake_conference_certificates": False,
        },
    )
    repository.create_dashboard_snapshot(
        db,
        tenant_id,
        status="ACTIVE",
        fake_metrics=False,
        incomplete_data=response.incomplete_data,
        data_source=DATA_SOURCE,
        summary_json=response.model_dump(),
        limitations_json=response.limitations,
        source_capability_id="A-037.2",
        source_matrix_row_id="A-037.2",
    )
    _audit(db, tenant_id, source_entity_type="research_dashboard", source_entity_id=None, event_type=ResearchAuditEventType.DASHBOARD_SNAPSHOT_CREATED, actor_user_id="system-dashboard", previous_status=None, new_status="ACTIVE")
    _commit(db)
    return response


def get_research_matrix_summary_service(db: Session, tenant_id: int) -> ResearchScienceMatrixSummaryResponse:
    validate_tenant_id(tenant_id)
    return ResearchScienceMatrixSummaryResponse(
        contract_version=CONTRACT_VERSION,
        source_spec_commit=SOURCE_SPEC_COMMIT,
        source_product_map_commit=SOURCE_PRODUCT_MAP_COMMIT,
        master_matrix_commit=MASTER_MATRIX_COMMIT,
        master_matrix_rows=MASTER_MATRIX_ROW_COUNT,
        capability_count=RESEARCH_SCIENCE_CAPABILITY_COUNT,
        runtime_mode=RUNTIME_MODE,
        autonomy_mode=AUTONOMY_MODE,
        route_count_expected="38-45",
        table_count_expected=EXPECTED_TABLE_COUNT,
    )


def get_research_health_service(db: Session, tenant_id: int) -> ResearchScienceHealthResponse:
    tenant_id = validate_tenant_id(tenant_id)
    health = repository.get_research_health_summary(db, tenant_id)
    return ResearchScienceHealthResponse(
        tenant_id=tenant_id,
        module=MODULE_NAME,
        target_level=TARGET_LEVEL,
        foundation_status=FOUNDATION_STATUS,
        runtime_mode=RUNTIME_MODE,
        contract_version=CONTRACT_VERSION,
        provider_integration_enabled=False,
        external_database_sync_enabled=False,
        official_verification_enabled=False,
        hidden_score_present=False,
        fake_metrics=False,
        incomplete_data=health["total_records"] == 0,
        limitations=_merge_limitations([]),
        route_count=EXPECTED_ROUTE_COUNT,
        table_count=EXPECTED_TABLE_COUNT,
    )


def list_research_limitations_service(db: Session, tenant_id: int) -> ResearchScienceLimitationsResponse:
    tenant_id = validate_tenant_id(tenant_id)
    items = repository.list_research_limitations(db, tenant_id)
    limitations = [item.limitation_text for item in items] or _merge_limitations([])
    return ResearchScienceLimitationsResponse(items=limitations)


def _sum_bucket(values: dict[str, int]) -> int:
    return sum(int(v or 0) for v in values.values())


def get_research_brain_shell_service(tenant_id: int) -> ResearchBrainShellResponse:
    tenant_id = validate_tenant_id(tenant_id)
    return ResearchBrainShellResponse(
        tenant_id=tenant_id,
        owner_module="research_science",
        runtime_boundary="UNIFIED_READ_ONLY_RUNTIME_SHELL",
        navigation_entry="/console/research-brain",
        bridge_modules=[
            "research",
            "research_projects",
            "research_grants",
            "publication_registry",
            "research_ethics",
            "analytics",
            "brain_core",
            "document_workflow",
        ],
        read_only_aggregation=True,
        provider_execution_enabled=False,
        external_calls_enabled=False,
    )


def get_research_brain_orchestration_service(db: Session, tenant_id: int) -> ResearchBrainOrchestrationResponse:
    tenant_id = validate_tenant_id(tenant_id)
    summary = repository.compute_research_dashboard_summary(db, tenant_id)
    return ResearchBrainOrchestrationResponse(
        tenant_id=tenant_id,
        projects=ResearchBrainOrchestrationItemResponse(
            source_module="research_science",
            read_only=True,
            total=_sum_bucket(summary["projects_summary"]),
            notes="Project aggregation over research_science project metadata.",
        ),
        grants=ResearchBrainOrchestrationItemResponse(
            source_module="research_science",
            read_only=True,
            total=_sum_bucket(summary["grants_summary"]),
            notes="Grant aggregation over research_science grants with research/research_grants bridge alignment.",
        ),
        publications=ResearchBrainOrchestrationItemResponse(
            source_module="research_science",
            read_only=True,
            total=_sum_bucket(summary["publications_summary"]),
            notes="Publication aggregation over research_science publications with publication_registry bridge alignment.",
        ),
        ethics=ResearchBrainOrchestrationItemResponse(
            source_module="research_ethics",
            read_only=True,
            total=_sum_bucket(summary["ethics_summary"]),
            notes="Ethics aggregation over research_ethics review pathways and research_science metadata visibility.",
        ),
        kpi=ResearchBrainOrchestrationItemResponse(
            source_module="analytics",
            read_only=True,
            total=4,
            notes="KPI exposure remains analytics-owned and read-only in shell batch.",
        ),
        signals=ResearchBrainOrchestrationItemResponse(
            source_module="brain_core",
            read_only=True,
            total=4,
            notes="Signal exposure remains brain_core-owned and read-only with no scoring engine activation.",
        ),
    )


def get_research_brain_context_service(db: Session, tenant_id: int) -> ResearchBrainContextResponse:
    tenant_id = validate_tenant_id(tenant_id)
    summary = repository.compute_research_dashboard_summary(db, tenant_id)
    research_health = get_research_health_snapshot(tenant_id).model_dump()
    publication_registry_contract = get_publication_registry_foundation_contract(tenant_id)
    research_projects_contract = get_research_projects_foundation_contract(tenant_id)
    research_grants_contract = evaluate_research_grants_readiness(tenant_id=tenant_id, grant_payload={})
    ethics_rows = list_ethics_reviews(tenant_id)

    return ResearchBrainContextResponse(
        tenant_id=tenant_id,
        context={
            "research": ResearchBrainContextSourceResponse(
                source="research",
                contract_status="ACTIVE_BRIDGE",
                read_only=True,
                summary={
                    "grants_total": research_health.get("grants_total", 0),
                    "publications_total": research_health.get("publications_total", 0),
                    "labs_total": research_health.get("labs_total", 0),
                },
            ),
            "publication_registry": ResearchBrainContextSourceResponse(
                source="publication_registry",
                contract_status=str(publication_registry_contract.get("contract_status") or "FOUNDATION_CONTRACT_READY"),
                read_only=True,
                summary={
                    "maturity_level": publication_registry_contract.get("maturity_level", "L2"),
                    "next_maturity_gap": publication_registry_contract.get("next_maturity_gap", "deterministic_service_logic_needed"),
                },
            ),
            "research_projects": ResearchBrainContextSourceResponse(
                source="research_projects",
                contract_status=str(research_projects_contract.get("contract_status") or "FOUNDATION_CONTRACT_READY"),
                read_only=True,
                summary={
                    "maturity_level": research_projects_contract.get("maturity_level", "L2"),
                    "project_total": _sum_bucket(summary["projects_summary"]),
                },
            ),
            "research_grants": ResearchBrainContextSourceResponse(
                source="research_grants",
                contract_status=str(research_grants_contract.get("evaluation_status") or "EVALUATED"),
                read_only=True,
                summary={
                    "classification": research_grants_contract.get("classification", "GRANT_INPUT_INCOMPLETE"),
                    "grants_total": _sum_bucket(summary["grants_summary"]),
                },
            ),
            "research_ethics": ResearchBrainContextSourceResponse(
                source="research_ethics",
                contract_status="ACTIVE_BRIDGE",
                read_only=True,
                summary={
                    "ethics_total": _sum_bucket(summary["ethics_summary"]),
                    "review_records": len(ethics_rows),
                },
            ),
        },
    )


def get_research_brain_kpi_surface_service(db: Session, tenant_id: int) -> ResearchBrainKpiSurfaceResponse:
    tenant_id = validate_tenant_id(tenant_id)
    summary = repository.compute_research_dashboard_summary(db, tenant_id)
    return ResearchBrainKpiSurfaceResponse(
        tenant_id=tenant_id,
        owner_module="analytics",
        publication_count=_sum_bucket(summary["publications_summary"]),
        grant_count=_sum_bucket(summary["grants_summary"]),
        project_count=_sum_bucket(summary["projects_summary"]),
        ethics_count=_sum_bucket(summary["ethics_summary"]),
        read_only=True,
        provider_execution_enabled=False,
    )


def get_research_brain_signal_surface_service(db: Session, tenant_id: int) -> ResearchBrainSignalSurfaceResponse:
    tenant_id = validate_tenant_id(tenant_id)
    summary = repository.compute_research_dashboard_summary(db, tenant_id)
    health = get_research_health_snapshot(tenant_id)
    project_delay_observed = int(summary["projects_summary"].get("ON_HOLD", 0))
    signals = [
        ResearchBrainSignalItemResponse(
            family="publication_risk",
            owner="brain_core",
            source="research.publications + research_science.publications_summary",
            consumer="research_dashboard",
            review_queue="research_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=int(health.stalled_publications),
        ),
        ResearchBrainSignalItemResponse(
            family="grant_risk",
            owner="brain_core",
            source="research_grants + research_science.grants_summary",
            consumer="grant_dashboard",
            review_queue="grants_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=int(health.grant_pipeline_at_risk),
        ),
        ResearchBrainSignalItemResponse(
            family="ethics_risk",
            owner="brain_core",
            source="research_ethics.reviews + research_science.ethics_summary",
            consumer="research_risk_dashboard",
            review_queue="ethics_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=_sum_bucket(summary["ethics_summary"]),
        ),
        ResearchBrainSignalItemResponse(
            family="project_delay",
            owner="brain_core",
            source="research_science.projects_summary + research audit/status history",
            consumer="research_operations_dashboard",
            review_queue="project_delay_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=project_delay_observed,
        ),
    ]
    return ResearchBrainSignalSurfaceResponse(tenant_id=tenant_id, signals=signals)


def get_research_brain_rbac_validation_service(tenant_id: int) -> ResearchBrainRbacValidationResponse:
    tenant_id = validate_tenant_id(tenant_id)
    role_requirements = {
        "researcher": [
            "research.read",
            "research_science.student_research.read",
            "research_science.publications.read",
        ],
        "laboratory_head": [
            "research.read",
            "research.write",
            "research_science.projects.read",
            "research_science.supervision.read",
        ],
        "project_manager": [
            "research.read",
            "research.write",
            "research_science.projects.update",
            "research_science.audit.read",
        ],
        "grant_manager": [
            "research.read",
            "research.write",
            "research_science.grants.update",
            "research_science.grant_deliverables.read",
        ],
        "ethics_reviewer": [
            "research.read",
            "research_science.ethics.read",
            "research_science.ethics.update",
            "research_science.audit.read",
        ],
        "dean": [
            "research.read",
            "research_science.dashboard.read",
            "research_science.projects.read",
            "research_science.audit.read",
        ],
        "vice_rector_science": [
            "research.read",
            "research_science.dashboard.read",
            "research_science.grants.read",
            "research_science.audit.read",
        ],
        "research_admin": [
            "research.read",
            "research.write",
            "research_science.admin.read",
            "research_science.audit.read",
        ],
    }

    available_permissions = set(permissions.ALL_PERMISSIONS)
    available_permissions.update({"research.read", "research.write"})

    roles: list[ResearchBrainRoleValidationResponse] = []
    for role, required in role_requirements.items():
        status = "PASS" if all(permission in available_permissions for permission in required) else "FAIL"
        roles.append(
            ResearchBrainRoleValidationResponse(
                role=role,
                required_permissions=required,
                status=status,
            )
        )

    rbac_pass = all(role.status == "PASS" for role in roles)
    audit_pass = "research_science.audit.read" in available_permissions

    return ResearchBrainRbacValidationResponse(
        tenant_id=tenant_id,
        tenant="PASS",
        rbac="PASS" if rbac_pass else "FAIL",
        audit="PASS" if audit_pass else "FAIL",
        roles=roles,
    )