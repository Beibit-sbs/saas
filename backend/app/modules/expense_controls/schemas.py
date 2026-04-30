"""Phase V-V2: Expense controls schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ExpenseRecordCreatePayload(BaseModel):
    cost_center_id: int = Field(gt=0)
    category: str = Field(min_length=1, max_length=64)
    amount: float = Field(gt=0.0)
    currency: str = Field(default="USD", min_length=1, max_length=8)
    status: str = Field(default="pending", min_length=1, max_length=32)
    description: str | None = Field(default=None, max_length=2000)
    payroll_ref: str | None = Field(default=None, max_length=128)
    approval_required: bool | None = Field(default=None)
    reviewer_notes: str | None = Field(default=None, max_length=500)


class ExpenseRecordResponse(BaseModel):
    id: int
    cost_center_id: int
    category: str
    amount: float
    currency: str
    status: str
    description: str | None
    payroll_ref: str | None
    tenant_id: int


class ExpenseRecordItemResponse(BaseModel):
    record: ExpenseRecordResponse


class ExpenseRecordListResponse(BaseModel):
    records: list[ExpenseRecordResponse]


class CostCenterCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=1, max_length=64)
    department_id: str | None = Field(default=None, max_length=64)
    budget_limit: float = Field(ge=0.0)
    currency: str = Field(default="USD", min_length=1, max_length=8)
    active: bool = True


class CostCenterResponse(BaseModel):
    id: int
    name: str
    code: str
    department_id: str | None
    budget_limit: float
    currency: str
    active: bool
    tenant_id: int


class CostCenterItemResponse(BaseModel):
    record: CostCenterResponse


class CostCenterListResponse(BaseModel):
    records: list[CostCenterResponse]


class ExpenseBrainContextResponse(BaseModel):
    tenant_id: int
    total_expenses: int
    total_cost_centers: int
    pending_expenses: int
    approved_expenses: int
    budget_exceeded_alerts: int
    risk_level: str
