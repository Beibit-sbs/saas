"""Phase X-X2: HR/Payroll router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.modules.hr_payroll.schemas import (
    HrEmployeeCreateSchema,
    HrEmployeeItemResponseSchema,
    HrEmployeeListResponseSchema,
    HrEmployeeStatus,
    HrEmployeeStatusUpdateSchema,
    PayrollCycleCreateSchema,
    PayrollCycleItemResponseSchema,
    PayrollCycleListResponseSchema,
    PayrollCycleStatus,
    PayrollCycleStatusUpdateSchema,
)
from app.modules.hr_payroll.service import (
    create_hr_employee,
    create_payroll_cycle,
    get_hr_employee,
    get_payroll_cycle,
    list_hr_employees,
    list_payroll_cycles,
    update_hr_employee_status,
    update_payroll_cycle_status,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/hr-payroll", tags=["hr-payroll"])


@router.get("/employees", response_model=HrEmployeeListResponseSchema)
def list_hr_employees_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    department_id: str | None = None,
    status: HrEmployeeStatus | None = None,
) -> HrEmployeeListResponseSchema:
    items = list_hr_employees(int(tenant["id"]), department_id=department_id, status=status)
    return HrEmployeeListResponseSchema(items=items)


@router.post("/employees", response_model=HrEmployeeItemResponseSchema)
def create_hr_employee_endpoint(
    payload: HrEmployeeCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> HrEmployeeItemResponseSchema:
    item = create_hr_employee(int(tenant["id"]), payload, actor)
    return HrEmployeeItemResponseSchema(item=item)


@router.get("/employees/{employee_id}", response_model=HrEmployeeItemResponseSchema)
def get_hr_employee_endpoint(
    employee_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> HrEmployeeItemResponseSchema:
    item = get_hr_employee(int(tenant["id"]), employee_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return HrEmployeeItemResponseSchema(item=item)


@router.patch("/employees/{employee_id}/status", response_model=HrEmployeeItemResponseSchema)
def update_hr_employee_status_endpoint(
    employee_id: int,
    payload: HrEmployeeStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> HrEmployeeItemResponseSchema:
    item = update_hr_employee_status(int(tenant["id"]), employee_id, payload, actor)
    if item is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return HrEmployeeItemResponseSchema(item=item)


@router.get("/cycles", response_model=PayrollCycleListResponseSchema)
def list_payroll_cycles_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: PayrollCycleStatus | None = None,
) -> PayrollCycleListResponseSchema:
    items = list_payroll_cycles(int(tenant["id"]), status=status)
    return PayrollCycleListResponseSchema(items=items)


@router.post("/cycles", response_model=PayrollCycleItemResponseSchema)
def create_payroll_cycle_endpoint(
    payload: PayrollCycleCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> PayrollCycleItemResponseSchema:
    item = create_payroll_cycle(int(tenant["id"]), payload, actor)
    return PayrollCycleItemResponseSchema(item=item)


@router.get("/cycles/{cycle_id}", response_model=PayrollCycleItemResponseSchema)
def get_payroll_cycle_endpoint(
    cycle_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> PayrollCycleItemResponseSchema:
    item = get_payroll_cycle(int(tenant["id"]), cycle_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Payroll cycle not found")
    return PayrollCycleItemResponseSchema(item=item)


@router.patch("/cycles/{cycle_id}/status", response_model=PayrollCycleItemResponseSchema)
def update_payroll_cycle_status_endpoint(
    cycle_id: int,
    payload: PayrollCycleStatusUpdateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> PayrollCycleItemResponseSchema:
    item = update_payroll_cycle_status(int(tenant["id"]), cycle_id, payload, actor)
    if item is None:
        raise HTTPException(status_code=404, detail="Payroll cycle not found")
    return PayrollCycleItemResponseSchema(item=item)
