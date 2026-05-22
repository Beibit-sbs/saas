"""Academic Operations backend foundation Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AcademicOperationsSafetySchema(BaseModel):
    human_review_required: bool = True
    automated_decision: bool = False
    provider_integration_enabled: bool = False
    platonus_sync_enabled: bool = False
    sis_sync_enabled: bool = False
    hidden_score_present: bool = False
    fake_metrics: bool = False
    official_grade_publication_enabled: bool = False
    automated_grading_enabled: bool = False
    automatic_sanction_enabled: bool = False
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)
    source_matrix_row_id: str | None = None
    source_capability_id: str | None = None


class MetadataRequestBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    notes: str | None = None
    external_ref: str | None = None
    student_ref: str | None = None
    faculty_ref: str | None = None
    course_ref: str | None = None
    canonical_module_ref: str | None = None
    source_matrix_row_id: str | None = None
    source_capability_id: str | None = None
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)


class MetadataResponseBase(AcademicOperationsSafetySchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None


class AcademicGroupCreateRequest(MetadataRequestBase):
    group_code: str
    group_name: str


class AcademicGroupUpdateRequest(MetadataRequestBase):
    group_name: str | None = None


class AcademicGroupResponse(MetadataResponseBase):
    group_code: str
    group_name: str
    external_ref: str | None = None
    notes: str | None = None


class AcademicGroupListResponse(BaseModel):
    items: list[AcademicGroupResponse]


class CohortCreateRequest(MetadataRequestBase):
    cohort_code: str
    cohort_name: str
    academic_group_ref: str | None = None


class CohortUpdateRequest(MetadataRequestBase):
    cohort_name: str | None = None
    academic_group_ref: str | None = None


class CohortResponse(MetadataResponseBase):
    cohort_code: str
    cohort_name: str
    academic_group_ref: str | None = None
    notes: str | None = None


class CohortListResponse(BaseModel):
    items: list[CohortResponse]


class CourseRegistrationMetadataCreateRequest(MetadataRequestBase):
    metadata: dict[str, Any] = Field(default_factory=dict)


class CourseRegistrationMetadataResponse(MetadataResponseBase):
    student_ref: str | None = None
    course_ref: str | None = None
    canonical_module_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class CourseRegistrationMetadataListResponse(BaseModel):
    items: list[CourseRegistrationMetadataResponse]


class GradebookMetadataCreateRequest(MetadataRequestBase):
    gradebook_key: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GradebookMetadataUpdateRequest(MetadataRequestBase):
    metadata: dict[str, Any] | None = None


class GradebookMetadataResponse(MetadataResponseBase):
    student_ref: str | None = None
    course_ref: str | None = None
    gradebook_key: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class GradebookMetadataListResponse(BaseModel):
    items: list[GradebookMetadataResponse]


class RetakePlanCreateRequest(MetadataRequestBase):
    plan_code: str
    retake_window: str | None = None


class RetakePlanUpdateRequest(MetadataRequestBase):
    retake_window: str | None = None


class RetakePlanResponse(MetadataResponseBase):
    student_ref: str | None = None
    course_ref: str | None = None
    plan_code: str
    retake_window: str | None = None


class RetakePlanListResponse(BaseModel):
    items: list[RetakePlanResponse]


class SummerSemesterTermCreateRequest(MetadataRequestBase):
    term_code: str
    display_name: str
    calendar_ref: str | None = None


class SummerSemesterTermUpdateRequest(MetadataRequestBase):
    display_name: str | None = None
    calendar_ref: str | None = None


class SummerSemesterTermResponse(MetadataResponseBase):
    term_code: str
    display_name: str
    calendar_ref: str | None = None


class SummerSemesterTermListResponse(BaseModel):
    items: list[SummerSemesterTermResponse]


class AdvisorTutorAssignmentCreateRequest(MetadataRequestBase):
    assignment_code: str


class AdvisorTutorAssignmentUpdateRequest(MetadataRequestBase):
    assignment_code: str | None = None


class AdvisorTutorAssignmentResponse(MetadataResponseBase):
    student_ref: str | None = None
    faculty_ref: str | None = None
    assignment_code: str
    notes: str | None = None


class AdvisorTutorAssignmentListResponse(BaseModel):
    items: list[AdvisorTutorAssignmentResponse]


class CanonicalModuleBridgeCreateRequest(MetadataRequestBase):
    bridge_type: str
    canonical_module_ref: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CanonicalModuleBridgeResponse(MetadataResponseBase):
    bridge_type: str
    canonical_module_ref: str
    external_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CanonicalModuleBridgeListResponse(BaseModel):
    items: list[CanonicalModuleBridgeResponse]


class StudentLifecycleBridgeResponse(MetadataResponseBase):
    bridge_key: str
    student_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentWorkflowBridgeResponse(MetadataResponseBase):
    bridge_key: str
    external_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutiveGovernanceBridgeResponse(MetadataResponseBase):
    bridge_key: str
    external_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityAccreditationBridgeResponse(MetadataResponseBase):
    bridge_key: str
    external_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AcademicOperationsDashboardResponse(BaseModel):
    tenant_id: int
    fake_metrics: bool = False
    data_source: str
    master_matrix_commit: str
    master_matrix_rows: int
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)
    canonical_bridge_counts: dict[str, int] = Field(default_factory=dict)


class AcademicOperationsAuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    entity_type: str
    entity_id: int | None = None
    event_type: str
    action: str
    actor_user_id: str | None = None
    previous_status: str | None = None
    new_status: str | None = None
    human_review_required: bool
    automated_decision: bool
    provider_integration_enabled: bool
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class AcademicOperationsEvidenceCreateRequest(MetadataRequestBase):
    entity_type: str
    entity_id: int | None = None
    evidence_kind: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AcademicOperationsEvidenceResponse(MetadataResponseBase):
    entity_type: str
    entity_id: int | None = None
    evidence_kind: str
    external_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AcademicOperationsEvidenceListResponse(BaseModel):
    items: list[AcademicOperationsEvidenceResponse]


class AcademicOperationsHealthResponse(BaseModel):
    tenant_id: int
    module: str
    target_level: str
    foundation_status: str
    duplicate_module_policy: str
    provider_integration_enabled: bool
    platonus_sync_enabled: bool
    sis_sync_enabled: bool
    hidden_score_present: bool
    fake_metrics: bool
    incomplete_data: bool
    limitations: list[str] = Field(default_factory=list)
    route_count: int
    table_count: int


class AcademicOperationsMatrixSummaryResponse(BaseModel):
    master_matrix_commit: str
    master_matrix_rows: int
    contract_version: str
    target_level: str
    duplicate_module_policy: str
    true_new_modules: list[str]
    canonical_reuse_map: dict[str, str]
    bridge_map: dict[str, str]
    forbidden_runtime_claims: list[str]
    required_limitations: list[str]