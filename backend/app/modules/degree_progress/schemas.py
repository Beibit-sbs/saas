from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProgramRequirementItemCreateSchema(BaseModel):
    course_id: int = Field(gt=0)
    credits: int = Field(ge=0)
    required: bool = True


class ProgramRequirementCreateSchema(BaseModel):
    program_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=255)
    minimum_credits: int = Field(ge=0)
    minimum_gpa: Decimal = Field(default=Decimal("0"), ge=0)
    is_active: bool = True
    items: list[ProgramRequirementItemCreateSchema] = Field(min_length=1)


class ProgramRequirementItemReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    requirement_id: int
    course_id: int
    required: bool
    credits: int


class ProgramRequirementReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tenant_id: int
    program_id: int
    name: str
    minimum_credits: int
    minimum_gpa: Decimal
    is_active: bool
    items: list[ProgramRequirementItemReadSchema]


class ProgramRequirementListResponseSchema(BaseModel):
    total: int
    items: list[ProgramRequirementReadSchema]


class RequirementStatusSchema(BaseModel):
    requirement_item_id: int
    course_id: int
    course_name: str | None = None
    required: bool
    credits: int
    completed: bool


class DegreeProgressSchema(BaseModel):
    student_profile_id: int
    program_id: int
    program_name: str | None = None
    requirement_id: int
    requirement_name: str
    credits_earned: int
    minimum_credits: int
    gpa: Decimal | None
    minimum_gpa: Decimal
    completed_requirements: list[RequirementStatusSchema]
    remaining_requirements: list[RequirementStatusSchema]
    graduation_eligible: bool


class GraduationEligibilitySchema(BaseModel):
    student_profile_id: int
    eligible: bool
    credits_earned: int
    minimum_credits: int
    gpa: Decimal | None
    minimum_gpa: Decimal
    remaining_required_items: int


class DegreeProgressConsistencyIssueSchema(BaseModel):
    issue_type: str
    student_profile_id: int | None = None
    program_id: int | None = None
    requirement_id: int | None = None
    active_requirement_count: int | None = None


class DegreeProgressConsistencyReportSchema(BaseModel):
    active_primary_binding_count: int
    active_requirement_count: int
    requirement_item_count: int
    issue_count: int
    issues: list[DegreeProgressConsistencyIssueSchema]
