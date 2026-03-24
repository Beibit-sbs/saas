from __future__ import annotations

from app.platform.analytics import service as analytics_service
from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork


class AnalyticsEventHandler:
    name = "analytics"

    def handle(self, event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, object]:
        projection = analytics_service.record_event_projection(event, uow=uow)
        return {
            "handler": self.name,
            "status": "recorded" if projection is not None else "duplicate",
            "event_type": event.event_type,
            "outbox_event_id": event.id,
        }