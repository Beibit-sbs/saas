"""Academic Operations service layer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.academic_operations import repository
from app.modules.academic_operations.dependencies import validate_tenant_id
from app.modules.academic_operations.models import AcademicOperationsAuditEventType, MODULE_NAME, TARGET_LEVEL
from app.modules.academic_operations.schemas import (
    AcademicOperationsDashboardResponse,
    AcademicOperationsHealthResponse,
    AcademicOperationsMatrixSummaryResponse,
)


MASTER_MATRIX_COMMIT = "c79cc31"
MASTER_MATRIX_ROW_COUNT = 467
CANONICAL_MODULE_REUSE_POLICY = "REUSE_EXISTING_CANONICAL_MODULES_ONLY"
NO_DUPLICATE_MODULE_POLICY = "REUSE_CANONICALS_AND_BRIDGE_ONLY"
ACADEMIC_OPERATIONS_TRUE_NEW_MODULES = [
    "academic_group_management",
    "cohort_management",
    "gradebook_metadata",
    "retake_management",
    "summer_semester_management",
    "advisor_tutor_management",
]
ACADEMIC_OPERATIONS_CANONICAL_REUSE_MAP = {
    "course_catalog": "course_catalog_management",
    "elective_course_selection": "elective_course_selection",
    "academic_committee_decisions": "committee_decision_registry",
    "prerequisite_validation": "prerequisite_management",
    "teaching_load_management": "teaching_load_contracts/workload_management",
    "thesis_supervision_management": "thesis_dissertation_management",
    "academic_debt_tracking": "degree_audit/academic_records",
}
ACADEMIC_OPERATIONS_BRIDGE_MAP = {
    "student_lifecycle": "academic_operations_to_student_lifecycle_bridge",
    "document_workflow": "academic_operations_to_document_workflow_bridge",
    "executive_governance": "academic_operations_to_executive_governance_bridge",
    "quality_accreditation": "academic_operations_to_quality_accreditation_bridge",
}
FORBIDDEN_RUNTIME_CLAIMS = [
    "official_grade_publication",
    "automated_grading",
    "automatic_student_sanction",
    "automatic_academic_dismissal",
    "hidden_student_score",
    "hidden_faculty_score",
    "provider_dispatch",
    "platonus_sync",
    "sis_sync",
]
REQUIRED_LIMITATIONS = [
    "metadata_only_foundation",
    "canonical_modules_reused_via_bridge",
    "no_official_grade_publication",
    "no_automated_grading",
    "no_provider_integration",
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


def _safety_defaults(actor: str | None = None, source_capability_id: str | None = None, source_matrix_row_id: str | None = None) -> dict[str, Any]:
    return {
        "human_review_required": True,
        "automated_decision": False,
        "provider_integration_enabled": False,
        "platonus_sync_enabled": False,
        "sis_sync_enabled": False,
        "hidden_score_present": False,
        "official_grade_publication_enabled": False,
        "automated_grading_enabled": False,
        "automatic_sanction_enabled": False,
        "created_by_user_id": actor,
        "updated_by_user_id": actor,
        "source_capability_id": source_capability_id,
        "source_matrix_row_id": source_matrix_row_id,
        "incomplete_data": True,
    }


def _audit(db: Session, tenant_id: int, *, entity_type: str, entity_id: int | None, event_type: str, actor_user_id: str, action: str, previous_status: str | None = None, new_status: str | None = None, payload: dict[str, Any] | None = None) -> None:
    repository.create_audit_event(
        db,
        tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        action=action,
        actor_user_id=actor_user_id,
        previous_status=previous_status,
        new_status=new_status,
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        payload_json=payload or {},
    )


def _update_payload(request, actor: str) -> dict[str, Any]:
    payload = request.model_dump(exclude_none=True)
    payload["limitations_json"] = _merge_limitations(payload.pop("limitations", None))
    payload["updated_by_user_id"] = actor
    payload["automated_decision"] = False
    payload["provider_integration_enabled"] = False
    payload["platonus_sync_enabled"] = False
    payload["sis_sync_enabled"] = False
    payload["hidden_score_present"] = False
    payload["official_grade_publication_enabled"] = False
    payload["automated_grading_enabled"] = False
    payload["automatic_sanction_enabled"] = False
    return payload


def _create_payload(request, actor: str) -> dict[str, Any]:
    payload = request.model_dump(exclude_none=True)
    payload["limitations_json"] = _merge_limitations(payload.pop("limitations", None))
    if "metadata" in payload:
        payload["metadata_json"] = payload.pop("metadata")
    return payload | _safety_defaults(actor, payload.get("source_capability_id"), payload.get("source_matrix_row_id"))


def create_academic_group_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_academic_group(db, tenant_id, **_create_payload(request, actor))
    _audit(db, tenant_id, entity_type="academic_group", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.ACADEMIC_GROUP_CREATED, actor_user_id=actor, action="create_academic_group", new_status=entity.status)
    _commit(db)
    return entity


def list_academic_groups_service(db: Session, tenant_id: int):
    return repository.list_academic_groups(db, validate_tenant_id(tenant_id))


def get_academic_group_service(db: Session, tenant_id: int, group_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_academic_group(db, tenant_id, group_id)
    if entity is None:
        raise DomainValidationError(f"academic_group {group_id} not found in tenant scope")
    return entity


def update_academic_group_service(db: Session, tenant_id: int, actor_user_id: str, group_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_academic_group_service(db, tenant_id, group_id)
    entity = repository.update_academic_group(db, tenant_id, group_id, **_update_payload(request, actor))
    _audit(db, tenant_id, entity_type="academic_group", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.ACADEMIC_GROUP_UPDATED, actor_user_id=actor, action="update_academic_group", previous_status=current.status, new_status=entity.status)
    _commit(db)
    return entity


def create_cohort_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_cohort(db, tenant_id, **_create_payload(request, actor))
    _audit(db, tenant_id, entity_type="cohort", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.COHORT_CREATED, actor_user_id=actor, action="create_cohort", new_status=entity.status)
    _commit(db)
    return entity


def list_cohorts_service(db: Session, tenant_id: int):
    return repository.list_cohorts(db, validate_tenant_id(tenant_id))


def get_cohort_service(db: Session, tenant_id: int, cohort_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_cohort(db, tenant_id, cohort_id)
    if entity is None:
        raise DomainValidationError(f"cohort {cohort_id} not found in tenant scope")
    return entity


def update_cohort_service(db: Session, tenant_id: int, actor_user_id: str, cohort_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_cohort_service(db, tenant_id, cohort_id)
    entity = repository.update_cohort(db, tenant_id, cohort_id, **_update_payload(request, actor))
    _audit(db, tenant_id, entity_type="cohort", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.COHORT_UPDATED, actor_user_id=actor, action="update_cohort", previous_status=current.status, new_status=entity.status)
    _commit(db)
    return entity


def create_course_registration_metadata_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_course_registration_metadata(db, tenant_id, **_create_payload(request, actor))
    _audit(db, tenant_id, entity_type="course_registration_metadata", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.COURSE_REGISTRATION_METADATA_CREATED, actor_user_id=actor, action="create_course_registration_metadata", new_status=entity.status)
    _commit(db)
    return entity


def list_course_registration_metadata_service(db: Session, tenant_id: int):
    return repository.list_course_registration_metadata(db, validate_tenant_id(tenant_id))


def create_gradebook_metadata_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_gradebook_metadata(db, tenant_id, **_create_payload(request, actor))
    _audit(db, tenant_id, entity_type="gradebook_metadata", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.GRADEBOOK_METADATA_CREATED, actor_user_id=actor, action="create_gradebook_metadata", new_status=entity.status)
    _commit(db)
    return entity


def list_gradebook_metadata_service(db: Session, tenant_id: int):
    return repository.list_gradebook_metadata(db, validate_tenant_id(tenant_id))


def get_gradebook_metadata_service(db: Session, tenant_id: int, gradebook_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_gradebook_metadata(db, tenant_id, gradebook_id)
    if entity is None:
        raise DomainValidationError(f"gradebook_metadata {gradebook_id} not found in tenant scope")
    return entity


def update_gradebook_metadata_service(db: Session, tenant_id: int, actor_user_id: str, gradebook_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_gradebook_metadata_service(db, tenant_id, gradebook_id)
    entity = repository.update_gradebook_metadata(db, tenant_id, gradebook_id, **_update_payload(request, actor))
    _audit(db, tenant_id, entity_type="gradebook_metadata", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.GRADEBOOK_METADATA_UPDATED, actor_user_id=actor, action="update_gradebook_metadata", previous_status=current.status, new_status=entity.status)
    _commit(db)
    return entity


def create_retake_plan_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_retake_plan(db, tenant_id, **_create_payload(request, actor))
    _audit(db, tenant_id, entity_type="retake_plan", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.RETAKE_PLAN_CREATED, actor_user_id=actor, action="create_retake_plan", new_status=entity.status)
    _commit(db)
    return entity


def list_retake_plans_service(db: Session, tenant_id: int):
    return repository.list_retake_plans(db, validate_tenant_id(tenant_id))


def get_retake_plan_service(db: Session, tenant_id: int, retake_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_retake_plan(db, tenant_id, retake_id)
    if entity is None:
        raise DomainValidationError(f"retake_plan {retake_id} not found in tenant scope")
    return entity


def update_retake_plan_service(db: Session, tenant_id: int, actor_user_id: str, retake_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_retake_plan_service(db, tenant_id, retake_id)
    entity = repository.update_retake_plan(db, tenant_id, retake_id, **_update_payload(request, actor))
    _audit(db, tenant_id, entity_type="retake_plan", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.RETAKE_PLAN_UPDATED, actor_user_id=actor, action="update_retake_plan", previous_status=current.status, new_status=entity.status)
    _commit(db)
    return entity


def create_summer_semester_term_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_summer_semester_term(db, tenant_id, **_create_payload(request, actor))
    _audit(db, tenant_id, entity_type="summer_semester_term", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.SUMMER_SEMESTER_CREATED, actor_user_id=actor, action="create_summer_semester_term", new_status=entity.status)
    _commit(db)
    return entity


def list_summer_semester_terms_service(db: Session, tenant_id: int):
    return repository.list_summer_semester_terms(db, validate_tenant_id(tenant_id))


def get_summer_semester_term_service(db: Session, tenant_id: int, term_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_summer_semester_term(db, tenant_id, term_id)
    if entity is None:
        raise DomainValidationError(f"summer_semester_term {term_id} not found in tenant scope")
    return entity


def update_summer_semester_term_service(db: Session, tenant_id: int, actor_user_id: str, term_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_summer_semester_term_service(db, tenant_id, term_id)
    entity = repository.update_summer_semester_term(db, tenant_id, term_id, **_update_payload(request, actor))
    _audit(db, tenant_id, entity_type="summer_semester_term", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.SUMMER_SEMESTER_UPDATED, actor_user_id=actor, action="update_summer_semester_term", previous_status=current.status, new_status=entity.status)
    _commit(db)
    return entity


def create_advisor_tutor_assignment_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_advisor_tutor_assignment(db, tenant_id, **_create_payload(request, actor))
    _audit(db, tenant_id, entity_type="advisor_tutor_assignment", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.ADVISOR_TUTOR_ASSIGNMENT_CREATED, actor_user_id=actor, action="create_advisor_tutor_assignment", new_status=entity.status)
    _commit(db)
    return entity


def list_advisor_tutor_assignments_service(db: Session, tenant_id: int):
    return repository.list_advisor_tutor_assignments(db, validate_tenant_id(tenant_id))


def get_advisor_tutor_assignment_service(db: Session, tenant_id: int, assignment_id: int):
    tenant_id = validate_tenant_id(tenant_id)
    entity = repository.get_advisor_tutor_assignment(db, tenant_id, assignment_id)
    if entity is None:
        raise DomainValidationError(f"advisor_tutor_assignment {assignment_id} not found in tenant scope")
    return entity


def update_advisor_tutor_assignment_service(db: Session, tenant_id: int, actor_user_id: str, assignment_id: int, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = get_advisor_tutor_assignment_service(db, tenant_id, assignment_id)
    entity = repository.update_advisor_tutor_assignment(db, tenant_id, assignment_id, **_update_payload(request, actor))
    _audit(db, tenant_id, entity_type="advisor_tutor_assignment", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.ADVISOR_TUTOR_ASSIGNMENT_UPDATED, actor_user_id=actor, action="update_advisor_tutor_assignment", previous_status=current.status, new_status=entity.status)
    _commit(db)
    return entity


def create_canonical_module_bridge_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_canonical_module_bridge(db, tenant_id, **_create_payload(request, actor))
    _audit(db, tenant_id, entity_type="canonical_module_bridge", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.CANONICAL_BRIDGE_CREATED, actor_user_id=actor, action="create_canonical_module_bridge", new_status=entity.status)
    _commit(db)
    return entity


def list_canonical_module_bridges_service(db: Session, tenant_id: int):
    return repository.list_canonical_module_bridges(db, validate_tenant_id(tenant_id))


def get_canonical_reuse_summary_service(db: Session, tenant_id: int) -> dict[str, Any]:
    tenant_id = validate_tenant_id(tenant_id)
    return {
        "tenant_id": tenant_id,
        "reuse_policy": CANONICAL_MODULE_REUSE_POLICY,
        "duplicate_policy": NO_DUPLICATE_MODULE_POLICY,
        "canonical_reuse_map": ACADEMIC_OPERATIONS_CANONICAL_REUSE_MAP,
        "bridge_map": ACADEMIC_OPERATIONS_BRIDGE_MAP,
        "bridge_counts": repository.get_canonical_bridge_summary(db, tenant_id),
    }


def get_academic_operations_dashboard_service(db: Session, tenant_id: int) -> AcademicOperationsDashboardResponse:
    tenant_id = validate_tenant_id(tenant_id)
    counts = repository.compute_dashboard_summary(db, tenant_id)
    flat_total = sum(sum(group.values()) for group in counts.values())
    incomplete_data = flat_total == 0 or sum(counts["canonical_bridges"].values()) == 0
    limitations = _merge_limitations(["dashboard_computed_from_metadata_only"])
    repository.create_dashboard_snapshot(
        db,
        tenant_id,
        status="ACTIVE",
        fake_metrics=False,
        incomplete_data=incomplete_data,
        data_source="computed_from_academic_operations_metadata",
        summary_json=counts,
        limitations_json=limitations,
        source_capability_id="VRT-203",
        source_matrix_row_id="VRT-203",
    )
    _commit(db)
    return AcademicOperationsDashboardResponse(
        tenant_id=tenant_id,
        fake_metrics=False,
        data_source="computed_from_academic_operations_metadata",
        master_matrix_commit=MASTER_MATRIX_COMMIT,
        master_matrix_rows=MASTER_MATRIX_ROW_COUNT,
        incomplete_data=incomplete_data,
        limitations=limitations,
        counts={key: sum(value.values()) for key, value in counts.items()},
        canonical_bridge_counts=repository.get_canonical_bridge_summary(db, tenant_id),
    )


def get_academic_operations_matrix_summary_service(db: Session, tenant_id: int) -> AcademicOperationsMatrixSummaryResponse:
    tenant_id = validate_tenant_id(tenant_id)
    _audit(db, tenant_id, entity_type="matrix_summary", entity_id=None, event_type=AcademicOperationsAuditEventType.MATRIX_SUMMARY_VIEWED, actor_user_id="system", action="get_matrix_summary")
    _commit(db)
    return AcademicOperationsMatrixSummaryResponse(
        master_matrix_commit=MASTER_MATRIX_COMMIT,
        master_matrix_rows=MASTER_MATRIX_ROW_COUNT,
        contract_version="A-036.2",
        target_level=TARGET_LEVEL,
        duplicate_module_policy=NO_DUPLICATE_MODULE_POLICY,
        true_new_modules=ACADEMIC_OPERATIONS_TRUE_NEW_MODULES,
        canonical_reuse_map=ACADEMIC_OPERATIONS_CANONICAL_REUSE_MAP,
        bridge_map=ACADEMIC_OPERATIONS_BRIDGE_MAP,
        forbidden_runtime_claims=FORBIDDEN_RUNTIME_CLAIMS,
        required_limitations=REQUIRED_LIMITATIONS,
    )


def attach_evidence_metadata_service(db: Session, tenant_id: int, actor_user_id: str, request):
    tenant_id = validate_tenant_id(tenant_id)
    actor = _validate_actor(actor_user_id)
    payload = _create_payload(request, actor)
    payload.pop("evidence_kind", None)
    payload.pop("entity_type", None)
    payload.pop("entity_id", None)
    entity = repository.attach_evidence_metadata(
        db,
        tenant_id,
        evidence_kind=request.evidence_kind,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        metadata_json=payload.pop("metadata_json", {}),
        **payload,
    )
    _audit(db, tenant_id, entity_type="evidence_metadata", entity_id=entity.id, event_type=AcademicOperationsAuditEventType.EVIDENCE_METADATA_ATTACHED, actor_user_id=actor, action="attach_evidence_metadata", new_status=entity.status)
    _commit(db)
    return entity


def list_evidence_metadata_service(db: Session, tenant_id: int):
    return repository.list_evidence_metadata(db, validate_tenant_id(tenant_id))


def list_audit_events_service(db: Session, tenant_id: int):
    return repository.list_audit_events(db, validate_tenant_id(tenant_id))


def get_academic_operations_health_service(db: Session, tenant_id: int) -> AcademicOperationsHealthResponse:
    tenant_id = validate_tenant_id(tenant_id)
    summary = repository.get_health_summary(db, tenant_id)
    _audit(db, tenant_id, entity_type="health", entity_id=None, event_type=AcademicOperationsAuditEventType.HEALTH_VIEWED, actor_user_id="system", action="get_health")
    _commit(db)
    return AcademicOperationsHealthResponse(
        tenant_id=tenant_id,
        module=MODULE_NAME,
        target_level=TARGET_LEVEL,
        foundation_status="MATRIX_GUIDED_CANONICAL_AWARE_BACKEND_FOUNDATION",
        duplicate_module_policy=NO_DUPLICATE_MODULE_POLICY,
        provider_integration_enabled=False,
        platonus_sync_enabled=False,
        sis_sync_enabled=False,
        hidden_score_present=False,
        fake_metrics=False,
        incomplete_data=summary["total_records"] == 0,
        limitations=_merge_limitations(["runtime_foundation_only"]),
        route_count=39,
        table_count=19,
    )