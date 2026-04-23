"""Listens to domain outcome events and ingests them into Brain Core learning loop."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.modules.platform_shared.events import DomainEvent, InProcessEventBus

if TYPE_CHECKING:
    from typing import Callable

logger = logging.getLogger(__name__)


class OutcomeListener:
    """Subscribes to domain outcome events and auto-feeds them into Brain Core."""

    OUTCOME_EVENT_TYPES = {
        "interventions.case_outcome.recorded",
        "workflows.case_outcome.recorded",
    }

    def __init__(self, event_bus: InProcessEventBus, on_outcome: Callable[[int, str, dict, str], None] | None = None) -> None:
        self._event_bus = event_bus
        self._on_outcome = on_outcome

    def subscribe(self) -> None:
        """Register listeners for all known outcome event types."""
        for event_type in self.OUTCOME_EVENT_TYPES:
            self._event_bus.subscribe(event_type, self._handle_outcome_event)

    def _handle_outcome_event(self, event: DomainEvent) -> None:
        """
        Handle domain outcome events and forward to Brain Core feedback loop.

        Expected event payload:
        {
            "case_id": str,
            "outcome_type": "completed|resolved|closed|...",
            "effectiveness": "positive|negative|neutral",
            "reason": str,
            "source_entity_type": "intervention_case|workflow_case|...",
        }
        """
        if event.tenant_id is None:
            logger.warning(
                "brain_core_outcome_rejected_missing_tenant",
                extra={"event_type": event.event_type},
            )
            return

        payload = dict(event.payload or {})
        case_id = payload.get("case_id")
        if not case_id:
            logger.warning(
                "brain_core_outcome_rejected_missing_case_id",
                extra={"event_type": event.event_type},
            )
            return

        outcome_data = {
            "case_id": case_id,
            "outcome_type": payload.get("outcome_type", "completed"),
            "effectiveness": payload.get("effectiveness", "neutral"),
            "notes": payload.get("reason", ""),
            "source_entity_type": payload.get("source_entity_type", "unknown"),
        }

        if self._on_outcome is not None:
            try:
                self._on_outcome(
                    event.tenant_id,
                    case_id=case_id,
                    payload=outcome_data,
                    actor="system",
                )
            except Exception as exc:
                logger.error(
                    "brain_core_outcome_ingestion_failed",
                    extra={
                        "event_type": event.event_type,
                        "case_id": case_id,
                        "error": str(exc),
                    },
                )
