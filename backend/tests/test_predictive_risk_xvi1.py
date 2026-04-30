"""Phase XVI-1 — Predictive Risk Engine tests.

Tests: 6/6
- test_predict_risk_worsening_trend          → trajectory=worsening, risk level escalates
- test_predict_risk_improving_trend          → trajectory=improving, risk decreases
- test_predict_risk_stable_trend             → trajectory=stable
- test_predict_risk_no_history               → empty history → low risk, 0 confidence
- test_predict_risk_horizon_scales           → longer horizon projects further
- test_predict_risk_via_brain_core_service   → BrainCoreService.predict_risk() round-trip
"""
from __future__ import annotations

import pytest

from app.modules.brain_core.reasoning.predictor import PredictiveRiskEngine
from app.modules.brain_core.service import BrainCoreService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _history(scores: list[float]) -> list[dict]:
    return [{"score": s} for s in scores]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_predict_risk_worsening_trend() -> None:
    engine = PredictiveRiskEngine()
    # Scores rising toward critical over 8 points
    history = _history([0.30, 0.38, 0.47, 0.55, 0.62, 0.70, 0.78, 0.85])
    result = engine.predict_risk(
        event_type="academic.attendance_risk.detected",
        tenant_id=1,
        entity_id="STU-001",
        history=history,
        horizon_days=7,
    )
    assert result["trajectory"] == "worsening"
    assert result["risk_level"] in ("high", "critical")
    assert result["predicted_score"] > result["current_score"]
    assert result["data_points"] == 8
    assert result["confidence"] > 0


def test_predict_risk_improving_trend() -> None:
    engine = PredictiveRiskEngine()
    history = _history([0.80, 0.72, 0.64, 0.55, 0.47, 0.38])
    result = engine.predict_risk(
        event_type="academic.grade_risk.detected",
        tenant_id=2,
        entity_id="STU-002",
        history=history,
        horizon_days=7,
    )
    assert result["trajectory"] == "improving"
    assert result["predicted_score"] < result["current_score"]
    assert result["risk_level"] in ("low", "medium")
    assert "improving_trend_detected" in result["factors"]


def test_predict_risk_stable_trend() -> None:
    engine = PredictiveRiskEngine()
    # Nearly flat scores
    history = _history([0.50, 0.51, 0.50, 0.52, 0.50])
    result = engine.predict_risk(
        event_type="faculty.workload_overload.detected",
        tenant_id=1,
        entity_id="FAC-007",
        history=history,
        horizon_days=14,
    )
    assert result["trajectory"] == "stable"
    assert result["risk_level"] == "medium"
    assert "stable_pattern" in result["factors"]


def test_predict_risk_no_history() -> None:
    engine = PredictiveRiskEngine()
    result = engine.predict_risk(
        event_type="academic.attendance_risk.detected",
        tenant_id=1,
        entity_id="STU-999",
        history=[],
        horizon_days=7,
    )
    assert result["risk_level"] == "low"
    assert result["confidence"] == 0.0
    assert result["predicted_score"] == 0.0
    assert result["data_points"] == 0
    assert "insufficient_history" in result["factors"]


def test_predict_risk_horizon_scales() -> None:
    """A worsening trend should project a higher risk at 30 days than at 7 days."""
    engine = PredictiveRiskEngine()
    history = _history([0.40, 0.48, 0.56, 0.64, 0.72])
    result_7 = engine.predict_risk(
        event_type="academic.attendance_risk.detected",
        tenant_id=1,
        entity_id="STU-100",
        history=history,
        horizon_days=7,
    )
    result_30 = engine.predict_risk(
        event_type="academic.attendance_risk.detected",
        tenant_id=1,
        entity_id="STU-100",
        history=history,
        horizon_days=30,
    )
    # Longer horizon → higher projected score for worsening trend
    assert result_30["predicted_score"] >= result_7["predicted_score"]


def test_predict_risk_via_brain_core_service() -> None:
    """BrainCoreService.predict_risk() delegates to PredictiveRiskEngine correctly."""
    service = BrainCoreService()
    history = _history([0.45, 0.55, 0.65, 0.75])
    result = service.predict_risk(
        event_type="academic.attendance_risk.detected",
        tenant_id=3,
        entity_id="STU-XYZ",
        history=history,
        horizon_days=14,
    )
    assert "predicted_score" in result
    assert "risk_level" in result
    assert "trajectory" in result
    assert result["tenant_id"] == 3
    assert result["entity_id"] == "STU-XYZ"
    assert result["horizon_days"] == 14
