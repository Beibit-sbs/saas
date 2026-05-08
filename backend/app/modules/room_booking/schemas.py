"""Room booking API schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class RoomCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    capacity: int = Field(ge=1)
    location: str | None = Field(default="", max_length=256)


class BookingRequestPayload(BaseModel):
    room_id: str = Field(min_length=1, max_length=128)
    requester_id: str = Field(min_length=1, max_length=128)
    start_time: str = Field(min_length=1, max_length=64)
    end_time: str = Field(min_length=1, max_length=64)
    required_capacity: int | None = Field(default=None, ge=1)
    purpose: str | None = Field(default="", max_length=512)


class BookingIdPayload(BaseModel):
    booking_id: str = Field(min_length=1, max_length=128)


class UtilizationCheckPayload(BaseModel):
    room_id: str = Field(min_length=1, max_length=128)
    total_slots: int = Field(ge=1)
    occupied_slots: int = Field(ge=0)


class RoomAllocationCheckPayload(BaseModel):
    room_id: str = Field(min_length=1, max_length=128)
    required_capacity: int = Field(ge=1)


class RoomItemResponse(BaseModel):
    room_id: str
    name: str
    capacity: int


class BookingItemResponse(BaseModel):
    booking_id: str
    room_id: str
    status: str


class GenericRoomBookingResponse(BaseModel):
    record: dict


class GenericRoomBookingListResponse(BaseModel):
    records: list[dict]
