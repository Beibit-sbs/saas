"""Phase V-V1: Budget planning schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class BudgetPlanCreatePayload(BaseModel):
    department_id: str = Field(min_length=1, max_length=64)
    fiscal_year: int = Field(ge=2000, le=2100)
    total_amount: float = Field(ge=0.0)
    currency: str = Field(default="USD", min_length=1, max_length=8)
    status: str = Field(default="draft", min_length=1, max_length=32)
    description: str | None = Field(default=None, max_length=2000)


class BudgetPlanResponse(BudgetPlanCreatePayload):
    id: int
    tenant_id: str | None = None


class BudgetPlanItemResponse(BaseModel):
    record: BudgetPlanResponse


class BudgetPlanListResponse(BaseModel):
    records: list[BudgetPlanResponse]


class BudgetAllocationCreatePayload(BaseModel):
    plan_id: int
    category: str = Field(min_length=1, max_length=64)
    allocated_amount: float = Field(ge=0.0)
    spent_amount: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="USD", min_length=1, max_length=8)
    notes: str | None = Field(default=None, max_length=2000)


class BudgetAllocationResponse(BudgetAllocationCreatePayload):
    id: int
    tenant_id: str | None = None


class BudgetAllocationItemResponse(BaseModel):
    record: BudgetAllocationResponse


class BudgetAllocationListResponse(BaseModel):
    records: list[BudgetAllocationResponse]
