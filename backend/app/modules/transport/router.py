"""Phase VI-VI2: Transport router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.transport.schemas import (
    TransportBookingCreatePayload,
    TransportBookingItemResponse,
    TransportBookingListResponse,
    TransportBrainContextResponse,
    TransportRouteCreatePayload,
    TransportRouteItemResponse,
    TransportRouteListResponse,
)
from app.modules.transport.service import (
    create_transport_booking,
    create_transport_route,
    get_transport_brain_context,
    list_transport_bookings,
    list_transport_routes,
)

router = APIRouter(prefix="/api/admin/transport", tags=["transport"])


@router.get("/routes", response_model=TransportRouteListResponse)
def list_routes_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: str | None = None,
) -> TransportRouteListResponse:
    return TransportRouteListResponse(
        records=list_transport_routes(int(tenant["id"]), status=status)
    )


@router.post("/routes", response_model=TransportRouteItemResponse, status_code=201)
def create_route_endpoint(
    payload: TransportRouteCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> TransportRouteItemResponse:
    return TransportRouteItemResponse(
        record=create_transport_route(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/bookings", response_model=TransportBookingListResponse)
def list_bookings_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    booking_status: str | None = None,
) -> TransportBookingListResponse:
    return TransportBookingListResponse(
        records=list_transport_bookings(int(tenant["id"]), booking_status=booking_status)
    )


@router.post("/bookings", response_model=TransportBookingItemResponse, status_code=201)
def create_booking_endpoint(
    payload: TransportBookingCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> TransportBookingItemResponse:
    return TransportBookingItemResponse(
        record=create_transport_booking(payload.model_dump(), int(tenant["id"]))
    )


@router.get("/brain-context", response_model=TransportBrainContextResponse)
def brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("operations.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> TransportBrainContextResponse:
    return TransportBrainContextResponse(**get_transport_brain_context(int(tenant["id"])))
