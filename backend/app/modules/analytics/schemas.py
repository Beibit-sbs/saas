from __future__ import annotations

from pydantic import BaseModel


class TenantAnalyticsKpiTrendPointReadSchema(BaseModel):
    snapshot_date: str
    value: int


class TenantAnalyticsKpiLineageReadSchema(BaseModel):
    source_type: str
    source_event_types: list[str]
    derived_from: str


class TenantAnalyticsKpiSourceBreakdownItemReadSchema(BaseModel):
    event_type: str
    count: int


class TenantAnalyticsKpiCardReadSchema(BaseModel):
    key: str
    title: str
    description: str
    value: int
    lineage: TenantAnalyticsKpiLineageReadSchema | None = None
    readiness_status: str | None = None
    source_status: str | None = None
    source_breakdown: list[TenantAnalyticsKpiSourceBreakdownItemReadSchema] | None = None
    severity: str | None = None
    threshold_basis: str | None = None
    policy_pack: str | None = None
    actionability_state: str | None = None
    trend: list[TenantAnalyticsKpiTrendPointReadSchema] | None = None


class TenantAnalyticsKpiSeverityCountsReadSchema(BaseModel):
    normal: int
    warning: int
    critical: int
    no_data: int


class TenantAnalyticsKpiActionabilityCountsReadSchema(BaseModel):
    no_action: int
    observe: int
    review: int
    act_now: int


class TenantAnalyticsKpiPortfolioSummaryReadSchema(BaseModel):
    total_kpis: int
    severity_counts: TenantAnalyticsKpiSeverityCountsReadSchema
    actionability_counts: TenantAnalyticsKpiActionabilityCountsReadSchema
    overall_portfolio_status: str


class TenantAnalyticsKpiChangeCountsReadSchema(BaseModel):
    improved: int
    declined: int
    unchanged: int
    no_data: int


class TenantAnalyticsKpiChangeDigestReadSchema(BaseModel):
    total_kpis: int
    change_counts: TenantAnalyticsKpiChangeCountsReadSchema
    overall_change_direction: str


class TenantAnalyticsKpiSourceMixCountsReadSchema(BaseModel):
    derived_from_events: int
    derived_from_usage: int
    derived_from_snapshot: int
    mixed_source: int
    empty: int


class TenantAnalyticsKpiSourceMixSummaryReadSchema(BaseModel):
    total_kpis: int
    source_mix_counts: TenantAnalyticsKpiSourceMixCountsReadSchema
    dominant_source_mode: str


class TenantAnalyticsKpiCapabilitiesReadSchema(BaseModel):
    supports_cards: bool
    supports_trends: bool
    supports_insights: bool
    supports_recommendations: bool
    supports_refresh: bool
    supports_refresh_history: bool
    supports_change_digest: bool
    supports_source_mix: bool
    supports_lineage: bool
    supports_source_breakdown: bool
    supports_thresholds: bool
    supports_actionability: bool


class TenantAnalyticsKpiSurfaceProfileReadSchema(BaseModel):
    audience_profiles: list[str]
    primary_audience: str
    consumption_mode: str


class TenantAnalyticsKpiFieldSemanticsReadSchema(BaseModel):
    capabilities: str
    sections: str
    contract_invariants: str
    contract_fingerprint: str
    surface_profile: str
    response_status: str
    request_id: str
    served_at: str


class TenantAnalyticsKpiCardFieldSemanticsReadSchema(BaseModel):
    severity: str
    threshold_basis: str
    policy_pack: str
    actionability_state: str
    source_status: str


class TenantAnalyticsKpiResponseExampleShapeReadSchema(BaseModel):
    readiness_status: str
    cards: str
    summary: str
    change_digest: str
    source_mix_summary: str
    capabilities: str
    sections: str


class TenantAnalyticsKpiResponseExamplesReadSchema(BaseModel):
    empty_shape: TenantAnalyticsKpiResponseExampleShapeReadSchema
    ready_shape: TenantAnalyticsKpiResponseExampleShapeReadSchema


class TenantAnalyticsKpiSurfaceMapEndpointReadSchema(BaseModel):
    name: str
    path: str
    role: str


class TenantAnalyticsKpiSurfaceMapReadSchema(BaseModel):
    family_id: str
    endpoints: list[TenantAnalyticsKpiSurfaceMapEndpointReadSchema]


class TenantAnalyticsKpiWorkflowHintsReadSchema(BaseModel):
    primary_flow: list[str]
    operational_flow: list[str]
    observability_flow: list[str]


class TenantAnalyticsKpiStabilityTiersReadSchema(BaseModel):
    stable_core_fields: list[str]
    extensible_metadata_blocks: list[str]
    data_dependent_blocks: list[str]
    stable_card_core_fields: list[str]
    optional_card_fields: list[str]


class TenantAnalyticsKpiContractFingerprintReadSchema(BaseModel):
    algorithm: str
    value: str
    fingerprint_basis: str


class TenantAnalyticsKpiContractCompatibilityReadSchema(BaseModel):
    compatibility_mode: str
    backward_compatible_with: list[str]
    stable_core_enforced: bool
    additive_metadata_extensions_allowed: bool
    data_dependent_blocks_may_vary: bool
    fingerprint_scope: str


