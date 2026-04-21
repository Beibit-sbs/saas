from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


CareerOpportunityType = Literal["internship", "job", "mentorship", "work_study"]
CareerOpportunityStatus = Literal["open", "in_review", "closed", "archived"]


class CareerOpportunityBaseSchema(BaseModel):
    student_id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=120)
    opportunity_type: CareerOpportunityType = "internship"
    status: CareerOpportunityStatus = "open"
    owner_id: str | None = Field(default=None, max_length=64)
    start_date: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=3000)


class CareerOpportunityCreateSchema(BaseModel):
    student_id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=120)
    opportunity_type: CareerOpportunityType = "internship"
    owner_id: str | None = Field(default=None, max_length=64)
    start_date: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=3000)


class CareerOpportunityStatusUpdateSchema(BaseModel):
    status: CareerOpportunityStatus
    notes: str | None = Field(default=None, max_length=3000)


class CareerOpportunitySchema(CareerOpportunityBaseSchema):
    id: int
    tenant_id: str | None = None


class CareerOpportunityListResponseSchema(BaseModel):
    items: list[CareerOpportunitySchema]


class CareerOpportunityItemResponseSchema(BaseModel):
    item: CareerOpportunitySchema
