"""Phase X-X2: HR/Payroll schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


HrEmployeeStatus = Literal["active", "on_leave", "terminated", "onboarding", "offboarding"]
PayrollCycleStatus = Literal["pending", "processing", "completed", "failed"]


class HrEmployeeCreateSchema(BaseModel):
    employee_code: str = Field(min_length=1, max_length=64)
    full_name: str = Field(min_length=1, max_length=200)
    department_id: str = Field(min_length=1, max_length=64)
    role_title: str = Field(min_length=1, max_length=120)
    status: HrEmployeeStatus = "active"


class HrEmployeeSchema(HrEmployeeCreateSchema):
    id: int
    tenant_id: str | None = None


class HrEmployeeStatusUpdateSchema(BaseModel):
    status: HrEmployeeStatus


class HrEmployeeItemResponseSchema(BaseModel):
    item: HrEmployeeSchema


class HrEmployeeListResponseSchema(BaseModel):
    items: list[HrEmployeeSchema]


class PayrollCycleCreateSchema(BaseModel):
    cycle_code: str = Field(min_length=1, max_length=64)
    period_label: str = Field(min_length=1, max_length=64)
    total_gross: float = Field(default=0.0, ge=0.0)
    total_net: float = Field(default=0.0, ge=0.0)
    employee_count: int = Field(default=1, ge=1)
    status: PayrollCycleStatus = "pending"


class PayrollCycleSchema(PayrollCycleCreateSchema):
    id: int
    tenant_id: str | None = None


class PayrollCycleStatusUpdateSchema(BaseModel):
    status: PayrollCycleStatus


class PayrollCycleItemResponseSchema(BaseModel):
    item: PayrollCycleSchema


class PayrollCycleListResponseSchema(BaseModel):
    items: list[PayrollCycleSchema]
