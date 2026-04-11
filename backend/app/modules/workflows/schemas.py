from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowStartRequestSchema(BaseModel):
    workflow_key: str = Field(..., min_length=1, max_length=128)
    entity_type: str = Field(..., min_length=1, max_length=128)
    entity_id: int = Field(..., gt=0)
    workflow_version_no: int | None = Field(None, ge=1)
    metadata_json: dict = Field(default_factory=dict)


class WorkflowTaskCompleteRequestSchema(BaseModel):
    expected_task_version: int = Field(..., ge=1)
    transition_action: str = Field("complete", min_length=1, max_length=64)
    reason: str | None = Field(None, max_length=2000)


class WorkflowTaskAssignRequestSchema(BaseModel):
    assignee_type: str = Field(..., min_length=1, max_length=64)
    assignee_ref: str = Field(..., min_length=1, max_length=255)
    expected_version: int = Field(..., ge=1)


class WorkflowTaskCommentRequestSchema(BaseModel):
    body: str = Field(..., min_length=1, max_length=10000)
    comment_type: str = Field("note", min_length=1, max_length=64)
    visibility: str = Field("internal", min_length=1, max_length=64)
    attachments_json: list = Field(default_factory=list)
    metadata_json: dict = Field(default_factory=dict)


class WorkflowInstanceReadSchema(BaseModel):
    id: int
    tenant_id: int
    workflow_definition_id: int
    workflow_definition_version_id: int
    entity_type: str
    entity_id: int
    status: str
    current_step_id: int | None
    initiated_by: str
    started_at: datetime
    due_at: datetime | None
    completed_at: datetime | None
    priority: int
    metadata_json: dict
    version: int
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowTaskReadSchema(BaseModel):
    id: int
    tenant_id: int
    workflow_instance_id: int
    workflow_step_id: int | None
    task_type: str
    status: str
    assignee_type: str
    assignee_ref: str
    title: str
    instructions: str | None
    due_at: datetime | None
    sequence_no: int
    is_blocking: bool
    claimed_at: datetime | None
    completed_at: datetime | None
    metadata_json: dict
    version: int
    created_by: str
    created_at: datetime
    updated_by: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowTaskCommentReadSchema(BaseModel):
    id: int
    tenant_id: int
    workflow_task_id: int
    comment_type: str
    visibility: str
    body: str
    attachments_json: list
    metadata_json: dict
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowInstanceListResponseSchema(BaseModel):
    total: int = Field(..., ge=0)
    items: list[WorkflowInstanceReadSchema]


class WorkflowTaskListResponseSchema(BaseModel):
    total: int = Field(..., ge=0)
    items: list[WorkflowTaskReadSchema]


class WorkflowConsistencyIssueSchema(BaseModel):
    issue_type: str
    workflow_instance_id: int | None = None
    workflow_task_id: int | None = None
    comment_id: int | None = None
    reference_id: int | None = None
    detail: str


class WorkflowConsistencyReportSchema(BaseModel):
    definition_count: int = Field(..., ge=0)
    definition_version_count: int = Field(..., ge=0)
    step_count: int = Field(..., ge=0)
    instance_count: int = Field(..., ge=0)
    task_count: int = Field(..., ge=0)
    comment_count: int = Field(..., ge=0)
    issue_count: int = Field(..., ge=0)
    issues: list[WorkflowConsistencyIssueSchema] = Field(default_factory=list)
