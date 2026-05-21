"""Pydantic schemas for Student Lifecycle Suite backend foundation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class _MutationRequest(_StrictModel):
    limitations: list[str] = Field(default_factory=list)


class _BaseEntityResponse(_StrictModel):
    id: int
    tenant_id: int
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    human_review_required: bool = True
    automated_decision: bool = False
    provider_integration_enabled: bool = False
    limitations: list[str] = Field(default_factory=list)


class ApplicantCreateRequest(_MutationRequest):
    applicant_code: str
    program_interest: str | None = None
    entry_term: str | None = None
    notes: str | None = None
    source_available: bool = False


class ApplicantUpdateRequest(_MutationRequest):
    program_interest: str | None = None
    entry_term: str | None = None
    notes: str | None = None
    human_review_required: bool | None = None


class ApplicantStatusUpdateRequest(_StrictModel):
    new_status: str
    reason: str | None = None


class ApplicantResponse(_BaseEntityResponse):
    applicant_code: str
    program_interest: str | None = None
    entry_term: str | None = None
    notes: str | None = None
    source_available: bool = False
    archived_at: datetime | None = None


class ApplicantStatusHistoryResponse(_StrictModel):
    id: int
    tenant_id: int
    applicant_id: int
    previous_status: str | None = None
    new_status: str
    actor_user_id: str
    reason: str | None = None
    created_at: datetime


class StudentProfileCreateRequest(_MutationRequest):
    student_code: str
    source_applicant_id: int | None = None
    program_code: str | None = None
    notes: str | None = None


class StudentProfileUpdateRequest(_MutationRequest):
    program_code: str | None = None
    notes: str | None = None
    human_review_required: bool | None = None


class StudentStatusUpdateRequest(_StrictModel):
    new_status: str
    reason: str | None = None


class StudentProfileResponse(_BaseEntityResponse):
    student_code: str
    source_applicant_id: int | None = None
    program_code: str | None = None
    notes: str | None = None
    archived_at: datetime | None = None


class StudentStatusHistoryResponse(_StrictModel):
    id: int
    tenant_id: int
    student_id: int
    previous_status: str | None = None
    new_status: str
    actor_user_id: str
    reason: str | None = None
    created_at: datetime


class StudentEnrollmentCreateRequest(_MutationRequest):
    student_id: int
    term_code: str
    notes: str | None = None


class StudentEnrollmentUpdateRequest(_MutationRequest):
    notes: str | None = None
    human_review_required: bool | None = None


class EnrollmentReviewRequest(_StrictModel):
    new_status: str
    comment: str | None = None


class StudentEnrollmentResponse(_BaseEntityResponse):
    student_id: int
    term_code: str
    notes: str | None = None
    archived_at: datetime | None = None


class EnrollmentStatusHistoryResponse(_StrictModel):
    id: int
    tenant_id: int
    enrollment_id: int
    previous_status: str | None = None
    new_status: str
    actor_user_id: str
    reason: str | None = None
    created_at: datetime


class AcademicRecordCreateRequest(_MutationRequest):
    student_id: int
    record_name: str
    source_available: bool = False


class AcademicRecordResponse(_BaseEntityResponse):
    student_id: int
    record_name: str
    source_available: bool = False
    result_metadata: dict[str, Any] = Field(default_factory=dict)
    archived_at: datetime | None = None


class TranscriptPreviewCreateRequest(_MutationRequest):
    student_id: int
    academic_record_id: int
    preview_payload: dict[str, Any] = Field(default_factory=dict)


class TranscriptPreviewResponse(_BaseEntityResponse):
    student_id: int
    academic_record_id: int
    official_document: bool = False
    preview_payload: dict[str, Any] = Field(default_factory=dict)


class DegreeProgressSnapshotCreateRequest(_MutationRequest):
    student_id: int
    incomplete_data: bool = True
    completion_summary: dict[str, Any] = Field(default_factory=dict)


class DegreeProgressSnapshotResponse(_BaseEntityResponse):
    student_id: int
    data_source: Literal["computed_from_student_lifecycle_metadata"] = "computed_from_student_lifecycle_metadata"
    incomplete_data: bool = True
    hidden_score_present: bool = False
    completion_summary: dict[str, Any] = Field(default_factory=dict)


class GraduationReadinessReviewRequest(_StrictModel):
    new_status: str
    note: str | None = None


class GraduationReadinessReviewResponse(DegreeProgressSnapshotResponse):
    note: str | None = None


class StudentRequestCreateRequest(_MutationRequest):
    student_id: int
    request_type: str
    description: str | None = None


class StudentRequestReviewRequest(_StrictModel):
    new_status: str
    decision_note: str | None = None


class StudentRequestResponse(_BaseEntityResponse):
    student_id: int
    request_type: str
    description: str | None = None
    decision_note: str | None = None
    archived_at: datetime | None = None


class StudentAppealCreateRequest(_MutationRequest):
    student_id: int
    appeal_type: str
    description: str | None = None


class StudentAppealReviewRequest(_StrictModel):
    new_status: str
    decision_note: str | None = None


class StudentAppealResponse(_BaseEntityResponse):
    student_id: int
    appeal_type: str
    description: str | None = None
    decision_note: str | None = None
    archived_at: datetime | None = None


class SuccessSignalCreateRequest(_MutationRequest):
    student_id: int
    signal_type: str
    summary: str | None = None


class InterventionPlanCreateRequest(_MutationRequest):
    student_id: int
    signal_type: str
    plan_summary: str


class InterventionFollowupRequest(_StrictModel):
    outcome_note: str
    continued: bool = False


class InterventionPlanResponse(_BaseEntityResponse):
    student_id: int
    signal_type: str
    plan_summary: str
    hidden_score_present: bool = False
    followups: list[dict[str, Any]] = Field(default_factory=list)
    archived_at: datetime | None = None


class StudentLifecycleAuditEventResponse(_StrictModel):
    id: int
    tenant_id: int
    entity_type: str
    entity_id: int
    event_type: str
    actor_user_id: str
    previous_status: str | None = None
    new_status: str | None = None
    human_review_required: bool = True
    automated_decision: bool = False
    provider_integration_enabled: bool = False
    action: str
    request_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class StudentLifecycleEvidenceMetadataRequest(_StrictModel):
    audit_event_id: int
    entity_type: str
    entity_id: int
    evidence_type: str
    evidence_ref: str
    limitations: list[str] = Field(default_factory=list)


class StudentLifecycleEvidenceMetadataResponse(_StrictModel):
    id: int
    tenant_id: int
    audit_event_id: int
    entity_type: str
    entity_id: int
    evidence_type: str
    evidence_ref: str
    limitations: list[str] = Field(default_factory=list)
    created_by_user_id: str
    created_at: datetime


class StudentLifecycleDashboardResponse(_StrictModel):
    tenant_id: int
    generated_at: datetime
    fake_metrics: bool = False
    data_source: Literal["computed_from_student_lifecycle_metadata"] = "computed_from_student_lifecycle_metadata"
    incomplete_data: bool
    limitations: list[str] = Field(default_factory=list)
    applicant_counts_by_status: dict[str, int] = Field(default_factory=dict)
    student_counts_by_status: dict[str, int] = Field(default_factory=dict)
    enrollment_counts_by_status: dict[str, int] = Field(default_factory=dict)
    transcript_preview_counts: dict[str, int] = Field(default_factory=dict)
    degree_progress_counts: dict[str, int] = Field(default_factory=dict)
    request_counts_by_status: dict[str, int] = Field(default_factory=dict)
    appeal_counts_by_status: dict[str, int] = Field(default_factory=dict)
    intervention_counts_by_status: dict[str, int] = Field(default_factory=dict)
    human_review_required_count: int
    provider_integration_enabled: bool = False
    automated_decision_count: int = 0
    hidden_score_present: bool = False


class StudentLifecycleHealthResponse(_StrictModel):
    tenant_id: int
    generated_at: datetime
    module_name: str = "student_lifecycle"
    route_count: int
    table_count: int
    fake_metrics: bool = False
    data_source: Literal["computed_from_student_lifecycle_metadata"] = "computed_from_student_lifecycle_metadata"
    incomplete_data: bool
    limitations: list[str] = Field(default_factory=list)
    provider_integration_enabled: bool = False
    automated_decision_count: int = 0
    hidden_score_present: bool = False