"""HR / Staff Governance backend foundation Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HRSafetySchema(BaseModel):
	human_review_required: bool = True
	fake_data: bool = False
	provider_connected: bool = False
	limitations: list[str] = Field(default_factory=list)
	metadata: dict[str, Any] = Field(default_factory=dict)


class HRMetadataRequestBase(BaseModel):
	model_config = ConfigDict(extra="forbid")

	status: str | None = None
	title: str | None = None
	notes: str | None = None
	source_reference: str | None = None
	evidence_status: str | None = None
	staff_ref: str | None = None
	employee_number: str | None = None
	department_ref: str | None = None
	position_ref: str | None = None
	faculty_ref: str | None = None
	recruitment_ref: str | None = None
	onboarding_ref: str | None = None
	leave_ref: str | None = None
	request_ref: str | None = None
	appeal_ref: str | None = None
	exception_ref: str | None = None
	appraisal_ref: str | None = None
	certification_ref: str | None = None
	case_ref: str | None = None
	offboarding_ref: str | None = None
	bridge_ref: str | None = None
	profile_ref: str | None = None
	provider_name: str | None = None
	source_entity_type: str | None = None
	source_entity_id: int | None = None
	metadata: dict[str, Any] = Field(default_factory=dict)
	limitations: list[str] = Field(default_factory=list)


class HRReviewActionBase(BaseModel):
	model_config = ConfigDict(extra="forbid")

	reviewer_id: str
	decision: str
	notes: str | None = None
	status: str | None = None
	evidence_refs: list[str] = Field(default_factory=list)
	metadata: dict[str, Any] = Field(default_factory=dict)


class HRMetadataResponseBase(HRSafetySchema):
	model_config = ConfigDict(from_attributes=True)

	id: int
	tenant_id: int
	status: str
	source_reference: str | None = None
	evidence_status: str | None = None
	notes: str | None = None
	created_by_id: str | None = None
	updated_by_id: str | None = None
	created_at: datetime | None = None
	updated_at: datetime | None = None


class HRFoundationSummaryResponse(BaseModel):
	tenant_id: int
	module: str
	target_level: str
	foundation_status: str
	contract_version: str
	source_spec_commit: str
	source_product_map_commit: str
	source_vertical_selection_commit: str
	product_vertical: str
	capability_family_count: int
	detailed_capability_count: int
	workflow_group_count: int
	role_count: int
	runtime_mode: str
	data_source: str
	table_count: int
	route_count: int
	permission_count: int


class HRSafetyBoundaryResponse(BaseModel):
	tenant_id: int
	human_review_required: bool = True
	automatic_hiring_decision_enabled: bool = False
	automatic_firing_decision_enabled: bool = False
	automatic_hr_disciplinary_decision_enabled: bool = False
	automatic_leave_approval_enabled: bool = False
	automatic_leave_rejection_enabled: bool = False
	automatic_payroll_decision_enabled: bool = False
	autonomous_access_revocation_enabled: bool = False
	provider_live_integration_enabled: bool = False
	one_c_live_sync_enabled: bool = False
	payroll_live_sync_enabled: bool = False
	external_db_sync_enabled: bool = False
	hidden_employee_score_present: bool = False
	hidden_faculty_score_present: bool = False
	discriminatory_score_present: bool = False
	fake_metrics: bool = False
	fake_hr_data: bool = False


class HRDashboardSummaryResponse(BaseModel):
	tenant_id: int
	generated_at: datetime | None = None
	contract_version: str
	source_spec_commit: str
	source_product_map_commit: str
	source_vertical_selection_commit: str
	runtime_mode: str
	data_source: str
	fake_metrics: bool = False
	fake_hr_data: bool = False
	incomplete_data: bool = True
	human_review_required: bool = True
	provider_connected: bool = False
	live_provider_sync: bool = False
	payroll_execution_enabled: bool = False
	automatic_decision_enabled: bool = False
	hidden_score_present: bool = False
	limitation_flags: list[str] = Field(default_factory=list)
	staff_lifecycle_summary: dict[str, int] = Field(default_factory=dict)
	recruitment_readiness: dict[str, int] = Field(default_factory=dict)
	onboarding_progress: dict[str, int] = Field(default_factory=dict)
	employee_record_completeness: dict[str, int] = Field(default_factory=dict)
	leave_request_review_status: dict[str, int] = Field(default_factory=dict)
	training_certification_risk: dict[str, int] = Field(default_factory=dict)
	disciplinary_human_review_queue: dict[str, int] = Field(default_factory=dict)
	offboarding_access_review: dict[str, int] = Field(default_factory=dict)
	workload_bridge_visibility: dict[str, int] = Field(default_factory=dict)
	payroll_readiness_profile: dict[str, int] = Field(default_factory=dict)
	provider_readiness_status: dict[str, int] = Field(default_factory=dict)
	limitations: list[str] = Field(default_factory=list)


class HRStaffProfileCreate(HRMetadataRequestBase):
	staff_ref: str
	full_name: str


class HRStaffProfileUpdate(HRMetadataRequestBase):
	full_name: str | None = None


class HRStaffProfileResponse(HRMetadataResponseBase):
	staff_ref: str
	full_name: str
	department_ref: str | None = None
	position_ref: str | None = None


class HREmployeeRecordCreate(HRMetadataRequestBase):
	employee_number: str
	full_name: str


class HREmployeeRecordUpdate(HRMetadataRequestBase):
	full_name: str | None = None


class HREmployeeRecordResponse(HRMetadataResponseBase):
	employee_number: str
	staff_ref: str | None = None
	full_name: str
	position_ref: str | None = None


class HRRecruitmentRequestCreate(HRMetadataRequestBase):
	recruitment_ref: str | None = None
	title: str


class HRRecruitmentRequestUpdate(HRMetadataRequestBase):
	title: str | None = None


class HRRecruitmentRequestResponse(HRMetadataResponseBase):
	recruitment_ref: str
	department_ref: str | None = None
	title: str


class HRHiringCommitteeReviewCreate(HRReviewActionBase):
	recruitment_ref: str | None = None


class HRHiringCommitteeReviewResponse(HRMetadataResponseBase):
	review_ref: str
	recruitment_ref: str | None = None
	reviewer_id: str | None = None
	decision: str


class HROnboardingCaseCreate(HRMetadataRequestBase):
	onboarding_ref: str | None = None
	title: str


class HROnboardingCaseUpdate(HRMetadataRequestBase):
	title: str | None = None


class HROnboardingCaseResponse(HRMetadataResponseBase):
	onboarding_ref: str
	staff_ref: str | None = None
	title: str


class HRProbationReviewCreate(HRReviewActionBase):
	onboarding_ref: str | None = None


class HRProbationReviewResponse(HRMetadataResponseBase):
	review_ref: str
	onboarding_ref: str | None = None
	reviewer_id: str | None = None
	decision: str


class HRLeaveRequestCreate(HRMetadataRequestBase):
	leave_ref: str | None = None
	title: str
	leave_type: str | None = None


class HRLeaveReviewCreate(HRReviewActionBase):
	leave_ref: str | None = None


class HRLeaveRequestResponse(HRMetadataResponseBase):
	leave_ref: str
	staff_ref: str | None = None
	leave_type: str | None = None
	title: str


class HRAppraisalCycleCreate(HRMetadataRequestBase):
	appraisal_ref: str | None = None
	title: str


class HRAppraisalReviewCreate(HRReviewActionBase):
	appraisal_ref: str | None = None


class HRAppraisalResponse(HRMetadataResponseBase):
	appraisal_ref: str
	staff_ref: str | None = None
	title: str


class HRTrainingCertificationCreate(HRMetadataRequestBase):
	certification_ref: str | None = None
	title: str


class HRTrainingCertificationResponse(HRMetadataResponseBase):
	certification_ref: str
	staff_ref: str | None = None
	title: str


class HRStaffRequestCreate(HRMetadataRequestBase):
	request_ref: str | None = None
	title: str
	request_type: str | None = None


class HRStaffRequestResponse(HRMetadataResponseBase):
	request_ref: str
	staff_ref: str | None = None
	request_type: str | None = None
	title: str


class HRStaffAppealCreate(HRMetadataRequestBase):
	appeal_ref: str | None = None
	title: str


class HRStaffAppealResponse(HRMetadataResponseBase):
	appeal_ref: str
	staff_ref: str | None = None
	title: str


class HRPolicyExceptionCreate(HRMetadataRequestBase):
	exception_ref: str | None = None
	title: str


class HRPolicyExceptionResponse(HRMetadataResponseBase):
	exception_ref: str
	staff_ref: str | None = None
	policy_ref: str | None = None
	title: str


class HRDisciplinaryCaseCreate(HRMetadataRequestBase):
	case_ref: str | None = None
	title: str


class HRDisciplinaryReviewCreate(HRReviewActionBase):
	case_ref: str | None = None


class HRDisciplinaryCaseResponse(HRMetadataResponseBase):
	case_ref: str
	staff_ref: str | None = None
	title: str


class HROffboardingCaseCreate(HRMetadataRequestBase):
	offboarding_ref: str | None = None
	title: str


class HRAccessLifecycleReviewCreate(HRReviewActionBase):
	offboarding_ref: str | None = None


class HROffboardingCaseResponse(HRMetadataResponseBase):
	offboarding_ref: str
	staff_ref: str | None = None
	title: str


class HRWorkloadBridgeRecordCreate(HRMetadataRequestBase):
	bridge_ref: str | None = None
	bridge_target: str
	staff_ref: str | None = None


class HRWorkloadBridgeRecordResponse(HRMetadataResponseBase):
	bridge_ref: str
	bridge_target: str
	staff_ref: str | None = None
	read_only_first: bool = True
	mutation_allowed: bool = False


class HRPayrollReadinessProfileCreate(HRMetadataRequestBase):
	profile_ref: str | None = None
	provider_name: str | None = None


class HRPayrollReadinessResponse(HRMetadataResponseBase):
	profile_ref: str
	staff_ref: str | None = None
	provider_name: str
	payroll_execution_enabled: bool = False
	live_provider_sync: bool = False


class HRProviderReadinessEvidenceCreate(HRMetadataRequestBase):
	provider_name: str


class HRProviderReadinessResponse(HRMetadataResponseBase):
	evidence_ref: str
	provider_name: str
	readiness_status: str
	credentials_present: bool = False
	live_call_count: int = 0
	sync_count: int = 0
	external_submission_count: int = 0
	live_integration_deferred: bool = True


class HRAuditEventResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	tenant_id: int
	event_type: str
	source_entity_type: str
	source_entity_id: int | None = None
	actor_user_id: str | None = None
	previous_status: str | None = None
	new_status: str | None = None
	payload: dict[str, Any] = Field(default_factory=dict)
	human_review_required: bool = True
	provider_connected: bool = False
	hidden_score_present: bool = False
	created_at: datetime | None = None


class HREvidenceResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	id: int
	tenant_id: int
	status: str
	source_entity_type: str
	source_entity_id: int | None = None
	evidence_type: str
	title: str
	reference_uri: str | None = None
	storage_ref: str | None = None
	source_reference: str | None = None
	evidence_status: str | None = None
	human_review_required: bool = True
	fake_data: bool = False
	provider_connected: bool = False
	notes: str | None = None
	created_by_id: str | None = None
	updated_by_id: str | None = None
	limitations: list[str] = Field(default_factory=list)
	metadata: dict[str, Any] = Field(default_factory=dict)
	created_at: datetime | None = None
	updated_at: datetime | None = None


class HRLimitationResponse(BaseModel):
	code: str
	text: str
	source_entity_type: str | None = None
	source_entity_id: int | None = None
	metadata: dict[str, Any] = Field(default_factory=dict)