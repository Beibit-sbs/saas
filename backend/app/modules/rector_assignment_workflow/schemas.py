"""Rector Assignment Workflow — Pydantic Schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------

class AssigneeSpec(BaseModel):
    user_id: int | None = None
    unit_id: int | None = None
    role_on_assignment: str = "RESPONSIBLE"
    notes: str | None = None


class TaskSpec(BaseModel):
    title: str = Field(..., max_length=500)
    description: str | None = None
    assignee_user_id: int | None = None
    assignee_unit_id: int | None = None
    due_date: date | None = None


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class AssignmentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    category: str | None = None
    priority: str = Field(default="NORMAL")
    due_date: date | None = None
    responsible_unit_id: int | None = None
    recurrence_type: str = Field(default="NONE")
    publish_now: bool = False
    assignees: list[AssigneeSpec] = Field(default_factory=list)
    tasks: list[TaskSpec] = Field(default_factory=list)
    template_id: int | None = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = {"LOW", "NORMAL", "HIGH", "CRITICAL"}
        if v not in allowed:
            raise ValueError(f"priority must be one of {allowed}")
        return v

    @field_validator("recurrence_type")
    @classmethod
    def validate_recurrence_type(cls, v: str) -> str:
        allowed = {"NONE", "DAILY", "WEEKLY", "MONTHLY", "CUSTOM"}
        if v not in allowed:
            raise ValueError(f"recurrence_type must be one of {allowed}")
        return v


class AssignmentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    priority: str | None = None
    due_date: date | None = None
    responsible_unit_id: int | None = None
    category: str | None = None
    version: int = Field(..., ge=1)


class AssignmentAssignRequest(BaseModel):
    assignees: list[AssigneeSpec] = Field(..., min_length=1)
    reason: str | None = None


class AssignmentReportCreateRequest(BaseModel):
    reporting_period_start: date
    reporting_period_end: date
    progress_percent: int = Field(..., ge=0, le=100)
    summary: str = Field(..., min_length=1, max_length=10000)
    blockers: str | None = None
    next_steps: str | None = None

    @field_validator("reporting_period_end")
    @classmethod
    def validate_period(cls, v: date, info: Any) -> date:
        start = info.data.get("reporting_period_start")
        if start and v < start:
            raise ValueError("reporting_period_end must be >= reporting_period_start")
        return v


class EvidenceCreateRequest(BaseModel):
    evidence_type: str = Field(...)
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    url: str | None = None
    file_id: int | None = None
    text_content: str | None = None
    report_id: int | None = None

    @field_validator("evidence_type")
    @classmethod
    def validate_evidence_type(cls, v: str) -> str:
        allowed = {"FILE", "LINK", "TEXT", "SYSTEM_REFERENCE"}
        if v not in allowed:
            raise ValueError(f"evidence_type must be one of {allowed}")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is not None and not v.startswith("https://"):
            raise ValueError("url must start with https://")
        return v


class CommentCreateRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)
    visibility: str = Field(default="ASSIGNEES")
    parent_comment_id: int | None = None

    @field_validator("visibility")
    @classmethod
    def validate_visibility(cls, v: str) -> str:
        allowed = {"INTERNAL", "ASSIGNEES", "LEADERSHIP"}
        if v not in allowed:
            raise ValueError(f"visibility must be one of {allowed}")
        return v


class StatusActionRequest(BaseModel):
    reason: str | None = None
    comment: str | None = None


class EscalationRequest(BaseModel):
    reason: str = Field(..., min_length=1)
    escalation_level: int = Field(..., ge=1, le=4)
    escalated_to_role: str = Field(..., min_length=1)
    escalated_to_user_id: int | None = None


class ReportReviewRequest(BaseModel):
    action: str = Field(...)
    comment: str | None = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in {"return", "approve"}:
            raise ValueError("action must be 'return' or 'approve'")
        return v


class AssignmentTemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: str | None = None
    category: str | None = None
    default_priority: str = Field(default="NORMAL")
    default_due_days: int | None = Field(default=None, ge=1)
    default_recurrence_type: str = Field(default="NONE")
    template_body: list[dict] | None = None


class AssignmentTemplateUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=256)
    description: str | None = None
    category: str | None = None
    default_priority: str | None = None
    default_due_days: int | None = None
    default_recurrence_type: str | None = None
    template_body: list[dict] | None = None
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class AssigneeResponse(BaseModel):
    id: int
    user_id: int | None
    unit_id: int | None
    role_on_assignment: str
    status: str
    assigned_at: datetime
    accepted_at: datetime | None

    model_config = {"from_attributes": True}


class TaskResponse(BaseModel):
    id: int
    title: str
    status: str
    assignee_user_id: int | None
    due_date: Any | None

    model_config = {"from_attributes": True}


class AssignmentResponse(BaseModel):
    id: int
    tenant_id: int
    title: str
    description: str | None
    category: str | None
    priority: str
    status: str
    due_date: Any | None
    recurrence_type: str
    originator_user_id: int
    responsible_unit_id: int | None
    is_overdue: bool = False
    version: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None

    model_config = {"from_attributes": True}


class AssignmentDetailResponse(AssignmentResponse):
    tasks: list[TaskResponse] = Field(default_factory=list)
    assignees: list[AssigneeResponse] = Field(default_factory=list)


class AssignmentListResponse(BaseModel):
    items: list[AssignmentResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class AssignmentReportResponse(BaseModel):
    id: int
    assignment_id: int
    submitted_by_user_id: int
    reporting_period_start: Any
    reporting_period_end: Any
    progress_percent: int
    summary: str
    blockers: str | None
    next_steps: str | None
    status: str
    submitted_at: datetime
    reviewed_by_user_id: int | None = None
    reviewed_at: datetime | None = None
    review_comment: str | None = None

    model_config = {"from_attributes": True}


class AssignmentReportListResponse(BaseModel):
    items: list[AssignmentReportResponse]
    total: int


class AssignmentEvidenceResponse(BaseModel):
    id: int
    assignment_id: int
    report_id: int | None
    evidence_type: str
    title: str
    description: str | None
    url: str | None
    file_id: int | None
    uploaded_by_user_id: int
    created_at: datetime
    is_deleted: bool

    model_config = {"from_attributes": True}


class AssignmentEvidenceListResponse(BaseModel):
    items: list[AssignmentEvidenceResponse]
    total: int


class AssignmentCommentResponse(BaseModel):
    id: int
    assignment_id: int
    author_user_id: int
    author_role: str | None
    body: str
    visibility: str
    created_at: datetime
    parent_comment_id: int | None
    is_deleted: bool

    model_config = {"from_attributes": True}


class AssignmentCommentListResponse(BaseModel):
    items: list[AssignmentCommentResponse]
    total: int


class AssignmentAuditEventResponse(BaseModel):
    id: int
    tenant_id: int
    assignment_id: int | None
    event_type: str
    action: str
    actor_user_id: int | None
    actor_role: str | None
    request_id: str | None
    payload_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignmentAuditEventListResponse(BaseModel):
    items: list[AssignmentAuditEventResponse]
    total: int


class AssignmentTemplateResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: str | None
    category: str | None
    default_priority: str
    default_due_days: int | None
    default_recurrence_type: str
    is_active: bool
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssignmentTemplateListResponse(BaseModel):
    items: list[AssignmentTemplateResponse]
    total: int


class UnitCountEntry(BaseModel):
    unit_id: int | None
    count: int
    overdue_count: int


class DashboardSummaryResponse(BaseModel):
    tenant_id: int
    computed_at: datetime
    total_assignments: int
    active_count: int
    draft_count: int
    overdue_count: int
    escalated_count: int
    completed_count: int
    cancelled_count: int
    report_submitted_count: int
    returned_count: int
    due_this_week: int
    due_today: int
    completion_rate_30d: float
    average_days_to_complete: float | None
    by_status: dict[str, int]
    by_priority: dict[str, int]
    by_unit: list[UnitCountEntry]
    top_overdue: list[dict]
    data_source: str = "computed_from_assignments"
    fake_metrics: bool = False
