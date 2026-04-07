from __future__ import annotations

from pydantic import BaseModel, Field


class SkillCreateSchema(BaseModel):
    tenant_id: int
    skill_key: str
    name: str
    description: str = ""
    category: str
    level: str | None = None


class SkillReadSchema(BaseModel):
    id: int
    tenant_id: int
    skill_key: str
    name: str
    description: str
    category: str
    level: str | None = None
    created_at: str
    updated_at: str


class CompetencyCreateSchema(BaseModel):
    tenant_id: int
    competency_key: str
    name: str
    description: str = ""


class CompetencyReadSchema(BaseModel):
    id: int
    tenant_id: int
    competency_key: str
    name: str
    description: str
    created_at: str
    updated_at: str


class CourseSkillCreateSchema(BaseModel):
    tenant_id: int
    course_id: str
    skill_id: int
    weight: float = Field(default=1.0, ge=0)


class CourseSkillReadSchema(BaseModel):
    id: int
    tenant_id: int
    course_id: str
    skill_id: int
    skill_key: str
    skill_name: str
    weight: float
    created_at: str
    updated_at: str


class StudentSkillReadSchema(BaseModel):
    id: int
    tenant_id: int
    student_id: str
    skill_id: int
    skill_key: str
    skill_name: str
    proficiency_level: float
    source: str
    last_updated: str
    created_at: str
    updated_at: str
