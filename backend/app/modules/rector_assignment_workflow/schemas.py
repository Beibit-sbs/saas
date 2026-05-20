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
    # A-031.5-RUNTIME expansion fields
    overdue_aging_buckets: "OverdueAgingBuckets | None" = None
    completion_trend_by_week: "list[WeeklyTrend]" = Field(default_factory=list)
    report_submission_compliance: float | None = None
    escalation_rate: float | None = None
    average_revision_cycles: float | None = None
    evidence_attachment_rate: float | None = None
    assignments_without_recent_report: int = 0
    unit_completion_table: "list[UnitCompletionEntry]" = Field(default_factory=list)


# ---------------------------------------------------------------------------
# A-031.5-RUNTIME: Dashboard expansion sub-schemas
# ---------------------------------------------------------------------------

class OverdueAgingBuckets(BaseModel):
    days_1_3: int = 0
    days_4_7: int = 0
    days_8_14: int = 0
    days_15_plus: int = 0


class WeeklyTrend(BaseModel):
    week_start: "date"
    completed_count: int = 0
    created_count: int = 0


class UnitCompletionEntry(BaseModel):
    unit_id: int | None = None
    unit_name: str | None = None
    total: int = 0
    completed: int = 0
    overdue: int = 0
    completion_rate: float | None = None


# Trigger model rebuild so forward refs resolve
DashboardSummaryResponse.model_rebuild()


# ---------------------------------------------------------------------------
# A-031.5-RUNTIME: Outbox event schemas
# ---------------------------------------------------------------------------

class RectorAssignmentOutboxEventResponse(BaseModel):
    id: int
    tenant_id: int
    assignment_id: int
    event_type: str
    recipient_user_id: int | None
    recipient_role: str | None
    channel: str
    payload_json: dict
    status: str
    retry_count: int
    next_retry_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RectorAssignmentOutboxEventListResponse(BaseModel):
    items: list[RectorAssignmentOutboxEventResponse]
    total: int


# ---------------------------------------------------------------------------
# A-031.5-RUNTIME: SLA Policy schemas
# ---------------------------------------------------------------------------

class RectorAssignmentSlaPolicyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    priority: str | None = None
    due_days: int = Field(..., ge=1)
    warning_before_hours: int = Field(48, ge=1)
    overdue_after_hours: int = Field(0, ge=0)
    escalation_after_hours: int = Field(72, ge=1)


class RectorAssignmentSlaPolicyUpdateRequest(BaseModel):
    name: str | None = None
    priority: str | None = None
    due_days: int | None = Field(None, ge=1)
    warning_before_hours: int | None = Field(None, ge=1)
    overdue_after_hours: int | None = Field(None, ge=0)
    escalation_after_hours: int | None = Field(None, ge=1)


class RectorAssignmentSlaPolicyResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    priority: str | None
    due_days: int
    warning_before_hours: int
    overdue_after_hours: int
    escalation_after_hours: int
    is_active: bool
    created_by_user_id: int | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None

    model_config = {"from_attributes": True}


class RectorAssignmentSlaPolicyListResponse(BaseModel):
    items: list[RectorAssignmentSlaPolicyResponse]
    total: int


# ---------------------------------------------------------------------------
# A-031.5-RUNTIME: Escalation Policy schemas
# ---------------------------------------------------------------------------

class RectorAssignmentEscalationPolicyCreateRequest(BaseModel):
    assignment_priority: str = Field(..., min_length=1, max_length=20)
    escalation_level: int = Field(..., ge=1, le=4)
    escalate_to_role: str = Field(..., min_length=1, max_length=100)
    escalate_after_hours: int = Field(72, ge=1)
    require_manual_confirmation: bool = True


class RectorAssignmentEscalationPolicyUpdateRequest(BaseModel):
    assignment_priority: str | None = None
    escalation_level: int | None = Field(None, ge=1, le=4)
    escalate_to_role: str | None = None
    escalate_after_hours: int | None = Field(None, ge=1)
    require_manual_confirmation: bool | None = None


class RectorAssignmentEscalationPolicyResponse(BaseModel):
    id: int
    tenant_id: int
    assignment_priority: str
    escalation_level: int
    escalate_to_role: str
    escalate_after_hours: int
    require_manual_confirmation: bool
    is_active: bool
    created_by_user_id: int | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None

    model_config = {"from_attributes": True}


class RectorAssignmentEscalationPolicyListResponse(BaseModel):
    items: list[RectorAssignmentEscalationPolicyResponse]
    total: int
