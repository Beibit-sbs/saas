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
    CitationAnalyticsSummary,
    ExternalResearchIdentity,
    PublicationImpactProfile,
    Researcher,
    ResearcherActivityProfileResponse,
    ResearcherDashboardSummaryResponse,
    ResearcherGrantSummary,
    ResearcherListResponse,
    ResearcherProfile,
    ResearcherProjectSummary,
    ResearcherPublicationSummary,
    ResearcherRiskProfileResponse,
    ResearchRiskProfile,
    ResearchRiskSignal,
    ResearchRiskSummary,
    ResearchRiskTrend,
    ResearcherScientometricSummary,
    ResearcherRankingItem,
    ResearcherRankingResponse,
    ResearcherScientometricProfile,
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
    ScientometricTrend,
    ScientometricsSummaryResponse,
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


def _to_researcher_id(value: str | None) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _merge_unique(existing: list[str], values: list[str]) -> list[str]:
    merged = list(existing)
    for value in values:
        candidate = str(value or "").strip()
        if candidate and candidate not in merged:
            merged.append(candidate)
    return merged


def _compute_risk_level(*, active_projects: int, active_grants: int, publication_count: int, pending_ethics: int) -> str:
    if active_projects >= 5 or active_grants >= 3 or pending_ethics >= 3:
        return "HIGH"
    if active_projects >= 3 or active_grants >= 2 or publication_count == 0 or pending_ethics >= 1:
        return "MEDIUM"
    return "LOW"


def _severity_from_score(score: float) -> str:
    if score >= 80.0:
        return "CRITICAL"
    if score >= 60.0:
        return "HIGH"
    if score >= 35.0:
        return "MEDIUM"
    return "LOW"


def _trend_from_delta(current_score: float, previous_score: float) -> str:
    if current_score - previous_score >= 5.0:
        return "up"
    if previous_score - current_score >= 5.0:
        return "down"
    return "stable"


def _cap_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


