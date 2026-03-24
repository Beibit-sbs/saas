from __future__ import annotations

from typing import Any

from app.platform.uow import UnitOfWork


def create_tenant(slug: str, name: str) -> dict[str, Any]:
    with UnitOfWork() as uow:
        return uow.tenant_repository.create_tenant(slug, name, conn=uow.conn)


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
