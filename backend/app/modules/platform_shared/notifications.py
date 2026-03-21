from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Protocol


NotificationChannel = Literal["email", "in_app", "system_alert", "sms", "push"]


@dataclass(frozen=True)
class NotificationTemplateRef:
    tenant_id: int
    key: str
    locale: str = "en"


@dataclass(frozen=True)
class NotificationMessage:
    tenant_id: int
    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    template: NotificationTemplateRef | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class NotificationService(Protocol):
    def send(self, message: NotificationMessage) -> dict[str, object]:
        ...


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InMemoryNotificationService:
    def __init__(self) -> None:
        self._items: list[dict[str, object]] = []

    def send(self, message: NotificationMessage) -> dict[str, object]:
        if int(message.tenant_id) <= 0:
            raise ValueError("tenant_id is required")
        if not message.recipient.strip():
            raise ValueError("recipient is required")
        if not message.body.strip():
            raise ValueError("body is required")
        row = {
            "tenant_id": int(message.tenant_id),
            "channel": message.channel,
            "recipient": message.recipient.strip(),
            "subject": message.subject.strip(),
            "body": message.body,
            "template_key": message.template.key if message.template else None,
            "created_at": _now_iso(),
            "metadata": dict(message.metadata),
        }
        self._items.append(row)
        return {"status": "queued", "item": row}

    def snapshot(self) -> list[dict[str, object]]:
        return list(self._items)
