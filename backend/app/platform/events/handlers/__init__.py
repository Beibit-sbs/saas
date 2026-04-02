from __future__ import annotations

from typing import Any, Protocol

from app.platform.events.handlers.analytics_handler import AnalyticsEventHandler
from app.platform.events.handlers.automation_handler import AutomationEventHandler
from app.platform.events.handlers.context_projection_handler import ContextProjectionHandler
from app.platform.events.handlers.education_graph_inference_handler import EducationGraphInferenceHandler
from app.platform.events.handlers.notification_handler import NotificationEventHandler
from app.platform.events.handlers.webhook_handler import WebhookEventHandler
from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork


class EventHandler(Protocol):
    name: str

    def handle(self, event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, Any]:
        ...

__all__ = [
    "AnalyticsEventHandler",
    "AutomationEventHandler",
    "ContextProjectionHandler",
    "EducationGraphInferenceHandler",
    "EventHandler",
    "NotificationEventHandler",
    "WebhookEventHandler",
]