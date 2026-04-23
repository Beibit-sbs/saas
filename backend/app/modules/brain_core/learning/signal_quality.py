from __future__ import annotations

from collections import Counter
from typing import Any


class SignalQualityTracker:
    """Tracks basic quality counters for incoming signals."""

    def __init__(self) -> None:
        self._counters: Counter[str] = Counter()

    def record(self, signal: dict[str, Any]) -> None:
        self._counters["total"] += 1
        if signal.get("tenant_id"):
            self._counters["tenant_scoped"] += 1
        else:
            self._counters["missing_tenant"] += 1
        if signal.get("event_type"):
            self._counters["event_type_present"] += 1

    def snapshot(self) -> dict[str, int]:
        return dict(self._counters)
