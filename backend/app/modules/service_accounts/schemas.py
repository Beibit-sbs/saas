from __future__ import annotations

from pydantic import BaseModel, Field


class ServiceAccountCreatePayload(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    permissions: list[str] = Field(min_length=1)
    platform_global: bool = False


class ServiceAccountTokenPayload(BaseModel):
    secret: str = Field(min_length=8, max_length=256)


class ServiceAccountCreateResponse(BaseModel):
    account: dict[str, object]
    idempotent_replay: bool
