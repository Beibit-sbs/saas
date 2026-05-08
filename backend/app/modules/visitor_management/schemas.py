"""A-018.6: Visitor Management schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class VisitorRegisterPayload(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    host_id: str = Field(min_length=1, max_length=64)
    purpose: str = Field(default="", max_length=256)
    visit_date: str = Field(min_length=1, max_length=32)


class VisitorRegisterResponse(BaseModel):
    visit_id: str
    status: str


class VisitActionResponse(BaseModel):
    visit_id: str
    status: str


class VisitActionWithBadgeResponse(BaseModel):
    visit_id: str
    status: str
    badge: str


class VisitRejectPayload(BaseModel):
    reason: str = Field(default="", max_length=256)


class VisitCancelPayload(BaseModel):
    reason: str = Field(default="", max_length=256)


class VisitCheckInPayload(BaseModel):
    badge_number: str = Field(min_length=1, max_length=64)


class UnauthorizedAttemptPayload(BaseModel):
    visitor_name: str = Field(min_length=1, max_length=128)
    zone: str = Field(min_length=1, max_length=64)
    access_point_id: str | None = Field(default=None, max_length=64)
    reason: str | None = Field(default=None, max_length=256)


class UnauthorizedAttemptResponse(BaseModel):
    log_id: str
    event: str


class VisitListResponse(BaseModel):
    records: list[dict]