class ScientometricsService:
    """Read-only scientometrics runtime with provider-ready contracts only."""

    PROVIDERS = ("ORCID", "Scopus", "WebOfScience", "GoogleScholar", "DOI")

    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = validate_tenant_id(tenant_id)

    def _provider_status(self, provider_name: str, publication_count: int) -> str:
        if provider_name == "DOI" and publication_count > 0:
            return "READY"
        if publication_count > 0:
            return "PENDING"
        return "NOT_CONNECTED"

    def _external_identities(self, researcher_id: str, publication_count: int) -> list[ExternalResearchIdentity]:
        return [
            ExternalResearchIdentity(
                provider_name=provider,
                provider_identifier=f"{provider.lower()}:{researcher_id}",
                provider_status=self._provider_status(provider, publication_count),
            )
            for provider in self.PROVIDERS
        ]

    def _publication_records(self, researcher_id: str) -> list[Any]:
        publications = repository.list_publication_metadata(self.db, self.tenant_id)
        return [item for item in publications if _to_researcher_id(getattr(item, "faculty_ref", None)) == researcher_id]

    def _top_publications(self, researcher_id: str) -> list[str]:
        records = self._publication_records(researcher_id)
        scored: list[tuple[int, str]] = []
        for item in records:
            metadata_json = getattr(item, "metadata_json", {}) or {}
            scored.append(
                (
                    int(metadata_json.get("citation_count") or 0),
                    str(getattr(item, "publication_ref", None) or getattr(item, "title", None) or f"publication-{item.id}"),
                )
            )
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [identifier for _, identifier in scored[:3]]

    def _international_publications(self, researcher_id: str) -> int:
        count = 0
        for item in self._publication_records(researcher_id):
            metadata_json = getattr(item, "metadata_json", {}) or {}
            if bool(metadata_json.get("is_international") or metadata_json.get("international_collaboration")):
                count += 1
        return count

    def _indexed_publications(self, researcher_id: str) -> int:
        count = 0
        for item in self._publication_records(researcher_id):
            metadata_json = getattr(item, "metadata_json", {}) or {}
            if bool(metadata_json.get("indexed") or metadata_json.get("indexed_source")):
                count += 1
        return count

    def _trend_direction(self, citation_count: int, publication_count: int) -> str:
        if citation_count >= 20 and publication_count >= 3:
            return "up"
        if citation_count <= 2:
            return "down"
        return "stable"

    def _scientometric_risk(self, trend_direction: str, impact_score: float) -> str:
        if trend_direction == "down" or impact_score < 35.0:
            return "HIGH"
        if impact_score < 60.0:
            return "MEDIUM"
        return "LOW"

    def _impact_score(self, citation_count: int, h_index: int, i10_index: int, indexed_publications: int) -> float:
        return round((citation_count * 0.4) + (h_index * 8.0) + (i10_index * 4.0) + (indexed_publications * 2.0), 2)

    def researcher_scientometric_profile(self, researcher_id: str) -> ResearcherScientometricProfile:
        researcher = get_researcher_service(self.db, self.tenant_id, researcher_id)
        publication_count = int(researcher.publication_count)
        citation_count = int(researcher.citation_count)
        h_index = int(researcher.h_index)
        i10_index = citation_count // 10
        indexed_publications = self._indexed_publications(researcher_id)
        international_publications = self._international_publications(researcher_id)
        top_publications = self._top_publications(researcher_id)
        trend_direction = self._trend_direction(citation_count, publication_count)
        impact_score = self._impact_score(citation_count, h_index, i10_index, indexed_publications)
        scientometric_risk = self._scientometric_risk(trend_direction, impact_score)
        return ResearcherScientometricProfile(
            researcher_id=researcher_id,
            citation_count=citation_count,
            h_index=h_index,
            i10_index=i10_index,
            publication_count=publication_count,
            international_publications=international_publications,
            indexed_publications=indexed_publications,
            top_publications=top_publications,
            trend_direction=trend_direction,
            impact_score=impact_score,
            scientometric_risk=scientometric_risk,
            external_identities=self._external_identities(researcher_id, publication_count),
            trends=self.scientometric_trend_analysis(researcher_id),
        )

    def citation_summary(self, researcher_id: str) -> CitationAnalyticsSummary:
        profile = self.researcher_scientometric_profile(researcher_id)
        return CitationAnalyticsSummary(
            researcher_id=profile.researcher_id,
            citation_count=profile.citation_count,
            h_index=profile.h_index,
            i10_index=profile.i10_index,
            publication_count=profile.publication_count,
            international_publications=profile.international_publications,
            indexed_publications=profile.indexed_publications,
            top_publications=profile.top_publications,
            trend_direction=profile.trend_direction,
            impact_score=profile.impact_score,
            scientometric_risk=profile.scientometric_risk,
        )

    def publication_analytics(self, researcher_id: str) -> PublicationImpactProfile:
        profile = self.researcher_scientometric_profile(researcher_id)
        return PublicationImpactProfile(
            researcher_id=profile.researcher_id,
            publication_count=profile.publication_count,
            international_publications=profile.international_publications,
            indexed_publications=profile.indexed_publications,
            top_publications=profile.top_publications,
            citation_count=profile.citation_count,
            h_index=profile.h_index,
            i10_index=profile.i10_index,
            trend_direction=profile.trend_direction,
            impact_score=profile.impact_score,
            scientometric_risk=profile.scientometric_risk,
        )

    def impact_analysis(self, researcher_id: str) -> PublicationImpactProfile:
        return self.publication_analytics(researcher_id)

    def scientometric_trend_analysis(self, researcher_id: str) -> list[ScientometricTrend]:
        profile = get_researcher_service(self.db, self.tenant_id, researcher_id)
        i10_index = int(profile.citation_count) // 10
        baseline = ScientometricTrend(
            period="trailing_12m",
            citation_count=max(0, int(profile.citation_count) - 2),
            h_index=max(0, int(profile.h_index) - 1),
            i10_index=max(0, i10_index - 1),
            trend_direction="stable",
            impact_score=max(0.0, self._impact_score(max(0, int(profile.citation_count) - 2), max(0, int(profile.h_index) - 1), max(0, i10_index - 1), 0)),
        )
        current = ScientometricTrend(
            period="current",
            citation_count=int(profile.citation_count),
            h_index=int(profile.h_index),
            i10_index=i10_index,
            trend_direction=self._trend_direction(int(profile.citation_count), int(profile.publication_count)),
            impact_score=self._impact_score(int(profile.citation_count), int(profile.h_index), i10_index, 0),
        )
        return [baseline, current]

    def researcher_ranking(self) -> ResearcherRankingResponse:
        registry = _build_researcher_registry(self.db, self.tenant_id)
        ranked_profiles: list[ResearcherScientometricProfile] = [self.researcher_scientometric_profile(item.researcher_id) for item in registry]
        ranked_profiles.sort(key=lambda item: item.impact_score, reverse=True)
        ranking_items = [
            ResearcherRankingItem(
                researcher_id=item.researcher_id,
                rank=index + 1,
                impact_score=item.impact_score,
                scientometric_risk=item.scientometric_risk,
            )
            for index, item in enumerate(ranked_profiles)
        ]
        return ResearcherRankingResponse(tenant_id=self.tenant_id, items=ranking_items)

    def scientometrics_dashboard(self) -> ScientometricsSummaryResponse:
        registry = _build_researcher_registry(self.db, self.tenant_id)
        profiles: list[ResearcherScientometricProfile] = [self.researcher_scientometric_profile(item.researcher_id) for item in registry]
        profiles.sort(key=lambda item: item.impact_score, reverse=True)

        citation_board = [self.citation_summary(profile.researcher_id) for profile in profiles]
        citation_board.sort(key=lambda item: item.citation_count, reverse=True)

        h_index_board = [self.citation_summary(profile.researcher_id) for profile in profiles]
        h_index_board.sort(key=lambda item: item.h_index, reverse=True)

        publication_impact = [self.publication_analytics(profile.researcher_id) for profile in profiles]
        trend_summary = [
            ScientometricTrend(
                period=profile.researcher_id,
                citation_count=profile.citation_count,
                h_index=profile.h_index,
                i10_index=profile.i10_index,
                trend_direction=profile.trend_direction,
                impact_score=profile.impact_score,
            )
            for profile in profiles
        ]

        return ScientometricsSummaryResponse(
            tenant_id=self.tenant_id,
            top_researchers=profiles[:5],
            citation_leaderboard=citation_board[:5],
            h_index_leaderboard=h_index_board[:5],
            publication_impact_summary=publication_impact[:5],
            scientometric_trend_summary=trend_summary[:5],
            provider_execution_enabled=False,
            external_calls_enabled=False,
        )


