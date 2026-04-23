from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BrainCoreObservability:
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    latency_samples: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    traces: list[dict[str, Any]] = field(default_factory=list)

    def increment(self, name: str, value: int = 1) -> None:
        self.counters[name] = int(self.counters.get(name, 0)) + int(value)

    def record_latency_ms(self, name: str, latency_ms: float) -> None:
        self.latency_samples[name].append(float(latency_ms))

    def record_trace(self, *, tenant_id: int, correlation_id: str | None, signal_id: str | None, decision_id: str | None) -> None:
        self.traces.append(
            {
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
                "signal_id": signal_id,
                "decision_id": decision_id,
            }
        )

    def snapshot_metrics(self) -> dict[str, Any]:
        def _avg(values: list[float]) -> float:
            return (sum(values) / len(values)) if values else 0.0

        return {
            "counters": dict(self.counters),
            "latency_ms": {name: {"count": len(values), "avg": _avg(values)} for name, values in self.latency_samples.items()},
            "traces_total": len(self.traces),
        }

    def snapshot_traces(self, limit: int = 100) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        return list(self.traces[-limit:])
