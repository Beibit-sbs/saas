from __future__ import annotations

from app.platform.developer import service as developer_service
from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork
from app.platform.webhooks.service import webhook_service


class WebhookDispatcher:
    def dispatch_outbox_event(self, event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, object]:
        platform_result = webhook_service.dispatch_event_to_subscriptions(event=event, uow=uow)
        developer_result = developer_service.developer_service.dispatch_event_to_subscribed_apps(event=event, uow=uow)
        return {
            **platform_result,
            "developer_apps_attempted": developer_result["attempted"],
            "developer_apps_delivered": developer_result["delivered"],
            "developer_apps_failed": developer_result["failed"],
        }

    def retry_failed_deliveries(self, *, limit: int = 100, actor: str = "platform-system") -> dict[str, int]:
        return webhook_service.retry_failed_deliveries(limit=limit, actor=actor)


webhook_dispatcher = WebhookDispatcher()