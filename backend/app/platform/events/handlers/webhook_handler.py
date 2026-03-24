from __future__ import annotations

from app.platform.webhooks.dispatcher import webhook_dispatcher
from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork


class WebhookEventHandler:
    name = "webhook"

    def handle(self, event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, object]:
        result = webhook_dispatcher.dispatch_outbox_event(event, uow=uow)
        return {"handler": self.name, "status": "processed", **result}