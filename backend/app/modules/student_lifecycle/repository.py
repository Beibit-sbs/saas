"""Repository helpers for Student Lifecycle Suite backend foundation."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import TenantResourceNotFoundError, validate_tenant_id_provided
from app.modules.student_lifecycle.models import (
    StudentLifecycleAcademicRecord,
    StudentLifecycleApplicant,
    StudentLifecycleApplicantStatusHistory,
    StudentLifecycleAuditEvent,
    StudentLifecycleDegreeProgressSnapshot,
    StudentLifecycleEnrollment,
    StudentLifecycleEnrollmentStatusHistory,
    StudentLifecycleEvidenceMetadata,
    StudentLifecycleInterventionPlan,
    StudentLifecycleStudentAppeal,
    StudentLifecycleStudentProfile,
    StudentLifecycleStudentRequest,
    StudentLifecycleStudentStatusHistory,
    StudentLifecycleTranscriptPreview,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _normalized_limitations(value: list[str] | None) -> list[str]:
    return list(value or [])


def _require(resource: object | None, tenant_id: int, resource_name: str, resource_id: int) -> object:
    if resource is None:
        raise TenantResourceNotFoundError(f"{resource_name} {resource_id} not found for tenant {tenant_id}")
    return resource


def _tenant_filtered_get(db: Session, model, tenant_id: int, resource_id: int):
    validate_tenant_id_provided(tenant_id)
    return db.execute(select(model).where(and_(model.tenant_id == tenant_id, model.id == resource_id))).scalar_one_or_none()


def _tenant_filtered_list(db: Session, model, tenant_id: int):
    validate_tenant_id_provided(tenant_id)
    return list(db.execute(select(model).where(model.tenant_id == tenant_id).order_by(model.created_at.desc())).scalars().all())


def _count_by_status(db: Session, model, tenant_id: int) -> dict[str, int]:
    rows = db.execute(
        select(model.status, func.count()).where(model.tenant_id == tenant_id).group_by(model.status)
    ).all()
    return {str(status): int(total) for status, total in rows}


def create_applicant(db: Session, tenant_id: int, **kwargs) -> StudentLifecycleApplicant:
    obj = StudentLifecycleApplicant(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def get_applicant(db: Session, tenant_id: int, applicant_id: int) -> StudentLifecycleApplicant | None:
    return _tenant_filtered_get(db, StudentLifecycleApplicant, tenant_id, applicant_id)


def list_applicants(db: Session, tenant_id: int) -> list[StudentLifecycleApplicant]:
    return _tenant_filtered_list(db, StudentLifecycleApplicant, tenant_id)


def update_applicant(db: Session, tenant_id: int, applicant_id: int, **kwargs) -> StudentLifecycleApplicant:
    obj = _require(get_applicant(db, tenant_id, applicant_id), tenant_id, "applicant", applicant_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def record_applicant_status(db: Session, tenant_id: int, applicant_id: int, previous_status: str | None, new_status: str, actor_user_id: str, reason: str | None = None) -> StudentLifecycleApplicantStatusHistory:
    obj = StudentLifecycleApplicantStatusHistory(
        tenant_id=tenant_id,
        applicant_id=applicant_id,
        previous_status=previous_status,
        new_status=new_status,
        actor_user_id=actor_user_id,
        reason=reason,
        created_at=_now(),
    )
    db.add(obj)
    db.flush()
    return obj


def list_applicant_status_history(db: Session, tenant_id: int, applicant_id: int) -> list[StudentLifecycleApplicantStatusHistory]:
    validate_tenant_id_provided(tenant_id)
    return list(db.execute(select(StudentLifecycleApplicantStatusHistory).where(and_(StudentLifecycleApplicantStatusHistory.tenant_id == tenant_id, StudentLifecycleApplicantStatusHistory.applicant_id == applicant_id)).order_by(StudentLifecycleApplicantStatusHistory.created_at.asc())).scalars().all())


def archive_applicant(db: Session, tenant_id: int, applicant_id: int) -> StudentLifecycleApplicant:
    return update_applicant(db, tenant_id, applicant_id, status="ARCHIVED", archived_at=_now())


def create_student_profile(db: Session, tenant_id: int, **kwargs) -> StudentLifecycleStudentProfile:
    obj = StudentLifecycleStudentProfile(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def get_student_profile(db: Session, tenant_id: int, student_id: int) -> StudentLifecycleStudentProfile | None:
    return _tenant_filtered_get(db, StudentLifecycleStudentProfile, tenant_id, student_id)


def list_student_profiles(db: Session, tenant_id: int) -> list[StudentLifecycleStudentProfile]:
    return _tenant_filtered_list(db, StudentLifecycleStudentProfile, tenant_id)


def update_student_profile(db: Session, tenant_id: int, student_id: int, **kwargs) -> StudentLifecycleStudentProfile:
    obj = _require(get_student_profile(db, tenant_id, student_id), tenant_id, "student", student_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def record_student_status(db: Session, tenant_id: int, student_id: int, previous_status: str | None, new_status: str, actor_user_id: str, reason: str | None = None) -> StudentLifecycleStudentStatusHistory:
    obj = StudentLifecycleStudentStatusHistory(
        tenant_id=tenant_id,
        student_id=student_id,
        previous_status=previous_status,
        new_status=new_status,
        actor_user_id=actor_user_id,
        reason=reason,
        created_at=_now(),
    )
    db.add(obj)
    db.flush()
    return obj


def list_student_status_history(db: Session, tenant_id: int, student_id: int) -> list[StudentLifecycleStudentStatusHistory]:
    validate_tenant_id_provided(tenant_id)
    return list(db.execute(select(StudentLifecycleStudentStatusHistory).where(and_(StudentLifecycleStudentStatusHistory.tenant_id == tenant_id, StudentLifecycleStudentStatusHistory.student_id == student_id)).order_by(StudentLifecycleStudentStatusHistory.created_at.asc())).scalars().all())


def create_student_enrollment(db: Session, tenant_id: int, **kwargs) -> StudentLifecycleEnrollment:
    obj = StudentLifecycleEnrollment(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def get_student_enrollment(db: Session, tenant_id: int, enrollment_id: int) -> StudentLifecycleEnrollment | None:
    return _tenant_filtered_get(db, StudentLifecycleEnrollment, tenant_id, enrollment_id)


def list_student_enrollments(db: Session, tenant_id: int) -> list[StudentLifecycleEnrollment]:
    return _tenant_filtered_list(db, StudentLifecycleEnrollment, tenant_id)


def update_student_enrollment(db: Session, tenant_id: int, enrollment_id: int, **kwargs) -> StudentLifecycleEnrollment:
    obj = _require(get_student_enrollment(db, tenant_id, enrollment_id), tenant_id, "enrollment", enrollment_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def record_enrollment_status(db: Session, tenant_id: int, enrollment_id: int, previous_status: str | None, new_status: str, actor_user_id: str, reason: str | None = None) -> StudentLifecycleEnrollmentStatusHistory:
    obj = StudentLifecycleEnrollmentStatusHistory(
        tenant_id=tenant_id,
        enrollment_id=enrollment_id,
        previous_status=previous_status,
        new_status=new_status,
        actor_user_id=actor_user_id,
        reason=reason,
        created_at=_now(),
    )
    db.add(obj)
    db.flush()
    return obj


def list_enrollment_status_history(db: Session, tenant_id: int, enrollment_id: int) -> list[StudentLifecycleEnrollmentStatusHistory]:
    validate_tenant_id_provided(tenant_id)
    return list(db.execute(select(StudentLifecycleEnrollmentStatusHistory).where(and_(StudentLifecycleEnrollmentStatusHistory.tenant_id == tenant_id, StudentLifecycleEnrollmentStatusHistory.enrollment_id == enrollment_id)).order_by(StudentLifecycleEnrollmentStatusHistory.created_at.asc())).scalars().all())


def create_academic_record(db: Session, tenant_id: int, **kwargs) -> StudentLifecycleAcademicRecord:
    obj = StudentLifecycleAcademicRecord(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def get_academic_record(db: Session, tenant_id: int, record_id: int) -> StudentLifecycleAcademicRecord | None:
    return _tenant_filtered_get(db, StudentLifecycleAcademicRecord, tenant_id, record_id)


def list_academic_records(db: Session, tenant_id: int) -> list[StudentLifecycleAcademicRecord]:
    return _tenant_filtered_list(db, StudentLifecycleAcademicRecord, tenant_id)


def update_academic_record(db: Session, tenant_id: int, record_id: int, **kwargs) -> StudentLifecycleAcademicRecord:
    obj = _require(get_academic_record(db, tenant_id, record_id), tenant_id, "academic_record", record_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def create_transcript_preview(db: Session, tenant_id: int, **kwargs) -> StudentLifecycleTranscriptPreview:
    obj = StudentLifecycleTranscriptPreview(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def get_transcript_preview(db: Session, tenant_id: int, preview_id: int) -> StudentLifecycleTranscriptPreview | None:
    return _tenant_filtered_get(db, StudentLifecycleTranscriptPreview, tenant_id, preview_id)


def list_transcript_previews(db: Session, tenant_id: int) -> list[StudentLifecycleTranscriptPreview]:
    return _tenant_filtered_list(db, StudentLifecycleTranscriptPreview, tenant_id)


def create_degree_progress_snapshot(db: Session, tenant_id: int, **kwargs) -> StudentLifecycleDegreeProgressSnapshot:
    obj = StudentLifecycleDegreeProgressSnapshot(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def get_degree_progress_snapshot(db: Session, tenant_id: int, snapshot_id: int) -> StudentLifecycleDegreeProgressSnapshot | None:
    return _tenant_filtered_get(db, StudentLifecycleDegreeProgressSnapshot, tenant_id, snapshot_id)


def get_latest_degree_progress_snapshot_for_student(db: Session, tenant_id: int, student_id: int) -> StudentLifecycleDegreeProgressSnapshot | None:
    validate_tenant_id_provided(tenant_id)
    return db.execute(select(StudentLifecycleDegreeProgressSnapshot).where(and_(StudentLifecycleDegreeProgressSnapshot.tenant_id == tenant_id, StudentLifecycleDegreeProgressSnapshot.student_id == student_id)).order_by(StudentLifecycleDegreeProgressSnapshot.created_at.desc())).scalar_one_or_none()


def list_degree_progress_snapshots(db: Session, tenant_id: int) -> list[StudentLifecycleDegreeProgressSnapshot]:
    return _tenant_filtered_list(db, StudentLifecycleDegreeProgressSnapshot, tenant_id)


def update_degree_progress_snapshot(db: Session, tenant_id: int, snapshot_id: int, **kwargs) -> StudentLifecycleDegreeProgressSnapshot:
    obj = _require(get_degree_progress_snapshot(db, tenant_id, snapshot_id), tenant_id, "degree_progress_snapshot", snapshot_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def create_student_request(db: Session, tenant_id: int, **kwargs) -> StudentLifecycleStudentRequest:
    obj = StudentLifecycleStudentRequest(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def get_student_request(db: Session, tenant_id: int, request_id: int) -> StudentLifecycleStudentRequest | None:
    return _tenant_filtered_get(db, StudentLifecycleStudentRequest, tenant_id, request_id)


def list_student_requests(db: Session, tenant_id: int) -> list[StudentLifecycleStudentRequest]:
    return _tenant_filtered_list(db, StudentLifecycleStudentRequest, tenant_id)


def update_student_request(db: Session, tenant_id: int, request_id: int, **kwargs) -> StudentLifecycleStudentRequest:
    obj = _require(get_student_request(db, tenant_id, request_id), tenant_id, "student_request", request_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def create_student_appeal(db: Session, tenant_id: int, **kwargs) -> StudentLifecycleStudentAppeal:
    obj = StudentLifecycleStudentAppeal(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def get_student_appeal(db: Session, tenant_id: int, appeal_id: int) -> StudentLifecycleStudentAppeal | None:
    return _tenant_filtered_get(db, StudentLifecycleStudentAppeal, tenant_id, appeal_id)


def list_student_appeals(db: Session, tenant_id: int) -> list[StudentLifecycleStudentAppeal]:
    return _tenant_filtered_list(db, StudentLifecycleStudentAppeal, tenant_id)


def update_student_appeal(db: Session, tenant_id: int, appeal_id: int, **kwargs) -> StudentLifecycleStudentAppeal:
    obj = _require(get_student_appeal(db, tenant_id, appeal_id), tenant_id, "student_appeal", appeal_id)
    for key, value in kwargs.items():
        setattr(obj, key, value)
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def create_intervention_plan(db: Session, tenant_id: int, **kwargs) -> StudentLifecycleInterventionPlan:
    obj = StudentLifecycleInterventionPlan(tenant_id=tenant_id, created_at=_now(), updated_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def get_intervention_plan(db: Session, tenant_id: int, plan_id: int) -> StudentLifecycleInterventionPlan | None:
    return _tenant_filtered_get(db, StudentLifecycleInterventionPlan, tenant_id, plan_id)


def list_intervention_plans(db: Session, tenant_id: int) -> list[StudentLifecycleInterventionPlan]:
    return _tenant_filtered_list(db, StudentLifecycleInterventionPlan, tenant_id)


def record_intervention_followup(db: Session, tenant_id: int, plan_id: int, followup: dict[str, object], status: str) -> StudentLifecycleInterventionPlan:
    obj = _require(get_intervention_plan(db, tenant_id, plan_id), tenant_id, "intervention_plan", plan_id)
    followups = list(obj.followups_json or [])
    followups.append(followup)
    obj.followups_json = followups
    obj.status = status
    obj.updated_at = _now()
    db.flush()
    db.refresh(obj)
    return obj


def create_audit_event(db: Session, tenant_id: int, **kwargs) -> StudentLifecycleAuditEvent:
    obj = StudentLifecycleAuditEvent(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_audit_events(db: Session, tenant_id: int) -> list[StudentLifecycleAuditEvent]:
    return _tenant_filtered_list(db, StudentLifecycleAuditEvent, tenant_id)


def attach_evidence_metadata(db: Session, tenant_id: int, **kwargs) -> StudentLifecycleEvidenceMetadata:
    obj = StudentLifecycleEvidenceMetadata(tenant_id=tenant_id, created_at=_now(), **kwargs)
    db.add(obj)
    db.flush()
    db.refresh(obj)
    return obj


def list_evidence_metadata(db: Session, tenant_id: int) -> list[StudentLifecycleEvidenceMetadata]:
    return _tenant_filtered_list(db, StudentLifecycleEvidenceMetadata, tenant_id)


def compute_student_lifecycle_dashboard_summary(db: Session, tenant_id: int) -> dict[str, object]:
    validate_tenant_id_provided(tenant_id)
    applicant_counts = _count_by_status(db, StudentLifecycleApplicant, tenant_id)
    student_counts = _count_by_status(db, StudentLifecycleStudentProfile, tenant_id)
    enrollment_counts = _count_by_status(db, StudentLifecycleEnrollment, tenant_id)
    transcript_counts = _count_by_status(db, StudentLifecycleTranscriptPreview, tenant_id)
    degree_counts = _count_by_status(db, StudentLifecycleDegreeProgressSnapshot, tenant_id)
    request_counts = _count_by_status(db, StudentLifecycleStudentRequest, tenant_id)
    appeal_counts = _count_by_status(db, StudentLifecycleStudentAppeal, tenant_id)
    intervention_counts = _count_by_status(db, StudentLifecycleInterventionPlan, tenant_id)
    human_review_required_count = sum(
        db.execute(select(func.count()).select_from(model).where(and_(model.tenant_id == tenant_id, model.human_review_required.is_(True)))).scalar_one()
        for model in (
            StudentLifecycleApplicant,
            StudentLifecycleStudentProfile,
            StudentLifecycleEnrollment,
            StudentLifecycleAcademicRecord,
            StudentLifecycleTranscriptPreview,
            StudentLifecycleDegreeProgressSnapshot,
            StudentLifecycleStudentRequest,
            StudentLifecycleStudentAppeal,
            StudentLifecycleInterventionPlan,
        )
    )
    return {
        "applicant_counts_by_status": applicant_counts,
        "student_counts_by_status": student_counts,
        "enrollment_counts_by_status": enrollment_counts,
        "transcript_preview_counts": transcript_counts,
        "degree_progress_counts": degree_counts,
        "request_counts_by_status": request_counts,
        "appeal_counts_by_status": appeal_counts,
        "intervention_counts_by_status": intervention_counts,
        "human_review_required_count": int(human_review_required_count),
        "incomplete_data": False,
        "limitations": [],
    }