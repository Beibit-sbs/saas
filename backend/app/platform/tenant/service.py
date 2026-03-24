from __future__ import annotations

from typing import Any

from app.platform.events.publisher import EventPublisher
from app.platform.uow import UnitOfWork


def create_tenant(
    slug: str,
    name: str,
    *,
    actor: str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> dict[str, Any]:
    with UnitOfWork() as uow:
        tenant = uow.tenant_repository.create_tenant(slug, name, conn=uow.conn)
        EventPublisher(uow=uow).publish_event(
            tenant_id=int(tenant["tenant_id"]),
            event_type="tenant.created",
            aggregate_type="tenant",
            aggregate_id=int(tenant["tenant_id"]),
            payload_json={
                "tenant_id": int(tenant["tenant_id"]),
                "slug": str(tenant["slug"]),
                "name": str(tenant["name"]),
                "status": str(tenant["status"]),
                "actor": actor,
            },
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        return tenant


def get_tenant_profile(tenant_id: int) -> dict[str, Any]:
    with UnitOfWork() as uow:
        return uow.tenant_repository.get_tenant_profile(int(tenant_id), conn=uow.conn)


def list_tenant_profiles() -> list[dict[str, Any]]:
    with UnitOfWork() as uow:
        return uow.tenant_repository.list_tenant_profiles(conn=uow.conn)


def patch_settings(tenant_id: int, settings: dict[str, Any]) -> dict[str, Any]:
    with UnitOfWork() as uow:
        return uow.tenant_repository.patch_settings(int(tenant_id), settings, conn=uow.conn)


def set_suspended(tenant_id: int, suspended: bool) -> dict[str, Any]:
    with UnitOfWork() as uow:
        return uow.tenant_repository.set_suspended(int(tenant_id), bool(suspended), conn=uow.conn)


def set_quotas(tenant_id: int, quotas: dict[str, int]) -> dict[str, Any]:
    with UnitOfWork() as uow:
        return uow.tenant_repository.set_quotas(int(tenant_id), quotas, conn=uow.conn)


def set_limits(tenant_id: int, limits: dict[str, int]) -> dict[str, Any]:
    with UnitOfWork() as uow:
        return uow.tenant_repository.set_limits(int(tenant_id), limits, conn=uow.conn)
