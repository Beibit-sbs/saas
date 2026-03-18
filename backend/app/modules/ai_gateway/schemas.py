from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AIModelUpsertPayload(BaseModel):
    provider: Literal["openai", "gemini", "anthropic", "custom"]
    provider_model_id: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=200)
    enabled: bool = True
    priority: int = Field(default=100, ge=0, le=10_000)
    metadata: dict[str, Any] | None = None


class AIModelEnabledPayload(BaseModel):
    enabled: bool


class AIChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=16_000)


class AIChatRequestPayload(BaseModel):
    model: str = Field(min_length=1, max_length=120)
    messages: list[AIChatMessage] = Field(min_length=1, max_length=100)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=16_384)
