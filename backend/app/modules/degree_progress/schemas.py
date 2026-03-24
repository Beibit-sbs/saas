from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class RequirementStatusSchema(BaseModel):
    requirement_item_id: int
    course_id: int
    required: bool
    credits: int
    completed: bool


class DegreeProgressSchema(BaseModel):
    student_profile_id: int
    program_id: int
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
