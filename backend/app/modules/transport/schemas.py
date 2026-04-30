"""Phase VI-VI2: Transport schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TransportRouteCreatePayload(BaseModel):
    route_code: str = Field(min_length=1, max_length=64)
    route_name: str = Field(min_length=1, max_length=128)
    status: str = Field(default="active", min_length=1, max_length=32)
    vehicle_type: str | None = Field(default=None, max_length=64)
    departure_time: str | None = Field(default=None, max_length=64)
    arrival_time: str | None = Field(default=None, max_length=64)
    capacity: int | None = Field(default=None, ge=0)
    assigned_driver: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=512)


class TransportRouteResponse(TransportRouteCreatePayload):
    id: int
    tenant_id: int


class TransportRouteItemResponse(BaseModel):
    record: TransportRouteResponse


class TransportRouteListResponse(BaseModel):
    records: list[TransportRouteResponse]


class TransportBookingCreatePayload(BaseModel):
    route_code: str = Field(min_length=1, max_length=64)
    student_id: str = Field(min_length=1, max_length=64)
    booking_status: str = Field(default="confirmed", min_length=1, max_length=32)
    seat_number: str | None = Field(default=None, max_length=16)
    journey_date: str | None = Field(default=None, max_length=32)


class TransportBookingResponse(TransportBookingCreatePayload):
    id: int
    tenant_id: int


class TransportBookingItemResponse(BaseModel):
    record: TransportBookingResponse


class TransportBookingListResponse(BaseModel):
    records: list[TransportBookingResponse]


class TransportBrainContextResponse(BaseModel):
    module: str
    tenant_id: int
    total_routes: int
    active_routes: int
    disrupted_routes: int
    cancelled_routes: int
    total_bookings: int
    risk_level: str
