from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreBundle:
    confidence_score: float
    severity_score: float
    urgency_score: float


class DecisionScoring:
    """Shared deterministic scoring helpers for Brain Core reasoning."""

    @staticmethod
    def from_labels(*, severity: str, urgency: str) -> ScoreBundle:
        severity_score = {"high": 0.9, "medium": 0.6, "low": 0.3}.get(str(severity), 0.3)
        urgency_score = {"high": 0.9, "medium": 0.6, "low": 0.3}.get(str(urgency), 0.3)
        confidence_score = min(1.0, (severity_score + urgency_score) / 2.0 + 0.15)
        return ScoreBundle(
            confidence_score=confidence_score,
            severity_score=severity_score,
            urgency_score=urgency_score,
        )
