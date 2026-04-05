"""Platform event ingestion service.

record_event() is a fire-and-forget side-effect. It never raises so
that callers (analytics endpoints, billing path) are never interrupted.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from app.platform.event_ingestion.types import VALID_EVENT_TYPES

if TYPE_CHECKING:
    from app.platform.uow import UnitOfWork

logger = logging.getLogger("app.platform.event_ingestion")


def record_event(
    tenant_id: int,
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    uow: "UnitOfWork | None" = None,
) -> dict[str, Any] | None:
    """Record a platform event as an append-only side effect.

    Never raises — callers must not be interrupted by event recording failures.
    Returns the recorded event dict on success, or None on any failure.
    """
    try:
        from app.platform.uow import UnitOfWork as _UnitOfWork  # local import to avoid circular

        normalized_tenant_id = int(tenant_id)
        normalized_type = str(event_type).strip().lower()
        payload_json = dict(payload or {})

        if normalized_type not in VALID_EVENT_TYPES:
            logger.warning("record_event: unknown event type %r — skipped", normalized_type)
            return None

        if uow is not None:
            return uow.platform_event_repository.record(
                tenant_id=normalized_tenant_id,
                event_type=normalized_type,
                payload_json=payload_json,
                conn=uow.conn,
            )

        with _UnitOfWork() as _uow:
            return _uow.platform_event_repository.record(
                tenant_id=normalized_tenant_id,
                event_type=normalized_type,
                payload_json=payload_json,
                conn=_uow.conn,
            )
    except Exception:  # noqa: BLE001
        logger.exception("record_event failed silently for tenant_id=%s type=%s", tenant_id, event_type)
        return None


def list_events_for_tenant(
    tenant_id: int,
    *,
    event_type: str | None = None,
    limit: int = 100,
    uow: "UnitOfWork | None" = None,
) -> list[dict[str, Any]]:
    """Return recorded platform events for a tenant. Used in tests and admin views."""
    from app.platform.uow import UnitOfWork as _UnitOfWork  # local import

    normalized_tenant_id = int(tenant_id)

    if uow is not None:
        return uow.platform_event_repository.list_for_tenant(
            normalized_tenant_id,
            event_type=event_type,
            limit=limit,
            conn=uow.conn,
        )

    with _UnitOfWork() as _uow:
        return _uow.platform_event_repository.list_for_tenant(
            normalized_tenant_id,
            event_type=event_type,
            limit=limit,
            conn=_uow.conn,
        )


def summary_for_tenant(
    tenant_id: int,
    *,
    uow: "UnitOfWork | None" = None,
) -> dict[str, int]:
    """Return counts per event_type for a tenant. Used in projection summary."""
    from app.platform.uow import UnitOfWork as _UnitOfWork  # local import

    normalized_tenant_id = int(tenant_id)

    if uow is not None:
        return uow.platform_event_repository.count_by_type_for_tenant(
            normalized_tenant_id, conn=uow.conn
        )

    with _UnitOfWork() as _uow:
        return _uow.platform_event_repository.count_by_type_for_tenant(
            normalized_tenant_id, conn=_uow.conn
        )


def clear_event_state() -> None:
    """Clear all in-memory platform event state. Used by test fixtures."""
    from app.platform.uow import _SHARED_PLATFORM_EVENT_REPOSITORY

    _SHARED_PLATFORM_EVENT_REPOSITORY.clear_state()
