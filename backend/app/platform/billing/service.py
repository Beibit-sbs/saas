from __future__ import annotations

from typing import Any

from app.platform.uow import UnitOfWork


def create_plan(code: str, name: str, price_cents: int, features: dict[str, bool], limits: dict[str, int]) -> dict[str, Any]:
    with UnitOfWork() as uow:
        return uow.billing_repository.create_plan(
            code=code,
            name=name,
            price_cents=price_cents,
            features=features,
            limits=limits,
            conn=uow.conn,
        )


def list_plans() -> list[dict[str, Any]]:
    with UnitOfWork() as uow:
        return uow.billing_repository.list_plans(conn=uow.conn)


def assign_plan(tenant_id: int, plan_code: str) -> dict[str, Any]:
    with UnitOfWork() as uow:
        # Atomic replacement of active subscription in a single transaction.
        return uow.billing_repository.assign_subscription(int(tenant_id), plan_code, conn=uow.conn)


def get_subscription(tenant_id: int) -> dict[str, Any] | None:
    with UnitOfWork() as uow:
        return uow.billing_repository.get_subscription(int(tenant_id), conn=uow.conn)


def increment_usage(tenant_id: int, metric: str, value: int, period_key: str = "current") -> dict[str, Any]:
    with UnitOfWork() as uow:
        # Atomic read-modify-write in repository transaction.
        return uow.usage_repository.increment(int(tenant_id), metric, int(value), period_key=period_key, conn=uow.conn)
