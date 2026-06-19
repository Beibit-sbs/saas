"""Digital Twin shell service (A-056.1).

Declares observed dimensions + reused sources. No fabricated simulation numbers.
"""

from __future__ import annotations

from typing import Any

from app.modules.digital_twin import schemas

# Existing signal registries the twin consumes (reuse — do not duplicate).
SOURCE_SIGNAL_REGISTRIES = [
    "student_risk_signal_registry",
    "finance_anomaly_signal_registry",
    "academic_quality_signal_registry",
    "procurement_risk_signal_registry",
    "curriculum_gap_signal_registry",
]

# Existing capacity/resource modules the twin reads (reuse — do not duplicate).
SOURCE_CAPACITY_MODULES = [
    "enrollments",
    "scheduling",
    "room_booking",
    "asset_inventory",
    "dormitory_management",
    "dining",
]

OBSERVED_DIMENSIONS = [
    "student_population",
    "staff_population",
    "rooms_and_buildings",
    "schedules",
    "budgets",
    "inventory",
    "service_workload",
    "security_events",
]

FORBIDDEN_ACTIONS = [
    "autonomous_budget_commitment",
    "autonomous_academic_decision",
    "autonomous_disciplinary_decision",
    "hidden_scoring",
    "supplier_order_without_human_approval",
    "any_execution_without_human_approval",
]


def _validate_tenant(tenant_id: Any) -> int:
    if isinstance(tenant_id, bool) or not isinstance(tenant_id, int) or tenant_id <= 0:
        raise ValueError("invalid_tenant_scope")
    return tenant_id


def get_state(tenant_id: Any) -> schemas.DigitalTwinStateResponse:
    tid = _validate_tenant(tenant_id)
    return schemas.DigitalTwinStateResponse(
        tenant_id=tid,
        observed_dimensions=list(OBSERVED_DIMENSIONS),
        source_signal_registries=list(SOURCE_SIGNAL_REGISTRIES),
        source_capacity_modules=list(SOURCE_CAPACITY_MODULES),
    )


def get_safety_boundaries(tenant_id: Any) -> schemas.DigitalTwinSafetyResponse:
    tid = _validate_tenant(tenant_id)
    return schemas.DigitalTwinSafetyResponse(
        tenant_id=tid,
        forbidden_actions=list(FORBIDDEN_ACTIONS),
    )
