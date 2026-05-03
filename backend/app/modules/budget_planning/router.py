"""Phase V-V1: Budget planning router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.tenant import get_current_tenant
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.budget_planning.schemas import (
    BudgetPlanCreatePayload,
    BudgetPlanItemResponse,
    BudgetPlanListResponse,
    BudgetPlanStatusUpdatePayload,
    BudgetAllocationCreatePayload,
    BudgetAllocationItemResponse,
    BudgetAllocationListResponse,
)
import app.modules.budget_planning.service as _svc
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/budget-planning", tags=["budget-planning"])


@router.get("/plans", response_model=BudgetPlanListResponse)
def list_budget_plans_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    department_id: str | None = None,
    fiscal_year: int | None = None,
) -> BudgetPlanListResponse:
    records = _svc.list_budget_plans(int(tenant["id"]), department_id=department_id, fiscal_year=fiscal_year)
    return BudgetPlanListResponse(records=records)


@router.post("/plans", response_model=BudgetPlanItemResponse, status_code=201)
def create_budget_plan_endpoint(
    payload: BudgetPlanCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> BudgetPlanItemResponse:
    try:
        record = _svc.create_budget_plan(payload.model_dump(), int(tenant["id"]), actor=_)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return BudgetPlanItemResponse(record=record)


@router.patch("/plans/{plan_id}/status", response_model=BudgetPlanItemResponse)
def update_budget_plan_status_endpoint(
    plan_id: int,
    payload: BudgetPlanStatusUpdatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> BudgetPlanItemResponse:
    try:
        record = _svc.update_budget_plan_status(int(tenant["id"]), plan_id, payload.status, actor=_)
    except DomainValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="Budget plan not found")
    return BudgetPlanItemResponse(record=record)


@router.get("/allocations", response_model=BudgetAllocationListResponse)
def list_budget_allocations_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    plan_id: int | None = None,
) -> BudgetAllocationListResponse:
    records = _svc.list_budget_allocations(int(tenant["id"]), plan_id=plan_id)
    return BudgetAllocationListResponse(records=records)


@router.post("/allocations", response_model=BudgetAllocationItemResponse, status_code=201)
def create_budget_allocation_endpoint(
    payload: BudgetAllocationCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> BudgetAllocationItemResponse:
    try:
        record = _svc.create_budget_allocation(payload.model_dump(), int(tenant["id"]), actor=_)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return BudgetAllocationItemResponse(record=record)


@router.get("/brain-context")
def get_budget_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    return _svc.get_budget_brain_context(int(tenant["id"]))
