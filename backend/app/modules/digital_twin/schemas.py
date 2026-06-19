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