class TenantAnalyticsKpiSectionsReadSchema(BaseModel):
    cards: str
    summary: str
    change_digest: str
    source_mix_summary: str
    capabilities: str
    contract_identity: str
    surface_profile: str
    field_semantics: str
    card_field_semantics: str
    response_examples: str
    surface_map: str
    workflow_hints: str
    stability_tiers: str
    contract_fingerprint: str
    contract_compatibility: str
    contract_invariants: str


class TenantAnalyticsKpiContractInvariantsReadSchema(BaseModel):
    guaranteed_top_level_fields: list[str]
    always_present_sections: list[str]
    optional_card_fields: list[str]
    empty_state_contract_stable: bool


class TenantAnalyticsKpiListReadSchema(BaseModel):
    surface_id: str | None = None
    contract_version: str | None = None
    capabilities: TenantAnalyticsKpiCapabilitiesReadSchema | None = None
    sections: TenantAnalyticsKpiSectionsReadSchema | None = None
    surface_profile: TenantAnalyticsKpiSurfaceProfileReadSchema | None = None
    field_semantics: TenantAnalyticsKpiFieldSemanticsReadSchema | None = None
    card_field_semantics: TenantAnalyticsKpiCardFieldSemanticsReadSchema | None = None
    response_examples: TenantAnalyticsKpiResponseExamplesReadSchema | None = None
    surface_map: TenantAnalyticsKpiSurfaceMapReadSchema | None = None
    workflow_hints: TenantAnalyticsKpiWorkflowHintsReadSchema | None = None
    stability_tiers: TenantAnalyticsKpiStabilityTiersReadSchema | None = None
    contract_fingerprint: TenantAnalyticsKpiContractFingerprintReadSchema | None = None
    contract_compatibility: TenantAnalyticsKpiContractCompatibilityReadSchema | None = None
    contract_invariants: TenantAnalyticsKpiContractInvariantsReadSchema | None = None
    request_id: str | None = None
    served_at: str | None = None
    response_status: str | None = None
    tenant_id: int
    snapshot_date: str | None = None
    generated_at: str | None = None
    readiness_status: str | None = None
    freshness_status: str | None = None
    source_mode: str | None = None
    kpis: list[TenantAnalyticsKpiCardReadSchema]
    summary: TenantAnalyticsKpiPortfolioSummaryReadSchema | None = None
    change_digest: TenantAnalyticsKpiChangeDigestReadSchema | None = None
    source_mix_summary: TenantAnalyticsKpiSourceMixSummaryReadSchema | None = None


class TenantAnalyticsKpiRefreshReadSchema(BaseModel):
    tenant_id: int
    refresh_executed: bool
    snapshot_date: str | None = None
    generated_at: str | None = None
    readiness_status: str | None = None
    freshness_status: str | None = None
    source_mode: str | None = None
    kpi_count: int


class TenantAnalyticsKpiRefreshHistoryItemReadSchema(BaseModel):
    event_id: int
    created_at: str
    status: str
    kpi_count: int
    snapshot_date: str | None = None
    generated_at: str | None = None


class TenantAnalyticsKpiRefreshHistoryReadSchema(BaseModel):
    tenant_id: int
    limit: int
    last_refresh_at: str | None = None
    last_refresh_status: str | None = None
    last_refresh_kpi_count: int | None = None
    recent_refreshes: list[TenantAnalyticsKpiRefreshHistoryItemReadSchema]


class TenantAnalyticsKpiTrendSeriesPointReadSchema(BaseModel):
    date: str
    value: int


class TenantAnalyticsKpiTrendSeriesReadSchema(BaseModel):
    key: str
    title: str
    description: str
    latest_value: int
    previous_value: int | None = None
    delta: int | None = None
    points: list[TenantAnalyticsKpiTrendSeriesPointReadSchema]


class TenantAnalyticsKpiTrendListReadSchema(BaseModel):
    tenant_id: int
    window_days: int
    snapshot_date: str | None = None
    generated_at: str | None = None
    trends: list[TenantAnalyticsKpiTrendSeriesReadSchema]


class TenantAnalyticsKpiInsightReadSchema(BaseModel):
    key: str
    title: str
    type: str
    summary: str
    value: int
    delta: int | None = None


class TenantAnalyticsKpiInsightListReadSchema(BaseModel):
    tenant_id: int
    window_days: int
    snapshot_date: str | None = None
    generated_at: str | None = None
    insights: list[TenantAnalyticsKpiInsightReadSchema]


class TenantAnalyticsKpiRecommendationReadSchema(BaseModel):
    key: str
    title: str
    type: str
    priority: str
    summary: str
    based_on: str


class TenantAnalyticsKpiRecommendationListReadSchema(BaseModel):
    tenant_id: int
    window_days: int
    snapshot_date: str | None = None
    generated_at: str | None = None
    recommendations: list[TenantAnalyticsKpiRecommendationReadSchema]


# ---------------------------------------------------------------------------
# Platform event projection / read layer v1
# ---------------------------------------------------------------------------

class PlatformEventItemSchema(BaseModel):
    id: int
    event_type: str
    created_at: str
    payload: dict


class PlatformEventListSchema(BaseModel):
    tenant_id: int
    items: list[PlatformEventItemSchema]
    count: int


class PlatformEventSummarySchema(BaseModel):
    tenant_id: int
    counts_by_type: dict[str, int]
    total: int
