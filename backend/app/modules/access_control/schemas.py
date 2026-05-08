"""Access Control API schemas (A-018.3 maturity closure)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class IssueCardPayload(BaseModel):
    holder_id: str = Field(min_length=1, max_length=128)
    zones: list[str] = Field(min_length=1)


class CardIdPayload(BaseModel):
    card_id: str = Field(min_length=1, max_length=128)


class SuspendCardPayload(BaseModel):
    card_id: str = Field(min_length=1, max_length=128)
    reason: str = Field(default="", max_length=512)


class AttemptAccessPayload(BaseModel):
    card_id: str = Field(min_length=1, max_length=128)
    zone: str = Field(min_length=1, max_length=128)


class GenericAccessControlResponse(BaseModel):
    record: dict


class GenericAccessControlListResponse(BaseModel):
    records: list[dict]
