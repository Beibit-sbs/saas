from __future__ import annotations

from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork
from app.platform.webhooks.service import webhook_service


class WebhookDispatcher:
    def dispatch_outbox_event(self, event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, object]:
        return webhook_service.dispatch_event_to_subscriptions(event=event, uow=uow)

    def retry_failed_deliveries(self, *, limit: int = 100, actor: str = "platform-system") -> dict[str, int]:
        return webhook_service.retry_failed_deliveries(limit=limit, actor=actor)


webhook_dispatcher = WebhookDispatcher()