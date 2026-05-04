"""Phase LXXVII — Subscription Management Router.

Endpoints:
  GET    /api/billing/subscriptions              — list (filter by tenant_id, plan_id, status)
  POST   /api/billing/subscriptions              — create subscription
  GET    /api/billing/subscriptions/stats        — stats summary
  GET    /api/billing/subscriptions/{sub_id}     — get by ID
  POST   /api/billing/subscriptions/{sub_id}/cancel   — cancel subscription
  POST   /api/billing/subscriptions/{sub_id}/upgrade  — upgrade plan
"""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.modules.rbac.security import permission_dependency
from app.modules.subscriptions.schemas import (
    SubscriptionCancelPayload,
    SubscriptionCreatePayload,
    SubscriptionItemResponse,
    SubscriptionListResponse,
    SubscriptionResponse,
    SubscriptionUpgradePayload,
)
from app.modules.subscriptions.service import (
    cancel_subscription,
    clear_subscriptions_state,
    create_subscription,
    get_subscription_by_id,
    get_subscriptions_stats,
    list_subscriptions,
    upgrade_subscription,
)

router = APIRouter(
    prefix="/api/billing/subscriptions",
    tags=["billing-subscriptions"],
    # A-009 Phase 2.1: Add permission_dependency guard (HIGH severity fix for 64 unguarded endpoints)
    dependencies=[Depends(permission_dependency("billing.admin.write"))],
)


# ─── GET /api/billing/subscriptions ──────────────────────────────────────────


@router.get("", response_model=SubscriptionListResponse)
def list_all_subscriptions(
    tenant_id: Optional[int] = Query(default=None),
    plan_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
) -> SubscriptionListResponse:
    rows = list_subscriptions(tenant_id=tenant_id, plan_id=plan_id, status=status)
    return SubscriptionListResponse(
        subscriptions=[SubscriptionResponse(**r) for r in rows]
    )


# ─── POST /api/billing/subscriptions ─────────────────────────────────────────


@router.post("", response_model=SubscriptionItemResponse, status_code=201)
def create_new_subscription(payload: SubscriptionCreatePayload) -> SubscriptionItemResponse:
    try:
        row = create_subscription(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SubscriptionItemResponse(subscription=SubscriptionResponse(**row))


# ─── GET /api/billing/subscriptions/stats ────────────────────────────────────


@router.get("/stats")
def get_stats() -> dict:
    return get_subscriptions_stats()


# ─── GET /api/billing/subscriptions/{sub_id} ─────────────────────────────────


@router.get("/{sub_id}", response_model=SubscriptionItemResponse)
def get_subscription(sub_id: str) -> SubscriptionItemResponse:
    try:
        row = get_subscription_by_id(sub_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SubscriptionItemResponse(subscription=SubscriptionResponse(**row))


# ─── POST /api/billing/subscriptions/{sub_id}/cancel ─────────────────────────


@router.post("/{sub_id}/cancel", response_model=SubscriptionItemResponse)
def cancel_sub(sub_id: str, payload: SubscriptionCancelPayload) -> SubscriptionItemResponse:
    try:
        row = cancel_subscription(sub_id, reason=payload.reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SubscriptionItemResponse(subscription=SubscriptionResponse(**row))


# ─── POST /api/billing/subscriptions/{sub_id}/upgrade ────────────────────────


@router.post("/{sub_id}/upgrade", response_model=SubscriptionItemResponse)
def upgrade_sub(sub_id: str, payload: SubscriptionUpgradePayload) -> SubscriptionItemResponse:
    try:
        row = upgrade_subscription(sub_id, payload.new_plan_id, notes=payload.notes)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return SubscriptionItemResponse(subscription=SubscriptionResponse(**row))