class ResearchRiskService:
    """Read-only research risk runtime built from existing research canonicals."""

    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = validate_tenant_id(tenant_id)

    def _ethics_review_rows(self) -> list[dict[str, Any]]:
        rows = list_ethics_reviews(self.tenant_id)
        return [row.model_dump(mode="json") if hasattr(row, "model_dump") else dict(row) for row in rows]

    def aggregate_risks(self) -> dict[str, float]:
        health = get_research_health_snapshot(self.tenant_id)
        registry = _build_researcher_registry(self.db, self.tenant_id)
        scientometrics = ScientometricsService(self.db, self.tenant_id).scientometrics_dashboard()
        ethics_rows = self._ethics_review_rows()

        stalled_publications = int(health.stalled_publications)
        grant_deadlines = int(health.grants_near_deadline)
        grant_pipeline_at_risk = int(health.grant_pipeline_at_risk)
        inactive_researchers = sum(1 for item in registry if item.active_projects == 0 and item.active_grants == 0)
        overloaded_researchers = sum(1 for item in registry if item.active_projects >= 4)
        low_visibility_profiles = sum(1 for item in scientometrics.publication_impact_summary if item.indexed_publications == 0)
        citation_decline_profiles = sum(1 for item in scientometrics.top_researchers if item.trend_direction == "down" or item.citation_count < 3)
        high_scientometric_profiles = sum(1 for item in scientometrics.top_researchers if item.scientometric_risk in {"HIGH", "MEDIUM"})
        ethics_expiring = 0
        ethics_pending = 0
        now = _now()
        for row in ethics_rows:
            status = str(row.get("status") or "").upper()
            if status in {"PENDING", "UNDER_REVIEW", "REVISION_REQUESTED"}:
                ethics_pending += 1
            expiry_raw = row.get("review_due_date") or row.get("expiry_date") or row.get("expires_at")
            if expiry_raw:
                try:
                    expiry = datetime.fromisoformat(str(expiry_raw).replace("Z", "+00:00"))
                except ValueError:
                    expiry = None
                if expiry is not None and expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=UTC)
                if expiry is not None and (expiry - now).days <= 30:
                    ethics_expiring += 1

        publication_risk = _cap_score((stalled_publications * 18.0) + (inactive_researchers * 8.0) + (citation_decline_profiles * 6.0))
        grant_risk = _cap_score((grant_deadlines * 20.0) + (grant_pipeline_at_risk * 22.0))
        ethics_risk = _cap_score((ethics_pending * 18.0) + (ethics_expiring * 16.0))
        scientometric_risk = _cap_score((high_scientometric_profiles * 16.0) + (low_visibility_profiles * 14.0) + (citation_decline_profiles * 10.0))
        execution_risk = _cap_score((overloaded_researchers * 16.0) + (inactive_researchers * 12.0) + (int(health.active_experiments == 0) * 20.0))
        return {
            "publication": publication_risk,
            "grant": grant_risk,
            "ethics": ethics_risk,
            "scientometric": scientometric_risk,
            "execution": execution_risk,
        }

    def calculate_risk_score(self, risks: dict[str, float]) -> float:
        if not risks:
            return 0.0
        return round(sum(risks.values()) / len(risks), 2)

    def determine_trend(self, current_score: float, previous_score: float) -> str:
        return _trend_from_delta(current_score, previous_score)

    def determine_severity(self, score: float) -> str:
        return _severity_from_score(score)

    def risk_signals(self) -> list[ResearchRiskSignal]:
        risks = self.aggregate_risks()
        registry = _build_researcher_registry(self.db, self.tenant_id)
        health = get_research_health_snapshot(self.tenant_id)
        scientometrics = ScientometricsService(self.db, self.tenant_id).scientometrics_dashboard()
        ethics_rows = self._ethics_review_rows()

        publication_entities = [item.researcher_id for item in registry if item.publication_count == 0 or item.active_projects == 0][:5]
        grant_entities = [item.researcher_id for item in registry if item.active_grants >= 2][:5]
        ethics_entities = [str(row.get("review_id") or row.get("ethics_ref") or "ethics-review") for row in ethics_rows[:5]]
        scientometric_entities = [item.researcher_id for item in scientometrics.top_researchers if item.scientometric_risk in {"HIGH", "MEDIUM"}][:5]
        execution_entities = [item.researcher_id for item in registry if item.active_projects >= 4 or (item.active_projects == 0 and item.active_grants == 0)][:5]

        return [
            ResearchRiskSignal(
                family="publication_delay",
                owner="brain_core",
                dimension="publication",
                source="research_science + research publication lifecycle metadata",
                severity=self.determine_severity(risks["publication"]),
                observed_count=int(health.stalled_publications),
                affected_entities=publication_entities,
                description="Publication output and delivery cadence indicate delay risk.",
            ),
            ResearchRiskSignal(
                family="grant_execution_risk",
                owner="brain_core",
                dimension="grant",
                source="research_grants readiness + research health snapshot",
                severity=self.determine_severity(risks["grant"]),
                observed_count=int(health.grants_near_deadline) + int(health.grant_pipeline_at_risk),
                affected_entities=grant_entities,
                description="Grant portfolio deadlines and pipeline pressure indicate delivery risk.",
            ),
            ResearchRiskSignal(
                family="ethics_expiration_risk",
                owner="brain_core",
                dimension="ethics",
                source="research_ethics review inventory",
                severity=self.determine_severity(risks["ethics"]),
                observed_count=len(ethics_rows),
                affected_entities=ethics_entities,
                description="Ethics reviews require renewal or nearing expiry windows.",
            ),
            ResearchRiskSignal(
                family="citation_decline_risk",
                owner="brain_core",
                dimension="scientometric",
                source="analytics-owned scientometric trends",
                severity=self.determine_severity(risks["scientometric"]),
                observed_count=sum(1 for item in scientometrics.top_researchers if item.trend_direction == "down" or item.citation_count < 3),
                affected_entities=scientometric_entities,
                description="Citation baseline and trend direction show declining visibility risk.",
            ),
            ResearchRiskSignal(
                family="low_visibility_risk",
                owner="brain_core",
                dimension="scientometric",
                source="publication_registry bridge and indexed publication counts",
                severity=self.determine_severity(risks["scientometric"]),
                observed_count=sum(1 for item in scientometrics.publication_impact_summary if item.indexed_publications == 0),
                affected_entities=scientometric_entities,
                description="Low indexed publication coverage limits research visibility.",
            ),
            ResearchRiskSignal(
                family="research_output_drop",
                owner="brain_core",
                dimension="execution",
                source="research_science workload and output summaries",
                severity=self.determine_severity(risks["execution"]),
                observed_count=sum(1 for item in registry if item.active_projects == 0 and item.active_grants == 0),
                affected_entities=execution_entities,
                description="Research execution throughput indicates output drop or inactivity risk.",
            ),
        ]

    def risk_trends(self) -> list[ResearchRiskTrend]:
        risks = self.aggregate_risks()
        previous = {dimension: _cap_score(score - max(5.0, score * 0.1)) for dimension, score in risks.items()}
        return [
            ResearchRiskTrend(
                dimension=dimension,
                current_score=current_score,
                previous_score=previous[dimension],
                trend_direction=self.determine_trend(current_score, previous[dimension]),
                severity=self.determine_severity(current_score),
            )
            for dimension, current_score in risks.items()
        ]

    def risk_summary(self) -> ResearchRiskSummary:
        risks = self.aggregate_risks()
        signals = self.risk_signals()
        overall = self.calculate_risk_score(risks)
        heatmap = {dimension: self.determine_severity(score) for dimension, score in risks.items()}
        top_critical = [signal.family for signal in signals if signal.severity in {"CRITICAL", "HIGH"}]
        return ResearchRiskSummary(
            overall_risk_score=overall,
            severity=self.determine_severity(overall),
            publication_risk=risks["publication"],
            grant_risk=risks["grant"],
            ethics_risk=risks["ethics"],
            scientometric_risk=risks["scientometric"],
            execution_risk=risks["execution"],
            risk_heatmap=heatmap,
            top_critical_risks=top_critical,
        )

    def generate_recommendations(self, summary: ResearchRiskSummary, signals: list[ResearchRiskSignal]) -> list[str]:
        recommendations: list[str] = []
        if summary.publication_risk >= 35.0:
            recommendations.append("Review stalled publications and prioritize evidence-backed publication completion plans.")
        if summary.grant_risk >= 35.0:
            recommendations.append("Escalate near-deadline grants for delivery review and milestone recovery planning.")
        if summary.ethics_risk >= 35.0:
            recommendations.append("Audit the ethics review queue for expirations, amendments, and pending approvals.")
        if summary.scientometric_risk >= 35.0:
            recommendations.append("Prioritize researcher visibility actions for low-indexed and citation-declining outputs.")
        if summary.execution_risk >= 35.0:
            recommendations.append("Rebalance project workload and confirm execution coverage for inactive or overloaded researchers.")
        if not recommendations:
            recommendations.append("Maintain current monitoring cadence; no critical research risk escalation is required.")
        if any(signal.family == "ethics_expiration_risk" and signal.observed_count > 0 for signal in signals):
            recommendations.append("Document ethics review follow-up actions in the research review queue for auditability.")
        return recommendations

    def risk_profile(self) -> ResearchRiskProfile:
        signals = self.risk_signals()
        trends = self.risk_trends()
        summary = self.risk_summary()
        return ResearchRiskProfile(
            tenant_id=self.tenant_id,
            generated_at=_now(),
            summary=summary,
            signals=signals,
            trends=trends,
            recommendations=self.generate_recommendations(summary, signals),
            provider_execution_enabled=False,
            external_calls_enabled=False,
        )


