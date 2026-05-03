"""Phase LXXVI — Plans Management Router.

Endpoints:
  GET    /api/billing/plans              — list plans (optional ?include_inactive=true)
  POST   /api/billing/plans              — create plan
  GET    /api/billing/plans/stats        — stats summary (total/active/inactive)
  GET    /api/billing/plans/{plan_id}    — get plan by ID
  PATCH  /api/billing/plans/{plan_id}    — update plan
  DELETE /api/billing/plans/{plan_id}    — deactivate plan (soft delete)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Response

from app.modules.plans.schemas import (
    PlanCreatePayload,
    PlanItemResponse,
    PlanListResponse,
    PlanResponse,
    PlanUpdatePayload,
)
from app.modules.plans.service import (
    clear_plans_state,
    create_plan,
    get_plan_by_id,
    list_plans,
    update_plan,
)

router = APIRouter(prefix="/api/billing/plans", tags=["billing-plans"])

MODULE = "app.modules.plans.router"


# ─── GET /api/billing/plans ───────────────────────────────────────────────────


@router.get("", response_model=PlanListResponse)
def list_all_plans(
    include_inactive: bool = Query(default=False),
) -> PlanListResponse:
    """List all plans. Pass include_inactive=true to include inactive plans."""
    rows = list_plans(include_inactive=include_inactive)
    return PlanListResponse(plans=[PlanResponse(**r) for r in rows])


# ─── POST /api/billing/plans ──────────────────────────────────────────────────


@router.post("", response_model=PlanItemResponse, status_code=201)
def create_new_plan(payload: PlanCreatePayload) -> PlanItemResponse:
    """Create a new billing plan."""
    try:
        row = create_plan(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PlanItemResponse(plan=PlanResponse(**row))


# ─── GET /api/billing/plans/stats ─────────────────────────────────────────────


@router.get("/stats", response_model=dict)
def get_plans_stats() -> dict:
    """Return aggregate stats: total, active, inactive plan counts."""
    all_rows = list_plans(include_inactive=True)
    active_count = sum(1 for r in all_rows if bool(r.get("active")))
    inactive_count = len(all_rows) - active_count
    return {
        "total": len(all_rows),
        "active": active_count,
        "inactive": inactive_count,
    }


# ─── GET /api/billing/plans/{plan_id} ────────────────────────────────────────


@router.get("/{plan_id}", response_model=PlanItemResponse)
def get_plan(plan_id: int) -> PlanItemResponse:
    """Get a single plan by ID."""
    if plan_id <= 0:
        raise HTTPException(status_code=422, detail="plan_id must be positive")
    row = get_plan_by_id(plan_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"plan {plan_id} not found")
    return PlanItemResponse(plan=PlanResponse(**row))


# ─── PATCH /api/billing/plans/{plan_id} ──────────────────────────────────────


@router.patch("/{plan_id}", response_model=PlanItemResponse)
def update_existing_plan(plan_id: int, payload: PlanUpdatePayload) -> PlanItemResponse:
    """Update an existing billing plan."""
    if plan_id <= 0:
        raise HTTPException(status_code=422, detail="plan_id must be positive")
    if get_plan_by_id(plan_id) is None:
        raise HTTPException(status_code=404, detail=f"plan {plan_id} not found")
    try:
        row = update_plan(plan_id, payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PlanItemResponse(plan=PlanResponse(**row))


# ─── DELETE /api/billing/plans/{plan_id} ─────────────────────────────────────


@router.delete("/{plan_id}", status_code=204, response_class=Response)
def deactivate_plan(plan_id: int) -> Response:
    """Soft-delete (deactivate) a billing plan by setting active=False."""
    if plan_id <= 0:
        raise HTTPException(status_code=422, detail="plan_id must be positive")
    existing = get_plan_by_id(plan_id)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"plan {plan_id} not found")
    if not bool(existing.get("active")):
        raise HTTPException(status_code=409, detail="plan is already inactive")
    try:
        update_plan(plan_id, {"active": False})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return Response(status_code=204)
