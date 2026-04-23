"""Phase XII-XII1: Faculty Copilot schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LessonPlanRequestSchema(BaseModel):
    faculty_id: str = Field(min_length=1, max_length=128)
    course_title: str = Field(min_length=1, max_length=256)
    topic: str = Field(min_length=1, max_length=256)
    student_level: str | None = Field(default=None, max_length=128)
    duration_minutes: int = Field(default=90, ge=15, le=300)
    learning_objectives: list[str] = Field(default_factory=list)


class MaterialPackRequestSchema(BaseModel):
    faculty_id: str = Field(min_length=1, max_length=128)
    course_title: str = Field(min_length=1, max_length=256)
    topic: str = Field(min_length=1, max_length=256)
    material_type: Literal["slides", "worksheet", "quiz", "reading"] = "slides"
    constraints: str | None = Field(default=None, max_length=400)


class FacultyQnARequestSchema(BaseModel):
    faculty_id: str = Field(min_length=1, max_length=128)
    question: str = Field(min_length=1, max_length=2000)
    course_title: str | None = Field(default=None, max_length=256)
