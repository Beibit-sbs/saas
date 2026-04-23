"""Phase X-X3: Delinquency & Collections schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DelinquencyStatus = Literal["open", "in_review", "escalated", "resolved", "written_off"]
EscalationStage = Literal["stage_1", "stage_2", "stage_3", "legal"]


class DelinquencyRecordCreateSchema(BaseModel):
    student_id: str = Field(min_length=1, max_length=64)
    invoice_code: str = Field(min_length=1, max_length=64)
    amount_due: float = Field(ge=0.01)
    days_overdue: int = Field(ge=1)
    escalation_stage: EscalationStage = "stage_1"
    status: DelinquencyStatus = "open"


class DelinquencyRecordSchema(DelinquencyRecordCreateSchema):
    id: int
    tenant_id: str | None = None


class DelinquencyStatusUpdateSchema(BaseModel):
    status: DelinquencyStatus


class DelinquencyEscalationUpdateSchema(BaseModel):
    escalation_stage: EscalationStage


class DelinquencyItemResponseSchema(BaseModel):
    item: DelinquencyRecordSchema


class DelinquencyListResponseSchema(BaseModel):
    items: list[DelinquencyRecordSchema]
