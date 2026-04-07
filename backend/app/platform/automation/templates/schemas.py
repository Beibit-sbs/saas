"""Automation Templates - API Schemas."""

from pydantic import BaseModel, Field
from typing import Any


class AutomationTemplateReadSchema(BaseModel):
    """Schema for reading automation templates from API."""

    id: str
    template_key: str
    title: str
    description: str
    category: str
    event_type: str
    condition_json: dict[str, Any]
    actions_json: list[dict[str, Any]]
    is_system_template: bool
    created_at: str
    updated_at: str
    version: int


class InstantiateTemplateSchema(BaseModel):
    """Schema for requesting template instantiation."""

    rule_name: str | None = Field(None, description="Optional custom rule name (uses template title if not provided)")
    rule_description: str | None = Field(None, description="Optional custom rule description (uses template description if not provided)")
