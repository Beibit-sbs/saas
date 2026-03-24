from __future__ import annotations

from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork


class AnalyticsEventHandler:
    name = "analytics"

    def handle(self, event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, object]:
        _ = uow
        return {
            "handler": self.name,
            "status": "noop",
            "event_type": event.event_type,
        }