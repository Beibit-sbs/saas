"""Research / Science backend foundation Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

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


class ResearchBrainShellResponse(BaseModel):
    tenant_id: int
    owner_module: str
    runtime_boundary: str
    navigation_entry: str
    bridge_modules: list[str] = Field(default_factory=list)
    read_only_aggregation: bool = True
    provider_execution_enabled: bool = False
    external_calls_enabled: bool = False


class ResearchBrainOrchestrationItemResponse(BaseModel):
    source_module: str
    read_only: bool = True
    total: int = 0
    notes: str


class ResearchBrainOrchestrationResponse(BaseModel):
    tenant_id: int
    projects: ResearchBrainOrchestrationItemResponse
    grants: ResearchBrainOrchestrationItemResponse
    publications: ResearchBrainOrchestrationItemResponse
    ethics: ResearchBrainOrchestrationItemResponse
    kpi: ResearchBrainOrchestrationItemResponse
    signals: ResearchBrainOrchestrationItemResponse
    researchers: ResearchBrainOrchestrationItemResponse
    researcher_summary: ResearchBrainOrchestrationItemResponse
    researcher_health: ResearchBrainOrchestrationItemResponse
    researcher_workload: ResearchBrainOrchestrationItemResponse
    researcher_risk: ResearchBrainOrchestrationItemResponse
    scientometrics: ResearchBrainOrchestrationItemResponse
    citation_analytics: ResearchBrainOrchestrationItemResponse
    impact_analytics: ResearchBrainOrchestrationItemResponse
    publication_impact: ResearchBrainOrchestrationItemResponse
    researcher_ranking: ResearchBrainOrchestrationItemResponse
    risk_profile: ResearchBrainOrchestrationItemResponse
    risk_summary: ResearchBrainOrchestrationItemResponse
    risk_signals: ResearchBrainOrchestrationItemResponse
    risk_trends: ResearchBrainOrchestrationItemResponse
    risk_recommendations: ResearchBrainOrchestrationItemResponse
    dashboard_summary: ResearchBrainOrchestrationItemResponse
    dashboard_kpi_plane: ResearchBrainOrchestrationItemResponse
    dashboard_signal_plane: ResearchBrainOrchestrationItemResponse
    dashboard_risk_plane: ResearchBrainOrchestrationItemResponse
    dashboard_scientometric_plane: ResearchBrainOrchestrationItemResponse


class ResearchBrainContextSourceResponse(BaseModel):
    source: str
    contract_status: str
    read_only: bool = True
    summary: dict[str, Any] = Field(default_factory=dict)


class ResearchBrainContextResponse(BaseModel):
    tenant_id: int
    context: dict[str, ResearchBrainContextSourceResponse] = Field(default_factory=dict)


class ResearchBrainKpiSurfaceResponse(BaseModel):
    tenant_id: int
    owner_module: str
    publication_count: int
    grant_count: int
    project_count: int
    ethics_count: int
    read_only: bool = True
    provider_execution_enabled: bool = False


class ResearchBrainSignalItemResponse(BaseModel):
    family: str
    owner: str
    source: str
    consumer: str
    review_queue: str
    read_only: bool = True
    scoring_engine_enabled: bool = False
    observed_count: int = 0


class ResearchBrainSignalSurfaceResponse(BaseModel):
    tenant_id: int
    signals: list[ResearchBrainSignalItemResponse] = Field(default_factory=list)


class ResearchBrainRoleValidationResponse(BaseModel):
    role: str
    required_permissions: list[str] = Field(default_factory=list)
    status: str


class ResearchBrainRbacValidationResponse(BaseModel):
    tenant_id: int
    tenant: str
    rbac: str
    audit: str
    roles: list[ResearchBrainRoleValidationResponse] = Field(default_factory=list)


class ResearcherPublicationSummary(BaseModel):
    publication_count: int = 0
    citation_count: int = 0


class ResearcherGrantSummary(BaseModel):
    active_grants: int = 0


class ResearcherProjectSummary(BaseModel):
    active_projects: int = 0


class ResearcherScientometricSummary(BaseModel):
    h_index: int = 0
    citation_count: int = 0


class ResearcherProfile(BaseModel):
    researcher_id: str
    employee_id: str
    full_name: str
    position: str
    faculty: str | None = None
    department: str | None = None
    laboratory: str | None = None
    research_areas: list[str] = Field(default_factory=list)
    specializations: list[str] = Field(default_factory=list)
    status: str


class Researcher(BaseModel):
    researcher_id: str
    employee_id: str
    full_name: str
    position: str
    faculty: str | None = None
    department: str | None = None
    laboratory: str | None = None
    research_areas: list[str] = Field(default_factory=list)
    specializations: list[str] = Field(default_factory=list)
    active_projects: int = 0
    active_grants: int = 0
    publication_count: int = 0
    citation_count: int = 0
    h_index: int = 0
    risk_level: str = "LOW"
    status: str = "ACTIVE"


class ResearcherListResponse(BaseModel):
    items: list[Researcher] = Field(default_factory=list)


class ResearcherDashboardSummaryResponse(BaseModel):
    tenant_id: int
    total_researchers: int
    active_researchers: int
    high_risk_researchers: int
    publication_total: int
    active_projects_total: int
    active_grants_total: int


class ResearcherActivityProfileResponse(BaseModel):
    tenant_id: int
    researcher: ResearcherProfile
    project_summary: ResearcherProjectSummary
    grant_summary: ResearcherGrantSummary
    publication_summary: ResearcherPublicationSummary
    scientometric_summary: ResearcherScientometricSummary


class ResearcherRiskProfileResponse(BaseModel):
    tenant_id: int
    researcher_id: str
    risk_level: str
    workload: dict[str, int] = Field(default_factory=dict)
    signals: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


ProviderStatus = Literal["NOT_CONNECTED", "READY", "PENDING"]


class ExternalResearchIdentity(BaseModel):
    provider_name: str
    provider_identifier: str
    provider_status: ProviderStatus


class ScientometricTrend(BaseModel):
    period: str
    citation_count: int = 0
    h_index: int = 0
    i10_index: int = 0
    trend_direction: str = "stable"
    impact_score: float = 0.0


class PublicationImpactProfile(BaseModel):
    researcher_id: str
    publication_count: int = 0
    international_publications: int = 0
    indexed_publications: int = 0
    top_publications: list[str] = Field(default_factory=list)
    citation_count: int = 0
    h_index: int = 0
    i10_index: int = 0
    trend_direction: str = "stable"
    impact_score: float = 0.0
    scientometric_risk: str = "LOW"


class CitationAnalyticsSummary(BaseModel):
    researcher_id: str
    citation_count: int = 0
    h_index: int = 0
    i10_index: int = 0
    publication_count: int = 0
    international_publications: int = 0
    indexed_publications: int = 0
    top_publications: list[str] = Field(default_factory=list)
    trend_direction: str = "stable"
    impact_score: float = 0.0
    scientometric_risk: str = "LOW"


class ResearcherScientometricProfile(BaseModel):
    researcher_id: str
    citation_count: int = 0
    h_index: int = 0
    i10_index: int = 0
    publication_count: int = 0
    international_publications: int = 0
    indexed_publications: int = 0
    top_publications: list[str] = Field(default_factory=list)
    trend_direction: str = "stable"
    impact_score: float = 0.0
    scientometric_risk: str = "LOW"
    external_identities: list[ExternalResearchIdentity] = Field(default_factory=list)
    trends: list[ScientometricTrend] = Field(default_factory=list)


class ScientometricsSummaryResponse(BaseModel):
    tenant_id: int
    top_researchers: list[ResearcherScientometricProfile] = Field(default_factory=list)
    citation_leaderboard: list[CitationAnalyticsSummary] = Field(default_factory=list)
    h_index_leaderboard: list[CitationAnalyticsSummary] = Field(default_factory=list)
    publication_impact_summary: list[PublicationImpactProfile] = Field(default_factory=list)
    scientometric_trend_summary: list[ScientometricTrend] = Field(default_factory=list)
    provider_execution_enabled: bool = False
    external_calls_enabled: bool = False


class ResearcherRankingItem(BaseModel):
    researcher_id: str
    rank: int
    impact_score: float
    scientometric_risk: str


class ResearcherRankingResponse(BaseModel):
    tenant_id: int
    items: list[ResearcherRankingItem] = Field(default_factory=list)


class ResearchRiskSignal(BaseModel):
    family: str
    owner: str
    dimension: Literal["publication", "grant", "ethics", "scientometric", "execution"]
    source: str
    severity: str = "LOW"
    observed_count: int = 0
    affected_entities: list[str] = Field(default_factory=list)
    description: str
    read_only: bool = True


class ResearchRiskTrend(BaseModel):
    dimension: Literal["publication", "grant", "ethics", "scientometric", "execution"]
    current_score: float = 0.0
    previous_score: float = 0.0
    trend_direction: str = "stable"
    severity: str = "LOW"


class ResearchRiskSummary(BaseModel):
    overall_risk_score: float = 0.0
    severity: str = "LOW"
    publication_risk: float = 0.0
    grant_risk: float = 0.0
    ethics_risk: float = 0.0
    scientometric_risk: float = 0.0
    execution_risk: float = 0.0
    risk_heatmap: dict[str, str] = Field(default_factory=dict)
    top_critical_risks: list[str] = Field(default_factory=list)


class ResearchRiskProfile(BaseModel):
    tenant_id: int
    generated_at: datetime | None = None
    summary: ResearchRiskSummary
    signals: list[ResearchRiskSignal] = Field(default_factory=list)
    trends: list[ResearchRiskTrend] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    provider_execution_enabled: bool = False
    external_calls_enabled: bool = False


class ResearchDashboardKPIs(BaseModel):
    researchers: int = 0
    publications: int = 0
    citations: int = 0
    h_index: int = 0
    international_publications: int = 0
    indexed_publications: int = 0
    grants: int = 0
    ethics_reviews: int = 0
    risk_count: int = 0
    signal_count: int = 0


class ResearchDashboardSignals(BaseModel):
    owner: str = "brain_core"
    signals: list[ResearchRiskSignal] = Field(default_factory=list)
    signal_count: int = 0


class ResearchDashboardRisks(BaseModel):
    owner: str = "brain_core"
    critical_risks: int = 0
    medium_risks: int = 0
    low_risks: int = 0
    trend_direction: str = "stable"
    recommendations: list[str] = Field(default_factory=list)


class ResearchDashboardScientometrics(BaseModel):
    owner: str = "analytics"
    top_researchers: list[ResearcherScientometricProfile] = Field(default_factory=list)
    citation_leaderboard: list[CitationAnalyticsSummary] = Field(default_factory=list)
    h_index_leaderboard: list[CitationAnalyticsSummary] = Field(default_factory=list)
    impact_leaders: list[PublicationImpactProfile] = Field(default_factory=list)
    publication_leaders: list[PublicationImpactProfile] = Field(default_factory=list)


class ResearchDashboardActivity(BaseModel):
    generated_at: datetime | None = None
    publication_activity: int = 0
    grant_activity: int = 0
    ethics_activity: int = 0
    risk_activity: int = 0
    signal_activity: int = 0


class ResearchDashboardSummary(BaseModel):
    tenant_id: int
    generated_at: datetime | None = None
    kpis: ResearchDashboardKPIs
    signals: ResearchDashboardSignals
    risks: ResearchDashboardRisks
    scientometrics: ResearchDashboardScientometrics
    activity: ResearchDashboardActivity
    provider_execution_enabled: bool = False
    external_calls_enabled: bool = False