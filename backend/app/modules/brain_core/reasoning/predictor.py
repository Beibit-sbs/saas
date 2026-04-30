"""Predictive Risk Engine — forecasts risk levels based on historical signal trends."""
from __future__ import annotations

import statistics
from typing import Literal


RiskLevel = Literal["low", "medium", "high", "critical"]
Trajectory = Literal["worsening", "stable", "improving"]


def _trajectory(scores: list[float]) -> Trajectory:
    """Determine trend direction from a sequence of risk scores (oldest first)."""
    if len(scores) < 2:
        return "stable"
    delta = scores[-1] - scores[0]
    if delta > 0.1:
        return "worsening"
    if delta < -0.1:
        return "improving"
    return "stable"


def _project_score(scores: list[float], horizon_days: int) -> float:
    """Linear extrapolation of the last trend segment."""
    if len(scores) < 2:
        return scores[-1] if scores else 0.5
    # Use last two points for slope
    slope = (scores[-1] - scores[-2]) / max(1, len(scores) - 1)
    projected = scores[-1] + slope * (horizon_days / 7)
    return max(0.0, min(1.0, projected))


def _score_to_level(score: float) -> RiskLevel:
    if score >= 0.85:
        return "critical"
    if score >= 0.65:
        return "high"
    if score >= 0.40:
        return "medium"
    return "low"


class PredictiveRiskEngine:
    """
    Forecasts future risk levels based on historical signal data.

    Each history entry is a dict with at least:
        {"score": float, "timestamp": str}  # score in [0, 1]

    Returns a prediction dict with:
        risk_level, confidence, trajectory, predicted_score, horizon_days, factors
    """

    def predict_risk(
        self,
        *,
        event_type: str,
        tenant_id: int,
        entity_id: str,
        history: list[dict],
        horizon_days: int = 7,
    ) -> dict:
        """
        Predict risk level at horizon_days based on historical scores.

        Args:
            event_type: The Brain Core signal event type.
            tenant_id: Tenant scope.
            entity_id: Subject entity (student_id, faculty_id, etc.)
            history: List of historical data points {score: float, ...}
            horizon_days: How many days into the future to project (7/14/30).

        Returns:
            Prediction dict.
        """
        if not history:
            return self._empty_prediction(event_type, entity_id, tenant_id, horizon_days)

        scores = [float(h.get("score", 0.5)) for h in history]
        traj = _trajectory(scores)
        projected = _project_score(scores, horizon_days)
        risk_level = _score_to_level(projected)

        # Confidence: higher with more data points; lower with volatile data
        confidence = self._compute_confidence(scores)

        factors = self._extract_factors(event_type, scores, traj, projected)

        return {
            "event_type": event_type,
            "tenant_id": tenant_id,
            "entity_id": entity_id,
            "horizon_days": horizon_days,
            "predicted_score": round(projected, 4),
            "risk_level": risk_level,
            "trajectory": traj,
            "confidence": round(confidence, 4),
            "current_score": round(scores[-1], 4),
            "data_points": len(scores),
            "factors": factors,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _empty_prediction(
        self, event_type: str, entity_id: str, tenant_id: int, horizon_days: int
    ) -> dict:
        return {
            "event_type": event_type,
            "tenant_id": tenant_id,
            "entity_id": entity_id,
            "horizon_days": horizon_days,
            "predicted_score": 0.0,
            "risk_level": "low",
            "trajectory": "stable",
            "confidence": 0.0,
            "current_score": 0.0,
            "data_points": 0,
            "factors": ["insufficient_history"],
        }

    def _compute_confidence(self, scores: list[float]) -> float:
        """Confidence grows with data volume and shrinks with variance."""
        n = len(scores)
        volume_factor = min(1.0, n / 10.0)  # saturates at 10 data points
        if n < 2:
            variance_penalty = 0.5
        else:
            std = statistics.stdev(scores)
            variance_penalty = max(0.0, 1.0 - std * 2)
        return volume_factor * variance_penalty

    def _extract_factors(
        self,
        event_type: str,
        scores: list[float],
        trajectory: Trajectory,
        projected: float,
    ) -> list[str]:
        factors: list[str] = []
        if trajectory == "worsening":
            factors.append("consistent_deterioration_trend")
        elif trajectory == "improving":
            factors.append("improving_trend_detected")
        else:
            factors.append("stable_pattern")
        if projected >= 0.85:
            factors.append("critical_threshold_projection")
        elif projected >= 0.65:
            factors.append("high_risk_projection")
        if len(scores) >= 5:
            factors.append("sufficient_history")
        factors.append(f"event_type:{event_type}")
        return factors
