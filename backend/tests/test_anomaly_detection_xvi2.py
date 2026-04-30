from __future__ import annotations

from app.modules.brain_core.reasoning.anomaly_detector import AnomalyDetector
from app.modules.brain_core.service import BrainCoreService


def test_detects_high_spike() -> None:
    detector = AnomalyDetector()
    result = detector.detect(
        tenant_id=1,
        metric_name="attendance_gap_days",
        values=[1, 2, 2, 3, 4, 20],
        entity_ids=["a", "b", "c", "d", "e", "f"],
    )
    assert len(result["anomalies"]) == 1
    assert result["anomalies"][0]["entity_id"] == "f"
    assert result["anomalies"][0]["direction"] == "high"


def test_detects_low_outlier() -> None:
    detector = AnomalyDetector()
    result = detector.detect(
        tenant_id=1,
        metric_name="faculty_load_ratio",
        values=[0.95, 0.92, 0.93, 0.91, 0.20],
        entity_ids=["f1", "f2", "f3", "f4", "f5"],
    )
    assert len(result["anomalies"]) == 1
    assert result["anomalies"][0]["entity_id"] == "f5"
    assert result["anomalies"][0]["direction"] == "low"


def test_returns_empty_for_no_values() -> None:
    detector = AnomalyDetector()
    result = detector.detect(tenant_id=7, metric_name="budget_drift", values=[])
    assert result["method"] == "empty"
    assert result["anomalies"] == []


def test_returns_no_anomalies_for_insufficient_history() -> None:
    detector = AnomalyDetector()
    result = detector.detect(
        tenant_id=9,
        metric_name="room_faults",
        values=[1, 1, 2],
        entity_ids=["r1", "r2", "r3"],
    )
    assert result["method"] == "insufficient_history"
    assert result["anomalies"] == []


def test_service_detect_anomalies_delegates() -> None:
    service = BrainCoreService()
    result = service.detect_anomalies(
        tenant_id=5,
        metric_name="collections_delay_days",
        values=[2, 2, 3, 4, 15],
        entity_ids=["s1", "s2", "s3", "s4", "s5"],
    )
    assert result["tenant_id"] == 5
    assert result["metric_name"] == "collections_delay_days"
    assert result["anomalies"][0]["entity_id"] == "s5"