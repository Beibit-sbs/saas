from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SyllabusStatus = Literal["draft", "under_review", "approved", "published", "archived"]


class SyllabusCreateSchema(BaseModel):
    course_code: str = Field(min_length=1, max_length=32)
    course_title: str = Field(min_length=1, max_length=256)
    department_id: str = Field(min_length=1, max_length=64)
    faculty_id: str = Field(min_length=1, max_length=64)
    term_id: str = Field(min_length=1, max_length=32)
    status: SyllabusStatus = "draft"
    credit_hours: int | None = Field(default=None, ge=1, le=30)


class SyllabusUpdateSchema(BaseModel):
    course_title: str | None = Field(default=None, max_length=256)
    status: SyllabusStatus | None = None
    department_id: str | None = Field(default=None, max_length=64)
    faculty_id: str | None = Field(default=None, max_length=64)
    term_id: str | None = Field(default=None, max_length=32)


class SyllabusSchema(BaseModel):
    id: int
    tenant_id: str | None = None
    course_code: str
    course_title: str
    department_id: str
    faculty_id: str
    term_id: str
    status: str


class SyllabusListResponseSchema(BaseModel):
    items: list[SyllabusSchema]


class SyllabusItemResponseSchema(BaseModel):
    item: SyllabusSchema


class ApprovalWorkflowSchema(BaseModel):
    workflow_id: str
    syllabi_id: str
    current_step: int
    total_steps: int
    status: str
    initiated_at: str
    completed_at: str | None = None
    rejection_reason: str | None = None
    approval_steps: list[dict] = []


class SyllabusDashboardSummarySchema(BaseModel):
    total_syllabi: int
    status_breakdown: dict[str, int]