def _build_researcher_registry(db: Session, tenant_id: int) -> list[Researcher]:
    publications = repository.list_publication_metadata(db, tenant_id)
    grants = repository.list_grant_applications(db, tenant_id)
    projects = repository.list_research_projects(db, tenant_id)
    supervision = repository.list_scientific_supervisions(db, tenant_id)
    student_research = repository.list_student_research_work(db, tenant_id)
    ethics_requests = repository.list_ethics_requests(db, tenant_id)
    research_health = get_research_health_snapshot(tenant_id)

    index: dict[str, dict[str, Any]] = {}

    def ensure(researcher_id: str) -> dict[str, Any]:
        if researcher_id not in index:
            index[researcher_id] = {
                "researcher_id": researcher_id,
                "employee_id": researcher_id,
                "full_name": f"Researcher {researcher_id}",
                "position": "Research Staff",
                "faculty": None,
                "department": None,
                "laboratory": None,
                "research_areas": [],
                "specializations": [],
                "active_projects": 0,
                "active_grants": 0,
                "publication_count": 0,
                "citation_count": 0,
                "h_index": 0,
                "risk_level": "LOW",
                "status": "ACTIVE",
                "pending_ethics": 0,
            }
        return index[researcher_id]

    for item in publications:
        researcher_id = _to_researcher_id(getattr(item, "faculty_ref", None))
        if not researcher_id:
            continue
        entry = ensure(researcher_id)
        entry["publication_count"] += 1
        metadata_json = getattr(item, "metadata_json", {}) or {}
        citations = int(metadata_json.get("citation_count") or 0)
        entry["citation_count"] += citations
        entry["h_index"] = max(int(entry["h_index"]), int(metadata_json.get("h_index") or 0))
        entry["research_areas"] = _merge_unique(entry["research_areas"], list(metadata_json.get("research_areas") or []))
        entry["specializations"] = _merge_unique(entry["specializations"], list(metadata_json.get("specializations") or []))

    for item in grants:
        researcher_id = _to_researcher_id(getattr(item, "faculty_ref", None))
        if not researcher_id:
            continue
        entry = ensure(researcher_id)
        status = str(getattr(item, "status", "") or "").upper()
        if status in {"ACTIVE", "INTERNAL_REVIEW", "SUBMITTED_EXTERNALLY_BY_HUMAN", "DRAFT"}:
            entry["active_grants"] += 1
        entry["department"] = entry["department"] or getattr(item, "department_ref", None)

    for item in supervision:
        researcher_id = _to_researcher_id(getattr(item, "faculty_ref", None))
        if not researcher_id:
            continue
        entry = ensure(researcher_id)
        metadata_json = getattr(item, "metadata_json", {}) or {}
        entry["laboratory"] = entry["laboratory"] or metadata_json.get("lab_code")
        entry["specializations"] = _merge_unique(entry["specializations"], list(metadata_json.get("specializations") or []))

    for item in student_research:
        researcher_id = _to_researcher_id(getattr(item, "faculty_ref", None))
        if not researcher_id:
            continue
        entry = ensure(researcher_id)
        metadata_json = getattr(item, "metadata_json", {}) or {}
        entry["research_areas"] = _merge_unique(entry["research_areas"], list(metadata_json.get("research_areas") or []))

    for item in ethics_requests:
        researcher_id = _to_researcher_id(getattr(item, "faculty_ref", None))
        if not researcher_id:
            continue
        entry = ensure(researcher_id)
        status = str(getattr(item, "status", "") or "").upper()
        if status in {"PENDING", "UNDER_REVIEW", "REVISION_REQUESTED"}:
            entry["pending_ethics"] += 1

    default_project_load = int(research_health.active_experiments) if int(research_health.active_experiments) > 0 else 1
    for researcher_id, entry in index.items():
        entry["active_projects"] = max(int(entry["active_projects"]), min(default_project_load, 3))
        entry["risk_level"] = _compute_risk_level(
            active_projects=int(entry["active_projects"]),
            active_grants=int(entry["active_grants"]),
            publication_count=int(entry["publication_count"]),
            pending_ethics=int(entry["pending_ethics"]),
        )
        entry.pop("pending_ethics", None)
        if not entry["research_areas"]:
            entry["research_areas"] = ["research_foundation"]
        if not entry["specializations"]:
            entry["specializations"] = ["metadata_orchestration"]

    return [Researcher.model_validate(value) for value in sorted(index.values(), key=lambda x: x["researcher_id"])]


