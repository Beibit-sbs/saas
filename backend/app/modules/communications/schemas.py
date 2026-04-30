"""Phase VIII-1: Communications module schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class CommunicationMessageCreatePayload(BaseModel):
    message_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=256)
    message_type: str = Field(min_length=1, max_length=64)
    target_audience: str = Field(min_length=1, max_length=128)
    status: str = Field(default="draft", min_length=1, max_length=32)
    recipients_count: int = Field(default=0, ge=0)
    delivered_count: int = Field(default=0, ge=0)
    opened_count: int = Field(default=0, ge=0)
    integration_source: str | None = Field(default=None, max_length=64)
    channel: str | None = Field(default=None, max_length=32)
    reviewer_notes: str | None = Field(default=None, max_length=500)


class CommunicationMessageResponse(CommunicationMessageCreatePayload):
    id: int
    tenant_id: int


class CommunicationMessageItemResponse(BaseModel):
    record: CommunicationMessageResponse


class CommunicationMessageListResponse(BaseModel):
    records: list[CommunicationMessageResponse]


class CommunicationsBrainContextResponse(BaseModel):
    module: str
    tenant_id: int
    total_messages: int
    sent_messages: int
    delivery_rate: float
    open_rate: float
    delivery_health: str
