from __future__ import annotations

from typing import Any

from app.platform.automation import service as automation_service
from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork


class AutomationEventHandler:
    """Evaluates all active automation rules for each processed outbox event."""

    name = "automation"

    def handle(self, event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, Any]:
        result = automation_service.evaluate_event(event, uow=uow)
        return {"handler": self.name, "status": "processed", **result}
