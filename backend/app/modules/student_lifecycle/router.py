"""FastAPI router for Student Lifecycle Suite backend foundation."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.router_errors import integrity_error_to_http, permission_error_to_http, tenant_not_found_to_http, validation_error_to_http
from app.core.module_helpers.service_validation import DomainValidationError, OptimisticLockConflictError, TenantResourceNotFoundError
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.student_lifecycle import permissions, service
from app.modules.student_lifecycle.dependencies import get_student_lifecycle_db
from app.modules.student_lifecycle.models import TABLE_PREFIX
from app.modules.student_lifecycle.schemas import (
    AcademicRecordCreateRequest,
    AcademicRecordResponse,
    ApplicantCreateRequest,
    ApplicantResponse,
    ApplicantStatusHistoryResponse,
    ApplicantStatusUpdateRequest,
    ApplicantUpdateRequest,
    DegreeProgressSnapshotCreateRequest,
    DegreeProgressSnapshotResponse,
    EnrollmentReviewRequest,
    EnrollmentStatusHistoryResponse,
    GraduationReadinessReviewRequest,
    GraduationReadinessReviewResponse,
    InterventionFollowupRequest,
    InterventionPlanCreateRequest,
    InterventionPlanResponse,
    StudentAppealCreateRequest,
    StudentAppealResponse,
    StudentAppealReviewRequest,
    StudentEnrollmentCreateRequest,
    StudentEnrollmentResponse,
    StudentEnrollmentUpdateRequest,
    StudentLifecycleAuditEventResponse,
    StudentLifecycleDashboardResponse,
    StudentLifecycleEvidenceMetadataRequest,
    StudentLifecycleEvidenceMetadataResponse,
    StudentLifecycleHealthResponse,
    StudentProfileCreateRequest,
    StudentProfileResponse,
    StudentProfileUpdateRequest,
    StudentRequestCreateRequest,
    StudentRequestResponse,
    StudentRequestReviewRequest,
    StudentStatusHistoryResponse,
    StudentStatusUpdateRequest,
    TranscriptPreviewCreateRequest,
    TranscriptPreviewResponse,
)


router = APIRouter(prefix="/api/admin/student-lifecycle", tags=["student-lifecycle"])

_Tenant = Annotated[dict, Depends(get_current_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_student_lifecycle_db)]


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _handle(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        raise tenant_not_found_to_http(exc)
    if isinstance(exc, (DomainValidationError, ValueError)):
        raise validation_error_to_http(exc)
    if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
        raise integrity_error_to_http(exc)
    raise exc


def _resp(obj: Any, schema_cls):
    data = obj.__dict__.copy()
    if "limitations_json" in data:
        data["limitations"] = list(data.pop("limitations_json") or [])
    if "result_metadata_json" in data:
        data["result_metadata"] = dict(data.pop("result_metadata_json") or {})
    if "preview_payload_json" in data:
        data["preview_payload"] = dict(data.pop("preview_payload_json") or {})
    if "completion_summary_json" in data:
        data["completion_summary"] = dict(data.pop("completion_summary_json") or {})
    if "followups_json" in data:
        data["followups"] = list(data.pop("followups_json") or [])
    if "payload_json" in data:
        data["payload"] = dict(data.pop("payload_json") or {})
    return schema_cls.model_validate(data)


@router.get("/applicants", response_model=list[ApplicantResponse])
def list_applicants_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.APPLICANTS_READ))], tenant: _Tenant, db: _DB) -> list[ApplicantResponse]:
    try:
        return [_resp(item, ApplicantResponse) for item in service.list_applicants_service(db, int(tenant["id"]))]
    except Exception as exc:
        _handle(exc)


@router.post("/applicants", response_model=ApplicantResponse, status_code=status.HTTP_201_CREATED)
def create_applicant_endpoint(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.APPLICANTS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ApplicantResponse:
    try:
        body = _parse_payload(ApplicantCreateRequest, payload)
        return _resp(service.create_applicant_service(db, int(tenant["id"]), actor, body), ApplicantResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/applicants/{applicant_id}", response_model=ApplicantResponse)
def get_applicant_endpoint(applicant_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.APPLICANTS_READ))], tenant: _Tenant, db: _DB) -> ApplicantResponse:
    try:
        return _resp(service.get_applicant_service(db, int(tenant["id"]), applicant_id), ApplicantResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/applicants/{applicant_id}", response_model=ApplicantResponse)
def update_applicant_endpoint(applicant_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.APPLICANTS_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ApplicantResponse:
    try:
        body = _parse_payload(ApplicantUpdateRequest, payload)
        return _resp(service.update_applicant_service(db, int(tenant["id"]), applicant_id, body), ApplicantResponse)
    except Exception as exc:
        _handle(exc)


@router.post("/applicants/{applicant_id}/submit", response_model=ApplicantResponse)
def submit_applicant_endpoint(applicant_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.APPLICANTS_STATUS_UPDATE))], tenant: _Tenant, db: _DB) -> ApplicantResponse:
    try:
        return _resp(service.submit_applicant_service(db, int(tenant["id"]), actor, applicant_id), ApplicantResponse)
    except Exception as exc:
        _handle(exc)


@router.post("/applicants/{applicant_id}/status", response_model=ApplicantResponse)
def update_applicant_status_endpoint(applicant_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.APPLICANTS_STATUS_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ApplicantResponse:
    try:
        body = _parse_payload(ApplicantStatusUpdateRequest, payload)
        return _resp(service.update_applicant_status_service(db, int(tenant["id"]), actor, applicant_id, body.new_status, body.reason), ApplicantResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/applicants/{applicant_id}/status-history", response_model=list[ApplicantStatusHistoryResponse])
def list_applicant_status_history_endpoint(applicant_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.APPLICANTS_READ))], tenant: _Tenant, db: _DB) -> list[ApplicantStatusHistoryResponse]:
    try:
        return [_resp(item, ApplicantStatusHistoryResponse) for item in service.list_applicant_status_history_service(db, int(tenant["id"]), applicant_id)]
    except Exception as exc:
        _handle(exc)


@router.get("/students", response_model=list[StudentProfileResponse])
def list_students_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.STUDENTS_READ))], tenant: _Tenant, db: _DB) -> list[StudentProfileResponse]:
    try:
        return [_resp(item, StudentProfileResponse) for item in service.list_student_profiles_service(db, int(tenant["id"]))]
    except Exception as exc:
        _handle(exc)


@router.post("/students", response_model=StudentProfileResponse, status_code=status.HTTP_201_CREATED)
def create_student_endpoint(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.STUDENTS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentProfileResponse:
    try:
        body = _parse_payload(StudentProfileCreateRequest, payload)
        return _resp(service.create_student_profile_service(db, int(tenant["id"]), actor, body), StudentProfileResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/students/{student_id}", response_model=StudentProfileResponse)
def get_student_endpoint(student_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.STUDENTS_READ))], tenant: _Tenant, db: _DB) -> StudentProfileResponse:
    try:
        return _resp(service.get_student_profile_service(db, int(tenant["id"]), student_id), StudentProfileResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/students/{student_id}", response_model=StudentProfileResponse)
def update_student_endpoint(student_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.STUDENTS_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentProfileResponse:
    try:
        body = _parse_payload(StudentProfileUpdateRequest, payload)
        return _resp(service.update_student_profile_service(db, int(tenant["id"]), student_id, body), StudentProfileResponse)
    except Exception as exc:
        _handle(exc)


@router.post("/students/{student_id}/status", response_model=StudentProfileResponse)
def update_student_status_endpoint(student_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.STUDENTS_STATUS_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentProfileResponse:
    try:
        body = _parse_payload(StudentStatusUpdateRequest, payload)
        return _resp(service.update_student_profile_status_service(db, int(tenant["id"]), actor, student_id, body.new_status, body.reason), StudentProfileResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/students/{student_id}/status-history", response_model=list[StudentStatusHistoryResponse])
def list_student_status_history_endpoint(student_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.STUDENTS_READ))], tenant: _Tenant, db: _DB) -> list[StudentStatusHistoryResponse]:
    try:
        return [_resp(item, StudentStatusHistoryResponse) for item in service.list_student_status_history_service(db, int(tenant["id"]), student_id)]
    except Exception as exc:
        _handle(exc)


@router.get("/enrollment", response_model=list[StudentEnrollmentResponse])
def list_enrollment_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.ENROLLMENT_READ))], tenant: _Tenant, db: _DB) -> list[StudentEnrollmentResponse]:
    try:
        return [_resp(item, StudentEnrollmentResponse) for item in service.list_student_enrollments_service(db, int(tenant["id"]))]
    except Exception as exc:
        _handle(exc)


@router.post("/enrollment", response_model=StudentEnrollmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrollment_endpoint(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.ENROLLMENT_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentEnrollmentResponse:
    try:
        body = _parse_payload(StudentEnrollmentCreateRequest, payload)
        return _resp(service.create_student_enrollment_service(db, int(tenant["id"]), actor, body), StudentEnrollmentResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/enrollment/{enrollment_id}", response_model=StudentEnrollmentResponse)
def get_enrollment_endpoint(enrollment_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.ENROLLMENT_READ))], tenant: _Tenant, db: _DB) -> StudentEnrollmentResponse:
    try:
        return _resp(service.get_student_enrollment_service(db, int(tenant["id"]), enrollment_id), StudentEnrollmentResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/enrollment/{enrollment_id}", response_model=StudentEnrollmentResponse)
def update_enrollment_endpoint(enrollment_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.ENROLLMENT_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentEnrollmentResponse:
    try:
        body = _parse_payload(StudentEnrollmentUpdateRequest, payload)
        return _resp(service.update_student_enrollment_service(db, int(tenant["id"]), enrollment_id, body), StudentEnrollmentResponse)
    except Exception as exc:
        _handle(exc)


@router.post("/enrollment/{enrollment_id}/review", response_model=StudentEnrollmentResponse)
def review_enrollment_endpoint(enrollment_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.ENROLLMENT_REVIEW))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentEnrollmentResponse:
    try:
        body = _parse_payload(EnrollmentReviewRequest, payload)
        return _resp(service.review_student_enrollment_service(db, int(tenant["id"]), actor, enrollment_id, body), StudentEnrollmentResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/academic-records", response_model=list[AcademicRecordResponse])
def list_academic_records_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.RECORDS_READ))], tenant: _Tenant, db: _DB) -> list[AcademicRecordResponse]:
    try:
        return [_resp(item, AcademicRecordResponse) for item in service.list_academic_records_service(db, int(tenant["id"]))]
    except Exception as exc:
        _handle(exc)


@router.post("/academic-records", response_model=AcademicRecordResponse, status_code=status.HTTP_201_CREATED)
def create_academic_record_endpoint(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.RECORDS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> AcademicRecordResponse:
    try:
        body = _parse_payload(AcademicRecordCreateRequest, payload)
        return _resp(service.open_academic_record_service(db, int(tenant["id"]), actor, body), AcademicRecordResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/academic-records/{record_id}", response_model=AcademicRecordResponse)
def get_academic_record_endpoint(record_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.RECORDS_READ))], tenant: _Tenant, db: _DB) -> AcademicRecordResponse:
    try:
        return _resp(service.get_academic_record_service(db, int(tenant["id"]), record_id), AcademicRecordResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/transcripts", response_model=list[TranscriptPreviewResponse])
def list_transcripts_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.TRANSCRIPTS_READ))], tenant: _Tenant, db: _DB) -> list[TranscriptPreviewResponse]:
    try:
        return [_resp(item, TranscriptPreviewResponse) for item in service.list_transcript_previews_service(db, int(tenant["id"]))]
    except Exception as exc:
        _handle(exc)


@router.post("/transcripts/preview", response_model=TranscriptPreviewResponse, status_code=status.HTTP_201_CREATED)
def create_transcript_preview_endpoint(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.TRANSCRIPTS_PREVIEW))] = None, tenant: _Tenant = None, db: _DB = None) -> TranscriptPreviewResponse:
    try:
        body = _parse_payload(TranscriptPreviewCreateRequest, payload)
        return _resp(service.generate_transcript_preview_service(db, int(tenant["id"]), actor, body), TranscriptPreviewResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/transcripts/{preview_id}", response_model=TranscriptPreviewResponse)
def get_transcript_preview_endpoint(preview_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.TRANSCRIPTS_READ))], tenant: _Tenant, db: _DB) -> TranscriptPreviewResponse:
    try:
        return _resp(service.get_transcript_preview_service(db, int(tenant["id"]), preview_id), TranscriptPreviewResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/degree-progress/{student_id}", response_model=DegreeProgressSnapshotResponse)
def get_degree_progress_endpoint(student_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.DEGREE_PROGRESS_READ))], tenant: _Tenant, db: _DB) -> DegreeProgressSnapshotResponse:
    try:
        return _resp(service.get_degree_progress_snapshot_service(db, int(tenant["id"]), student_id), DegreeProgressSnapshotResponse)
    except Exception as exc:
        _handle(exc)


@router.post("/degree-progress/{student_id}/snapshot", response_model=DegreeProgressSnapshotResponse, status_code=status.HTTP_201_CREATED)
def compute_degree_progress_endpoint(student_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.DEGREE_PROGRESS_COMPUTE))] = None, tenant: _Tenant = None, db: _DB = None) -> DegreeProgressSnapshotResponse:
    try:
        body = _parse_payload(DegreeProgressSnapshotCreateRequest, payload)
        body = body.model_copy(update={"student_id": student_id})
        return _resp(service.compute_degree_progress_snapshot_service(db, int(tenant["id"]), actor, body), DegreeProgressSnapshotResponse)
    except Exception as exc:
        _handle(exc)


@router.post("/degree-progress/{student_id}/graduation-review", response_model=GraduationReadinessReviewResponse)
def review_graduation_readiness_endpoint(student_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.GRADUATION_READINESS_REVIEW))] = None, tenant: _Tenant = None, db: _DB = None) -> GraduationReadinessReviewResponse:
    try:
        body = _parse_payload(GraduationReadinessReviewRequest, payload)
        data = _resp(service.review_graduation_readiness_service(db, int(tenant["id"]), actor, student_id, body), GraduationReadinessReviewResponse)
        return data.model_copy(update={"note": body.note})
    except Exception as exc:
        _handle(exc)


@router.get("/requests", response_model=list[StudentRequestResponse])
def list_requests_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.REQUESTS_READ))], tenant: _Tenant, db: _DB) -> list[StudentRequestResponse]:
    try:
        return [_resp(item, StudentRequestResponse) for item in service.list_student_requests_service(db, int(tenant["id"]))]
    except Exception as exc:
        _handle(exc)


@router.post("/requests", response_model=StudentRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request_endpoint(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.REQUESTS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentRequestResponse:
    try:
        body = _parse_payload(StudentRequestCreateRequest, payload)
        return _resp(service.create_student_request_service(db, int(tenant["id"]), actor, body), StudentRequestResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/requests/{request_id}", response_model=StudentRequestResponse)
def get_request_endpoint(request_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.REQUESTS_READ))], tenant: _Tenant, db: _DB) -> StudentRequestResponse:
    try:
        return _resp(service.get_student_request_service(db, int(tenant["id"]), request_id), StudentRequestResponse)
    except Exception as exc:
        _handle(exc)


@router.post("/requests/{request_id}/review", response_model=StudentRequestResponse)
def review_request_endpoint(request_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.REQUESTS_REVIEW))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentRequestResponse:
    try:
        body = _parse_payload(StudentRequestReviewRequest, payload)
        return _resp(service.review_student_request_service(db, int(tenant["id"]), actor, request_id, body), StudentRequestResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/appeals", response_model=list[StudentAppealResponse])
def list_appeals_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.APPEALS_READ))], tenant: _Tenant, db: _DB) -> list[StudentAppealResponse]:
    try:
        return [_resp(item, StudentAppealResponse) for item in service.list_student_appeals_service(db, int(tenant["id"]))]
    except Exception as exc:
        _handle(exc)


@router.post("/appeals", response_model=StudentAppealResponse, status_code=status.HTTP_201_CREATED)
def create_appeal_endpoint(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.APPEALS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentAppealResponse:
    try:
        body = _parse_payload(StudentAppealCreateRequest, payload)
        return _resp(service.create_student_appeal_service(db, int(tenant["id"]), actor, body), StudentAppealResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/appeals/{appeal_id}", response_model=StudentAppealResponse)
def get_appeal_endpoint(appeal_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.APPEALS_READ))], tenant: _Tenant, db: _DB) -> StudentAppealResponse:
    try:
        return _resp(service.get_student_appeal_service(db, int(tenant["id"]), appeal_id), StudentAppealResponse)
    except Exception as exc:
        _handle(exc)


@router.post("/appeals/{appeal_id}/review", response_model=StudentAppealResponse)
def review_appeal_endpoint(appeal_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.APPEALS_REVIEW))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentAppealResponse:
    try:
        body = _parse_payload(StudentAppealReviewRequest, payload)
        return _resp(service.review_student_appeal_service(db, int(tenant["id"]), actor, appeal_id, body), StudentAppealResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/interventions/plans", response_model=list[InterventionPlanResponse])
def list_interventions_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.INTERVENTIONS_READ))], tenant: _Tenant, db: _DB) -> list[InterventionPlanResponse]:
    try:
        return [_resp(item, InterventionPlanResponse) for item in service.list_intervention_plans_service(db, int(tenant["id"]))]
    except Exception as exc:
        _handle(exc)


@router.post("/interventions/plans", response_model=InterventionPlanResponse, status_code=status.HTTP_201_CREATED)
def create_intervention_endpoint(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.INTERVENTIONS_PLAN_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> InterventionPlanResponse:
    try:
        body = _parse_payload(InterventionPlanCreateRequest, payload)
        return _resp(service.create_intervention_plan_service(db, int(tenant["id"]), actor, body), InterventionPlanResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/interventions/plans/{plan_id}", response_model=InterventionPlanResponse)
def get_intervention_endpoint(plan_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.INTERVENTIONS_READ))], tenant: _Tenant, db: _DB) -> InterventionPlanResponse:
    try:
        return _resp(service.get_intervention_plan_service(db, int(tenant["id"]), plan_id), InterventionPlanResponse)
    except Exception as exc:
        _handle(exc)


@router.post("/interventions/plans/{plan_id}/followups", response_model=InterventionPlanResponse)
def record_intervention_followup_endpoint(plan_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.INTERVENTIONS_FOLLOWUP_WRITE))] = None, tenant: _Tenant = None, db: _DB = None) -> InterventionPlanResponse:
    try:
        body = _parse_payload(InterventionFollowupRequest, payload)
        return _resp(service.record_intervention_followup_service(db, int(tenant["id"]), actor, plan_id, body), InterventionPlanResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/audit", response_model=list[StudentLifecycleAuditEventResponse])
def list_audit_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_READ))], tenant: _Tenant, db: _DB) -> list[StudentLifecycleAuditEventResponse]:
    try:
        return [_resp(item, StudentLifecycleAuditEventResponse) for item in service.list_student_lifecycle_audit_events_service(db, int(tenant["id"]))]
    except Exception as exc:
        _handle(exc)


@router.get("/evidence", response_model=list[StudentLifecycleEvidenceMetadataResponse])
def list_evidence_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_READ))], tenant: _Tenant, db: _DB) -> list[StudentLifecycleEvidenceMetadataResponse]:
    try:
        return [_resp(item, StudentLifecycleEvidenceMetadataResponse) for item in service.list_evidence_metadata_service(db, int(tenant["id"]))]
    except Exception as exc:
        _handle(exc)


@router.post("/evidence", response_model=StudentLifecycleEvidenceMetadataResponse, status_code=status.HTTP_201_CREATED)
def create_evidence_endpoint(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_ATTACH))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentLifecycleEvidenceMetadataResponse:
    try:
        body = _parse_payload(StudentLifecycleEvidenceMetadataRequest, payload)
        return _resp(service.attach_evidence_metadata_service(db, int(tenant["id"]), actor, body), StudentLifecycleEvidenceMetadataResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/dashboard", response_model=StudentLifecycleDashboardResponse)
def get_dashboard_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))], tenant: _Tenant, db: _DB) -> StudentLifecycleDashboardResponse:
    try:
        return service.get_student_lifecycle_dashboard_service(db, int(tenant["id"]), actor)
    except Exception as exc:
        _handle(exc)


@router.get("/health", response_model=StudentLifecycleHealthResponse)
def get_health_endpoint(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.HEALTH_READ))], tenant: _Tenant) -> StudentLifecycleHealthResponse:
    try:
        route_count = len([route for route in router.routes if getattr(route, "path", "").startswith(router.prefix)])
        return service.get_student_lifecycle_health_service(int(tenant["id"]), route_count=route_count, table_count=14)
    except Exception as exc:
        _handle(exc)


__all__ = ["router", "TABLE_PREFIX"]