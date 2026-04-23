from __future__ import annotations

import logging
from collections.abc import Callable

from app.modules.platform_shared.events import DomainEvent, InProcessEventBus

from app.modules.brain_core.signal_normalizer import normalize_domain_event


logger = logging.getLogger(__name__)


class SignalListener:
    """Subscribes to domain events and normalizes them into BrainSignal envelopes."""

    def __init__(self, event_bus: InProcessEventBus, on_signal: Callable[[dict], None] | None = None) -> None:
        self._event_bus = event_bus
        self._on_signal = on_signal

    def subscribe(self, event_types: list[str]) -> None:
        for event_type in event_types:
            self._event_bus.subscribe(event_type, self._handle_event)

    def _handle_event(self, event: DomainEvent) -> None:
        if event.tenant_id is None:
            logger.warning("brain_core_signal_rejected_missing_tenant", extra={"event_type": event.event_type})
            return

        normalized = normalize_domain_event(event)
        if self._on_signal is not None:
            self._on_signal(normalized)
