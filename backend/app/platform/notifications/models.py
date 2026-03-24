from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class NotificationRecord:
    id: int
    tenant_id: int
    channel: str
    target: str
    subject: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "queued"
    created_at: str = ""
