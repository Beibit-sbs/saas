"""Quality / Accreditation backend foundation Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QualityAccreditationSafetySchema(BaseModel):
    human_review_required: bool = True
    official_accreditation_approval_enabled: bool = False
    official_ministry_submission_enabled: bool = False
    official_ranking_claim_enabled: bool = False
    automatic_accreditation_decision_enabled: bool = False
    provider_integration_enabled: bool = False
    external_database_sync_enabled: bool = False
    hidden_score_present: bool = False
    autonomous_decision: bool = False
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)
    source_capability_id: str | None = None
    source_family_id: str | None = None


class QualityRecordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    title: str | None = None
    description: str | None = None
    notes: str | None = None
    framework_ref: str | None = None
    policy_ref: str | None = None
    standard_ref: str | None = None
    criterion_ref: str | None = None
    requirement_ref: str | None = None
    evidence_ref: str | None = None
    limitation_ref: str | None = None
    readiness_ref: str | None = None
    report_ref: str | None = None
    section_ref: str | None = None
    plan_ref: str | None = None
    action_ref: str | None = None
    audit_ref: str | None = None
    finding_ref: str | None = None
    cycle_ref: str | None = None
    assessment_ref: str | None = None
    feedback_ref: str | None = None
    survey_ref: str | None = None
    review_ref: str | None = None
    response_plan_ref: str | None = None
    workflow_ref: str | None = None
    gap_ref: str | None = None
    calendar_ref: str | None = None
    risk_ref: str | None = None
    bridge_ref: str | None = None
    signal_ref: str | None = None
    source_entity_type: str | None = None
    source_entity_id: int | None = None
    source_entity_ref: str | None = None
    source_vertical_ref: str | None = None
    target_reference: str | None = None
    owner_ref: str | None = None
    reviewer_ref: str | None = None
    committee_ref: str | None = None
    program_ref: str | None = None
    department_ref: str | None = None
    faculty_ref: str | None = None
    student_group_ref: str | None = None
    event_type: str | None = None
    signal_type: str | None = None
    limitation_code: str | None = None
    limitation_text: str | None = None
    risk_band: str | None = None
    completion_percent: int | None = None
    reference_uri: str | None = None
    source_capability_id: str | None = None
    source_family_id: str | None = None
    read_only_first: bool | None = None
    mutation_allowed: bool | None = None
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityEvidenceReviewActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = "REVIEWED_METADATA_ONLY"
    review_ref: str | None = None
    reviewer_ref: str | None = None
    notes: str | None = None
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityRecordResponse(QualityAccreditationSafetySchema):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived_at: datetime | None = None
    created_by_user_id: str | None = None
    updated_by_user_id: str | None = None
    title: str | None = None
    description: str | None = None
    notes: str | None = None
    framework_ref: str | None = None
    policy_ref: str | None = None
    standard_ref: str | None = None
    criterion_ref: str | None = None
    requirement_ref: str | None = None
    evidence_ref: str | None = None
    limitation_ref: str | None = None
    readiness_ref: str | None = None
    report_ref: str | None = None
    section_ref: str | None = None
    plan_ref: str | None = None
    action_ref: str | None = None
    audit_ref: str | None = None
    finding_ref: str | None = None
    cycle_ref: str | None = None
    assessment_ref: str | None = None
    feedback_ref: str | None = None
    survey_ref: str | None = None
    review_ref: str | None = None
    response_plan_ref: str | None = None
    workflow_ref: str | None = None
    gap_ref: str | None = None
    calendar_ref: str | None = None
    risk_ref: str | None = None
    bridge_ref: str | None = None
    signal_ref: str | None = None
    source_entity_type: str | None = None
    source_entity_id: int | None = None
    source_entity_ref: str | None = None
    source_vertical_ref: str | None = None
    target_reference: str | None = None
    owner_ref: str | None = None
    reviewer_ref: str | None = None
    committee_ref: str | None = None
    program_ref: str | None = None
    department_ref: str | None = None
    faculty_ref: str | None = None
    student_group_ref: str | None = None
    event_type: str | None = None
    signal_type: str | None = None
    limitation_code: str | None = None
    limitation_text: str | None = None
    risk_band: str | None = None
    completion_percent: int | None = None
    reference_uri: str | None = None
    fake_evidence: bool = False
    read_only_first: bool = True
    mutation_allowed: bool = False


class QualityRecordListResponse(BaseModel):
    items: list[QualityRecordResponse]


class QualityOverviewResponse(BaseModel):
    tenant_id: int
    module: str
    product_vertical: str
    contract_version: str
    runtime_mode: str
    table_count: int
    route_count: int
    readiness_items: int
    evidence_items: int
    bridge_items: int
    limitations: list[str] = Field(default_factory=list)
    boundary_summary: dict[str, bool] = Field(default_factory=dict)


class QualityHealthResponse(BaseModel):
    tenant_id: int
    module: str
    target_level: str
    foundation_status: str
    runtime_mode: str
    contract_version: str
    provider_integration_enabled: bool = False
    external_database_sync_enabled: bool = False
    official_accreditation_approval_enabled: bool = False
    official_ministry_submission_enabled: bool = False
    official_ranking_claim_enabled: bool = False
    hidden_score_present: bool = False
    fake_metrics: bool = False
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)
    route_count: int
    table_count: int


class QualityDashboardResponse(QualityAccreditationSafetySchema):
    tenant_id: int
    generated_at: datetime | None = None
    contract_version: str
    source_spec_commit: str
    source_product_map_commit: str
    source_vertical_selection_commit: str
    master_matrix_commit: str
    master_matrix_rows: int
    detailed_capability_count: int
    capability_family_count: int
    data_source: str
    fake_metrics: bool = False
    frameworks_summary: dict[str, int] = Field(default_factory=dict)
    standards_summary: dict[str, int] = Field(default_factory=dict)
    evidence_summary: dict[str, int] = Field(default_factory=dict)
    readiness_summary: dict[str, int] = Field(default_factory=dict)
    self_assessment_summary: dict[str, int] = Field(default_factory=dict)
    improvement_summary: dict[str, int] = Field(default_factory=dict)
    audit_summary: dict[str, int] = Field(default_factory=dict)
    program_review_summary: dict[str, int] = Field(default_factory=dict)
    bridge_summary: dict[str, int] = Field(default_factory=dict)
    brain_signal_summary: dict[str, int] = Field(default_factory=dict)
    boundary_summary: dict[str, bool] = Field(default_factory=dict)


class QualityMatrixSummaryResponse(BaseModel):
    contract_version: str
    source_spec_commit: str
    source_product_map_commit: str
    source_vertical_selection_commit: str
    master_matrix_commit: str
    master_matrix_rows: int
    detailed_capability_count: int
    capability_family_count: int
    runtime_mode: str
    route_count_expected: str
    table_count_expected: int
    permission_count_expected: int


class QualityLimitationsResponse(BaseModel):
    items: list[str] = Field(default_factory=list)


class QualityAuditEventResponse(BaseModel):
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
    created_at: datetime | None = None
    human_review_required: bool = True
    provider_integration_enabled: bool = False
    hidden_score_present: bool = False


class QualityAuditEventListResponse(BaseModel):
    items: list[QualityAuditEventResponse]


class QualityStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    source_entity_type: str
    source_entity_id: int | None = None
    previous_status: str | None = None
    new_status: str
    changed_by_user_id: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualityStatusHistoryListResponse(BaseModel):
    items: list[QualityStatusHistoryResponse]