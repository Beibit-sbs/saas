"""XVI4 — Executive Brain KPI Dashboard.

Aggregates Brain Core metrics for a single tenant into a structured
executive summary: signal volume, decision quality, outcome effectiveness,
anomaly exposure, and top-risk signal categories.
"""
from __future__ import annotations

from collections import Counter


class BrainKPIDashboard:
    """Pure-function dashboard generator (no DB, works off in-memory state)."""

    def generate(
        self,
        tenant_id: int,
        signals: list[dict],
        decisions: list[dict],
        outcomes: list[dict] | None = None,
    ) -> dict:
        """Return an executive KPI snapshot for *tenant_id*.

        Args:
            tenant_id: Tenant to scope the report to.
            signals: Full list of in-memory brain signals (pre-filtered or not).
            decisions: Full list of in-memory brain decisions.
            outcomes: Optional list of outcome records for effectiveness KPIs.

        Returns:
            A dict with the following top-level keys:
            - tenant_id
            - signal_volume: { total, by_event_type (top-5), unique_event_types }
            - decision_quality: { total, by_priority, by_type, avg_confidence_score,
                                  dispatched, approval_pending, cancelled, completed }
            - outcome_effectiveness: { total, positive, neutral, negative, rate }
            - top_risk_signals: list of { event_type, count }
            - brain_health: { active, recommendation_trigger_eligible }
        """
        t_signals = [s for s in signals if int(s.get("tenant_id") or 0) == tenant_id]
        t_decisions = [d for d in decisions if int(d.get("tenant_id") or 0) == tenant_id]
        t_outcomes = [o for o in (outcomes or []) if int(o.get("tenant_id") or 0) == tenant_id]

        # --- Signal volume ---
        event_type_counts: Counter = Counter(s.get("event_type", "unknown") for s in t_signals)
        top5 = [{"event_type": et, "count": cnt} for et, cnt in event_type_counts.most_common(5)]

        signal_volume = {
            "total": len(t_signals),
            "unique_event_types": len(event_type_counts),
            "top_event_types": top5,
        }

        # --- Decision quality ---
        priority_counts: Counter = Counter(d.get("priority", "unknown") for d in t_decisions)
        type_counts: Counter = Counter(d.get("decision_type", "unknown") for d in t_decisions)

        conf_scores = [
            float(d["confidence_score"])
            for d in t_decisions
            if d.get("confidence_score") is not None
        ]
        avg_confidence = round(sum(conf_scores) / len(conf_scores), 4) if conf_scores else 0.0

        status_counts: Counter = Counter(d.get("status", "unknown") for d in t_decisions)
        decision_quality = {
            "total": len(t_decisions),
            "by_priority": dict(priority_counts),
            "by_type": dict(type_counts),
            "avg_confidence_score": avg_confidence,
            "dispatched": status_counts.get("dispatched", 0),
            "approval_pending": status_counts.get("approval_pending", 0),
            "cancelled": status_counts.get("cancelled", 0),
            "completed": status_counts.get("completed", 0),
        }

        # --- Outcome effectiveness ---
        eff_counts: Counter = Counter(o.get("effectiveness", "unknown") for o in t_outcomes)
        total_outcomes = len(t_outcomes)
        positive = eff_counts.get("positive", 0)
        neutral = eff_counts.get("neutral", 0)
        negative = eff_counts.get("negative", 0)
        effectiveness_rate = round(positive / total_outcomes, 4) if total_outcomes > 0 else 0.0

        outcome_effectiveness = {
            "total": total_outcomes,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "effectiveness_rate": effectiveness_rate,
        }

        # --- Brain health ---
        attendance_signals = event_type_counts.get("academic.attendance_risk.detected", 0)
        workload_signals = event_type_counts.get("faculty.workload_overload.detected", 0)
        critical_decisions = priority_counts.get("critical", 0)

        brain_health = {
            "active": len(t_signals) > 0 or len(t_decisions) > 0,
            "recommendation_trigger_eligible": (
                attendance_signals >= 2 or workload_signals >= 2 or critical_decisions >= 2
            ),
        }

        return {
            "tenant_id": tenant_id,
            "signal_volume": signal_volume,
            "decision_quality": decision_quality,
            "outcome_effectiveness": outcome_effectiveness,
            "top_risk_signals": top5,
            "brain_health": brain_health,
        }


brain_kpi_dashboard = BrainKPIDashboard()
