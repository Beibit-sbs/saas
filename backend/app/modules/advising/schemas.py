from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


AdvisingSessionType = Literal["academic", "career", "personal", "mentoring"]

AdvisingSessionStatus = Literal["scheduled", "completed", "cancelled", "no_show"]


class AdvisingSessionBaseSchema(BaseModel):
    student_id: int = Field(ge=1)
    advisor_id: str = Field(min_length=1, max_length=64)
    session_type: AdvisingSessionType = "academic"
    status: AdvisingSessionStatus = "scheduled"
    scheduled_at: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)
    outcome: str | None = Field(default=None, max_length=1000)


class AdvisingSessionCreateSchema(BaseModel):
    student_id: int = Field(ge=1)
    advisor_id: str = Field(min_length=1, max_length=64)
    session_type: AdvisingSessionType = "academic"
    scheduled_at: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)
    meeting_link: str | None = Field(default=None, max_length=256)
    reviewer_notes: str | None = Field(default=None, max_length=500)


class AdvisingSessionStatusUpdateSchema(BaseModel):
    status: AdvisingSessionStatus
    outcome: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_outcome_for_closed_statuses(self) -> "AdvisingSessionStatusUpdateSchema":
        # Closing statuses must carry explicit outcome text for traceability.
        if self.status in {"completed", "cancelled", "no_show"} and not (self.outcome or "").strip():
            raise ValueError("outcome is required when closing an advising session")
        return self


class AdvisingSessionSchema(AdvisingSessionBaseSchema):
    id: int
    tenant_id: str | None = None


class AdvisingSessionListResponseSchema(BaseModel):
    items: list[AdvisingSessionSchema]


class AdvisingSessionItemResponseSchema(BaseModel):
    item: AdvisingSessionSchema
