from pydantic import BaseModel, Field


class TimetableChangeKpiDashboardVisibilitySchema(BaseModel):
    tenant_id: int | None = Field(default=None)
    module: str
    visibility_level: str = Field(default="L4")
    operational_status: str
    classification: str
    allowed_actions: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    safety_flags: dict[str, bool | str] = Field(default_factory=dict)
    evidence_notes: list[str] = Field(default_factory=list)
    no_autonomous_execution: bool = True
    readonly: bool = True
    tenant_scoped: bool = True


class KpiDashboardL5ReadinessSchema(BaseModel):
    tenant_id: int
    module: str
    readiness_level: str = Field(default="L5_READY")
    evidence_lineage_status: str
    evidence_sources: list[str] = Field(default_factory=list)
    evidence_completeness: str
    governance_mapping_status: str
    governance_category: str
    human_review_owner: str
    escalation_boundary: str
    allowed_governance_actions: list[str] = Field(default_factory=list)
    forbidden_autonomous_actions: list[str] = Field(default_factory=list)
    kpi_readiness_status: str
    brain_readiness_boundary: str
    human_review_required: bool = True
    confidence_status: str
    rationale_notes: str
    audit_evidence_notes: list[str] = Field(default_factory=list)
    safety_flags: dict[str, bool] = Field(default_factory=dict)
    no_autonomous_execution: bool = True
    no_l6_claim: bool = True
    tenant_scoped: bool = True