def list_researchers_service(db: Session, tenant_id: int) -> ResearcherListResponse:
    tenant_id = validate_tenant_id(tenant_id)
    return ResearcherListResponse(items=_build_researcher_registry(db, tenant_id))


def get_researcher_service(db: Session, tenant_id: int, researcher_id: str) -> Researcher:
    tenant_id = validate_tenant_id(tenant_id)
    normalized = _to_researcher_id(researcher_id)
    if not normalized:
        raise DomainValidationError("researcher_id is required")
    registry = _build_researcher_registry(db, tenant_id)
    for item in registry:
        if item.researcher_id == normalized:
            return item
    raise DomainValidationError(f"researcher {normalized} not found in tenant scope")


def get_researcher_dashboard_summary_service(db: Session, tenant_id: int) -> ResearcherDashboardSummaryResponse:
    tenant_id = validate_tenant_id(tenant_id)
    registry = _build_researcher_registry(db, tenant_id)
    return ResearcherDashboardSummaryResponse(
        tenant_id=tenant_id,
        total_researchers=len(registry),
        active_researchers=sum(1 for item in registry if item.status == "ACTIVE"),
        high_risk_researchers=sum(1 for item in registry if item.risk_level == "HIGH"),
        publication_total=sum(item.publication_count for item in registry),
        active_projects_total=sum(item.active_projects for item in registry),
        active_grants_total=sum(item.active_grants for item in registry),
    )


