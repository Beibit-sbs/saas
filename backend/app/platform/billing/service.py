from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.event_ingestion.types import BILLING_USAGE_RECORDED
from app.platform.uow import UnitOfWork


WRITE_ALLOWED_STATUSES = {"trial", "active"}


def create_plan(code: str, name: str, price_cents: int, features: dict[str, bool], limits: dict[str, int]) -> dict[str, Any]:
    with UnitOfWork() as uow:
        return uow.billing_repository.create_plan(
            code=str(code),
            name=str(name),
            price_cents=int(price_cents),
            features={str(key): bool(value) for key, value in dict(features).items()},
            limits={str(key): int(value) for key, value in dict(limits).items()},
            conn=uow.conn,
        )


def list_plans() -> list[dict[str, Any]]:
    with UnitOfWork() as uow:
        return uow.billing_repository.list_plans(conn=uow.conn)


def update_plan(plan_id: int, *, name: str | None = None, active: bool | None = None) -> dict[str, Any] | None:
    with UnitOfWork() as uow:
        return uow.billing_repository.update_plan(int(plan_id), name=name, active=active, conn=uow.conn)


def assign_plan(tenant_id: int, plan_code: str) -> dict[str, Any]:
    with UnitOfWork() as uow:
        return uow.billing_repository.assign_subscription(int(tenant_id), str(plan_code), conn=uow.conn)


def get_subscription(tenant_id: int) -> dict[str, Any] | None:
    with UnitOfWork() as uow:
        return uow.billing_repository.get_subscription(int(tenant_id), conn=uow.conn)


def assert_quota_with_increment(
    tenant_id: int,
    metric: str,
    *,
    increment: int = 1,
    period_key: str = "current",
) -> dict[str, Any]:
    normalized_tenant_id = int(tenant_id)
    normalized_metric = str(metric or "").strip().lower()
    normalized_period_key = str(period_key or "current").strip().lower() or "current"
    normalized_increment = max(0, int(increment))

    if normalized_tenant_id <= 0:
        raise HTTPException(status_code=400, detail="invalid tenant_id")
    if not normalized_metric:
        raise HTTPException(status_code=400, detail="metric is required")

    with UnitOfWork() as uow:
        subscription = uow.billing_repository.get_subscription(normalized_tenant_id, conn=uow.conn)
        if subscription is None:
            raise HTTPException(status_code=403, detail="billing_required: platform subscription state unavailable")

        status = str(subscription.get("status", "trial")).strip().lower()
        if status not in WRITE_ALLOWED_STATUSES:
            raise HTTPException(
                status_code=403,
                detail=f"billing_required: tenant subscription is '{status}' (read-only mode)",
            )

        plan_code = str(subscription.get("plan_code", "")).strip().lower()
        plan = uow.billing_repository.get_plan(plan_code, conn=uow.conn)
        if plan is None:
            raise HTTPException(status_code=403, detail="billing_required: platform plan configuration unavailable")

        limits = {str(key): int(value) for key, value in dict(plan.get("limits") or {}).items()}
        limit_value = int(limits.get(normalized_metric) or 0)
        usage_rows = uow.usage_repository.list_for_tenant_period(
            normalized_tenant_id,
            period_key=normalized_period_key,
            conn=uow.conn,
        )
        current_value = 0
        for row in usage_rows:
            if str(row.get("metric", "")).strip().lower() == normalized_metric:
                current_value = int(row.get("value", 0) or 0)
                break

    projected_value = current_value + normalized_increment
    if limit_value > 0 and projected_value > limit_value:
        raise HTTPException(
            status_code=403,
            detail=(
                f"billing_required: quota exceeded for '{normalized_metric}' "
                f"(limit={limit_value}, current={current_value}, projected={projected_value})"
            ),
        )

    return {
        "tenant_id": normalized_tenant_id,
        "metric": normalized_metric,
        "period_key": normalized_period_key,
        "limit_value": limit_value,
        "current_value": current_value,
        "projected_value": projected_value,
        "within_limit": True,
        "plan_code": plan_code,
        "subscription_status": status,
    }


def increment_usage(tenant_id: int, metric: str, value: int, period_key: str = "current") -> dict[str, Any]:
    normalized_tenant_id = int(tenant_id)
    normalized_metric = str(metric).strip().lower()
    normalized_period_key = str(period_key or "current").strip().lower() or "current"
    with UnitOfWork() as uow:
        result = uow.usage_repository.increment(
            normalized_tenant_id,
            normalized_metric,
            int(value),
            period_key=normalized_period_key,
            conn=uow.conn,
        )
        event_ingestion_service.record_event(
            normalized_tenant_id,
            BILLING_USAGE_RECORDED,
            {"metric": normalized_metric, "value": int(value), "period_key": normalized_period_key},
            uow=uow,
        )
    return result
