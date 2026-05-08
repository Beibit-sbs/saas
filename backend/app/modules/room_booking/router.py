"""Room booking router (A-018.2 maturity closure)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.room_booking.schemas import (
    BookingRequestPayload,
    GenericRoomBookingListResponse,
    GenericRoomBookingResponse,
    RoomAllocationCheckPayload,
    RoomCreatePayload,
    UtilizationCheckPayload,
)
from app.modules.room_booking import service as room_booking_service

router = APIRouter(prefix="/api/admin/room-booking", tags=["room-booking"])


def _to_http_422(exc: Exception) -> HTTPException:
    return HTTPException(status_code=422, detail=str(exc))


@router.get("/rooms", response_model=GenericRoomBookingListResponse)
def list_rooms_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericRoomBookingListResponse:
    return GenericRoomBookingListResponse(records=room_booking_service.list_rooms(int(tenant["id"])))


@router.post("/rooms", response_model=GenericRoomBookingResponse, status_code=201)
def create_room_endpoint(
    payload: RoomCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericRoomBookingResponse:
    try:
        record = room_booking_service.create_room(int(tenant["id"]), **payload.model_dump())
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericRoomBookingResponse(record=record)


@router.get("/bookings", response_model=GenericRoomBookingListResponse)
def list_bookings_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    room_id: str | None = None,
    status: str | None = None,
    requester_id: str | None = None,
) -> GenericRoomBookingListResponse:
    records = room_booking_service.list_bookings(
        int(tenant["id"]),
        room_id=room_id,
        status=status,
        requester_id=requester_id,
    )
    return GenericRoomBookingListResponse(records=records)


@router.post("/bookings/request", response_model=GenericRoomBookingResponse, status_code=201)
def request_booking_endpoint(
    payload: BookingRequestPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericRoomBookingResponse:
    try:
        record = room_booking_service.request_booking(int(tenant["id"]), **payload.model_dump())
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericRoomBookingResponse(record=record)


@router.post("/bookings/{booking_id}/approve", response_model=GenericRoomBookingResponse)
def approve_booking_endpoint(
    booking_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericRoomBookingResponse:
    try:
        record = room_booking_service.approve_booking(int(tenant["id"]), booking_id=booking_id)
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericRoomBookingResponse(record=record)


@router.post("/bookings/{booking_id}/check-in", response_model=GenericRoomBookingResponse)
def check_in_room_endpoint(
    booking_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericRoomBookingResponse:
    try:
        record = room_booking_service.check_in_room(int(tenant["id"]), booking_id=booking_id)
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericRoomBookingResponse(record=record)


@router.post("/bookings/{booking_id}/release", response_model=GenericRoomBookingResponse)
def release_room_endpoint(
    booking_id: str,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericRoomBookingResponse:
    try:
        record = room_booking_service.release_room(int(tenant["id"]), booking_id=booking_id)
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericRoomBookingResponse(record=record)


@router.post("/utilization/check", response_model=GenericRoomBookingResponse)
def check_utilization_endpoint(
    payload: UtilizationCheckPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericRoomBookingResponse:
    try:
        record = room_booking_service.check_utilization(int(tenant["id"]), **payload.model_dump())
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericRoomBookingResponse(record=record)


@router.post("/allocation/check", response_model=GenericRoomBookingResponse)
def check_room_allocation_endpoint(
    payload: RoomAllocationCheckPayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("scheduling.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> GenericRoomBookingResponse:
    try:
        record = room_booking_service.assess_room_allocation(int(tenant["id"]), **payload.model_dump())
    except ValueError as exc:
        raise _to_http_422(exc) from exc
    return GenericRoomBookingResponse(record=record)
