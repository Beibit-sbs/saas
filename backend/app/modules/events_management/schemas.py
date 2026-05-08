"""Events Management API schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class EventCreatePayload(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    category_id: str = Field(min_length=1, max_length=128)
    organizer_id: str = Field(min_length=1, max_length=128)
    capacity: int = Field(ge=1)
    start_time: str = Field(min_length=1, max_length=64)
    end_time: str = Field(min_length=1, max_length=64)


class ParticipantRegistrationPayload(BaseModel):
    student_id: str = Field(min_length=1, max_length=128)


class GenericEventsManagementResponse(BaseModel):
    record: dict


class GenericEventsManagementListResponse(BaseModel):
    records: list[dict]