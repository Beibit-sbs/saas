"""Digital Twin router (A-056.1) — read-only, tenant fail-closed, permission-guarded."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.digital_twin import permissions, schemas, service
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/digital-twin", tags=["digital_twin"])


def _tenant_id(tenant: dict[str, object]) -> int:
    try:
        return service._validate_tenant(tenant.get("id"))
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=400, detail="invalid_tenant_scope")


def _guard(fn):
    """Map service input-validation errors (e.g. non-finite growth) to a clean 400."""
    try:
        return fn()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/state", response_model=schemas.DigitalTwinStateResponse)
def get_digital_twin_state(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency(permissions.STATE_READ))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> schemas.DigitalTwinStateResponse:
    return service.get_state(_tenant_id(tenant))


@router.get("/safety-boundaries", response_model=schemas.DigitalTwinSafetyResponse)
def get_digital_twin_safety_boundaries(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency(permissions.SAFETY_READ))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> schemas.DigitalTwinSafetyResponse:
    return service.get_safety_boundaries(_tenant_id(tenant))


@router.post("/simulate/capacity", response_model=schemas.CapacityWhatIfResponse)
def simulate_digital_twin_capacity(
    payload: schemas.CapacityWhatIfRequest,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency(permissions.SIMULATE_RUN))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> schemas.CapacityWhatIfResponse:
    # Read-only deterministic projection; persists nothing, executes nothing.
    tid = _tenant_id(tenant)
    return _guard(lambda: service.simulate_capacity(tid, payload))


@router.post("/early-warning/capacity", response_model=schemas.CapacityEarlyWarningResponse)
def digital_twin_capacity_early_warning(
    payload: schemas.CapacityWhatIfRequest,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency(permissions.SIMULATE_RUN))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> schemas.CapacityEarlyWarningResponse:
    # Read-only warning readout; recommends human action, executes nothing.
    tid = _tenant_id(tenant)
    return _guard(lambda: service.capacity_early_warning(tid, payload))


@router.post("/scenarios/capacity", response_model=schemas.CapacityScenarioRegistryResponse)
def digital_twin_capacity_scenarios(
    payload: schemas.CapacityScenarioRequest,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency(permissions.SIMULATE_RUN))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> schemas.CapacityScenarioRegistryResponse:
    # Read-only named-scenario comparison for executive review; executes nothing.
    tid = _tenant_id(tenant)
    return _guard(lambda: service.run_capacity_scenarios(tid, payload))


@router.post("/simulate/resource", response_model=schemas.ResourceWhatIfResponse)
def simulate_digital_twin_resource(
    payload: schemas.ResourceWhatIfRequest,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency(permissions.SIMULATE_RUN))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> schemas.ResourceWhatIfResponse:
    # Read-only deterministic resource projection; persists nothing, executes nothing.
    tid = _tenant_id(tenant)
    return _guard(lambda: service.simulate_resource(tid, payload))


@router.post("/early-warning/resource", response_model=schemas.ResourceEarlyWarningResponse)
def digital_twin_resource_early_warning(
    payload: schemas.ResourceWhatIfRequest,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency(permissions.SIMULATE_RUN))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> schemas.ResourceEarlyWarningResponse:
    # Read-only resource shortage warning; recommends human action, executes nothing.
    tid = _tenant_id(tenant)
    return _guard(lambda: service.resource_early_warning(tid, payload))


@router.post("/scenarios/decision", response_model=schemas.ScenarioDecisionResponse)
def digital_twin_record_scenario_decision(
    payload: schemas.ScenarioDecisionRequest,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency(permissions.DECISION_RECORD))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> schemas.ScenarioDecisionResponse:
    # Records the human decision to the audit trail; executes nothing.
    return service.record_scenario_decision(_tenant_id(tenant), actor, payload)


@router.get("/scenarios/decisions", response_model=schemas.ScenarioDecisionLogResponse)
def list_digital_twin_scenario_decisions(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency(permissions.DECISION_READ))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> schemas.ScenarioDecisionLogResponse:
    # Read-only executive decision log from the audit trail.
    return service.list_scenario_decisions(_tenant_id(tenant))
