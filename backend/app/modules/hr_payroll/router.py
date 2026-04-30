"""Phase X-X2: HR/Payroll router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
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
import app.modules.hr_payroll.service as _svc
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
    items = _svc.list_hr_employees(int(tenant["id"]), department_id=department_id, status=status)
    return HrEmployeeListResponseSchema(items=items)


@router.post("/employees", response_model=HrEmployeeItemResponseSchema)
def create_hr_employee_endpoint(
    payload: HrEmployeeCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> HrEmployeeItemResponseSchema:
    try:
        item = _svc.create_hr_employee(int(tenant["id"]), payload, actor)
        return HrEmployeeItemResponseSchema(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/employees/{employee_id}", response_model=HrEmployeeItemResponseSchema)
def get_hr_employee_endpoint(
    employee_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> HrEmployeeItemResponseSchema:
    item = _svc.get_hr_employee(int(tenant["id"]), employee_id)
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
    try:
        item = _svc.update_hr_employee_status(int(tenant["id"]), employee_id, payload, actor)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return HrEmployeeItemResponseSchema(item=item)


@router.get("/cycles", response_model=PayrollCycleListResponseSchema)
def list_payroll_cycles_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    status: PayrollCycleStatus | None = None,
) -> PayrollCycleListResponseSchema:
    items = _svc.list_payroll_cycles(int(tenant["id"]), status=status)
    return PayrollCycleListResponseSchema(items=items)


@router.post("/cycles", response_model=PayrollCycleItemResponseSchema)
def create_payroll_cycle_endpoint(
    payload: PayrollCycleCreateSchema,
    actor: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> PayrollCycleItemResponseSchema:
    try:
        item = _svc.create_payroll_cycle(int(tenant["id"]), payload, actor)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PayrollCycleItemResponseSchema(item=item)


@router.get("/cycles/{cycle_id}", response_model=PayrollCycleItemResponseSchema)
def get_payroll_cycle_endpoint(
    cycle_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("hr.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> PayrollCycleItemResponseSchema:
    item = _svc.get_payroll_cycle(int(tenant["id"]), cycle_id)
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
    try:
        item = _svc.update_payroll_cycle_status(int(tenant["id"]), cycle_id, payload, actor)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="Payroll cycle not found")
    return PayrollCycleItemResponseSchema(item=item)
