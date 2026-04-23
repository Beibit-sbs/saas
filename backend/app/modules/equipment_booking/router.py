"""Phase VII-VII2: Equipment booking router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.equipment_booking.schemas import (
    EquipmentBookingBrainContextResponse,
    EquipmentBookingCreatePayload,
    EquipmentBookingItemResponse,
    EquipmentBookingListResponse,
    EquipmentItemCreatePayload,
    EquipmentItemItemResponse,
    EquipmentItemListResponse,
)
from app.modules.equipment_booking.service import (
    create_equipment,
    create_equipment_booking,
    get_equipment_booking_brain_context,
    list_equipment,
    list_equipment_bookings,
)

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
        records=list_equipment(int(tenant["id"]), category=category, status=status)
    )


@router.post("/equipment", response_model=EquipmentItemItemResponse, status_code=201)
def create_equipment_endpoint(
    payload: EquipmentItemCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EquipmentItemItemResponse:
    return EquipmentItemItemResponse(
        record=create_equipment(payload.model_dump(), int(tenant["id"]))
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
        records=list_equipment_bookings(
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
    return EquipmentBookingItemResponse(
        record=create_equipment_booking(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/brain-context", response_model=EquipmentBookingBrainContextResponse)
def get_equipment_booking_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("research.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> EquipmentBookingBrainContextResponse:
    return EquipmentBookingBrainContextResponse.model_validate(
        get_equipment_booking_brain_context(int(tenant["id"]))
    )
