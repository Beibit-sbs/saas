from __future__ import annotations

from typing import Any

__all__ = ["EventPublisher", "OutboxEventWorker", "outbox_worker"]


def __getattr__(name: str) -> Any:
    if name == "EventPublisher":
        from app.platform.events.publisher import EventPublisher

        return EventPublisher
    if name in {"OutboxEventWorker", "outbox_worker"}:
        from app.platform.events.worker import OutboxEventWorker, outbox_worker

        return OutboxEventWorker if name == "OutboxEventWorker" else outbox_worker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")