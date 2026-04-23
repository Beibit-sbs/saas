"""Phase XII-XII3: Prompt Management schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PromptTemplateCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    description: str | None = Field(default=None, max_length=1000)
    template_text: str = Field(min_length=1, max_length=10_000)
    variables: list[str] = Field(default_factory=list)
    category: Literal["academic", "faculty", "finance", "operations", "general"] = "general"
    is_active: bool = True


class PromptTemplateReadSchema(BaseModel):
    template_id: str
    name: str
    description: str | None
    template_text: str
    variables: list[str]
    category: str
    version: int
    is_active: bool
    created_by: str
    created_at: str


class PromptTemplateUpdateSchema(BaseModel):
    description: str | None = Field(default=None, max_length=1000)
    template_text: str | None = Field(default=None, max_length=10_000)
    variables: list[str] | None = None
    is_active: bool | None = None


class ABTestRouteSchema(BaseModel):
    template_id_a: str
    template_id_b: str
    traffic_split_pct: int = Field(default=50, ge=0, le=100, description="% traffic to variant A")
    context_key: str = Field(min_length=1, max_length=128, description="e.g. user_id for deterministic split")


class ABTestResultSchema(BaseModel):
    selected_template_id: str
    variant: Literal["A", "B"]
    traffic_split_pct: int
    context_key: str
