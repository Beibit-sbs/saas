"""Student Lifecycle Suite SQLAlchemy models for the controlled backend foundation."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


MODULE_NAME = "student_lifecycle"
TABLE_PREFIX = "sl_"
PROVIDER_INTEGRATION_ENABLED = False
SIS_SYNC_ENABLED = False
PLATONUS_LIVE_INTEGRATION_ENABLED = False
AUTONOMOUS_DECISION_ENABLED = False
FAKE_TRANSCRIPT_ENABLED = False
HIDDEN_SCORE_ENABLED = False
FAKE_METRICS_ENABLED = False


class ApplicantStatus:
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ADDITIONAL_INFO_REQUESTED = "ADDITIONAL_INFO_REQUESTED"
    DECISION_METADATA_RECORDED = "DECISION_METADATA_RECORDED"
    ACCEPTED = "ACCEPTED"
    STUDENT_PROFILE_PENDING = "STUDENT_PROFILE_PENDING"
    STUDENT_PROFILE_CREATED = "STUDENT_PROFILE_CREATED"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({
        DRAFT,
        SUBMITTED,
        UNDER_REVIEW,
        ADDITIONAL_INFO_REQUESTED,
        DECISION_METADATA_RECORDED,
        ACCEPTED,
        STUDENT_PROFILE_PENDING,
        STUDENT_PROFILE_CREATED,
        ARCHIVED,
    })


class StudentStatus:
    PROFILE_CREATED = "PROFILE_CREATED"
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    SUSPENDED = "SUSPENDED"
    WITHDRAWN = "WITHDRAWN"
    GRADUATED_METADATA = "GRADUATED_METADATA"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({PROFILE_CREATED, ACTIVE, ON_LEAVE, SUSPENDED, WITHDRAWN, GRADUATED_METADATA, ARCHIVED})


class EnrollmentStatus:
    DRAFT = "DRAFT"
    COURSE_SELECTION_PENDING = "COURSE_SELECTION_PENDING"
    SUBMITTED = "SUBMITTED"
    REGISTRAR_REVIEW = "REGISTRAR_REVIEW"
    ENROLLED = "ENROLLED"
    CHANGED = "CHANGED"
    WITHDRAWN = "WITHDRAWN"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"
    ALL = frozenset({DRAFT, COURSE_SELECTION_PENDING, SUBMITTED, REGISTRAR_REVIEW, ENROLLED, CHANGED, WITHDRAWN, SUSPENDED, CLOSED})


class AcademicRecordStatus:
    OPENED = "OPENED"
    RESULTS_METADATA_ENTERED = "RESULTS_METADATA_ENTERED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    REVIEWED = "REVIEWED"
    LOCKED_METADATA = "LOCKED_METADATA"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({OPENED, RESULTS_METADATA_ENTERED, REVIEW_REQUIRED, REVIEWED, LOCKED_METADATA, ARCHIVED})


class TranscriptPreviewStatus:
    NOT_GENERATED = "NOT_GENERATED"
    GENERATED_UNOFFICIAL_PREVIEW = "GENERATED_UNOFFICIAL_PREVIEW"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    RELEASED_UNOFFICIAL = "RELEASED_UNOFFICIAL"
    OFFICIAL_REQUEST_DEFERRED = "OFFICIAL_REQUEST_DEFERRED"
    ALL = frozenset({NOT_GENERATED, GENERATED_UNOFFICIAL_PREVIEW, REVIEW_REQUIRED, RELEASED_UNOFFICIAL, OFFICIAL_REQUEST_DEFERRED})


class DegreeProgressStatus:
    REQUIREMENTS_LOADED = "REQUIREMENTS_LOADED"
    COMPUTED_FROM_AVAILABLE_SOURCES = "COMPUTED_FROM_AVAILABLE_SOURCES"
    INCOMPLETE_DATA = "INCOMPLETE_DATA"
    ADVISOR_REVIEW_REQUIRED = "ADVISOR_REVIEW_REQUIRED"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    GRADUATION_READY_METADATA = "GRADUATION_READY_METADATA"
    NOT_READY_METADATA = "NOT_READY_METADATA"
    PENDING = "PENDING"
    ALL = frozenset({REQUIREMENTS_LOADED, COMPUTED_FROM_AVAILABLE_SOURCES, INCOMPLETE_DATA, ADVISOR_REVIEW_REQUIRED, HUMAN_REVIEW_REQUIRED, GRADUATION_READY_METADATA, NOT_READY_METADATA, PENDING})


class StudentRequestStatus:
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ROUTED = "ROUTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    DECISION_METADATA_RECORDED = "DECISION_METADATA_RECORDED"
    RESPONSE_ISSUED = "RESPONSE_ISSUED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({DRAFT, SUBMITTED, ROUTED, UNDER_REVIEW, DECISION_METADATA_RECORDED, RESPONSE_ISSUED, CLOSED, ARCHIVED})


class StudentAppealStatus:
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    ELIGIBILITY_CHECK = "ELIGIBILITY_CHECK"
    REVIEWER_REVIEW = "REVIEWER_REVIEW"
    COMMITTEE_REVIEW = "COMMITTEE_REVIEW"
    DECISION_METADATA_RECORDED = "DECISION_METADATA_RECORDED"
    RESPONSE_ISSUED = "RESPONSE_ISSUED"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"
    ALL = frozenset({DRAFT, SUBMITTED, ELIGIBILITY_CHECK, REVIEWER_REVIEW, COMMITTEE_REVIEW, DECISION_METADATA_RECORDED, RESPONSE_ISSUED, CLOSED, ARCHIVED})


class InterventionStatus:
    SIGNAL_REGISTERED = "SIGNAL_REGISTERED"
    ADVISOR_REVIEW_REQUIRED = "ADVISOR_REVIEW_REQUIRED"
    INTERVENTION_DRAFT = "INTERVENTION_DRAFT"
    CONTACT_PLANNED = "CONTACT_PLANNED"
    FOLLOW_UP_SCHEDULED = "FOLLOW_UP_SCHEDULED"
    PROGRESS_NOTE_RECORDED = "PROGRESS_NOTE_RECORDED"
    OUTCOME_METADATA_RECORDED = "OUTCOME_METADATA_RECORDED"
    CLOSED = "CLOSED"
    CONTINUED = "CONTINUED"
    ALL = frozenset({SIGNAL_REGISTERED, ADVISOR_REVIEW_REQUIRED, INTERVENTION_DRAFT, CONTACT_PLANNED, FOLLOW_UP_SCHEDULED, PROGRESS_NOTE_RECORDED, OUTCOME_METADATA_RECORDED, CLOSED, CONTINUED})


class StudentLifecycleAuditEventType:
    APPLICANT_CREATED = "APPLICANT_CREATED"
    APPLICANT_STATUS_CHANGED = "APPLICANT_STATUS_CHANGED"
    STUDENT_PROFILE_CREATED = "STUDENT_PROFILE_CREATED"
    STUDENT_STATUS_CHANGED = "STUDENT_STATUS_CHANGED"
    ENROLLMENT_CREATED = "ENROLLMENT_CREATED"
    ENROLLMENT_REVIEWED = "ENROLLMENT_REVIEWED"
    ACADEMIC_RECORD_OPENED = "ACADEMIC_RECORD_OPENED"
    TRANSCRIPT_PREVIEW_GENERATED = "TRANSCRIPT_PREVIEW_GENERATED"
    DEGREE_PROGRESS_COMPUTED = "DEGREE_PROGRESS_COMPUTED"
    GRADUATION_READINESS_REVIEWED = "GRADUATION_READINESS_REVIEWED"
    STUDENT_REQUEST_SUBMITTED = "STUDENT_REQUEST_SUBMITTED"
    STUDENT_REQUEST_REVIEWED = "STUDENT_REQUEST_REVIEWED"
    STUDENT_APPEAL_SUBMITTED = "STUDENT_APPEAL_SUBMITTED"
    STUDENT_APPEAL_REVIEWED = "STUDENT_APPEAL_REVIEWED"
    INTERVENTION_PLAN_CREATED = "INTERVENTION_PLAN_CREATED"
    INTERVENTION_FOLLOWUP_RECORDED = "INTERVENTION_FOLLOWUP_RECORDED"
    EVIDENCE_METADATA_ATTACHED = "EVIDENCE_METADATA_ATTACHED"
    DASHBOARD_VIEWED = "DASHBOARD_VIEWED"
    ALL = frozenset({
        APPLICANT_CREATED,
        APPLICANT_STATUS_CHANGED,
        STUDENT_PROFILE_CREATED,
        STUDENT_STATUS_CHANGED,
        ENROLLMENT_CREATED,
        ENROLLMENT_REVIEWED,
        ACADEMIC_RECORD_OPENED,
        TRANSCRIPT_PREVIEW_GENERATED,
        DEGREE_PROGRESS_COMPUTED,
        GRADUATION_READINESS_REVIEWED,
        STUDENT_REQUEST_SUBMITTED,
        STUDENT_REQUEST_REVIEWED,
        STUDENT_APPEAL_SUBMITTED,
        STUDENT_APPEAL_REVIEWED,
        INTERVENTION_PLAN_CREATED,
        INTERVENTION_FOLLOWUP_RECORDED,
        EVIDENCE_METADATA_ATTACHED,
        DASHBOARD_VIEWED,
    })


class StudentLifecycleApplicant(Base):
    __tablename__ = "sl_applicants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    applicant_code: Mapped[str] = mapped_column(String(64), nullable=False)
    program_interest: Mapped[str | None] = mapped_column(String(128), nullable=True)
    entry_term: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'DRAFT'"), default=ApplicantStatus.DRAFT)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"), default=True)
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    source_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    limitations_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"), default=list)
    created_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status_history: Mapped[list["StudentLifecycleApplicantStatusHistory"]] = relationship(back_populates="applicant")

    __table_args__ = (
        UniqueConstraint("tenant_id", "applicant_code", name="uq_sl_applicants_tenant_code"),
        Index("ix_sl_applicants_tenant_status", "tenant_id", "status"),
    )


class StudentLifecycleApplicantStatusHistory(Base):
    __tablename__ = "sl_applicant_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("sl_applicants.id"), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))

    applicant: Mapped[StudentLifecycleApplicant] = relationship(back_populates="status_history")

    __table_args__ = (Index("ix_sl_applicant_status_history_tenant_applicant", "tenant_id", "applicant_id"),)


class StudentLifecycleStudentProfile(Base):
    __tablename__ = "sl_student_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    student_code: Mapped[str] = mapped_column(String(64), nullable=False)
    source_applicant_id: Mapped[int | None] = mapped_column(ForeignKey("sl_applicants.id"), nullable=True)
    program_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'PROFILE_CREATED'"), default=StudentStatus.PROFILE_CREATED)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"), default=True)
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    limitations_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"), default=list)
    created_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "student_code", name="uq_sl_student_profiles_tenant_code"),
        Index("ix_sl_student_profiles_tenant_status", "tenant_id", "status"),
    )


class StudentLifecycleStudentStatusHistory(Base):
    __tablename__ = "sl_student_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sl_student_profiles.id"), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))

    __table_args__ = (Index("ix_sl_student_status_history_tenant_student", "tenant_id", "student_id"),)


class StudentLifecycleEnrollment(Base):
    __tablename__ = "sl_student_enrollments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sl_student_profiles.id"), nullable=False)
    term_code: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'DRAFT'"), default=EnrollmentStatus.DRAFT)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"), default=True)
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    limitations_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"), default=list)
    created_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_sl_student_enrollments_tenant_status", "tenant_id", "status"),)


class StudentLifecycleEnrollmentStatusHistory(Base):
    __tablename__ = "sl_enrollment_status_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("sl_student_enrollments.id"), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))

    __table_args__ = (Index("ix_sl_enrollment_status_history_tenant_enrollment", "tenant_id", "enrollment_id"),)


class StudentLifecycleAcademicRecord(Base):
    __tablename__ = "sl_academic_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sl_student_profiles.id"), nullable=False)
    record_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'OPENED'"), default=AcademicRecordStatus.OPENED)
    source_available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"), default=True)
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    result_metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"), default=dict)
    limitations_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"), default=list)
    created_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_sl_academic_records_tenant_status", "tenant_id", "status"),)


class StudentLifecycleTranscriptPreview(Base):
    __tablename__ = "sl_transcript_previews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sl_student_profiles.id"), nullable=False)
    academic_record_id: Mapped[int] = mapped_column(ForeignKey("sl_academic_records.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'GENERATED_UNOFFICIAL_PREVIEW'"), default=TranscriptPreviewStatus.GENERATED_UNOFFICIAL_PREVIEW)
    official_document: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"), default=True)
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    preview_payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"), default=dict)
    limitations_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"), default=list)
    created_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))

    __table_args__ = (Index("ix_sl_transcript_previews_tenant_status", "tenant_id", "status"),)


class StudentLifecycleDegreeProgressSnapshot(Base):
    __tablename__ = "sl_degree_progress_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sl_student_profiles.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'PENDING'"), default=DegreeProgressStatus.PENDING)
    data_source: Mapped[str] = mapped_column(String(128), nullable=False, server_default=sa_text("'computed_from_student_lifecycle_metadata'"), default="computed_from_student_lifecycle_metadata")
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"), default=True)
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"), default=True)
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    completion_summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"), default=dict)
    limitations_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"), default=list)
    created_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))

    __table_args__ = (Index("ix_sl_degree_progress_snapshots_tenant_status", "tenant_id", "status"),)


class StudentLifecycleStudentRequest(Base):
    __tablename__ = "sl_student_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sl_student_profiles.id"), nullable=False)
    request_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'DRAFT'"), default=StudentRequestStatus.DRAFT)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"), default=True)
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"), default=list)
    created_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_sl_student_requests_tenant_status", "tenant_id", "status"),)


class StudentLifecycleStudentAppeal(Base):
    __tablename__ = "sl_student_appeals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sl_student_profiles.id"), nullable=False)
    appeal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'DRAFT'"), default=StudentAppealStatus.DRAFT)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"), default=True)
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    limitations_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"), default=list)
    created_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_sl_student_appeals_tenant_status", "tenant_id", "status"),)


class StudentLifecycleInterventionPlan(Base):
    __tablename__ = "sl_intervention_plans"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("sl_student_profiles.id"), nullable=False)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'SIGNAL_REGISTERED'"), default=InterventionStatus.SIGNAL_REGISTERED)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"), default=True)
    hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    followups_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"), default=list)
    limitations_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"), default=list)
    created_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_sl_intervention_plans_tenant_status", "tenant_id", "status"),)


class StudentLifecycleAuditEvent(Base):
    __tablename__ = "sl_student_lifecycle_audit_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"), default=True)
    automated_decision: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    provider_integration_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"), default=False)
    action: Mapped[str] = mapped_column(String(256), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"), default=dict)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))

    __table_args__ = (Index("ix_sl_audit_events_tenant_entity", "tenant_id", "entity_type", "entity_id"),)


class StudentLifecycleEvidenceMetadata(Base):
    __tablename__ = "sl_student_lifecycle_evidence_metadata"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    audit_event_id: Mapped[int] = mapped_column(ForeignKey("sl_student_lifecycle_audit_events.id"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    limitations_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"), default=list)
    created_by_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))

    audit_event: Mapped[StudentLifecycleAuditEvent] = relationship()

    __table_args__ = (Index("ix_sl_evidence_metadata_tenant_entity", "tenant_id", "entity_type", "entity_id"),)