"""Phase V-V2: Expense controls router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.tenant import get_current_tenant
from app.modules.expense_controls.schemas import (
    ExpenseRecordCreatePayload,
    CostCenterCreatePayload,
)
import app.modules.expense_controls.service as _svc
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/expense-controls", tags=["expense-controls"])


@router.get("/expenses")
def list_expense_records_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    cost_center_id: int | None = None,
    status: str | None = None,
) -> dict:
    records = _svc.list_expense_records(int(tenant["id"]), cost_center_id=cost_center_id, status=status)
    return {"records": records}


@router.post("/expenses", status_code=201)
def create_expense_record_endpoint(
    payload: ExpenseRecordCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    try:
        record = _svc.create_expense_record(payload.model_dump(), int(tenant["id"]))
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"record": record}


@router.get("/cost-centers")
def list_cost_centers_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    active: bool | None = None,
) -> dict:
    records = _svc.list_cost_centers(int(tenant["id"]), active=active)
    return {"records": records}


@router.post("/cost-centers", status_code=201)
def create_cost_center_endpoint(
    payload: CostCenterCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    record = _svc.create_cost_center(payload.model_dump(), int(tenant["id"]))
    return {"record": record}


@router.get("/brain-context")
def get_expense_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    return _svc.get_expense_brain_context(int(tenant["id"]))
