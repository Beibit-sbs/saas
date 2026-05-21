"""Service layer for Student Lifecycle Suite backend foundation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, validate_tenant_id_provided
from app.modules.student_lifecycle import repository
from app.modules.student_lifecycle.models import (
    ApplicantStatus,
    DegreeProgressStatus,
    EnrollmentStatus,
    InterventionStatus,
    StudentAppealStatus,
    StudentLifecycleAuditEventType,
    StudentRequestStatus,
    StudentStatus,
    TranscriptPreviewStatus,
)
from app.modules.student_lifecycle.schemas import StudentLifecycleDashboardResponse, StudentLifecycleHealthResponse


def _now() -> datetime:
    return datetime.now(UTC)


APPLICANT_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    ApplicantStatus.DRAFT: frozenset({ApplicantStatus.SUBMITTED, ApplicantStatus.ARCHIVED}),
    ApplicantStatus.SUBMITTED: frozenset({ApplicantStatus.UNDER_REVIEW, ApplicantStatus.ARCHIVED}),
    ApplicantStatus.UNDER_REVIEW: frozenset({ApplicantStatus.ADDITIONAL_INFO_REQUESTED, ApplicantStatus.DECISION_METADATA_RECORDED, ApplicantStatus.ARCHIVED}),
    ApplicantStatus.ADDITIONAL_INFO_REQUESTED: frozenset({ApplicantStatus.UNDER_REVIEW, ApplicantStatus.ARCHIVED}),
    ApplicantStatus.DECISION_METADATA_RECORDED: frozenset({ApplicantStatus.ACCEPTED, ApplicantStatus.ARCHIVED}),
    ApplicantStatus.ACCEPTED: frozenset({ApplicantStatus.STUDENT_PROFILE_PENDING, ApplicantStatus.ARCHIVED}),
    ApplicantStatus.STUDENT_PROFILE_PENDING: frozenset({ApplicantStatus.STUDENT_PROFILE_CREATED, ApplicantStatus.ARCHIVED}),
    ApplicantStatus.STUDENT_PROFILE_CREATED: frozenset({ApplicantStatus.ARCHIVED}),
    ApplicantStatus.ARCHIVED: frozenset(),
}

STUDENT_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    StudentStatus.PROFILE_CREATED: frozenset({StudentStatus.ACTIVE, StudentStatus.ARCHIVED}),
    StudentStatus.ACTIVE: frozenset({StudentStatus.ON_LEAVE, StudentStatus.SUSPENDED, StudentStatus.WITHDRAWN, StudentStatus.GRADUATED_METADATA, StudentStatus.ARCHIVED}),
    StudentStatus.ON_LEAVE: frozenset({StudentStatus.ACTIVE, StudentStatus.ARCHIVED}),
    StudentStatus.SUSPENDED: frozenset({StudentStatus.ACTIVE, StudentStatus.ARCHIVED}),
    StudentStatus.WITHDRAWN: frozenset({StudentStatus.ARCHIVED}),
    StudentStatus.GRADUATED_METADATA: frozenset({StudentStatus.ARCHIVED}),
    StudentStatus.ARCHIVED: frozenset(),
}

ENROLLMENT_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    EnrollmentStatus.DRAFT: frozenset({EnrollmentStatus.COURSE_SELECTION_PENDING, EnrollmentStatus.CLOSED}),
    EnrollmentStatus.COURSE_SELECTION_PENDING: frozenset({EnrollmentStatus.SUBMITTED, EnrollmentStatus.CLOSED}),
    EnrollmentStatus.SUBMITTED: frozenset({EnrollmentStatus.REGISTRAR_REVIEW, EnrollmentStatus.CLOSED}),
    EnrollmentStatus.REGISTRAR_REVIEW: frozenset({EnrollmentStatus.ENROLLED, EnrollmentStatus.CLOSED}),
    EnrollmentStatus.ENROLLED: frozenset({EnrollmentStatus.CHANGED, EnrollmentStatus.WITHDRAWN, EnrollmentStatus.SUSPENDED, EnrollmentStatus.CLOSED}),
    EnrollmentStatus.CHANGED: frozenset({EnrollmentStatus.ENROLLED, EnrollmentStatus.CLOSED}),
    EnrollmentStatus.WITHDRAWN: frozenset({EnrollmentStatus.CLOSED}),
    EnrollmentStatus.SUSPENDED: frozenset({EnrollmentStatus.CLOSED}),
    EnrollmentStatus.CLOSED: frozenset(),
}

REQUEST_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    StudentRequestStatus.DRAFT: frozenset({StudentRequestStatus.SUBMITTED, StudentRequestStatus.ARCHIVED}),
    StudentRequestStatus.SUBMITTED: frozenset({StudentRequestStatus.ROUTED, StudentRequestStatus.ARCHIVED}),
    StudentRequestStatus.ROUTED: frozenset({StudentRequestStatus.UNDER_REVIEW, StudentRequestStatus.ARCHIVED}),
    StudentRequestStatus.UNDER_REVIEW: frozenset({StudentRequestStatus.DECISION_METADATA_RECORDED, StudentRequestStatus.ARCHIVED}),
    StudentRequestStatus.DECISION_METADATA_RECORDED: frozenset({StudentRequestStatus.RESPONSE_ISSUED, StudentRequestStatus.ARCHIVED}),
    StudentRequestStatus.RESPONSE_ISSUED: frozenset({StudentRequestStatus.CLOSED}),
    StudentRequestStatus.CLOSED: frozenset({StudentRequestStatus.ARCHIVED}),
    StudentRequestStatus.ARCHIVED: frozenset(),
}

APPEAL_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    StudentAppealStatus.DRAFT: frozenset({StudentAppealStatus.SUBMITTED, StudentAppealStatus.ARCHIVED}),
    StudentAppealStatus.SUBMITTED: frozenset({StudentAppealStatus.ELIGIBILITY_CHECK, StudentAppealStatus.ARCHIVED}),
    StudentAppealStatus.ELIGIBILITY_CHECK: frozenset({StudentAppealStatus.REVIEWER_REVIEW, StudentAppealStatus.ARCHIVED}),
    StudentAppealStatus.REVIEWER_REVIEW: frozenset({StudentAppealStatus.COMMITTEE_REVIEW, StudentAppealStatus.DECISION_METADATA_RECORDED, StudentAppealStatus.ARCHIVED}),
    StudentAppealStatus.COMMITTEE_REVIEW: frozenset({StudentAppealStatus.DECISION_METADATA_RECORDED, StudentAppealStatus.ARCHIVED}),
    StudentAppealStatus.DECISION_METADATA_RECORDED: frozenset({StudentAppealStatus.RESPONSE_ISSUED, StudentAppealStatus.ARCHIVED}),
    StudentAppealStatus.RESPONSE_ISSUED: frozenset({StudentAppealStatus.CLOSED}),
    StudentAppealStatus.CLOSED: frozenset({StudentAppealStatus.ARCHIVED}),
    StudentAppealStatus.ARCHIVED: frozenset(),
}

INTERVENTION_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    InterventionStatus.SIGNAL_REGISTERED: frozenset({InterventionStatus.ADVISOR_REVIEW_REQUIRED}),
    InterventionStatus.ADVISOR_REVIEW_REQUIRED: frozenset({InterventionStatus.INTERVENTION_DRAFT}),
    InterventionStatus.INTERVENTION_DRAFT: frozenset({InterventionStatus.CONTACT_PLANNED}),
    InterventionStatus.CONTACT_PLANNED: frozenset({InterventionStatus.FOLLOW_UP_SCHEDULED}),
    InterventionStatus.FOLLOW_UP_SCHEDULED: frozenset({InterventionStatus.PROGRESS_NOTE_RECORDED}),
    InterventionStatus.PROGRESS_NOTE_RECORDED: frozenset({InterventionStatus.OUTCOME_METADATA_RECORDED}),
    InterventionStatus.OUTCOME_METADATA_RECORDED: frozenset({InterventionStatus.CLOSED, InterventionStatus.CONTINUED}),
    InterventionStatus.CLOSED: frozenset(),
    InterventionStatus.CONTINUED: frozenset({InterventionStatus.FOLLOW_UP_SCHEDULED, InterventionStatus.CLOSED}),
}


def _validate_actor(actor_user_id: str | int | None) -> str:
    actor = str(actor_user_id or "").strip()
    if not actor:
        raise DomainValidationError("actor_user_id is required")
    return actor


def _validate_transition(current_status: str, new_status: str, allowed: dict[str, frozenset[str]], name: str) -> None:
    if new_status == current_status:
        raise DomainValidationError(f"{name} status transition must change current status")
    next_values = allowed.get(current_status)
    if next_values is None or new_status not in next_values:
        raise DomainValidationError(f"invalid_{name}_status_transition: {current_status} -> {new_status}")


def _audit(db: Session, tenant_id: int, *, entity_type: str, entity_id: int, event_type: str, actor_user_id: str, action: str, previous_status: str | None = None, new_status: str | None = None, human_review_required: bool = True, payload: dict[str, Any] | None = None) -> None:
    repository.create_audit_event(
        db,
        tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        actor_user_id=actor_user_id,
        previous_status=previous_status,
        new_status=new_status,
        human_review_required=human_review_required,
        automated_decision=False,
        provider_integration_enabled=False,
        action=action,
        payload_json=payload or {},
    )


def _commit(db: Session):
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _limitations(values: list[str] | None, fallback: list[str] | None = None) -> list[str]:
    combined = list(values or [])
    for item in fallback or []:
        if item not in combined:
            combined.append(item)
    return combined


def create_applicant_service(db: Session, tenant_id: int, actor_user_id: str, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_applicant(
        db,
        tenant_id,
        applicant_code=request.applicant_code,
        program_interest=request.program_interest,
        entry_term=request.entry_term,
        notes=request.notes,
        source_available=request.source_available,
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        limitations_json=_limitations(request.limitations),
        created_by_user_id=actor,
    )
    repository.record_applicant_status(db, tenant_id, entity.id, None, entity.status, actor, "applicant_created")
    _audit(db, tenant_id, entity_type="applicant", entity_id=entity.id, event_type=StudentLifecycleAuditEventType.APPLICANT_CREATED, actor_user_id=actor, action="create_applicant", new_status=entity.status)
    _commit(db)
    return entity


def list_applicants_service(db: Session, tenant_id: int) -> list[Any]:
    return repository.list_applicants(db, validate_tenant_id_provided(tenant_id))


def get_applicant_service(db: Session, tenant_id: int, applicant_id: int) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    entity = repository.get_applicant(db, tenant_id, applicant_id)
    if entity is None:
        raise DomainValidationError(f"applicant {applicant_id} not found in tenant scope")
    return entity


def update_applicant_service(db: Session, tenant_id: int, applicant_id: int, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    payload = request.model_dump(exclude_none=True)
    payload["limitations_json"] = _limitations(payload.pop("limitations", None))
    return repository.update_applicant(db, tenant_id, applicant_id, **payload)


def submit_applicant_service(db: Session, tenant_id: int, actor_user_id: str, applicant_id: int) -> Any:
    return update_applicant_status_service(db, tenant_id, actor_user_id, applicant_id, ApplicantStatus.SUBMITTED, "submitted")


def update_applicant_status_service(db: Session, tenant_id: int, actor_user_id: str, applicant_id: int, new_status: str, reason: str | None = None) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = get_applicant_service(db, tenant_id, applicant_id)
    _validate_transition(entity.status, new_status, APPLICANT_ALLOWED_TRANSITIONS, "applicant")
    previous_status = entity.status
    updated = repository.update_applicant(db, tenant_id, applicant_id, status=new_status, archived_at=_now() if new_status == ApplicantStatus.ARCHIVED else entity.archived_at)
    repository.record_applicant_status(db, tenant_id, applicant_id, previous_status, new_status, actor, reason)
    _audit(db, tenant_id, entity_type="applicant", entity_id=applicant_id, event_type=StudentLifecycleAuditEventType.APPLICANT_STATUS_CHANGED, actor_user_id=actor, action="update_applicant_status", previous_status=previous_status, new_status=new_status, human_review_required=updated.human_review_required)
    _commit(db)
    return updated


def list_applicant_status_history_service(db: Session, tenant_id: int, applicant_id: int) -> list[Any]:
    return repository.list_applicant_status_history(db, validate_tenant_id_provided(tenant_id), applicant_id)


def create_student_profile_service(db: Session, tenant_id: int, actor_user_id: str, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_student_profile(
        db,
        tenant_id,
        student_code=request.student_code,
        source_applicant_id=request.source_applicant_id,
        program_code=request.program_code,
        notes=request.notes,
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        limitations_json=_limitations(request.limitations),
        created_by_user_id=actor,
    )
    repository.record_student_status(db, tenant_id, entity.id, None, entity.status, actor, "student_profile_created")
    _audit(db, tenant_id, entity_type="student", entity_id=entity.id, event_type=StudentLifecycleAuditEventType.STUDENT_PROFILE_CREATED, actor_user_id=actor, action="create_student_profile", new_status=entity.status)
    _commit(db)
    return entity


def list_student_profiles_service(db: Session, tenant_id: int) -> list[Any]:
    return repository.list_student_profiles(db, validate_tenant_id_provided(tenant_id))


def get_student_profile_service(db: Session, tenant_id: int, student_id: int) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    entity = repository.get_student_profile(db, tenant_id, student_id)
    if entity is None:
        raise DomainValidationError(f"student {student_id} not found in tenant scope")
    return entity


def update_student_profile_service(db: Session, tenant_id: int, student_id: int, request) -> Any:
    payload = request.model_dump(exclude_none=True)
    payload["limitations_json"] = _limitations(payload.pop("limitations", None))
    return repository.update_student_profile(db, validate_tenant_id_provided(tenant_id), student_id, **payload)


def update_student_profile_status_service(db: Session, tenant_id: int, actor_user_id: str, student_id: int, new_status: str, reason: str | None = None) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = get_student_profile_service(db, tenant_id, student_id)
    _validate_transition(entity.status, new_status, STUDENT_ALLOWED_TRANSITIONS, "student")
    previous_status = entity.status
    updated = repository.update_student_profile(db, tenant_id, student_id, status=new_status, archived_at=_now() if new_status == StudentStatus.ARCHIVED else entity.archived_at)
    repository.record_student_status(db, tenant_id, student_id, previous_status, new_status, actor, reason)
    _audit(db, tenant_id, entity_type="student", entity_id=student_id, event_type=StudentLifecycleAuditEventType.STUDENT_STATUS_CHANGED, actor_user_id=actor, action="update_student_status", previous_status=previous_status, new_status=new_status, human_review_required=updated.human_review_required)
    _commit(db)
    return updated


def list_student_status_history_service(db: Session, tenant_id: int, student_id: int) -> list[Any]:
    return repository.list_student_status_history(db, validate_tenant_id_provided(tenant_id), student_id)


def create_student_enrollment_service(db: Session, tenant_id: int, actor_user_id: str, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_student_enrollment(
        db,
        tenant_id,
        student_id=request.student_id,
        term_code=request.term_code,
        notes=request.notes,
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        limitations_json=_limitations(request.limitations),
        created_by_user_id=actor,
    )
    repository.record_enrollment_status(db, tenant_id, entity.id, None, entity.status, actor, "enrollment_created")
    _audit(db, tenant_id, entity_type="enrollment", entity_id=entity.id, event_type=StudentLifecycleAuditEventType.ENROLLMENT_CREATED, actor_user_id=actor, action="create_student_enrollment", new_status=entity.status)
    _commit(db)
    return entity


def list_student_enrollments_service(db: Session, tenant_id: int) -> list[Any]:
    return repository.list_student_enrollments(db, validate_tenant_id_provided(tenant_id))


def get_student_enrollment_service(db: Session, tenant_id: int, enrollment_id: int) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    entity = repository.get_student_enrollment(db, tenant_id, enrollment_id)
    if entity is None:
        raise DomainValidationError(f"enrollment {enrollment_id} not found in tenant scope")
    return entity


def update_student_enrollment_service(db: Session, tenant_id: int, enrollment_id: int, request) -> Any:
    payload = request.model_dump(exclude_none=True)
    payload["limitations_json"] = _limitations(payload.pop("limitations", None))
    return repository.update_student_enrollment(db, validate_tenant_id_provided(tenant_id), enrollment_id, **payload)


def review_student_enrollment_service(db: Session, tenant_id: int, actor_user_id: str, enrollment_id: int, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = get_student_enrollment_service(db, tenant_id, enrollment_id)
    _validate_transition(entity.status, request.new_status, ENROLLMENT_ALLOWED_TRANSITIONS, "enrollment")
    previous_status = entity.status
    updated = repository.update_student_enrollment(db, tenant_id, enrollment_id, status=request.new_status)
    repository.record_enrollment_status(db, tenant_id, enrollment_id, previous_status, request.new_status, actor, request.comment)
    _audit(db, tenant_id, entity_type="enrollment", entity_id=enrollment_id, event_type=StudentLifecycleAuditEventType.ENROLLMENT_REVIEWED, actor_user_id=actor, action="review_student_enrollment", previous_status=previous_status, new_status=request.new_status, human_review_required=updated.human_review_required)
    _commit(db)
    return updated


def list_enrollment_status_history_service(db: Session, tenant_id: int, enrollment_id: int) -> list[Any]:
    return repository.list_enrollment_status_history(db, validate_tenant_id_provided(tenant_id), enrollment_id)


def open_academic_record_service(db: Session, tenant_id: int, actor_user_id: str, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_academic_record(
        db,
        tenant_id,
        student_id=request.student_id,
        record_name=request.record_name,
        source_available=request.source_available,
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        result_metadata_json={},
        limitations_json=_limitations(request.limitations, ["Official transcript issuance is not implemented in this foundation slice."]),
        created_by_user_id=actor,
    )
    _audit(db, tenant_id, entity_type="academic_record", entity_id=entity.id, event_type=StudentLifecycleAuditEventType.ACADEMIC_RECORD_OPENED, actor_user_id=actor, action="open_academic_record", new_status=entity.status, human_review_required=True)
    _commit(db)
    return entity


def list_academic_records_service(db: Session, tenant_id: int) -> list[Any]:
    return repository.list_academic_records(db, validate_tenant_id_provided(tenant_id))


def get_academic_record_service(db: Session, tenant_id: int, record_id: int) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    entity = repository.get_academic_record(db, tenant_id, record_id)
    if entity is None:
        raise DomainValidationError(f"academic_record {record_id} not found in tenant scope")
    return entity


def generate_transcript_preview_service(db: Session, tenant_id: int, actor_user_id: str, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_transcript_preview(
        db,
        tenant_id,
        student_id=request.student_id,
        academic_record_id=request.academic_record_id,
        status=TranscriptPreviewStatus.GENERATED_UNOFFICIAL_PREVIEW,
        official_document=False,
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        preview_payload_json=request.preview_payload,
        limitations_json=_limitations(request.limitations, ["Unofficial preview only; official transcript issuing is deferred."]),
        created_by_user_id=actor,
    )
    _audit(db, tenant_id, entity_type="transcript_preview", entity_id=entity.id, event_type=StudentLifecycleAuditEventType.TRANSCRIPT_PREVIEW_GENERATED, actor_user_id=actor, action="generate_transcript_preview", new_status=entity.status, human_review_required=True)
    _commit(db)
    return entity


def list_transcript_previews_service(db: Session, tenant_id: int) -> list[Any]:
    return repository.list_transcript_previews(db, validate_tenant_id_provided(tenant_id))


def get_transcript_preview_service(db: Session, tenant_id: int, preview_id: int) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    entity = repository.get_transcript_preview(db, tenant_id, preview_id)
    if entity is None:
        raise DomainValidationError(f"transcript_preview {preview_id} not found in tenant scope")
    return entity


def compute_degree_progress_snapshot_service(db: Session, tenant_id: int, actor_user_id: str, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    status = DegreeProgressStatus.INCOMPLETE_DATA if request.incomplete_data else DegreeProgressStatus.COMPUTED_FROM_AVAILABLE_SOURCES
    limitations = _limitations(request.limitations)
    if request.incomplete_data:
        limitations = _limitations(limitations, ["Completion percentages remain non-authoritative when source data is incomplete."])
    entity = repository.create_degree_progress_snapshot(
        db,
        tenant_id,
        student_id=request.student_id,
        status=status,
        data_source="computed_from_student_lifecycle_metadata",
        incomplete_data=request.incomplete_data,
        hidden_score_present=False,
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        completion_summary_json=request.completion_summary,
        limitations_json=limitations,
        created_by_user_id=actor,
    )
    _audit(db, tenant_id, entity_type="degree_progress_snapshot", entity_id=entity.id, event_type=StudentLifecycleAuditEventType.DEGREE_PROGRESS_COMPUTED, actor_user_id=actor, action="compute_degree_progress_snapshot", new_status=entity.status, human_review_required=True)
    _commit(db)
    return entity


def get_degree_progress_snapshot_service(db: Session, tenant_id: int, student_id: int) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    entity = repository.get_latest_degree_progress_snapshot_for_student(db, tenant_id, student_id)
    if entity is None:
        raise DomainValidationError(f"degree_progress snapshot for student {student_id} not found in tenant scope")
    return entity


def review_graduation_readiness_service(db: Session, tenant_id: int, actor_user_id: str, student_id: int, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = get_degree_progress_snapshot_service(db, tenant_id, student_id)
    previous_status = entity.status
    if request.new_status not in {
        DegreeProgressStatus.HUMAN_REVIEW_REQUIRED,
        DegreeProgressStatus.GRADUATION_READY_METADATA,
        DegreeProgressStatus.NOT_READY_METADATA,
        DegreeProgressStatus.ADVISOR_REVIEW_REQUIRED,
    }:
        raise DomainValidationError("graduation readiness review status is not allowed in the foundation slice")
    updated = repository.update_degree_progress_snapshot(
        db,
        tenant_id,
        entity.id,
        status=request.new_status,
        human_review_required=True,
        limitations_json=_limitations(list(entity.limitations_json or []), [request.note] if request.note else []),
    )
    _audit(db, tenant_id, entity_type="degree_progress_snapshot", entity_id=entity.id, event_type=StudentLifecycleAuditEventType.GRADUATION_READINESS_REVIEWED, actor_user_id=actor, action="review_graduation_readiness", previous_status=previous_status, new_status=request.new_status, human_review_required=True)
    _commit(db)
    return updated


def create_student_request_service(db: Session, tenant_id: int, actor_user_id: str, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_student_request(
        db,
        tenant_id,
        student_id=request.student_id,
        request_type=request.request_type,
        description=request.description,
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        limitations_json=_limitations(request.limitations),
        created_by_user_id=actor,
    )
    _audit(db, tenant_id, entity_type="student_request", entity_id=entity.id, event_type=StudentLifecycleAuditEventType.STUDENT_REQUEST_SUBMITTED, actor_user_id=actor, action="create_student_request", new_status=entity.status, human_review_required=True)
    _commit(db)
    return entity


def list_student_requests_service(db: Session, tenant_id: int) -> list[Any]:
    return repository.list_student_requests(db, validate_tenant_id_provided(tenant_id))


def get_student_request_service(db: Session, tenant_id: int, request_id: int) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    entity = repository.get_student_request(db, tenant_id, request_id)
    if entity is None:
        raise DomainValidationError(f"student_request {request_id} not found in tenant scope")
    return entity


def review_student_request_service(db: Session, tenant_id: int, actor_user_id: str, request_id: int, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = get_student_request_service(db, tenant_id, request_id)
    _validate_transition(entity.status, request.new_status, REQUEST_ALLOWED_TRANSITIONS, "student_request")
    previous_status = entity.status
    updated = repository.update_student_request(db, tenant_id, request_id, status=request.new_status, decision_note=request.decision_note, automated_decision=False, provider_integration_enabled=False, human_review_required=True)
    _audit(db, tenant_id, entity_type="student_request", entity_id=request_id, event_type=StudentLifecycleAuditEventType.STUDENT_REQUEST_REVIEWED, actor_user_id=actor, action="review_student_request", previous_status=previous_status, new_status=request.new_status, human_review_required=True)
    _commit(db)
    return updated


def create_student_appeal_service(db: Session, tenant_id: int, actor_user_id: str, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_student_appeal(
        db,
        tenant_id,
        student_id=request.student_id,
        appeal_type=request.appeal_type,
        description=request.description,
        human_review_required=True,
        automated_decision=False,
        provider_integration_enabled=False,
        limitations_json=_limitations(request.limitations),
        created_by_user_id=actor,
    )
    _audit(db, tenant_id, entity_type="student_appeal", entity_id=entity.id, event_type=StudentLifecycleAuditEventType.STUDENT_APPEAL_SUBMITTED, actor_user_id=actor, action="create_student_appeal", new_status=entity.status, human_review_required=True)
    _commit(db)
    return entity


def list_student_appeals_service(db: Session, tenant_id: int) -> list[Any]:
    return repository.list_student_appeals(db, validate_tenant_id_provided(tenant_id))


def get_student_appeal_service(db: Session, tenant_id: int, appeal_id: int) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    entity = repository.get_student_appeal(db, tenant_id, appeal_id)
    if entity is None:
        raise DomainValidationError(f"student_appeal {appeal_id} not found in tenant scope")
    return entity


def review_student_appeal_service(db: Session, tenant_id: int, actor_user_id: str, appeal_id: int, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = get_student_appeal_service(db, tenant_id, appeal_id)
    _validate_transition(entity.status, request.new_status, APPEAL_ALLOWED_TRANSITIONS, "student_appeal")
    previous_status = entity.status
    updated = repository.update_student_appeal(db, tenant_id, appeal_id, status=request.new_status, decision_note=request.decision_note, automated_decision=False, provider_integration_enabled=False, human_review_required=True)
    _audit(db, tenant_id, entity_type="student_appeal", entity_id=appeal_id, event_type=StudentLifecycleAuditEventType.STUDENT_APPEAL_REVIEWED, actor_user_id=actor, action="review_student_appeal", previous_status=previous_status, new_status=request.new_status, human_review_required=True)
    _commit(db)
    return updated


def create_intervention_plan_service(db: Session, tenant_id: int, actor_user_id: str, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.create_intervention_plan(
        db,
        tenant_id,
        student_id=request.student_id,
        signal_type=request.signal_type,
        plan_summary=request.plan_summary,
        human_review_required=True,
        hidden_score_present=False,
        automated_decision=False,
        provider_integration_enabled=False,
        followups_json=[],
        limitations_json=_limitations(request.limitations),
        created_by_user_id=actor,
    )
    _audit(db, tenant_id, entity_type="intervention_plan", entity_id=entity.id, event_type=StudentLifecycleAuditEventType.INTERVENTION_PLAN_CREATED, actor_user_id=actor, action="create_intervention_plan", new_status=entity.status, human_review_required=True)
    _commit(db)
    return entity


def list_intervention_plans_service(db: Session, tenant_id: int) -> list[Any]:
    return repository.list_intervention_plans(db, validate_tenant_id_provided(tenant_id))


def get_intervention_plan_service(db: Session, tenant_id: int, plan_id: int) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    entity = repository.get_intervention_plan(db, tenant_id, plan_id)
    if entity is None:
        raise DomainValidationError(f"intervention_plan {plan_id} not found in tenant scope")
    return entity


def record_intervention_followup_service(db: Session, tenant_id: int, actor_user_id: str, plan_id: int, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = get_intervention_plan_service(db, tenant_id, plan_id)
    if entity.status not in INTERVENTION_ALLOWED_TRANSITIONS:
        raise DomainValidationError("intervention plan is not in a known lifecycle state")
    target_status = InterventionStatus.CONTINUED if request.continued else InterventionStatus.CLOSED
    if entity.status == InterventionStatus.SIGNAL_REGISTERED:
        target_status = InterventionStatus.ADVISOR_REVIEW_REQUIRED
    elif entity.status == InterventionStatus.ADVISOR_REVIEW_REQUIRED:
        target_status = InterventionStatus.INTERVENTION_DRAFT
    elif entity.status == InterventionStatus.INTERVENTION_DRAFT:
        target_status = InterventionStatus.CONTACT_PLANNED
    elif entity.status == InterventionStatus.CONTACT_PLANNED:
        target_status = InterventionStatus.FOLLOW_UP_SCHEDULED
    elif entity.status == InterventionStatus.FOLLOW_UP_SCHEDULED:
        target_status = InterventionStatus.PROGRESS_NOTE_RECORDED
    elif entity.status == InterventionStatus.PROGRESS_NOTE_RECORDED:
        target_status = InterventionStatus.OUTCOME_METADATA_RECORDED
    elif entity.status == InterventionStatus.OUTCOME_METADATA_RECORDED:
        target_status = InterventionStatus.CONTINUED if request.continued else InterventionStatus.CLOSED
    _validate_transition(entity.status, target_status, INTERVENTION_ALLOWED_TRANSITIONS, "intervention")
    updated = repository.record_intervention_followup(
        db,
        tenant_id,
        plan_id,
        {"actor_user_id": actor, "outcome_note": request.outcome_note, "recorded_at": _now().isoformat(), "continued": request.continued},
        target_status,
    )
    _audit(db, tenant_id, entity_type="intervention_plan", entity_id=plan_id, event_type=StudentLifecycleAuditEventType.INTERVENTION_FOLLOWUP_RECORDED, actor_user_id=actor, action="record_intervention_followup", previous_status=entity.status, new_status=target_status, human_review_required=True)
    _commit(db)
    return updated


def attach_evidence_metadata_service(db: Session, tenant_id: int, actor_user_id: str, request) -> Any:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    entity = repository.attach_evidence_metadata(
        db,
        tenant_id,
        audit_event_id=request.audit_event_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        evidence_type=request.evidence_type,
        evidence_ref=request.evidence_ref,
        limitations_json=_limitations(request.limitations),
        created_by_user_id=actor,
    )
    _audit(db, tenant_id, entity_type=request.entity_type, entity_id=request.entity_id, event_type=StudentLifecycleAuditEventType.EVIDENCE_METADATA_ATTACHED, actor_user_id=actor, action="attach_evidence_metadata", payload={"evidence_type": request.evidence_type, "evidence_ref": request.evidence_ref})
    _commit(db)
    return entity


def list_evidence_metadata_service(db: Session, tenant_id: int) -> list[Any]:
    return repository.list_evidence_metadata(db, validate_tenant_id_provided(tenant_id))


def list_student_lifecycle_audit_events_service(db: Session, tenant_id: int) -> list[Any]:
    return repository.list_audit_events(db, validate_tenant_id_provided(tenant_id))


def get_student_lifecycle_dashboard_service(db: Session, tenant_id: int, actor_user_id: str) -> StudentLifecycleDashboardResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    summary = repository.compute_student_lifecycle_dashboard_summary(db, tenant_id)
    _audit(db, tenant_id, entity_type="dashboard", entity_id=tenant_id, event_type=StudentLifecycleAuditEventType.DASHBOARD_VIEWED, actor_user_id=actor, action="view_dashboard", human_review_required=False)
    _commit(db)
    return StudentLifecycleDashboardResponse(
        tenant_id=tenant_id,
        generated_at=_now(),
        fake_metrics=False,
        data_source="computed_from_student_lifecycle_metadata",
        incomplete_data=bool(summary["incomplete_data"]),
        limitations=list(summary["limitations"]),
        applicant_counts_by_status=summary["applicant_counts_by_status"],
        student_counts_by_status=summary["student_counts_by_status"],
        enrollment_counts_by_status=summary["enrollment_counts_by_status"],
        transcript_preview_counts=summary["transcript_preview_counts"],
        degree_progress_counts=summary["degree_progress_counts"],
        request_counts_by_status=summary["request_counts_by_status"],
        appeal_counts_by_status=summary["appeal_counts_by_status"],
        intervention_counts_by_status=summary["intervention_counts_by_status"],
        human_review_required_count=int(summary["human_review_required_count"]),
        provider_integration_enabled=False,
        automated_decision_count=0,
        hidden_score_present=False,
    )


def get_student_lifecycle_health_service(tenant_id: int, route_count: int, table_count: int) -> StudentLifecycleHealthResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    return StudentLifecycleHealthResponse(
        tenant_id=tenant_id,
        generated_at=_now(),
        route_count=route_count,
        table_count=table_count,
        fake_metrics=False,
        data_source="computed_from_student_lifecycle_metadata",
        incomplete_data=False,
        limitations=[
            "Controlled backend foundation only.",
            "Frontend, provider integration, and official transcript issuing remain deferred.",
        ],
        provider_integration_enabled=False,
        automated_decision_count=0,
        hidden_score_present=False,
    )