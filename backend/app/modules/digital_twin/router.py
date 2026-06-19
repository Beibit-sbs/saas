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
    return service.simulate_capacity(_tenant_id(tenant), payload)


@router.post("/early-warning/capacity", response_model=schemas.CapacityEarlyWarningResponse)
def digital_twin_capacity_early_warning(
    payload: schemas.CapacityWhatIfRequest,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency(permissions.SIMULATE_RUN))],
    tenant: Annotated[dict[str, object], Depends(get_current_tenant)],
) -> schemas.CapacityEarlyWarningResponse:
    # Read-only warning readout; recommends human action, executes nothing.
    return service.capacity_early_warning(_tenant_id(tenant), payload)