def get_researcher_activity_profile_service(db: Session, tenant_id: int, researcher_id: str) -> ResearcherActivityProfileResponse:
    tenant_id = validate_tenant_id(tenant_id)
    researcher = get_researcher_service(db, tenant_id, researcher_id)
    profile = ResearcherProfile(
        researcher_id=researcher.researcher_id,
        employee_id=researcher.employee_id,
        full_name=researcher.full_name,
        position=researcher.position,
        faculty=researcher.faculty,
        department=researcher.department,
        laboratory=researcher.laboratory,
        research_areas=researcher.research_areas,
        specializations=researcher.specializations,
        status=researcher.status,
    )
    return ResearcherActivityProfileResponse(
        tenant_id=tenant_id,
        researcher=profile,
        project_summary=ResearcherProjectSummary(active_projects=researcher.active_projects),
        grant_summary=ResearcherGrantSummary(active_grants=researcher.active_grants),
        publication_summary=ResearcherPublicationSummary(
            publication_count=researcher.publication_count,
            citation_count=researcher.citation_count,
        ),
        scientometric_summary=ResearcherScientometricSummary(
            h_index=researcher.h_index,
            citation_count=researcher.citation_count,
        ),
    )


def get_researcher_risk_profile_service(db: Session, tenant_id: int, researcher_id: str) -> ResearcherRiskProfileResponse:
    tenant_id = validate_tenant_id(tenant_id)
    researcher = get_researcher_service(db, tenant_id, researcher_id)
    signals: list[str] = []
    notes: list[str] = []

    if researcher.publication_count == 0:
        signals.append("publication_gap")
        notes.append("No publication records currently attached to this researcher.")
    if researcher.active_grants >= 2:
        signals.append("grant_expiration")
        notes.append("Multiple active grants require near-term expiration review.")
    if researcher.active_projects >= 4:
        signals.append("project_overload")
        notes.append("Project load suggests potential supervision and delivery pressure.")
    if researcher.active_projects == 0 and researcher.active_grants == 0:
        signals.append("inactive_researcher")
        notes.append("No active project or grant workload is currently observed.")
    if researcher.citation_count < 3:
        signals.append("citation_decline")
        notes.append("Citation baseline is low and requires human review.")
    if researcher.risk_level in {"HIGH", "MEDIUM"}:
        signals.append("ethics_delay")
        notes.append("Risk profile suggests checking ethics review queue delays.")

    return ResearcherRiskProfileResponse(
        tenant_id=tenant_id,
        researcher_id=researcher.researcher_id,
        risk_level=researcher.risk_level,
        workload={
            "active_projects": researcher.active_projects,
            "active_grants": researcher.active_grants,
            "publication_count": researcher.publication_count,
        },
        signals=signals,
        notes=notes,
    )


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
    researcher_summary = get_researcher_dashboard_summary_service(db, tenant_id)
    scientometrics = ScientometricsService(db, tenant_id).scientometrics_dashboard()
    risk_profile = ResearchRiskService(db, tenant_id).risk_profile()
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
            total=6,
            notes="Signal exposure remains brain_core-owned and read-only with no scoring engine activation.",
        ),
        researchers=ResearchBrainOrchestrationItemResponse(
            source_module="research_science",
            read_only=True,
            total=researcher_summary.total_researchers,
            notes="Canonical researcher registry remains research_science-owned with bridge-only enrichment.",
        ),
        researcher_summary=ResearchBrainOrchestrationItemResponse(
            source_module="research_science",
            read_only=True,
            total=researcher_summary.total_researchers,
            notes="Researcher summary aggregates activity and productivity indicators.",
        ),
        researcher_health=ResearchBrainOrchestrationItemResponse(
            source_module="research_science",
            read_only=True,
            total=researcher_summary.active_researchers,
            notes="Researcher health is derived from active status and risk bands.",
        ),
        researcher_workload=ResearchBrainOrchestrationItemResponse(
            source_module="research_science",
            read_only=True,
            total=researcher_summary.active_projects_total + researcher_summary.active_grants_total,
            notes="Workload is read-only and based on active projects plus active grants.",
        ),
        researcher_risk=ResearchBrainOrchestrationItemResponse(
            source_module="brain_core",
            read_only=True,
            total=researcher_summary.high_risk_researchers,
            notes="Researcher risk surface is consumed through brain_core-owned signal families.",
        ),
        scientometrics=ResearchBrainOrchestrationItemResponse(
            source_module="analytics",
            read_only=True,
            total=len(scientometrics.top_researchers),
            notes="Scientometrics runtime is analytics-owned and exposed via read-only Research Brain shell.",
        ),
        citation_analytics=ResearchBrainOrchestrationItemResponse(
            source_module="analytics",
            read_only=True,
            total=len(scientometrics.citation_leaderboard),
            notes="Citation analytics is bridge-backed and provider-ready only (no live provider execution).",
        ),
        impact_analytics=ResearchBrainOrchestrationItemResponse(
            source_module="analytics",
            read_only=True,
            total=len(scientometrics.h_index_leaderboard),
            notes="Impact analytics exposes h-index and impact score summaries from metadata-only sources.",
        ),
        publication_impact=ResearchBrainOrchestrationItemResponse(
            source_module="publication_registry",
            read_only=True,
            total=len(scientometrics.publication_impact_summary),
            notes="Publication impact uses publication_registry bridge data with no duplicate publication ownership.",
        ),
        researcher_ranking=ResearchBrainOrchestrationItemResponse(
            source_module="analytics",
            read_only=True,
            total=len(scientometrics.top_researchers),
            notes="Researcher ranking is read-only and derived from scientometric impact score.",
        ),
        risk_profile=ResearchBrainOrchestrationItemResponse(
            source_module="brain_core",
            read_only=True,
            total=1,
            notes="Research risk profile is brain_core-owned and aggregated from existing canonicals only.",
        ),
        risk_summary=ResearchBrainOrchestrationItemResponse(
            source_module="brain_core",
            read_only=True,
            total=1,
            notes="Research risk summary exposes overall score, heatmap, and top critical risks.",
        ),
        risk_signals=ResearchBrainOrchestrationItemResponse(
            source_module="brain_core",
            read_only=True,
            total=len(risk_profile.signals),
            notes="Risk signal inventory remains read-only with no scoring-engine activation.",
        ),
        risk_trends=ResearchBrainOrchestrationItemResponse(
            source_module="brain_core",
            read_only=True,
            total=len(risk_profile.trends),
            notes="Risk trends are deterministic comparisons over current bridge-backed snapshots.",
        ),
        risk_recommendations=ResearchBrainOrchestrationItemResponse(
            source_module="brain_core",
            read_only=True,
            total=len(risk_profile.recommendations),
            notes="Recommendations remain advisory and human-review gated.",
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
    registry = _build_researcher_registry(db, tenant_id)
    scientometrics = ScientometricsService(db, tenant_id).scientometrics_dashboard()
    health = get_research_health_snapshot(tenant_id)
    risk_signals = ResearchRiskService(db, tenant_id).risk_signals()
    project_overload_count = sum(1 for item in registry if item.active_projects >= 4)
    inactive_count = sum(1 for item in registry if item.active_projects == 0 and item.active_grants == 0)
    citation_decline_count = sum(1 for item in registry if item.citation_count < 3)
    ethics_delay_count = sum(1 for item in registry if item.risk_level in {"MEDIUM", "HIGH"})
    publication_stagnation_count = sum(1 for item in scientometrics.publication_impact_summary if item.publication_count <= 1)
    impact_drop_count = sum(1 for item in scientometrics.publication_impact_summary if item.impact_score < 50.0)
    low_visibility_count = sum(1 for item in scientometrics.publication_impact_summary if item.indexed_publications == 0)
    ranking_drop_count = sum(1 for item in scientometrics.top_researchers if item.scientometric_risk in {"MEDIUM", "HIGH"})
    signals = [
        ResearchBrainSignalItemResponse(
            family="publication_gap",
            owner="brain_core",
            source="research.publications + research_science researcher publication summaries",
            consumer="researcher_registry",
            review_queue="research_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=int(health.stalled_publications),
        ),
        ResearchBrainSignalItemResponse(
            family="grant_expiration",
            owner="brain_core",
            source="research_grants + grant deadline/risk snapshot",
            consumer="researcher_workload",
            review_queue="grants_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=max(int(health.grants_near_deadline), int(health.grant_pipeline_at_risk)),
        ),
        ResearchBrainSignalItemResponse(
            family="project_overload",
            owner="brain_core",
            source="research_science supervision/project workload summaries",
            consumer="researcher_workload",
            review_queue="project_delay_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=project_overload_count,
        ),
        ResearchBrainSignalItemResponse(
            family="inactive_researcher",
            owner="brain_core",
            source="researcher registry activity aggregates",
            consumer="researcher_health",
            review_queue="research_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=inactive_count,
        ),
        ResearchBrainSignalItemResponse(
            family="citation_decline",
            owner="brain_core",
            source="publication citations from researcher publication summaries",
            consumer="researcher_risk",
            review_queue="scientometrics_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=citation_decline_count,
        ),
        ResearchBrainSignalItemResponse(
            family="publication_stagnation",
            owner="brain_core",
            source="publication throughput from publication impact profiles",
            consumer="scientometrics_dashboard",
            review_queue="scientometrics_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=publication_stagnation_count,
        ),
        ResearchBrainSignalItemResponse(
            family="impact_drop",
            owner="brain_core",
            source="impact_score trends from analytics-owned scientometrics profiles",
            consumer="impact_analytics",
            review_queue="scientometrics_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=impact_drop_count,
        ),
        ResearchBrainSignalItemResponse(
            family="low_visibility",
            owner="brain_core",
            source="indexed publication ratios from publication impact summaries",
            consumer="publication_impact",
            review_queue="scientometrics_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=low_visibility_count,
        ),
        ResearchBrainSignalItemResponse(
            family="researcher_ranking_drop",
            owner="brain_core",
            source="researcher ranking deltas over scientometric risk labels",
            consumer="researcher_ranking",
            review_queue="scientometrics_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=ranking_drop_count,
        ),
        ResearchBrainSignalItemResponse(
            family="ethics_delay",
            owner="brain_core",
            source="research_ethics queue pressure + researcher risk aggregation",
            consumer="researcher_risk",
            review_queue="ethics_review_queue",
            read_only=True,
            scoring_engine_enabled=False,
            observed_count=ethics_delay_count,
        ),
    ]
    signals.extend(
        ResearchBrainSignalItemResponse(
            family=signal.family,
            owner=signal.owner,
            source=signal.source,
            consumer="research_risk_dashboard",
            review_queue="research_risk_review_queue",
            read_only=signal.read_only,
            scoring_engine_enabled=False,
            observed_count=signal.observed_count,
        )
        for signal in risk_signals
    )
    return ResearchBrainSignalSurfaceResponse(tenant_id=tenant_id, signals=signals)


def get_researcher_scientometric_profile_service(db: Session, tenant_id: int, researcher_id: str) -> ResearcherScientometricProfile:
    return ScientometricsService(db, tenant_id).researcher_scientometric_profile(researcher_id)


def get_researcher_citation_summary_service(db: Session, tenant_id: int, researcher_id: str) -> CitationAnalyticsSummary:
    return ScientometricsService(db, tenant_id).citation_summary(researcher_id)


def get_researcher_impact_analysis_service(db: Session, tenant_id: int, researcher_id: str) -> PublicationImpactProfile:
    return ScientometricsService(db, tenant_id).impact_analysis(researcher_id)


def get_researcher_publication_impact_service(db: Session, tenant_id: int, researcher_id: str) -> PublicationImpactProfile:
    return ScientometricsService(db, tenant_id).publication_analytics(researcher_id)


def get_researcher_scientometric_trends_service(db: Session, tenant_id: int, researcher_id: str) -> list[ScientometricTrend]:
    return ScientometricsService(db, tenant_id).scientometric_trend_analysis(researcher_id)


def get_scientometrics_dashboard_service(db: Session, tenant_id: int) -> ScientometricsSummaryResponse:
    return ScientometricsService(db, tenant_id).scientometrics_dashboard()


def get_scientometric_researcher_ranking_service(db: Session, tenant_id: int) -> ResearcherRankingResponse:
    return ScientometricsService(db, tenant_id).researcher_ranking()


def get_research_risk_profile_service(db: Session, tenant_id: int) -> ResearchRiskProfile:
    return ResearchRiskService(db, tenant_id).risk_profile()


def get_research_risk_summary_service(db: Session, tenant_id: int) -> ResearchRiskSummary:
    return ResearchRiskService(db, tenant_id).risk_summary()


def get_research_risk_signals_service(db: Session, tenant_id: int) -> list[ResearchRiskSignal]:
    return ResearchRiskService(db, tenant_id).risk_signals()


def get_research_risk_trends_service(db: Session, tenant_id: int) -> list[ResearchRiskTrend]:
    return ResearchRiskService(db, tenant_id).risk_trends()


def get_research_risk_recommendations_service(db: Session, tenant_id: int) -> list[str]:
    profile = ResearchRiskService(db, tenant_id).risk_profile()
    return profile.recommendations


def get_research_brain_rbac_validation_service(tenant_id: int) -> ResearchBrainRbacValidationResponse:
    tenant_id = validate_tenant_id(tenant_id)
    role_requirements = {
        "research_admin": [
            "research.read",
            "research.write",
            "research_science.admin.read",
            "research_science.audit.read",
        ],
        "research_manager": [
            "research.read",
            "research.write",
            "research_science.projects.read",
            "research_science.grants.read",
            "research_science.audit.read",
        ],
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
        "vice_rector_science": [
            "research.read",
            "research_science.dashboard.read",
            "research_science.grants.read",
            "research_science.audit.read",
        ],
        "auditor": [
            "research.read",
            "research_science.overview.read",
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