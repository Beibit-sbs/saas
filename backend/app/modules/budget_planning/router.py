"""Phase V-V1: Budget planning router."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.tenant import get_current_tenant
from app.modules.budget_planning.schemas import (
    BudgetPlanCreatePayload,
    BudgetPlanItemResponse,
    BudgetPlanListResponse,
    BudgetAllocationCreatePayload,
    BudgetAllocationItemResponse,
    BudgetAllocationListResponse,
)
from app.modules.budget_planning.service import (
    create_budget_allocation,
    create_budget_plan,
    get_budget_brain_context,
    list_budget_allocations,
    list_budget_plans,
)
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
    records = list_budget_plans(int(tenant["id"]), department_id=department_id, fiscal_year=fiscal_year)
    return BudgetPlanListResponse(records=records)


@router.post("/plans", response_model=BudgetPlanItemResponse, status_code=201)
def create_budget_plan_endpoint(
    payload: BudgetPlanCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> BudgetPlanItemResponse:
    record = create_budget_plan(payload.model_dump(), int(tenant["id"]))
    return BudgetPlanItemResponse(record=record)


@router.get("/allocations", response_model=BudgetAllocationListResponse)
def list_budget_allocations_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    plan_id: int | None = None,
) -> BudgetAllocationListResponse:
    records = list_budget_allocations(int(tenant["id"]), plan_id=plan_id)
    return BudgetAllocationListResponse(records=records)


@router.post("/allocations", response_model=BudgetAllocationItemResponse, status_code=201)
def create_budget_allocation_endpoint(
    payload: BudgetAllocationCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> BudgetAllocationItemResponse:
    record = create_budget_allocation(payload.model_dump(), int(tenant["id"]))
    return BudgetAllocationItemResponse(record=record)


@router.get("/brain-context")
def get_budget_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("finance.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    return get_budget_brain_context(int(tenant["id"]))
