from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class WorkflowDefinition:
    tenant_id: int
    key: str
    initial_state: str
    transitions: dict[str, list[str]]


@dataclass(frozen=True)
class WorkflowTask:
    tenant_id: int
    workflow_key: str
    state: str
    actor: str
    entity_type: str
    entity_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def can_transition(definition: WorkflowDefinition, *, current_state: str, next_state: str) -> bool:
    allowed = definition.transitions.get(current_state, [])
    return next_state in allowed
