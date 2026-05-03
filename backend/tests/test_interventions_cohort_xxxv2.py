"""XXXV.2: Interventions — Cohort Analytics (12 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.interventions.service import (
    analyze_cohort_risk,
    get_cohort_risk_snapshots,
    _segment_students_by_risk,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _student(risk_score: float, cohort_id: str = "C1", student_id: str = "S1") -> dict:
    return {"id": student_id, "student_id": student_id, "risk_score": risk_score, "cohort_id": cohort_id}


def _make_students(*scores: float, cohort_id: str = "C1") -> list[dict]:
    return [_student(s, cohort_id=cohort_id, student_id=str(i + 1)) for i, s in enumerate(scores)]


# ─── 1. Segment helper unit tests ─────────────────────────────────────────────

def test_segment_high_risk_above_threshold() -> None:
    students = _make_students(0.9, 0.3, 0.5)
    result = _segment_students_by_risk(students, threshold=0.7)
    assert len(result["high"]) == 1
    assert result["high"][0]["risk_score"] == 0.9


def test_segment_medium_risk_band() -> None:
    students = _make_students(0.4, 0.1)
    result = _segment_students_by_risk(students, threshold=0.7)
    assert len(result["medium"]) == 1  # 0.4 >= 0.35 (threshold*0.5)
    assert len(result["low"]) == 1


def test_segment_handles_missing_risk_score() -> None:
    students = [{"id": "X", "student_id": "X"}]  # no risk_score key
    result = _segment_students_by_risk(students, threshold=0.7)
    assert len(result["low"]) == 1  # defaults to 0.0 → low


# ─── 2. analyze_cohort_risk ───────────────────────────────────────────────────

def _setup_analyze(students, snapshot_id=42, trigger_id=99):
    """Return (list_patch, create_patch, pub_patch)."""
    return students, snapshot_id, trigger_id


@patch("app.modules.interventions.service.EventPublisher")
@patch("app.modules.interventions.service.create_entity_for_tenant")
@patch("app.modules.interventions.service.list_entities_for_tenant")
def test_analyze_cohort_returns_segment_counts(mock_list, mock_create, mock_pub_cls) -> None:
    mock_list.return_value = _make_students(0.9, 0.4, 0.1)
    mock_create.return_value = {"id": 1}
    mock_pub = MagicMock()
    mock_pub_cls.return_value = mock_pub

    result = analyze_cohort_risk(tenant_id=1, threshold=0.7)

    assert result["total_students"] == 3
    assert result["segments"]["high"] == 1
    assert result["segments"]["medium"] == 1
    assert result["segments"]["low"] == 1


@patch("app.modules.interventions.service.EventPublisher")
@patch("app.modules.interventions.service.create_entity_for_tenant")
@patch("app.modules.interventions.service.list_entities_for_tenant")
def test_analyze_cohort_fires_analyzed_event(mock_list, mock_create, mock_pub_cls) -> None:
    mock_list.return_value = _make_students(0.8)
    mock_create.return_value = {"id": 10}
    mock_pub = MagicMock()
    mock_pub_cls.return_value = mock_pub

    analyze_cohort_risk(tenant_id=1)

    calls = [str(c) for c in mock_pub.publish_event.call_args_list]
    assert any("interventions.cohort.analyzed" in c for c in calls)


@patch("app.modules.interventions.service.EventPublisher")
@patch("app.modules.interventions.service.create_entity_for_tenant")
@patch("app.modules.interventions.service.list_entities_for_tenant")
def test_analyze_high_risk_fires_auto_triggered_event(mock_list, mock_create, mock_pub_cls) -> None:
    mock_list.return_value = _make_students(0.95, 0.80)  # both high-risk
    mock_create.return_value = {"id": 5}
    mock_pub = MagicMock()
    mock_pub_cls.return_value = mock_pub

    result = analyze_cohort_risk(tenant_id=1, threshold=0.7)

    assert result["auto_triggered_count"] == 2
    calls_str = " ".join(str(c) for c in mock_pub.publish_event.call_args_list)
    assert "interventions.auto_triggered" in calls_str


@patch("app.modules.interventions.service.EventPublisher")
@patch("app.modules.interventions.service.create_entity_for_tenant")
@patch("app.modules.interventions.service.list_entities_for_tenant")
def test_analyze_no_high_risk_no_auto_trigger(mock_list, mock_create, mock_pub_cls) -> None:
    mock_list.return_value = _make_students(0.1, 0.2)
    mock_create.return_value = {"id": 3}
    mock_pub = MagicMock()
    mock_pub_cls.return_value = mock_pub

    result = analyze_cohort_risk(tenant_id=1, threshold=0.7)

    assert result["auto_triggered_count"] == 0
    calls_str = " ".join(str(c) for c in mock_pub.publish_event.call_args_list)
    assert "interventions.auto_triggered" not in calls_str


@patch("app.modules.interventions.service.EventPublisher")
@patch("app.modules.interventions.service.create_entity_for_tenant")
@patch("app.modules.interventions.service.list_entities_for_tenant")
def test_analyze_filters_by_cohort_id(mock_list, mock_create, mock_pub_cls) -> None:
    all_students = _make_students(0.9, cohort_id="C1") + _make_students(0.85, cohort_id="C2")
    mock_list.return_value = all_students
    mock_create.return_value = {"id": 7}
    mock_pub = MagicMock()
    mock_pub_cls.return_value = mock_pub

    result = analyze_cohort_risk(tenant_id=1, cohort_id="C1", threshold=0.7)

    assert result["total_students"] == 1
    assert result["cohort_id"] == "C1"


@patch("app.modules.interventions.service.EventPublisher")
@patch("app.modules.interventions.service.create_entity_for_tenant")
@patch("app.modules.interventions.service.list_entities_for_tenant")
def test_analyze_persists_snapshot(mock_list, mock_create, mock_pub_cls) -> None:
    mock_list.return_value = _make_students(0.9)
    mock_create.return_value = {"id": 20}
    mock_pub_cls.return_value = MagicMock()

    result = analyze_cohort_risk(tenant_id=1)

    assert result["snapshot_id"] == 20
    # First create_entity_for_tenant call should be for the snapshot
    first_call_args = mock_create.call_args_list[0]
    assert first_call_args[0][0] == "cohort_risk_snapshots"


def test_analyze_invalid_tenant_raises() -> None:
    with pytest.raises(ValueError, match="tenant_id"):
        analyze_cohort_risk(tenant_id=0)


@patch("app.modules.interventions.service.EventPublisher")
@patch("app.modules.interventions.service.create_entity_for_tenant")
@patch("app.modules.interventions.service.list_entities_for_tenant")
def test_analyze_survives_event_publisher_failure(mock_list, mock_create, mock_pub_cls) -> None:
    mock_list.return_value = _make_students(0.9)
    mock_create.return_value = {"id": 1}
    mock_pub = MagicMock()
    mock_pub.publish_event.side_effect = RuntimeError("broker down")
    mock_pub_cls.return_value = mock_pub

    # Must not raise
    result = analyze_cohort_risk(tenant_id=1)
    assert result["total_students"] == 1


# ─── 3. get_cohort_risk_snapshots ─────────────────────────────────────────────

@patch("app.modules.interventions.service.list_entities_for_tenant")
def test_get_snapshots_returns_all_for_tenant(mock_list) -> None:
    mock_list.return_value = [
        {"id": 1, "cohort_id": "C1", "tenant_id": 1},
        {"id": 2, "cohort_id": "C2", "tenant_id": 1},
    ]
    rows = get_cohort_risk_snapshots(tenant_id=1)
    assert len(rows) == 2


@patch("app.modules.interventions.service.list_entities_for_tenant")
def test_get_snapshots_filters_by_cohort_id(mock_list) -> None:
    mock_list.return_value = [
        {"id": 1, "cohort_id": "C1", "tenant_id": 1},
        {"id": 2, "cohort_id": "C2", "tenant_id": 1},
    ]
    rows = get_cohort_risk_snapshots(tenant_id=1, cohort_id="C1")
    assert len(rows) == 1
    assert rows[0]["cohort_id"] == "C1"
