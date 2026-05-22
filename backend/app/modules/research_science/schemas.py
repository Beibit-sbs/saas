"""Research / Science backend foundation Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResearchScienceSafetySchema(BaseModel):
    human_review_required: bool = True
    autonomous_decision: bool = False
    provider_integration_enabled: bool = False
    external_database_sync_enabled: bool = False
    official_verification_enabled: bool = False
    hidden_score_present: bool = False
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)
    source_matrix_row_id: str | None = None
    source_capability_id: str | None = None


class MetadataRequestBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = None
    title: str | None = None
    notes: str | None = None
    external_ref: str | None = None
    student_ref: str | None = None
    faculty_ref: str | None = None
    department_ref: str | None = None
    program_ref: str | None = None
    project_ref: str | None = None
    publication_ref: str | None = None
    conference_ref: str | None = None
    grant_ref: str | None = None
    ethics_ref: str | None = None
    bridge_ref: str | None = None
    source_matrix_row_id: str | None = None
    source_capability_id: str | None = None
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MetadataResponseBase(ResearchScienceSafetySchema):
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


class DashboardSafetySchema(ResearchScienceSafetySchema):
    fake_metrics: bool = False


class EvidenceSafetySchema(ResearchScienceSafetySchema):
    fake_evidence: bool = False


class PublicationSafetySchema(ResearchScienceSafetySchema):
    fake_publication: bool = False
    autonomous_publication_verification_enabled: bool = False


class ConferenceSafetySchema(ResearchScienceSafetySchema):
    fake_certificate: bool = False


class GrantSafetySchema(ResearchScienceSafetySchema):
    fake_grant_evidence: bool = False
    autonomous_grant_submission_enabled: bool = False


class EthicsSafetySchema(ResearchScienceSafetySchema):
    autonomous_ethics_approval_enabled: bool = False


class ResearchScienceHealthResponse(BaseModel):
    tenant_id: int
    module: str
    target_level: str
    foundation_status: str
    runtime_mode: str
    contract_version: str
    provider_integration_enabled: bool = False
    external_database_sync_enabled: bool = False
    official_verification_enabled: bool = False
    hidden_score_present: bool = False
    fake_metrics: bool = False
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)
    route_count: int
    table_count: int


class ResearchScienceDashboardResponse(DashboardSafetySchema):
    tenant_id: int
    generated_at: datetime | None = None
    contract_version: str
    source_spec_commit: str
    master_matrix_commit: str
    master_matrix_rows: int
    capability_count: int
    data_source: str
    projects_summary: dict[str, int] = Field(default_factory=dict)
    student_research_summary: dict[str, int] = Field(default_factory=dict)
    supervision_summary: dict[str, int] = Field(default_factory=dict)
    publications_summary: dict[str, int] = Field(default_factory=dict)
    conferences_summary: dict[str, int] = Field(default_factory=dict)
    grants_summary: dict[str, int] = Field(default_factory=dict)
    ethics_summary: dict[str, int] = Field(default_factory=dict)
    evidence_summary: dict[str, int] = Field(default_factory=dict)
    bridge_summary: dict[str, int] = Field(default_factory=dict)
    brain_readiness_summary: dict[str, int] = Field(default_factory=dict)
    boundary_summary: dict[str, bool] = Field(default_factory=dict)


class ResearchScienceMatrixSummaryResponse(BaseModel):
    contract_version: str
    source_spec_commit: str
    source_product_map_commit: str
    master_matrix_commit: str
    master_matrix_rows: int
    capability_count: int
    runtime_mode: str
    autonomy_mode: str
    route_count_expected: str
    table_count_expected: int


class ResearchScienceLimitationsResponse(BaseModel):
    items: list[str] = Field(default_factory=list)


class ResearchProjectCreateRequest(MetadataRequestBase):
    project_ref: str
    title: str


class ResearchProjectUpdateRequest(MetadataRequestBase):
    project_ref: str | None = None
    title: str | None = None


class ResearchProjectResponse(MetadataResponseBase):
    project_ref: str
    department_ref: str | None = None
    program_ref: str | None = None
    external_ref: str | None = None
    title: str
    notes: str | None = None


class ResearchProjectListResponse(BaseModel):
    items: list[ResearchProjectResponse]


class StudentResearchWorkCreateRequest(MetadataRequestBase):
    topic_title: str


class StudentResearchWorkUpdateRequest(MetadataRequestBase):
    topic_title: str | None = None


class StudentResearchWorkResponse(MetadataResponseBase):
    student_ref: str | None = None
    faculty_ref: str | None = None
    project_ref: str | None = None
    publication_ref: str | None = None
    conference_ref: str | None = None
    topic_title: str
    notes: str | None = None


class StudentResearchWorkListResponse(BaseModel):
    items: list[StudentResearchWorkResponse]


class ScientificSupervisionCreateRequest(MetadataRequestBase):
    supervision_ref: str


class ScientificSupervisionUpdateRequest(MetadataRequestBase):
    supervision_ref: str | None = None


class ScientificSupervisionResponse(MetadataResponseBase):
    student_ref: str | None = None
    faculty_ref: str | None = None
    project_ref: str | None = None
    supervision_ref: str
    notes: str | None = None


class ScientificSupervisionListResponse(BaseModel):
    items: list[ScientificSupervisionResponse]


class PublicationMetadataCreateRequest(MetadataRequestBase):
    publication_ref: str
    title: str


class PublicationMetadataUpdateRequest(MetadataRequestBase):
    publication_ref: str | None = None
    title: str | None = None


class PublicationMetadataResponse(MetadataResponseBase, PublicationSafetySchema):
    publication_ref: str
    faculty_ref: str | None = None
    student_ref: str | None = None
    project_ref: str | None = None
    external_ref: str | None = None
    title: str


class PublicationMetadataListResponse(BaseModel):
    items: list[PublicationMetadataResponse]


class ConferenceParticipationCreateRequest(MetadataRequestBase):
    conference_ref: str
    title: str


class ConferenceParticipationUpdateRequest(MetadataRequestBase):
    conference_ref: str | None = None
    title: str | None = None


class ConferenceParticipationResponse(MetadataResponseBase, ConferenceSafetySchema):
    conference_ref: str
    faculty_ref: str | None = None
    student_ref: str | None = None
    project_ref: str | None = None
    external_ref: str | None = None
    title: str


class ConferenceParticipationListResponse(BaseModel):
    items: list[ConferenceParticipationResponse]


class GrantApplicationCreateRequest(MetadataRequestBase):
    grant_ref: str
    title: str


class GrantApplicationUpdateRequest(MetadataRequestBase):
    grant_ref: str | None = None
    title: str | None = None


class GrantApplicationResponse(MetadataResponseBase, GrantSafetySchema):
    grant_ref: str
    project_ref: str | None = None
    department_ref: str | None = None
    faculty_ref: str | None = None
    external_ref: str | None = None
    title: str


class GrantApplicationListResponse(BaseModel):
    items: list[GrantApplicationResponse]


class GrantDeliverableCreateRequest(MetadataRequestBase):
    deliverable_ref: str
    title: str


class GrantDeliverableUpdateRequest(MetadataRequestBase):
    deliverable_ref: str | None = None
    title: str | None = None


class GrantDeliverableResponse(MetadataResponseBase, GrantSafetySchema):
    grant_ref: str | None = None
    project_ref: str | None = None
    external_ref: str | None = None
    deliverable_ref: str
    title: str


class GrantDeliverableListResponse(BaseModel):
    items: list[GrantDeliverableResponse]


class ResearchEthicsRequestCreateRequest(MetadataRequestBase):
    ethics_ref: str
    title: str


class ResearchEthicsRequestUpdateRequest(MetadataRequestBase):
    ethics_ref: str | None = None
    title: str | None = None


class ResearchEthicsRequestResponse(MetadataResponseBase, EthicsSafetySchema):
    ethics_ref: str
    project_ref: str | None = None
    faculty_ref: str | None = None
    student_ref: str | None = None
    title: str


class ResearchEthicsRequestListResponse(BaseModel):
    items: list[ResearchEthicsRequestResponse]


class ResearchEthicsAmendmentCreateRequest(MetadataRequestBase):
    amendment_ref: str
    title: str


class ResearchEthicsAmendmentResponse(MetadataResponseBase):
    ethics_ref: str | None = None
    project_ref: str | None = None
    external_ref: str | None = None
    amendment_ref: str
    title: str


class ResearchEthicsAmendmentListResponse(BaseModel):
    items: list[ResearchEthicsAmendmentResponse]


class ResearchEvidenceCreateRequest(MetadataRequestBase):
    source_entity_type: str
    source_entity_id: int | None = None
    evidence_type: str
    title: str
    description: str | None = None
    reference_uri: str | None = None
    storage_ref: str | None = None
    verification_status: str = "METADATA_ONLY"


class ResearchEvidenceResponse(MetadataResponseBase, EvidenceSafetySchema):
    source_entity_type: str
    source_entity_id: int | None = None
    evidence_type: str
    title: str
    description: str | None = None
    reference_uri: str | None = None
    storage_ref: str | None = None
    submitted_by_user_id: str | None = None
    submitted_at: datetime | None = None
    verification_status: str
    verified_by_user_id: str | None = None
    reviewed_at: datetime | None = None
    provider_verified: bool = False
    official_external_verification: bool = False


class ResearchEvidenceListResponse(BaseModel):
    items: list[ResearchEvidenceResponse]


class ResearchAuditEventResponse(BaseModel):
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
    request_id: str | None = None
    created_at: datetime | None = None
    human_review_required: bool = True
    autonomous_decision: bool = False
    provider_integration_enabled: bool = False
    hidden_score_present: bool = False


class ResearchAuditEventListResponse(BaseModel):
    items: list[ResearchAuditEventResponse]


class ResearchStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    source_entity_type: str
    source_entity_id: int | None = None
    previous_status: str | None = None
    new_status: str
    changed_by_user_id: str | None = None
    changed_at: datetime | None = None
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    human_review_required: bool = True


class ResearchBridgeCreateRequest(MetadataRequestBase):
    bridge_target: str
    source_entity_type: str
    source_entity_id: int | None = None
    target_reference: str | None = None
    bridge_status: str | None = None


class ResearchBridgeResponse(MetadataResponseBase):
    bridge_target: str
    source_entity_type: str
    source_entity_id: int | None = None
    target_reference: str | None = None
    bridge_status: str
    bridge_ref: str | None = None
    read_only_first: bool = True
    mutation_allowed: bool = False
    provider_sync_enabled: bool = False
    external_submission_enabled: bool = False


class ResearchBridgeListResponse(BaseModel):
    items: list[ResearchBridgeResponse]


class ResearchBridgeSummaryResponse(BaseModel):
    tenant_id: int
    bridge_counts: dict[str, int] = Field(default_factory=dict)
    read_only_first: bool = True
    mutation_allowed: bool = False
    provider_sync_enabled: bool = False
    external_submission_enabled: bool = False