from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AidType = Literal["scholarship", "grant", "tuition_discount", "stipend"]
AidStatus = Literal["pending", "approved", "disbursed", "rejected"]


class FinancialAidRecordBaseSchema(BaseModel):
    student_id: int = Field(ge=1)
    aid_type: AidType = "scholarship"
    amount: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    status: AidStatus = "pending"
    term: str = Field(min_length=1, max_length=32)
    reviewer_id: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=3000)


class FinancialAidRecordCreateSchema(BaseModel):
    student_id: int = Field(ge=1)
    aid_type: AidType = "scholarship"
    amount: float = Field(gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    term: str = Field(min_length=1, max_length=32)
    reviewer_id: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=3000)


class FinancialAidRecordStatusUpdateSchema(BaseModel):
    status: AidStatus
    notes: str | None = Field(default=None, max_length=3000)


class FinancialAidRecordSchema(FinancialAidRecordBaseSchema):
    id: int
    tenant_id: str | None = None


class FinancialAidRecordListResponseSchema(BaseModel):
    items: list[FinancialAidRecordSchema]


class FinancialAidRecordItemResponseSchema(BaseModel):
    item: FinancialAidRecordSchema
