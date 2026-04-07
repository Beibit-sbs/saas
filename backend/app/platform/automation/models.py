from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AutomationRuleModel:
    """A tenant-scoped automation rule that reacts to a specific event type."""

    id: int
    tenant_id: int
    name: str
    description: str
    event_type: str
    condition_json: dict[str, Any]   # {"field": "grade_value", "operator": "<", "value": 50}
    actions_json: list[dict[str, Any]]  # [{"type": "send_notification", ...}, ...]
    is_active: bool
    created_at: str
    updated_at: str
    version: int = 1


@dataclass(slots=True)
class AutomationExecutionModel:
    """Record of a single automation rule execution triggered by an event."""

    id: int
    tenant_id: int
    rule_id: int
    event_id: int
    status: str          # pending | completed | failed
    result_json: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    executed_at: str = ""
    created_at: str = ""
