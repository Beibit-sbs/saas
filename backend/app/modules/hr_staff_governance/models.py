"""HR / Staff Governance backend foundation SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.core.db import Base


MODULE_NAME = "hr_staff_governance"
TABLE_PREFIX = "hr_"
TARGET_LEVEL = "L3"
CONTRACT_VERSION = "A-039.2"
FOUNDATION_STATUS = "HR_STAFF_GOVERNANCE_METADATA_EVIDENCE_BACKEND_FOUNDATION"
SOURCE_SPEC_COMMIT = "09e968b"
SOURCE_PRODUCT_MAP_COMMIT = "eaff24f"
SOURCE_VERTICAL_SELECTION_COMMIT = "449a407"
PRODUCT_VERTICAL = "HR / Staff Governance Suite"
CAPABILITY_FAMILY_COUNT = 14
DETAILED_CAPABILITY_COUNT = 54
WORKFLOW_GROUP_COUNT = 12
ROLE_COUNT = 15
RUNTIME_MODE = "METADATA_EVIDENCE_HUMAN_REVIEW_ONLY"
DATA_SOURCE = "computed_from_hr_staff_governance_metadata"

AUTOMATIC_HIRING_DECISION_ENABLED = False
AUTOMATIC_FIRING_DECISION_ENABLED = False
AUTOMATIC_HR_DISCIPLINARY_DECISION_ENABLED = False
AUTOMATIC_LEAVE_APPROVAL_ENABLED = False
AUTOMATIC_LEAVE_REJECTION_ENABLED = False
AUTOMATIC_PAYROLL_DECISION_ENABLED = False
AUTONOMOUS_ACCESS_REVOCATION_ENABLED = False
PROVIDER_LIVE_INTEGRATION_ENABLED = False
ONE_C_LIVE_SYNC_ENABLED = False
PAYROLL_LIVE_SYNC_ENABLED = False
EXTERNAL_DB_SYNC_ENABLED = False
HIDDEN_EMPLOYEE_SCORE_PRESENT = False
HIDDEN_FACULTY_SCORE_PRESENT = False
DISCRIMINATORY_SCORE_PRESENT = False
FAKE_METRICS = False
FAKE_HR_DATA = False
HUMAN_REVIEW_REQUIRED = True

EXPECTED_TABLE_COUNT = 36
EXPECTED_ROUTE_COUNT = 62
EXPECTED_PERMISSION_COUNT = 56


class StaffStatus:
	DRAFT = "DRAFT"
	ACTIVE = "ACTIVE"
	ON_LEAVE = "ON_LEAVE"
	SUSPENDED_METADATA_ONLY = "SUSPENDED_METADATA_ONLY"
	EXIT_PENDING = "EXIT_PENDING"
	EXITED_METADATA_ONLY = "EXITED_METADATA_ONLY"
	ARCHIVED = "ARCHIVED"
	ALL = frozenset({DRAFT, ACTIVE, ON_LEAVE, SUSPENDED_METADATA_ONLY, EXIT_PENDING, EXITED_METADATA_ONLY, ARCHIVED})


class RecruitmentStatus:
	DRAFT = "DRAFT"
	SUBMITTED = "SUBMITTED"
	UNDER_REVIEW = "UNDER_REVIEW"
	SHORTLISTED = "SHORTLISTED"
	COMMITTEE_REVIEW = "COMMITTEE_REVIEW"
	EVIDENCE_COMPLETE = "EVIDENCE_COMPLETE"
	CLOSED_METADATA_ONLY = "CLOSED_METADATA_ONLY"
	CANCELLED = "CANCELLED"
	ALL = frozenset({DRAFT, SUBMITTED, UNDER_REVIEW, SHORTLISTED, COMMITTEE_REVIEW, EVIDENCE_COMPLETE, CLOSED_METADATA_ONLY, CANCELLED})


class OnboardingStatus:
	DRAFT = "DRAFT"
	DOCUMENT_COLLECTION = "DOCUMENT_COLLECTION"
	IN_PROGRESS = "IN_PROGRESS"
	PROBATION_STARTED = "PROBATION_STARTED"
	REVIEW_REQUIRED = "REVIEW_REQUIRED"
	COMPLETE_METADATA_ONLY = "COMPLETE_METADATA_ONLY"
	BLOCKED = "BLOCKED"
	ALL = frozenset({DRAFT, DOCUMENT_COLLECTION, IN_PROGRESS, PROBATION_STARTED, REVIEW_REQUIRED, COMPLETE_METADATA_ONLY, BLOCKED})


class LeaveRequestStatus:
	DRAFT = "DRAFT"
	SUBMITTED = "SUBMITTED"
	MANAGER_REVIEW = "MANAGER_REVIEW"
	HR_REVIEW = "HR_REVIEW"
	APPROVED_METADATA_ONLY = "APPROVED_METADATA_ONLY"
	REJECTED_METADATA_ONLY = "REJECTED_METADATA_ONLY"
	CANCELLED = "CANCELLED"
	ALL = frozenset({DRAFT, SUBMITTED, MANAGER_REVIEW, HR_REVIEW, APPROVED_METADATA_ONLY, REJECTED_METADATA_ONLY, CANCELLED})


class AppraisalStatus:
	DRAFT = "DRAFT"
	OPEN = "OPEN"
	REVIEW_IN_PROGRESS = "REVIEW_IN_PROGRESS"
	HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
	COMPLETED_METADATA_ONLY = "COMPLETED_METADATA_ONLY"
	ARCHIVED = "ARCHIVED"
	ALL = frozenset({DRAFT, OPEN, REVIEW_IN_PROGRESS, HUMAN_REVIEW_REQUIRED, COMPLETED_METADATA_ONLY, ARCHIVED})


class TrainingStatus:
	PLANNED = "PLANNED"
	IN_PROGRESS = "IN_PROGRESS"
	COMPLETED_METADATA_ONLY = "COMPLETED_METADATA_ONLY"
	EXPIRING = "EXPIRING"
	EXPIRED = "EXPIRED"
	EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"
	ALL = frozenset({PLANNED, IN_PROGRESS, COMPLETED_METADATA_ONLY, EXPIRING, EXPIRED, EVIDENCE_REQUIRED})


class DisciplinaryCaseStatus:
	INTAKE = "INTAKE"
	HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
	EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
	COMMITTEE_REVIEW = "COMMITTEE_REVIEW"
	OUTCOME_RECORDED_METADATA_ONLY = "OUTCOME_RECORDED_METADATA_ONLY"
	CLOSED_METADATA_ONLY = "CLOSED_METADATA_ONLY"
	ESCALATED = "ESCALATED"
	ALL = frozenset({INTAKE, HUMAN_REVIEW_REQUIRED, EVIDENCE_COLLECTION, COMMITTEE_REVIEW, OUTCOME_RECORDED_METADATA_ONLY, CLOSED_METADATA_ONLY, ESCALATED})


class OffboardingStatus:
	DRAFT = "DRAFT"
	CLEARANCE_IN_PROGRESS = "CLEARANCE_IN_PROGRESS"
	ACCESS_REVIEW_REQUIRED = "ACCESS_REVIEW_REQUIRED"
	HANDOVER_REQUIRED = "HANDOVER_REQUIRED"
	COMPLETE_METADATA_ONLY = "COMPLETE_METADATA_ONLY"
	BLOCKED = "BLOCKED"
	ALL = frozenset({DRAFT, CLEARANCE_IN_PROGRESS, ACCESS_REVIEW_REQUIRED, HANDOVER_REQUIRED, COMPLETE_METADATA_ONLY, BLOCKED})


class ProviderReadinessStatus:
	NOT_CONFIGURED = "NOT_CONFIGURED"
	PROFILE_DRAFT = "PROFILE_DRAFT"
	PROFILE_READY_NON_LIVE = "PROFILE_READY_NON_LIVE"
	DATA_QUALITY_REVIEW = "DATA_QUALITY_REVIEW"
	LIVE_DEFERRED = "LIVE_DEFERRED"
	BLOCKED = "BLOCKED"
	ALL = frozenset({NOT_CONFIGURED, PROFILE_DRAFT, PROFILE_READY_NON_LIVE, DATA_QUALITY_REVIEW, LIVE_DEFERRED, BLOCKED})


class ReviewDecision:
	APPROVE_METADATA_ONLY = "APPROVE_METADATA_ONLY"
	REJECT_METADATA_ONLY = "REJECT_METADATA_ONLY"
	REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"
	ESCALATE_TO_COMMITTEE = "ESCALATE_TO_COMMITTEE"
	NO_DECISION = "NO_DECISION"
	ALL = frozenset({APPROVE_METADATA_ONLY, REJECT_METADATA_ONLY, REQUEST_MORE_EVIDENCE, ESCALATE_TO_COMMITTEE, NO_DECISION})


class AuditEventType:
	STAFF_PROFILE_CREATED = "STAFF_PROFILE_CREATED"
	EMPLOYEE_RECORD_UPDATED = "EMPLOYEE_RECORD_UPDATED"
	RECRUITMENT_REQUEST_CREATED = "RECRUITMENT_REQUEST_CREATED"
	RECRUITMENT_REVIEW_RECORDED = "RECRUITMENT_REVIEW_RECORDED"
	HIRING_EVIDENCE_PACK_CREATED = "HIRING_EVIDENCE_PACK_CREATED"
	ONBOARDING_CASE_CREATED = "ONBOARDING_CASE_CREATED"
	ONBOARDING_CHECKLIST_UPDATED = "ONBOARDING_CHECKLIST_UPDATED"
	PROBATION_REVIEW_RECORDED = "PROBATION_REVIEW_RECORDED"
	LEAVE_REQUEST_SUBMITTED = "LEAVE_REQUEST_SUBMITTED"
	LEAVE_REVIEW_RECORDED = "LEAVE_REVIEW_RECORDED"
	APPRAISAL_CYCLE_CREATED = "APPRAISAL_CYCLE_CREATED"
	APPRAISAL_REVIEW_RECORDED = "APPRAISAL_REVIEW_RECORDED"
	TRAINING_CERTIFICATION_RECORDED = "TRAINING_CERTIFICATION_RECORDED"
	CERTIFICATION_EXPIRY_FLAGGED = "CERTIFICATION_EXPIRY_FLAGGED"
	STAFF_REQUEST_CREATED = "STAFF_REQUEST_CREATED"
	STAFF_APPEAL_RECORDED = "STAFF_APPEAL_RECORDED"
	POLICY_EXCEPTION_RECORDED = "POLICY_EXCEPTION_RECORDED"
	DISCIPLINARY_CASE_INTAKE_CREATED = "DISCIPLINARY_CASE_INTAKE_CREATED"
	DISCIPLINARY_EVIDENCE_ADDED = "DISCIPLINARY_EVIDENCE_ADDED"
	DISCIPLINARY_REVIEW_RECORDED = "DISCIPLINARY_REVIEW_RECORDED"
	OFFBOARDING_CASE_CREATED = "OFFBOARDING_CASE_CREATED"
	ACCESS_REVIEW_RECORDED = "ACCESS_REVIEW_RECORDED"
	WORKLOAD_BRIDGE_RECORD_CREATED = "WORKLOAD_BRIDGE_RECORD_CREATED"
	PAYROLL_READINESS_PROFILE_CREATED = "PAYROLL_READINESS_PROFILE_CREATED"
	PROVIDER_READINESS_EVIDENCE_RECORDED = "PROVIDER_READINESS_EVIDENCE_RECORDED"
	DASHBOARD_SNAPSHOT_COMPUTED = "DASHBOARD_SNAPSHOT_COMPUTED"
	LIMITATION_FLAG_RECORDED = "LIMITATION_FLAG_RECORDED"
	HUMAN_REVIEW_REQUIRED_FLAGGED = "HUMAN_REVIEW_REQUIRED_FLAGGED"
	FORBIDDEN_AUTOMATION_ATTEMPT_BLOCKED = "FORBIDDEN_AUTOMATION_ATTEMPT_BLOCKED"
	ALL = frozenset(
		{
			STAFF_PROFILE_CREATED,
			EMPLOYEE_RECORD_UPDATED,
			RECRUITMENT_REQUEST_CREATED,
			RECRUITMENT_REVIEW_RECORDED,
			HIRING_EVIDENCE_PACK_CREATED,
			ONBOARDING_CASE_CREATED,
			ONBOARDING_CHECKLIST_UPDATED,
			PROBATION_REVIEW_RECORDED,
			LEAVE_REQUEST_SUBMITTED,
			LEAVE_REVIEW_RECORDED,
			APPRAISAL_CYCLE_CREATED,
			APPRAISAL_REVIEW_RECORDED,
			TRAINING_CERTIFICATION_RECORDED,
			CERTIFICATION_EXPIRY_FLAGGED,
			STAFF_REQUEST_CREATED,
			STAFF_APPEAL_RECORDED,
			POLICY_EXCEPTION_RECORDED,
			DISCIPLINARY_CASE_INTAKE_CREATED,
			DISCIPLINARY_EVIDENCE_ADDED,
			DISCIPLINARY_REVIEW_RECORDED,
			OFFBOARDING_CASE_CREATED,
			ACCESS_REVIEW_RECORDED,
			WORKLOAD_BRIDGE_RECORD_CREATED,
			PAYROLL_READINESS_PROFILE_CREATED,
			PROVIDER_READINESS_EVIDENCE_RECORDED,
			DASHBOARD_SNAPSHOT_COMPUTED,
			LIMITATION_FLAG_RECORDED,
			HUMAN_REVIEW_REQUIRED_FLAGGED,
			FORBIDDEN_AUTOMATION_ATTEMPT_BLOCKED,
		}
	)


ALLOWED_STAFF_STATUS_TRANSITIONS = {
	StaffStatus.DRAFT: frozenset({StaffStatus.ACTIVE, StaffStatus.ARCHIVED}),
	StaffStatus.ACTIVE: frozenset({StaffStatus.ON_LEAVE, StaffStatus.SUSPENDED_METADATA_ONLY, StaffStatus.EXIT_PENDING, StaffStatus.ARCHIVED}),
	StaffStatus.ON_LEAVE: frozenset({StaffStatus.ACTIVE, StaffStatus.EXIT_PENDING, StaffStatus.ARCHIVED}),
	StaffStatus.SUSPENDED_METADATA_ONLY: frozenset({StaffStatus.ACTIVE, StaffStatus.EXIT_PENDING, StaffStatus.ARCHIVED}),
	StaffStatus.EXIT_PENDING: frozenset({StaffStatus.EXITED_METADATA_ONLY, StaffStatus.ARCHIVED}),
	StaffStatus.EXITED_METADATA_ONLY: frozenset({StaffStatus.ARCHIVED}),
	StaffStatus.ARCHIVED: frozenset(),
}

ALLOWED_RECRUITMENT_STATUS_TRANSITIONS = {
	RecruitmentStatus.DRAFT: frozenset({RecruitmentStatus.SUBMITTED, RecruitmentStatus.CANCELLED}),
	RecruitmentStatus.SUBMITTED: frozenset({RecruitmentStatus.UNDER_REVIEW, RecruitmentStatus.CANCELLED}),
	RecruitmentStatus.UNDER_REVIEW: frozenset({RecruitmentStatus.SHORTLISTED, RecruitmentStatus.COMMITTEE_REVIEW, RecruitmentStatus.CANCELLED}),
	RecruitmentStatus.SHORTLISTED: frozenset({RecruitmentStatus.COMMITTEE_REVIEW, RecruitmentStatus.CANCELLED}),
	RecruitmentStatus.COMMITTEE_REVIEW: frozenset({RecruitmentStatus.EVIDENCE_COMPLETE, RecruitmentStatus.CANCELLED}),
	RecruitmentStatus.EVIDENCE_COMPLETE: frozenset({RecruitmentStatus.CLOSED_METADATA_ONLY, RecruitmentStatus.CANCELLED}),
	RecruitmentStatus.CLOSED_METADATA_ONLY: frozenset(),
	RecruitmentStatus.CANCELLED: frozenset(),
}

ALLOWED_ONBOARDING_STATUS_TRANSITIONS = {
	OnboardingStatus.DRAFT: frozenset({OnboardingStatus.DOCUMENT_COLLECTION, OnboardingStatus.BLOCKED}),
	OnboardingStatus.DOCUMENT_COLLECTION: frozenset({OnboardingStatus.IN_PROGRESS, OnboardingStatus.BLOCKED}),
	OnboardingStatus.IN_PROGRESS: frozenset({OnboardingStatus.PROBATION_STARTED, OnboardingStatus.REVIEW_REQUIRED, OnboardingStatus.BLOCKED}),
	OnboardingStatus.PROBATION_STARTED: frozenset({OnboardingStatus.REVIEW_REQUIRED, OnboardingStatus.COMPLETE_METADATA_ONLY, OnboardingStatus.BLOCKED}),
	OnboardingStatus.REVIEW_REQUIRED: frozenset({OnboardingStatus.COMPLETE_METADATA_ONLY, OnboardingStatus.BLOCKED}),
	OnboardingStatus.COMPLETE_METADATA_ONLY: frozenset(),
	OnboardingStatus.BLOCKED: frozenset({OnboardingStatus.IN_PROGRESS, OnboardingStatus.REVIEW_REQUIRED}),
}

ALLOWED_LEAVE_STATUS_TRANSITIONS = {
	LeaveRequestStatus.DRAFT: frozenset({LeaveRequestStatus.SUBMITTED, LeaveRequestStatus.CANCELLED}),
	LeaveRequestStatus.SUBMITTED: frozenset({LeaveRequestStatus.MANAGER_REVIEW, LeaveRequestStatus.CANCELLED}),
	LeaveRequestStatus.MANAGER_REVIEW: frozenset({LeaveRequestStatus.HR_REVIEW, LeaveRequestStatus.REJECTED_METADATA_ONLY, LeaveRequestStatus.CANCELLED}),
	LeaveRequestStatus.HR_REVIEW: frozenset({LeaveRequestStatus.APPROVED_METADATA_ONLY, LeaveRequestStatus.REJECTED_METADATA_ONLY, LeaveRequestStatus.CANCELLED}),
	LeaveRequestStatus.APPROVED_METADATA_ONLY: frozenset(),
	LeaveRequestStatus.REJECTED_METADATA_ONLY: frozenset(),
	LeaveRequestStatus.CANCELLED: frozenset(),
}

ALLOWED_APPRAISAL_STATUS_TRANSITIONS = {
	AppraisalStatus.DRAFT: frozenset({AppraisalStatus.OPEN, AppraisalStatus.ARCHIVED}),
	AppraisalStatus.OPEN: frozenset({AppraisalStatus.REVIEW_IN_PROGRESS, AppraisalStatus.HUMAN_REVIEW_REQUIRED, AppraisalStatus.ARCHIVED}),
	AppraisalStatus.REVIEW_IN_PROGRESS: frozenset({AppraisalStatus.HUMAN_REVIEW_REQUIRED, AppraisalStatus.COMPLETED_METADATA_ONLY, AppraisalStatus.ARCHIVED}),
	AppraisalStatus.HUMAN_REVIEW_REQUIRED: frozenset({AppraisalStatus.COMPLETED_METADATA_ONLY, AppraisalStatus.ARCHIVED}),
	AppraisalStatus.COMPLETED_METADATA_ONLY: frozenset({AppraisalStatus.ARCHIVED}),
	AppraisalStatus.ARCHIVED: frozenset(),
}

ALLOWED_TRAINING_STATUS_TRANSITIONS = {
	TrainingStatus.PLANNED: frozenset({TrainingStatus.IN_PROGRESS, TrainingStatus.EVIDENCE_REQUIRED}),
	TrainingStatus.IN_PROGRESS: frozenset({TrainingStatus.COMPLETED_METADATA_ONLY, TrainingStatus.EVIDENCE_REQUIRED}),
	TrainingStatus.COMPLETED_METADATA_ONLY: frozenset({TrainingStatus.EXPIRING, TrainingStatus.EXPIRED}),
	TrainingStatus.EXPIRING: frozenset({TrainingStatus.EXPIRED, TrainingStatus.COMPLETED_METADATA_ONLY}),
	TrainingStatus.EXPIRED: frozenset({TrainingStatus.PLANNED, TrainingStatus.EVIDENCE_REQUIRED}),
	TrainingStatus.EVIDENCE_REQUIRED: frozenset({TrainingStatus.IN_PROGRESS, TrainingStatus.COMPLETED_METADATA_ONLY}),
}

ALLOWED_DISCIPLINARY_STATUS_TRANSITIONS = {
	DisciplinaryCaseStatus.INTAKE: frozenset({DisciplinaryCaseStatus.HUMAN_REVIEW_REQUIRED, DisciplinaryCaseStatus.ESCALATED}),
	DisciplinaryCaseStatus.HUMAN_REVIEW_REQUIRED: frozenset({DisciplinaryCaseStatus.EVIDENCE_COLLECTION, DisciplinaryCaseStatus.ESCALATED}),
	DisciplinaryCaseStatus.EVIDENCE_COLLECTION: frozenset({DisciplinaryCaseStatus.COMMITTEE_REVIEW, DisciplinaryCaseStatus.ESCALATED}),
	DisciplinaryCaseStatus.COMMITTEE_REVIEW: frozenset({DisciplinaryCaseStatus.OUTCOME_RECORDED_METADATA_ONLY, DisciplinaryCaseStatus.ESCALATED}),
	DisciplinaryCaseStatus.OUTCOME_RECORDED_METADATA_ONLY: frozenset({DisciplinaryCaseStatus.CLOSED_METADATA_ONLY}),
	DisciplinaryCaseStatus.CLOSED_METADATA_ONLY: frozenset(),
	DisciplinaryCaseStatus.ESCALATED: frozenset({DisciplinaryCaseStatus.COMMITTEE_REVIEW, DisciplinaryCaseStatus.CLOSED_METADATA_ONLY}),
}

ALLOWED_OFFBOARDING_STATUS_TRANSITIONS = {
	OffboardingStatus.DRAFT: frozenset({OffboardingStatus.CLEARANCE_IN_PROGRESS, OffboardingStatus.BLOCKED}),
	OffboardingStatus.CLEARANCE_IN_PROGRESS: frozenset({OffboardingStatus.ACCESS_REVIEW_REQUIRED, OffboardingStatus.HANDOVER_REQUIRED, OffboardingStatus.BLOCKED}),
	OffboardingStatus.ACCESS_REVIEW_REQUIRED: frozenset({OffboardingStatus.HANDOVER_REQUIRED, OffboardingStatus.COMPLETE_METADATA_ONLY, OffboardingStatus.BLOCKED}),
	OffboardingStatus.HANDOVER_REQUIRED: frozenset({OffboardingStatus.COMPLETE_METADATA_ONLY, OffboardingStatus.BLOCKED}),
	OffboardingStatus.COMPLETE_METADATA_ONLY: frozenset(),
	OffboardingStatus.BLOCKED: frozenset({OffboardingStatus.CLEARANCE_IN_PROGRESS, OffboardingStatus.ACCESS_REVIEW_REQUIRED}),
}

ALLOWED_PROVIDER_READINESS_STATUS_TRANSITIONS = {
	ProviderReadinessStatus.NOT_CONFIGURED: frozenset({ProviderReadinessStatus.PROFILE_DRAFT, ProviderReadinessStatus.BLOCKED}),
	ProviderReadinessStatus.PROFILE_DRAFT: frozenset({ProviderReadinessStatus.PROFILE_READY_NON_LIVE, ProviderReadinessStatus.BLOCKED}),
	ProviderReadinessStatus.PROFILE_READY_NON_LIVE: frozenset({ProviderReadinessStatus.DATA_QUALITY_REVIEW, ProviderReadinessStatus.LIVE_DEFERRED, ProviderReadinessStatus.BLOCKED}),
	ProviderReadinessStatus.DATA_QUALITY_REVIEW: frozenset({ProviderReadinessStatus.PROFILE_READY_NON_LIVE, ProviderReadinessStatus.LIVE_DEFERRED, ProviderReadinessStatus.BLOCKED}),
	ProviderReadinessStatus.LIVE_DEFERRED: frozenset({ProviderReadinessStatus.PROFILE_READY_NON_LIVE, ProviderReadinessStatus.BLOCKED}),
	ProviderReadinessStatus.BLOCKED: frozenset({ProviderReadinessStatus.PROFILE_DRAFT, ProviderReadinessStatus.PROFILE_READY_NON_LIVE}),
}


def _jsonb_default_empty_object():
	return sa_text("'{}'::jsonb")


def _jsonb_default_empty_list():
	return sa_text("'[]'::jsonb")


@declarative_mixin
class HRFoundationMixin:
	tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
	source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
	evidence_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
	human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
	fake_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	provider_connected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	notes: Mapped[str | None] = mapped_column(Text, nullable=True)
	created_by_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
	updated_by_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
	metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=_jsonb_default_empty_object())
	limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=_jsonb_default_empty_list())
	created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
	updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))


def _reviewable_model(class_name: str, table_name: str, *, default_status: str = "DRAFT", extra_columns: dict[str, object] | None = None, unique_fields: tuple[str, ...] = ()):
	attributes: dict[str, object] = {
		"__tablename__": table_name,
		"__module__": __name__,
		"id": mapped_column(BigInteger, primary_key=True, autoincrement=True),
		"status": mapped_column(String(64), nullable=False, default=default_status, server_default=sa_text(f"'{default_status}'")),
	}
	attributes.update(extra_columns or {})
	table_args: list[object] = [Index(f"ix_{table_name}_tenant_status", "tenant_id", "status")]
	for field_name in unique_fields:
		table_args.append(UniqueConstraint("tenant_id", field_name, name=f"uq_{table_name}_{field_name}"))
	attributes["__table_args__"] = tuple(table_args)
	return type(class_name, (Base, HRFoundationMixin), attributes)


StaffProfile = _reviewable_model("StaffProfile", "hr_staff_profiles", default_status=StaffStatus.DRAFT, extra_columns={"staff_ref": mapped_column(String(128), nullable=False), "full_name": mapped_column(String(255), nullable=False), "department_ref": mapped_column(String(128), nullable=True), "position_ref": mapped_column(String(128), nullable=True)}, unique_fields=("staff_ref",))
EmployeeRecord = _reviewable_model("EmployeeRecord", "hr_employee_records", default_status=StaffStatus.DRAFT, extra_columns={"employee_number": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "full_name": mapped_column(String(255), nullable=False), "position_ref": mapped_column(String(128), nullable=True)}, unique_fields=("employee_number",))
StaffStatusHistory = _reviewable_model("StaffStatusHistory", "hr_staff_status_history", default_status=StaffStatus.DRAFT, extra_columns={"staff_ref": mapped_column(String(128), nullable=True), "previous_status": mapped_column(String(64), nullable=True), "changed_by_id": mapped_column(String(255), nullable=True), "reason": mapped_column(Text, nullable=True)})
PositionAssignment = _reviewable_model("PositionAssignment", "hr_position_assignments", default_status=StaffStatus.DRAFT, extra_columns={"assignment_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "position_ref": mapped_column(String(128), nullable=True)}, unique_fields=("assignment_ref",))
DepartmentAssignment = _reviewable_model("DepartmentAssignment", "hr_department_assignments", default_status=StaffStatus.DRAFT, extra_columns={"assignment_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "department_ref": mapped_column(String(128), nullable=True)}, unique_fields=("assignment_ref",))
FacultyProfile = _reviewable_model("FacultyProfile", "hr_faculty_profiles", default_status=StaffStatus.DRAFT, extra_columns={"faculty_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "teaching_profile": mapped_column(String(255), nullable=True)}, unique_fields=("faculty_ref",))
RecruitmentRequest = _reviewable_model("RecruitmentRequest", "hr_recruitment_requests", default_status=RecruitmentStatus.DRAFT, extra_columns={"recruitment_ref": mapped_column(String(128), nullable=False), "department_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("recruitment_ref",))
RecruitmentPipelineItem = _reviewable_model("RecruitmentPipelineItem", "hr_recruitment_pipeline_items", default_status=RecruitmentStatus.DRAFT, extra_columns={"pipeline_ref": mapped_column(String(128), nullable=False), "recruitment_ref": mapped_column(String(128), nullable=True), "candidate_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("pipeline_ref",))
CandidateShortlistMetadata = _reviewable_model("CandidateShortlistMetadata", "hr_candidate_shortlist_metadata", default_status=RecruitmentStatus.SHORTLISTED, extra_columns={"shortlist_ref": mapped_column(String(128), nullable=False), "candidate_ref": mapped_column(String(128), nullable=True), "recruitment_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("shortlist_ref",))
HiringCommitteeReview = _reviewable_model("HiringCommitteeReview", "hr_hiring_committee_reviews", default_status=RecruitmentStatus.COMMITTEE_REVIEW, extra_columns={"review_ref": mapped_column(String(128), nullable=False), "recruitment_ref": mapped_column(String(128), nullable=True), "reviewer_id": mapped_column(String(255), nullable=True), "decision": mapped_column(String(64), nullable=False, default=ReviewDecision.NO_DECISION, server_default=sa_text("'NO_DECISION'"))}, unique_fields=("review_ref",))
HiringEvidencePack = _reviewable_model("HiringEvidencePack", "hr_hiring_evidence_packs", default_status=RecruitmentStatus.EVIDENCE_COMPLETE, extra_columns={"evidence_pack_ref": mapped_column(String(128), nullable=False), "recruitment_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False), "reference_uri": mapped_column(String(255), nullable=True)}, unique_fields=("evidence_pack_ref",))
OnboardingCase = _reviewable_model("OnboardingCase", "hr_onboarding_cases", default_status=OnboardingStatus.DRAFT, extra_columns={"onboarding_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("onboarding_ref",))
OnboardingChecklistItem = _reviewable_model("OnboardingChecklistItem", "hr_onboarding_checklist_items", default_status=OnboardingStatus.DOCUMENT_COLLECTION, extra_columns={"checklist_ref": mapped_column(String(128), nullable=False), "onboarding_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("checklist_ref",))
ProbationReview = _reviewable_model("ProbationReview", "hr_probation_reviews", default_status=OnboardingStatus.REVIEW_REQUIRED, extra_columns={"review_ref": mapped_column(String(128), nullable=False), "onboarding_ref": mapped_column(String(128), nullable=True), "reviewer_id": mapped_column(String(255), nullable=True), "decision": mapped_column(String(64), nullable=False, default=ReviewDecision.NO_DECISION, server_default=sa_text("'NO_DECISION'"))}, unique_fields=("review_ref",))
LeaveRequest = _reviewable_model("LeaveRequest", "hr_leave_requests", default_status=LeaveRequestStatus.DRAFT, extra_columns={"leave_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "leave_type": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("leave_ref",))
AbsenceMetadata = _reviewable_model("AbsenceMetadata", "hr_absence_metadata", default_status=LeaveRequestStatus.SUBMITTED, extra_columns={"absence_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("absence_ref",))
LeaveBalanceSnapshot = _reviewable_model("LeaveBalanceSnapshot", "hr_leave_balance_snapshots", default_status=LeaveRequestStatus.SUBMITTED, extra_columns={"snapshot_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "balance_days": mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0"))}, unique_fields=("snapshot_ref",))
StaffAttendanceMetadata = _reviewable_model("StaffAttendanceMetadata", "hr_staff_attendance_metadata", default_status=LeaveRequestStatus.SUBMITTED, extra_columns={"attendance_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("attendance_ref",))
StaffRequest = _reviewable_model("StaffRequest", "hr_staff_requests", default_status=RecruitmentStatus.DRAFT, extra_columns={"request_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "request_type": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("request_ref",))
StaffAppeal = _reviewable_model("StaffAppeal", "hr_staff_appeals", default_status=RecruitmentStatus.DRAFT, extra_columns={"appeal_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("appeal_ref",))
PolicyException = _reviewable_model("PolicyException", "hr_policy_exceptions", default_status=RecruitmentStatus.DRAFT, extra_columns={"exception_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "policy_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("exception_ref",))
PerformanceAppraisalCycle = _reviewable_model("PerformanceAppraisalCycle", "hr_performance_appraisal_cycles", default_status=AppraisalStatus.DRAFT, extra_columns={"appraisal_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("appraisal_ref",))
AppraisalReviewEvidence = _reviewable_model("AppraisalReviewEvidence", "hr_appraisal_review_evidence", default_status=AppraisalStatus.HUMAN_REVIEW_REQUIRED, extra_columns={"review_ref": mapped_column(String(128), nullable=False), "appraisal_ref": mapped_column(String(128), nullable=True), "reviewer_id": mapped_column(String(255), nullable=True), "decision": mapped_column(String(64), nullable=False, default=ReviewDecision.NO_DECISION, server_default=sa_text("'NO_DECISION'"))}, unique_fields=("review_ref",))
TrainingCertification = _reviewable_model("TrainingCertification", "hr_training_certifications", default_status=TrainingStatus.PLANNED, extra_columns={"certification_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("certification_ref",))
CertificationExpiryTracking = _reviewable_model("CertificationExpiryTracking", "hr_certification_expiry_tracking", default_status=TrainingStatus.EXPIRING, extra_columns={"tracking_ref": mapped_column(String(128), nullable=False), "certification_ref": mapped_column(String(128), nullable=True), "days_until_expiry": mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0"))}, unique_fields=("tracking_ref",))
StaffDevelopmentPlan = _reviewable_model("StaffDevelopmentPlan", "hr_staff_development_plans", default_status=TrainingStatus.PLANNED, extra_columns={"plan_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("plan_ref",))
DisciplinaryCase = _reviewable_model("DisciplinaryCase", "hr_disciplinary_cases", default_status=DisciplinaryCaseStatus.INTAKE, extra_columns={"case_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("case_ref",))
DisciplinaryReviewEvidence = _reviewable_model("DisciplinaryReviewEvidence", "hr_disciplinary_review_evidence", default_status=DisciplinaryCaseStatus.HUMAN_REVIEW_REQUIRED, extra_columns={"review_ref": mapped_column(String(128), nullable=False), "case_ref": mapped_column(String(128), nullable=True), "reviewer_id": mapped_column(String(255), nullable=True), "decision": mapped_column(String(64), nullable=False, default=ReviewDecision.NO_DECISION, server_default=sa_text("'NO_DECISION'"))}, unique_fields=("review_ref",))
ExitOffboardingCase = _reviewable_model("ExitOffboardingCase", "hr_exit_offboarding_cases", default_status=OffboardingStatus.DRAFT, extra_columns={"offboarding_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "title": mapped_column(String(255), nullable=False)}, unique_fields=("offboarding_ref",))
AccessLifecycleReview = _reviewable_model("AccessLifecycleReview", "hr_access_lifecycle_reviews", default_status=OffboardingStatus.ACCESS_REVIEW_REQUIRED, extra_columns={"review_ref": mapped_column(String(128), nullable=False), "offboarding_ref": mapped_column(String(128), nullable=True), "reviewer_id": mapped_column(String(255), nullable=True), "decision": mapped_column(String(64), nullable=False, default=ReviewDecision.NO_DECISION, server_default=sa_text("'NO_DECISION'"))}, unique_fields=("review_ref",))
WorkloadBridgeRecord = _reviewable_model("WorkloadBridgeRecord", "hr_workload_bridge_records", default_status=RecruitmentStatus.DRAFT, extra_columns={"bridge_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "bridge_target": mapped_column(String(128), nullable=False), "read_only_first": mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true")), "mutation_allowed": mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))}, unique_fields=("bridge_ref",))
PayrollReadinessProfile = _reviewable_model("PayrollReadinessProfile", "hr_payroll_readiness_profiles", default_status=ProviderReadinessStatus.NOT_CONFIGURED, extra_columns={"profile_ref": mapped_column(String(128), nullable=False), "staff_ref": mapped_column(String(128), nullable=True), "provider_name": mapped_column(String(128), nullable=False, default="HR_PAYROLL_PROVIDER", server_default=sa_text("'HR_PAYROLL_PROVIDER'")), "payroll_execution_enabled": mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false")), "live_provider_sync": mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))}, unique_fields=("profile_ref",))
ProviderReadinessEvidence = _reviewable_model("ProviderReadinessEvidence", "hr_provider_readiness_evidence", default_status=ProviderReadinessStatus.NOT_CONFIGURED, extra_columns={"evidence_ref": mapped_column(String(128), nullable=False), "provider_name": mapped_column(String(128), nullable=False), "readiness_status": mapped_column(String(64), nullable=False, default=ProviderReadinessStatus.NOT_CONFIGURED, server_default=sa_text("'NOT_CONFIGURED'")), "credentials_present": mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false")), "live_call_count": mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0")), "sync_count": mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0")), "external_submission_count": mapped_column(Integer, nullable=False, default=0, server_default=sa_text("0")), "live_integration_deferred": mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))}, unique_fields=("evidence_ref",))


class StaffComplianceDashboardSnapshot(Base):
	__tablename__ = "hr_staff_compliance_dashboard_snapshots"

	id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
	tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
	status: Mapped[str] = mapped_column(String(64), nullable=False, default="ACTIVE_METADATA_ONLY", server_default=sa_text("'ACTIVE_METADATA_ONLY'"))
	fake_metrics: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	fake_hr_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	provider_connected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	live_provider_sync: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	payroll_execution_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	automatic_decision_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
	incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
	data_source: Mapped[str] = mapped_column(String(128), nullable=False, default=DATA_SOURCE, server_default=sa_text(f"'{DATA_SOURCE}'"))
	summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=_jsonb_default_empty_object())
	limitation_flags_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=_jsonb_default_empty_list())
	created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))

	__table_args__ = (Index("ix_hr_staff_compliance_dashboard_snapshots_tenant_created_at", "tenant_id", "created_at"),)


class AuditEvent(Base):
	__tablename__ = "hr_audit_events"

	id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
	tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
	event_type: Mapped[str] = mapped_column(String(128), nullable=False)
	source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
	source_entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
	actor_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
	previous_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
	new_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
	payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=_jsonb_default_empty_object())
	human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
	provider_connected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	hidden_score_present: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))

	__table_args__ = (Index("ix_hr_audit_events_tenant_created_at", "tenant_id", "created_at"),)


class EvidenceRepository(Base):
	__tablename__ = "hr_evidence_repository"

	id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
	tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
	status: Mapped[str] = mapped_column(String(64), nullable=False, default="METADATA_ONLY", server_default=sa_text("'METADATA_ONLY'"))
	source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
	source_entity_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
	evidence_type: Mapped[str] = mapped_column(String(128), nullable=False)
	title: Mapped[str] = mapped_column(String(255), nullable=False)
	reference_uri: Mapped[str | None] = mapped_column(String(255), nullable=True)
	storage_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
	source_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
	evidence_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
	human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=sa_text("true"))
	fake_data: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	provider_connected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=sa_text("false"))
	notes: Mapped[str | None] = mapped_column(Text, nullable=True)
	created_by_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
	updated_by_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
	limitations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=_jsonb_default_empty_list())
	metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=_jsonb_default_empty_object())
	created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
	updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))

	__table_args__ = (
		Index("ix_hr_evidence_repository_tenant_created_at", "tenant_id", "created_at"),
		Index("ix_hr_evidence_repository_tenant_entity", "tenant_id", "source_entity_type", "source_entity_id"),
	)


TABLE_NAMES = {
	"hr_staff_profiles",
	"hr_employee_records",
	"hr_staff_status_history",
	"hr_position_assignments",
	"hr_department_assignments",
	"hr_faculty_profiles",
	"hr_recruitment_requests",
	"hr_recruitment_pipeline_items",
	"hr_candidate_shortlist_metadata",
	"hr_hiring_committee_reviews",
	"hr_hiring_evidence_packs",
	"hr_onboarding_cases",
	"hr_onboarding_checklist_items",
	"hr_probation_reviews",
	"hr_leave_requests",
	"hr_absence_metadata",
	"hr_leave_balance_snapshots",
	"hr_staff_attendance_metadata",
	"hr_staff_requests",
	"hr_staff_appeals",
	"hr_policy_exceptions",
	"hr_performance_appraisal_cycles",
	"hr_appraisal_review_evidence",
	"hr_training_certifications",
	"hr_certification_expiry_tracking",
	"hr_staff_development_plans",
	"hr_disciplinary_cases",
	"hr_disciplinary_review_evidence",
	"hr_exit_offboarding_cases",
	"hr_access_lifecycle_reviews",
	"hr_workload_bridge_records",
	"hr_payroll_readiness_profiles",
	"hr_provider_readiness_evidence",
	"hr_staff_compliance_dashboard_snapshots",
	"hr_audit_events",
	"hr_evidence_repository",
}