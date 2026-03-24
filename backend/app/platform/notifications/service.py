from __future__ import annotations

from typing import Any

from app.platform.uow import UnitOfWork

def dispatch_notification(
    tenant_id: int,
    channel: str,
    target: str,
    payload: dict[str, Any],
    subject: str | None = None,
) -> dict[str, Any]:
    normalized_channel = str(channel).strip().lower()
    if normalized_channel not in {"email", "in_app", "webhook"}:
        raise ValueError("unsupported notification channel")
    with UnitOfWork() as uow:
        return uow.notification_repository.dispatch(
            tenant_id=int(tenant_id),
            channel=normalized_channel,
            target=target,
            payload=payload,
            subject=subject,
            conn=uow.conn,
        )


def list_notifications(tenant_id: int, limit: int = 100) -> list[dict[str, Any]]:
    with UnitOfWork() as uow:
        return uow.notification_repository.list_for_tenant(int(tenant_id), limit=limit, conn=uow.conn)
