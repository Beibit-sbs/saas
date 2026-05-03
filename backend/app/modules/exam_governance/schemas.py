from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ExamStatus = Literal["scheduled", "in_progress", "completed", "cancelled"]
ExamType = Literal["midterm", "final", "quiz", "practical"]
ProctoringMode = Literal["in_person", "remote", "hybrid"]


class ExamCreateSchema(BaseModel):
    course_code: str = Field(min_length=1, max_length=32)
    course_title: str = Field(min_length=1, max_length=256)
    faculty_id: str = Field(min_length=1, max_length=64)
    exam_type: ExamType = "midterm"
    term_id: str = Field(min_length=1, max_length=32)
    status: ExamStatus = "scheduled"
    scheduled_date: str | None = Field(default=None, max_length=32)
    scheduled_time: str | None = Field(default=None, max_length=16)
    duration_minutes: int = Field(default=120, ge=1)
    is_proctored: bool = True
    proctoring_mode: ProctoringMode = "in_person"
    location_room: str | None = Field(default=None, max_length=64)


class ExamUpdateSchema(BaseModel):
    course_title: str | None = Field(default=None, max_length=256)
    status: ExamStatus | None = None
    scheduled_date: str | None = Field(default=None, max_length=32)
    scheduled_time: str | None = Field(default=None, max_length=16)
    duration_minutes: int | None = Field(default=None, ge=1)
    is_proctored: bool | None = None
    proctoring_mode: ProctoringMode | None = None


class ExamSchema(BaseModel):
    id: int
    tenant_id: str | None = None
    course_code: str
    course_title: str
    faculty_id: str
    exam_type: str
    term_id: str
    status: str
    scheduled_date: str | None = None
    scheduled_time: str | None = None
    duration_minutes: int
    is_proctored: bool
    proctoring_mode: str


class ExamListResponseSchema(BaseModel):
    items: list[ExamSchema]


class ExamItemResponseSchema(BaseModel):
    item: ExamSchema


class ExamDashboardSummarySchema(BaseModel):
    total_exams: int
    status_breakdown: dict[str, int]
    exam_type_breakdown: dict[str, int]


class ExamStatisticsSchema(BaseModel):
    exam_id: int
    total_registrations: int
    completion_rate: float
    average_score: float | None = None
    pass_rate: float | None = None


class ExamGradeInputSchema(BaseModel):
    average_score: float = Field(ge=0.0, le=100.0)
    pass_rate: float = Field(ge=0.0, le=1.0)


class ExamGradeResponseSchema(BaseModel):
    exam_id: int
    average_score: float
    pass_rate: float
    graded_by: str
    status: str
