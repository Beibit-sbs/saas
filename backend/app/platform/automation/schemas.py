from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AutomationRuleCreateSchema(BaseModel):
    tenant_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    event_type: str = Field(min_length=3, max_length=128)
    condition_json: dict[str, Any] = Field(default_factory=dict)
    actions_json: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True


class AutomationRuleReadSchema(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str
    event_type: str
    condition_json: dict[str, Any]
    actions_json: list[dict[str, Any]]
    is_active: bool
    created_at: str
    updated_at: str
    version: int


class AutomationExecutionReadSchema(BaseModel):
    id: int
    tenant_id: int
    rule_id: int
    event_id: int
    status: str
    result_json: dict[str, Any]
    error_message: str | None
    executed_at: str
    created_at: str
