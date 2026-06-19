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


def _live_enrollment_count(tenant_id: int) -> int | None:
    """Best-effort tenant-scoped enrollment count from the enrollments module.

    Returns None on any failure so the caller can fall back honestly (no fabrication).
    """
    try:
        from app.modules.enrollments import service as enrollments_service

        rows = enrollments_service.list_enrollments(tenant_id)
        return len(rows) if isinstance(rows, list) else None
    except Exception:
        return None


def simulate_capacity(tenant_id: Any, request: schemas.CapacityWhatIfRequest) -> schemas.CapacityWhatIfResponse:
    """Deterministic capacity what-if. No fabricated values; missing inputs -> incomplete_data.

    A-056.4: when use_live_sources is set, current_students is read live from the
    enrollments module (best-effort); on failure it falls back to the caller value.
    """
    tid = _validate_tenant(tenant_id)

    current_students = request.current_students
    students_mode = "caller_provided"
    live_sources_used: list[str] = []
    if request.use_live_sources:
        live = _live_enrollment_count(tid)
        if live is not None:
            current_students = live
            students_mode = "live"
            live_sources_used.append("enrollments")

    projected = round(current_students * (1 + request.intake_growth_percent / 100))
    incomplete = False

    classroom_util: float | None = None
    if request.classroom_capacity > 0:
        classroom_util = round(projected / request.classroom_capacity, 4)
    else:
        incomplete = True

    housing_need = round(projected * request.housing_demand_ratio)
    dorm_pressure: float | None = None
    if request.dormitory_capacity > 0:
        dorm_pressure = round(housing_need / request.dormitory_capacity, 4)
    elif request.housing_demand_ratio > 0:
        incomplete = True

    risks: list[str] = []
    if classroom_util is not None and classroom_util > 1.0:
        risks.append("classroom_capacity_exceeded")
    if dorm_pressure is not None and dorm_pressure > 1.0:
        risks.append("dormitory_capacity_exceeded")

    evidence = [
        schemas.CapacityWhatIfEvidence(field="current_students", value=float(current_students), source_module="enrollments", mode=students_mode),
        schemas.CapacityWhatIfEvidence(field="classroom_capacity", value=float(request.classroom_capacity), source_module="scheduling", mode="caller_provided"),
        schemas.CapacityWhatIfEvidence(field="dormitory_capacity", value=float(request.dormitory_capacity), source_module="dormitory_management", mode="caller_provided"),
    ]

    return schemas.CapacityWhatIfResponse(
        tenant_id=tid,
        projected_students=projected,
        classroom_utilization=classroom_util,
        dormitory_pressure=dorm_pressure,
        risks=risks,
        evidence=evidence,
        live_sources_used=live_sources_used,
        incomplete_data=incomplete,
    )


def _severity(metric: float) -> str | None:
    if metric > 1.2:
        return "high"
    if metric > 1.0:
        return "medium"
    return None


def capacity_early_warning(tenant_id: Any, request: schemas.CapacityWhatIfRequest) -> schemas.CapacityEarlyWarningResponse:
    """Read-only early-warning readout over the capacity projection.

    Produces human-gated warnings with recommended (NOT executed) actions. Does
    not fabricate signal data: signal registries are declared as candidate
    sources to be live-wired later, not as live counts.
    """
    projection = simulate_capacity(tenant_id, request)
    warnings: list[schemas.EarlyWarningItem] = []

    if projection.classroom_utilization is not None:
        sev = _severity(projection.classroom_utilization)
        if sev:
            warnings.append(
                schemas.EarlyWarningItem(
                    signal="classroom_capacity_risk",
                    severity=sev,
                    metric=projection.classroom_utilization,
                    threshold=1.0,
                    recommended_human_action="escalate_to_scheduling_and_facilities",
                )
            )

    if projection.dormitory_pressure is not None:
        sev = _severity(projection.dormitory_pressure)
        if sev:
            warnings.append(
                schemas.EarlyWarningItem(
                    signal="dormitory_capacity_risk",
                    severity=sev,
                    metric=projection.dormitory_pressure,
                    threshold=1.0,
                    recommended_human_action="escalate_to_housing_office",
                )
            )

    return schemas.CapacityEarlyWarningResponse(
        tenant_id=projection.tenant_id,
        projection=projection,
        warnings=warnings,
        candidate_signal_sources=list(SOURCE_SIGNAL_REGISTRIES),
        incomplete_data=projection.incomplete_data,
    )
