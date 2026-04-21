from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Protocol
from uuid import uuid4

from app.platform.events.registry import (
    normalize_event_type,
    registered_tenant_aware_event_types,
    validate_event_publish_inputs,
)


TENANT_AWARE_EVENT_TYPES = registered_tenant_aware_event_types()


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
    normalized_tenant_id = int(tenant_id) if tenant_id is not None else None
    if normalized_tenant_id is not None and normalized_tenant_id <= 0:
        raise ValueError("tenant_id must be positive")

    payload_dict = dict(payload or {})
    normalized_type = validate_event_publish_inputs(
        tenant_id=normalized_tenant_id,
        event_type=event_type,
        payload=payload_dict,
    )

    return DomainEvent(
        event_id=str(uuid4()),
        event_type=normalized_type,
        occurred_at=_now_iso(),
        tenant_id=normalized_tenant_id,
        actor=str(actor).strip() if actor else None,
        correlation_id=str(correlation_id).strip() if correlation_id else None,
        payload=payload_dict,
    )


class InProcessEventBus:
    """Minimal in-process dispatcher with a stable API surface for future outbox/event-broker upgrade."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._handlers: dict[str, list[Callable[[DomainEvent], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[DomainEvent], None]) -> None:
        normalized = normalize_event_type(event_type)
        with self._lock:
            self._handlers.setdefault(normalized, []).append(handler)

    def publish(self, event: DomainEvent) -> None:
        with self._lock:
            handlers = list(self._handlers.get(event.event_type, []))
        for handler in handlers:
            handler(event)
