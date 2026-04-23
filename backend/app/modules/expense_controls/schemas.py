"""Phase V-V2: Expense controls schemas."""
from __future__ import annotations

from pydantic import BaseModel


class ExpenseRecordCreatePayload(BaseModel):
    cost_center_id: int
    category: str
    amount: float
    currency: str = "USD"
    status: str = "pending"
    description: str | None = None
    payroll_ref: str | None = None


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
    name: str
    code: str
    department_id: str | None = None
    budget_limit: float
    currency: str = "USD"
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
