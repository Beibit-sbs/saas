from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.interventions.playbook_models import (
    PlaybookAssigneeRole,
    PlaybookExecutionStatus,
    PlaybookStepActionType,
    PlaybookStepExecutionStatus,
    PlaybookTriggerType,
)


# ---------------------------------------------------------------------------
# App Playbook (template)
# ---------------------------------------------------------------------------


class PlaybookStepCreateSchema(BaseModel):
    step_order: int = Field(ge=0, le=100)
    title: str = Field(min_length=2, max_length=255)
    action_type: PlaybookStepActionType
    rationale: str | None = Field(default=None, max_length=4000)
    is_mandatory: bool = True
    due_days_offset: int = Field(default=3, ge=0, le=365)
    assignee_role: PlaybookAssigneeRole = PlaybookAssigneeRole.ADVISOR
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class PlaybookCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    trigger_threshold_id: int | None = Field(default=None, gt=0)
    enabled: bool = True
    steps: list[PlaybookStepCreateSchema] = Field(default_factory=list)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class PlaybookUpdateSchema(BaseModel):
    expected_version: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=4000)
    trigger_threshold_id: int | None = Field(default=None, gt=0)
    enabled: bool | None = None
    metadata_json: dict[str, Any] | None = None


class PlaybookStepReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    playbook_id: int
    step_order: int
    title: str
    action_type: PlaybookStepActionType
    rationale: str | None
    is_mandatory: bool
    due_days_offset: int
    assignee_role: PlaybookAssigneeRole
    metadata_json: dict[str, Any]


class PlaybookReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    name: str
    description: str | None
    trigger_threshold_id: int | None
    enabled: bool
    version: int
    metadata_json: dict[str, Any]
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime
    steps: list[PlaybookStepReadSchema] = Field(default_factory=list)


class PlaybookListResponseSchema(BaseModel):
    items: list[PlaybookReadSchema]
    total: int


# ---------------------------------------------------------------------------
# Playbook Execution
# ---------------------------------------------------------------------------


class PlaybookExecutionStartSchema(BaseModel):
    playbook_id: int = Field(gt=0)
    case_id: int | None = Field(default=None, gt=0)
    student_profile_id: int | None = Field(default=None, gt=0)
    triggered_by: PlaybookTriggerType = PlaybookTriggerType.MANUAL
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class PlaybookStepExecutionReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_id: int
    step_id: int
    status: PlaybookStepExecutionStatus
    performed_by: str | None
    performed_at: datetime | None
    outcome_note: str | None
    metadata_json: dict[str, Any]


class PlaybookExecutionReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    playbook_id: int
    case_id: int | None
    student_profile_id: int | None
    triggered_by: PlaybookTriggerType
    status: PlaybookExecutionStatus
    started_at: datetime
    completed_at: datetime | None
    abandoned_at: datetime | None
    abandon_reason: str | None
    outcome_delta_score: float | None
    metadata_json: dict[str, Any]
    created_by: str
    created_at: datetime
    updated_at: datetime
    step_executions: list[PlaybookStepExecutionReadSchema] = Field(default_factory=list)


class PlaybookExecutionListResponseSchema(BaseModel):
    items: list[PlaybookExecutionReadSchema]
    total: int


class PlaybookStepCompleteSchema(BaseModel):
    outcome_note: str | None = Field(default=None, max_length=4000)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class PlaybookStepSkipSchema(BaseModel):
    outcome_note: str | None = Field(default=None, max_length=4000)


class PlaybookExecutionAbandonSchema(BaseModel):
    abandon_reason: str = Field(min_length=3, max_length=2000)
