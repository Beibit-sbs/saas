"""Read-only metadata contracts for the Digital Twin shell (A-056.1).

No fabricated metrics. The shell declares WHICH existing sources the twin
observes and the safety boundaries it operates under; it does not compute or
expose simulated numbers yet.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DigitalTwinSafetyFlags(BaseModel):
    no_autonomous_budget_commitment: bool = True
    no_autonomous_academic_decision: bool = True
    no_autonomous_disciplinary_decision: bool = True
    no_hidden_scoring: bool = True
    no_supplier_order_without_human_approval: bool = True
    all_recommendations_explain_evidence: bool = True
    all_accepted_actions_audited: bool = True
    fake_metrics: bool = False
    provider_live_enabled: bool = False


class DigitalTwinStateResponse(BaseModel):
    tenant_id: int
    module: str = "digital_twin"
    runtime_mode: str = "METADATA_OBSERVATION_SIMULATION_HUMAN_REVIEW_ONLY"
    incomplete_data: bool = True
    # Dimensions the twin observes — sourced from existing modules, not duplicated.
    observed_dimensions: list[str] = Field(default_factory=list)
    # Existing signal registries the twin consumes (reuse, no duplication).
    source_signal_registries: list[str] = Field(default_factory=list)
    # Existing capacity/resource sources the twin reads.
    source_capacity_modules: list[str] = Field(default_factory=list)
    operating_principle: str = (
        "Brain sees. Digital twin simulates. Workflow proposes. Human approves. Audit records."
    )
    safety_flags: DigitalTwinSafetyFlags = Field(default_factory=DigitalTwinSafetyFlags)


class DigitalTwinSafetyResponse(BaseModel):
    tenant_id: int
    module: str = "digital_twin"
    runtime_mode: str = "METADATA_OBSERVATION_SIMULATION_HUMAN_REVIEW_ONLY"
    forbidden_actions: list[str] = Field(default_factory=list)
    safety_flags: DigitalTwinSafetyFlags = Field(default_factory=DigitalTwinSafetyFlags)


class CapacityWhatIfRequest(BaseModel):
    """Caller-provided baselines (each tagged to a source module in the response).

    Deterministic projection only; no value is fabricated. Until A-056.4 wires
    these to live enrollments/scheduling reads, inputs are caller-provided and
    the response marks incomplete_data accordingly.
    """

    current_students: int = Field(ge=0)
    # Plain float (no ge/le) so inf/nan are accepted into the model and validated in the
    # service -> clean 400, instead of a pydantic 422 whose body echoes inf and then fails
    # to serialize (Starlette json.dumps(allow_nan=False)).
    intake_growth_percent: float
    classroom_capacity: int = Field(default=0, ge=0)
    dormitory_capacity: int = Field(default=0, ge=0)
    housing_demand_ratio: float = 0.0
    # A-056.4: best-effort live read of current_students from the enrollments module.
    use_live_sources: bool = False


class CapacityWhatIfEvidence(BaseModel):
    field: str
    value: float
    source_module: str
    mode: str = "caller_provided"  # "live" when read from a source, else "caller_provided"


class CapacityWhatIfResponse(BaseModel):
    tenant_id: int
    module: str = "digital_twin"
    runtime_mode: str = "METADATA_OBSERVATION_SIMULATION_HUMAN_REVIEW_ONLY"
    scenario: str = "intake_growth"
    projected_students: int
    classroom_utilization: float | None = None
    dormitory_pressure: float | None = None
    risks: list[str] = Field(default_factory=list)
    evidence: list[CapacityWhatIfEvidence] = Field(default_factory=list)
    live_sources_used: list[str] = Field(default_factory=list)
    incomplete_data: bool = False
    human_review_required: bool = True
    safety_flags: DigitalTwinSafetyFlags = Field(default_factory=DigitalTwinSafetyFlags)


class EarlyWarningItem(BaseModel):
    signal: str
    severity: str  # "high" | "medium"
    metric: float
    threshold: float
    recommended_human_action: str
    requires_human_approval: bool = True
    no_autonomous_action: bool = True


class CapacityEarlyWarningResponse(BaseModel):
    tenant_id: int
    module: str = "digital_twin"
    runtime_mode: str = "METADATA_OBSERVATION_SIMULATION_HUMAN_REVIEW_ONLY"
    projection: CapacityWhatIfResponse
    warnings: list[EarlyWarningItem] = Field(default_factory=list)
    # Signal registries that would enrich warnings once live-instance wiring exists.
    candidate_signal_sources: list[str] = Field(default_factory=list)
    incomplete_data: bool = False
    human_review_required: bool = True
    safety_flags: DigitalTwinSafetyFlags = Field(default_factory=DigitalTwinSafetyFlags)


class CapacityScenarioRequest(BaseModel):
    """Run several named intake-growth scenarios at once for executive review."""

    current_students: int = Field(ge=0)
    classroom_capacity: int = Field(default=0, ge=0)
    dormitory_capacity: int = Field(default=0, ge=0)
    housing_demand_ratio: float = Field(default=0.0, ge=0, le=1)
    use_live_sources: bool = False
    # Plain list[float]; non-finite/out-of-range elements are validated in the service -> 400.
    intake_growth_scenarios: list[float] = Field(default_factory=lambda: [0.0, 10.0, 20.0, 30.0])


class CapacityScenarioItem(BaseModel):
    name: str
    intake_growth_percent: float
    projection: CapacityWhatIfResponse
    warnings: list[EarlyWarningItem] = Field(default_factory=list)


class CapacityScenarioRegistryResponse(BaseModel):
    tenant_id: int
    module: str = "digital_twin"
    runtime_mode: str = "METADATA_OBSERVATION_SIMULATION_HUMAN_REVIEW_ONLY"
    scenarios: list[CapacityScenarioItem] = Field(default_factory=list)
    incomplete_data: bool = False
    human_review_required: bool = True
    safety_flags: DigitalTwinSafetyFlags = Field(default_factory=DigitalTwinSafetyFlags)


class ScenarioDecisionRequest(BaseModel):
    """A human reviewer's decision on a what-if scenario. Recorded for audit only;
    the twin executes nothing as a result."""

    scenario_name: str
    decision: str = Field(pattern="^(accepted|rejected|deferred)$")
    rationale: str
    intake_growth_percent: float | None = None


class ScenarioDecisionResponse(BaseModel):
    tenant_id: int
    module: str = "digital_twin"
    recorded: bool = True
    audit_action: str = "digital_twin.scenario_decision_recorded"
    correlation_id: str
    scenario_name: str
    decision: str
    reviewer: str
    no_autonomous_execution: bool = True
    human_review_required: bool = True
    safety_flags: DigitalTwinSafetyFlags = Field(default_factory=DigitalTwinSafetyFlags)


class ScenarioDecisionLogItem(BaseModel):
    correlation_id: str | None = None
    reviewer: str | None = None
    scenario_name: str | None = None
    decision: str | None = None
    rationale: str | None = None
    timestamp: str | None = None


class ScenarioDecisionLogResponse(BaseModel):
    tenant_id: int
    module: str = "digital_twin"
    count: int = 0
    decisions: list[ScenarioDecisionLogItem] = Field(default_factory=list)
    no_autonomous_execution: bool = True
    safety_flags: DigitalTwinSafetyFlags = Field(default_factory=DigitalTwinSafetyFlags)


# --- A-056.10: resource-consumption what-if (supplies / utilities) ---

class ResourceWhatIfRequest(BaseModel):
    """Project days-of-stock remaining for a consumable / utility resource.

    daily_consumption is a plain float (no constraint) so inf/nan are validated in
    the service -> clean 400 (never a 500 or an inf-in-422 serialisation failure)."""

    resource_name: str
    current_stock: float = Field(ge=0)
    daily_consumption: float  # validated finite & >= 0 in the service
    lead_time_days: int = Field(default=0, ge=0)
    safety_buffer_days: int = Field(default=0, ge=0)


class ResourceWhatIfResponse(BaseModel):
    tenant_id: int
    module: str = "digital_twin"
    runtime_mode: str = "METADATA_OBSERVATION_SIMULATION_HUMAN_REVIEW_ONLY"
    resource_name: str
    projected_days_remaining: float | None = None
    reorder_needed: bool = False
    risks: list[str] = Field(default_factory=list)
    evidence: list[CapacityWhatIfEvidence] = Field(default_factory=list)
    incomplete_data: bool = False
    human_review_required: bool = True
    safety_flags: DigitalTwinSafetyFlags = Field(default_factory=DigitalTwinSafetyFlags)


class ResourceEarlyWarningResponse(BaseModel):
    tenant_id: int
    module: str = "digital_twin"
    runtime_mode: str = "METADATA_OBSERVATION_SIMULATION_HUMAN_REVIEW_ONLY"
    projection: ResourceWhatIfResponse
    warnings: list[EarlyWarningItem] = Field(default_factory=list)
    candidate_signal_sources: list[str] = Field(default_factory=list)
    incomplete_data: bool = False
    human_review_required: bool = True
    safety_flags: DigitalTwinSafetyFlags = Field(default_factory=DigitalTwinSafetyFlags)
