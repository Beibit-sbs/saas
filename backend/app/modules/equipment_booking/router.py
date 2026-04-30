"""Phase VII-VII2: Equipment booking router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.equipment_booking.schemas import (
    EquipmentBookingBrainContextResponse,
    EquipmentBookingCreatePayload,
    EquipmentBookingItemResponse,
    EquipmentBookingListResponse,
    EquipmentBookingStatusUpdatePayload,
    EquipmentItemCreatePayload,
    EquipmentItemItemResponse,
    EquipmentItemListResponse,
)
import app.modules.equipment_booking.service as _svc

router = APIRouter(prefix="/api/admin/equipment-booking", tags=["equipment-booking"])


@router.get("/equipment", response_model=EquipmentItemListResponse)
def list_equipment_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    category: str | None = None,
    status: str | None = None,
) -> EquipmentItemListResponse:
    return EquipmentItemListResponse(
        records=_svc.list_equipment(int(tenant["id"]), category=category, status=status)
    )


@router.post("/equipment", response_model=EquipmentItemItemResponse, status_code=201)
def create_equipment_endpoint(
    payload: EquipmentItemCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EquipmentItemItemResponse:
    return EquipmentItemItemResponse(
        record=_svc.create_equipment(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/bookings", response_model=EquipmentBookingListResponse)
def list_equipment_bookings_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    booking_status: str | None = None,
    equipment_code: str | None = None,
) -> EquipmentBookingListResponse:
    return EquipmentBookingListResponse(
        records=_svc.list_equipment_bookings(
            int(tenant["id"]), booking_status=booking_status, equipment_code=equipment_code
        )
    )


@router.post("/bookings", response_model=EquipmentBookingItemResponse, status_code=201)
def create_equipment_booking_endpoint(
    payload: EquipmentBookingCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EquipmentBookingItemResponse:
    try:
        record = _svc.create_equipment_booking(payload.model_dump(), int(tenant["id"]))
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return EquipmentBookingItemResponse(
        record=record
    )


@router.patch("/bookings/{booking_id}/status", response_model=EquipmentBookingItemResponse)
def update_equipment_booking_status_endpoint(
    booking_id: int,
    payload: EquipmentBookingStatusUpdatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EquipmentBookingItemResponse:
    try:
        record = _svc.update_equipment_booking_status(
            booking_id=booking_id,
            status=payload.booking_status,
            tenant_id=int(tenant["id"]),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return EquipmentBookingItemResponse(record=record)


@router.get("/brain-context", response_model=EquipmentBookingBrainContextResponse)
def get_equipment_booking_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EquipmentBookingBrainContextResponse:
    return EquipmentBookingBrainContextResponse.model_validate(
        _svc.get_equipment_booking_brain_context(int(tenant["id"]))
    )
