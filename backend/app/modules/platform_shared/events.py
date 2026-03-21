from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Protocol
from uuid import uuid4


TENANT_AWARE_EVENT_TYPES = {
    "tenant.created",
    "user.created",
    "role.assigned",
    "ai.chat.executed",
    "integration.updated",
    "workflow.approved",
    "student.created",
    "file.uploaded",
}


@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    event_type: str
    occurred_at: str
    tenant_id: int | None
    actor: str | None
    correlation_id: str | None
    payload: dict[str, Any] = field(default_factory=dict)


class EventPublisher(Protocol):
    def publish(self, event: DomainEvent) -> None:
        ...


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_domain_event(
    *,
    event_type: str,
    payload: dict[str, Any] | None = None,
    tenant_id: int | None = None,
    actor: str | None = None,
    correlation_id: str | None = None,
) -> DomainEvent:
    normalized_type = str(event_type).strip().lower()
    if not normalized_type:
        raise ValueError("event_type is required")

    normalized_tenant_id = int(tenant_id) if tenant_id is not None else None
    if normalized_type in TENANT_AWARE_EVENT_TYPES and (normalized_tenant_id is None or normalized_tenant_id <= 0):
        raise ValueError("tenant-aware event requires tenant_id")

    if normalized_tenant_id is not None and normalized_tenant_id <= 0:
        raise ValueError("tenant_id must be positive")

    return DomainEvent(
        event_id=str(uuid4()),
        event_type=normalized_type,
        occurred_at=_now_iso(),
        tenant_id=normalized_tenant_id,
        actor=str(actor).strip() if actor else None,
        correlation_id=str(correlation_id).strip() if correlation_id else None,
        payload=dict(payload or {}),
    )


class InProcessEventBus:
    """Minimal in-process dispatcher with a stable API surface for future outbox/event-broker upgrade."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._handlers: dict[str, list[Callable[[DomainEvent], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        normalized = str(event_type).strip().lower()
        if not normalized:
            raise ValueError("event_type is required")
        with self._lock:
            self._handlers.setdefault(normalized, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        with self._lock:
            handlers = list(self._handlers.get(event.event_type, []))
        for handler in handlers:
            handler(event)
