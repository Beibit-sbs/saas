"""Phase LXXV — Quotas Router.

Endpoints:
  GET  /api/quotas                      — list all quota rows (optional ?plan_id=)
  GET  /api/quotas/plans/{plan_id}      — get quota map for a plan
  PUT  /api/quotas/plans/{plan_id}      — update quota values for a plan
  GET  /api/quotas/tenants/{tenant_id}  — get resolved quotas for a tenant
  GET  /api/quotas/check                — check a single quota key for a tenant
  GET  /api/quotas/consistency          — get plan-quota consistency report
"""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.modules.rbac.security import permission_dependency
from app.modules.quotas.schemas import (
    PlanQuotaConsistencyReportSchema,
    PlanQuotaPayload,
    QuotaListResponse,
    QuotaResponse,
    TenantQuotaCheckResponse,
)
from app.modules.quotas.service import (
    check_quota,
    get_plan_quota_consistency_report,
    get_plan_quotas,
    list_quotas,
    resolve_tenant_quotas,
    update_plan_quotas,
)

router = APIRouter(
    prefix="/api/quotas",
    tags=["quotas"],
    # A-009 Phase 2.1: Add permission_dependency guard (HIGH severity fix for 64 unguarded endpoints)
    dependencies=[Depends(permission_dependency("billing.admin.read"))],
)

MODULE = "app.modules.quotas.router"


# ─── GET /api/quotas ──────────────────────────────────────────────────────────


@router.get("", response_model=QuotaListResponse)
def list_all_quotas(
    plan_id: Optional[int] = Query(default=None, gt=0),
) -> QuotaListResponse:
    """List all quota rows, optionally filtered by plan_id."""
    rows = list_quotas(plan_id=plan_id)
    return QuotaListResponse(quotas=[QuotaResponse(**r) for r in rows])


# ─── GET /api/quotas/plans/{plan_id} ─────────────────────────────────────────


@router.get("/plans/{plan_id}", response_model=dict)
def get_plan_quota_map(plan_id: int) -> dict:
    """Return the quota map (key → limit_value) for a plan."""
    if plan_id <= 0:
        raise HTTPException(status_code=422, detail="plan_id must be positive")
    quotas = get_plan_quotas(plan_id=plan_id)
    return {"plan_id": plan_id, "quotas": quotas}


# ─── PUT /api/quotas/plans/{plan_id} ─────────────────────────────────────────


@router.put("/plans/{plan_id}", response_model=QuotaListResponse)
def set_plan_quotas(plan_id: int, payload: PlanQuotaPayload) -> QuotaListResponse:
    """Update quota values for a plan."""
    if plan_id <= 0:
        raise HTTPException(status_code=422, detail="plan_id must be positive")
    try:
        rows = update_plan_quotas(plan_id=plan_id, quotas=payload.quotas)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return QuotaListResponse(quotas=[QuotaResponse(**r) for r in rows])


# ─── GET /api/quotas/tenants/{tenant_id} ─────────────────────────────────────


@router.get("/tenants/{tenant_id}", response_model=dict)
def get_tenant_quotas(tenant_id: int) -> dict:
    """Return the resolved quota map for a tenant (inherits from plan)."""
    if tenant_id <= 0:
        raise HTTPException(status_code=422, detail="tenant_id must be positive")
    try:
        quotas = resolve_tenant_quotas(tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"tenant_id": tenant_id, "quotas": quotas}


# ─── GET /api/quotas/check ───────────────────────────────────────────────────


@router.get("/check", response_model=TenantQuotaCheckResponse)
def check_tenant_quota(
    tenant_id: int = Query(gt=0),
    quota_key: str = Query(min_length=1),
) -> TenantQuotaCheckResponse:
    """Check a single quota key for a tenant and return limit/current/status."""
    try:
        result = check_quota(tenant_id=tenant_id, quota_key=quota_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TenantQuotaCheckResponse(**result)


# ─── GET /api/quotas/consistency ─────────────────────────────────────────────


@router.get("/consistency", response_model=PlanQuotaConsistencyReportSchema)
def get_consistency_report() -> PlanQuotaConsistencyReportSchema:
    """Return a plan-quota consistency report (missing keys, orphaned rows)."""
    return get_plan_quota_consistency_report()
