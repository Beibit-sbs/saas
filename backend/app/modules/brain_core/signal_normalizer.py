from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.modules.platform_shared.events import DomainEvent


def normalize_domain_event(event: DomainEvent) -> dict:
    """Normalize domain events into canonical BrainSignal envelope."""
    return {
        "signal_id": str(uuid4()),
        "tenant_id": event.tenant_id,
        "correlation_id": event.correlation_id or str(uuid4()),
        "event_type": event.event_type,
        "signal_class": event.event_type.split(".", 1)[0] if "." in event.event_type else "unknown",
        "source_module": (event.event_type.split(".", 1)[0] if "." in event.event_type else "unknown"),
        "source_entity_type": event.payload.get("source_entity_type", "unknown"),
        "source_entity_id": str(event.payload.get("source_entity_id", "unknown")),
        "occurred_at": event.occurred_at,
        "subject": {
            "student_id": event.payload.get("student_id"),
            "faculty_id": event.payload.get("faculty_id"),
            "course_id": event.payload.get("course_id"),
            "section_id": event.payload.get("section_id"),
        },
        "payload": dict(event.payload or {}),
        "metadata": {
            "event_id": event.event_id,
            "actor": event.actor,
            "normalized_at": datetime.now(timezone.utc).isoformat(),
        },
    }
