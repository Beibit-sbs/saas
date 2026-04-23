"""Phase X-X1: Faculty performance KPI schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


FacultyKpiStatus = Literal["satisfactory", "needs_improvement", "on_probation"]


class FacultyKpiCreateSchema(BaseModel):
    faculty_id: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=200)
    department_id: str = Field(min_length=1, max_length=64)
    kpi_period: str = Field(min_length=1, max_length=32)
    teaching_score: float = Field(default=0.0, ge=0.0, le=100.0)
    research_score: float = Field(default=0.0, ge=0.0, le=100.0)
    service_score: float = Field(default=0.0, ge=0.0, le=100.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)
    status: FacultyKpiStatus = "satisfactory"


class FacultyKpiSchema(FacultyKpiCreateSchema):
    id: int
    tenant_id: str | None = None


class FacultyKpiStatusUpdateSchema(BaseModel):
    status: FacultyKpiStatus


class FacultyKpiItemResponseSchema(BaseModel):
    item: FacultyKpiSchema


class FacultyKpiListResponseSchema(BaseModel):
    items: list[FacultyKpiSchema]
