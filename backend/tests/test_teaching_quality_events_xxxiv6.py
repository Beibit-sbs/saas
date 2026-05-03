"""
XXXIV.6 — teaching_quality 10-step loop tests.

Covers: EVALUATION_SUBMITTED, SCORE_UPDATED, LOW_SCORE_ALERT events.
8 tests total.
"""
from __future__ import annotations

from unittest.mock import MagicMock, call, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TENANT = 42
_RECORD_ID = "rec-99"

_GOOD_PAYLOAD: dict = {
    "faculty_id": "FAC-001",
    "course_id": "CS-101",
    "term_id": "2026-S1",
    "quality_score": 85.0,
    "kpi_score": 90.0,
}

_LOW_SCORE_PAYLOAD: dict = {
    "faculty_id": "FAC-002",
    "course_id": "CS-202",
    "term_id": "2026-S1",
    "quality_score": 45.0,  # below 60.0 threshold
    "kpi_score": 55.0,
}

_ACTIVE_CONTRACT = [{"faculty_id": "FAC-001", "status": "active"}]
_ACTIVE_CONTRACT_2 = [{"faculty_id": "FAC-002", "status": "active"}]


def _make_record(payload: dict, rid: str = _RECORD_ID) -> dict:
    return {**payload, "id": rid}


# ---------------------------------------------------------------------------
# 1. create_quality_metric publishes evaluation.submitted
# ---------------------------------------------------------------------------

def test_create_quality_metric_publishes_evaluation_submitted() -> None:
    record = _make_record(_GOOD_PAYLOAD)

    with (
        patch("app.modules.teaching_quality.service.list_entities_for_tenant", return_value=_ACTIVE_CONTRACT),
        patch("app.modules.teaching_quality.service.create_teaching_quality_record", return_value=record),
        patch("app.modules.teaching_quality.service.create_entity_for_tenant"),
        patch("app.modules.teaching_quality.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        from app.modules.teaching_quality.service import create_quality_metric
        result = create_quality_metric(_GOOD_PAYLOAD, _TENANT)

    assert result["id"] == _RECORD_ID
    event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
    assert "teaching_quality.evaluation.submitted" in event_types


# ---------------------------------------------------------------------------
# 2. Low score also publishes low_score.alert
# ---------------------------------------------------------------------------

def test_create_quality_metric_low_score_publishes_alert() -> None:
    record = _make_record(_LOW_SCORE_PAYLOAD, "rec-low")

    with (
        patch("app.modules.teaching_quality.service.list_entities_for_tenant", return_value=_ACTIVE_CONTRACT_2),
        patch("app.modules.teaching_quality.service.create_teaching_quality_record", return_value=record),
        patch("app.modules.teaching_quality.service.create_entity_for_tenant"),
        patch("app.modules.teaching_quality.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        from app.modules.teaching_quality.service import create_quality_metric
        create_quality_metric(_LOW_SCORE_PAYLOAD, _TENANT)

    event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
    assert "teaching_quality.evaluation.submitted" in event_types
    assert "teaching_quality.low_score.alert" in event_types


# ---------------------------------------------------------------------------
# 3. Good score does NOT publish low_score.alert
# ---------------------------------------------------------------------------

def test_create_quality_metric_good_score_no_alert() -> None:
    record = _make_record(_GOOD_PAYLOAD)

    with (
        patch("app.modules.teaching_quality.service.list_entities_for_tenant", return_value=_ACTIVE_CONTRACT),
        patch("app.modules.teaching_quality.service.create_teaching_quality_record", return_value=record),
        patch("app.modules.teaching_quality.service.create_entity_for_tenant"),
        patch("app.modules.teaching_quality.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        from app.modules.teaching_quality.service import create_quality_metric
        create_quality_metric(_GOOD_PAYLOAD, _TENANT)

    event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
    assert "teaching_quality.low_score.alert" not in event_types


# ---------------------------------------------------------------------------
# 4. create_quality_metric creates action_log entity
# ---------------------------------------------------------------------------

def test_create_quality_metric_creates_action_log_entity() -> None:
    record = _make_record(_GOOD_PAYLOAD)

    with (
        patch("app.modules.teaching_quality.service.list_entities_for_tenant", return_value=_ACTIVE_CONTRACT),
        patch("app.modules.teaching_quality.service.create_teaching_quality_record", return_value=record),
        patch("app.modules.teaching_quality.service.create_entity_for_tenant") as mock_create,
        patch("app.modules.teaching_quality.service.EventPublisher"),
    ):
        from app.modules.teaching_quality.service import create_quality_metric
        create_quality_metric(_GOOD_PAYLOAD, _TENANT)

    entity_names = [c.args[0] for c in mock_create.call_args_list]
    assert "teaching_quality_action_logs" in entity_names


# ---------------------------------------------------------------------------
# 5. Guard blocks terminated faculty
# ---------------------------------------------------------------------------

def test_create_quality_metric_guard_blocks_terminated_faculty() -> None:
    terminated_contract = [{"faculty_id": "FAC-BAD", "status": "terminated"}]

    with (
        patch("app.modules.teaching_quality.service.list_entities_for_tenant", return_value=terminated_contract),
        patch("app.modules.teaching_quality.service.EventPublisher"),
    ):
        from app.core.module_helpers.service_validation import DomainValidationError
        from app.modules.teaching_quality.service import create_quality_metric

        payload = {**_GOOD_PAYLOAD, "faculty_id": "FAC-BAD"}
        try:
            create_quality_metric(payload, _TENANT)
            assert False, "Expected DomainValidationError"
        except DomainValidationError:
            pass


# ---------------------------------------------------------------------------
# 6. update_quality_score publishes score.updated
# ---------------------------------------------------------------------------

def test_update_quality_score_publishes_score_updated() -> None:
    updated_record = {"id": "rec-99", "faculty_id": "FAC-001", "quality_score": 75.0, "kpi_score": 80.0}

    with (
        patch("app.modules.teaching_quality.service.update_entity_for_tenant", return_value=updated_record),
        patch("app.modules.teaching_quality.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        from app.modules.teaching_quality.service import update_quality_score
        result = update_quality_score(99, {"quality_score": 75.0}, _TENANT)

    assert result["id"] == "rec-99"
    event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
    assert "teaching_quality.score.updated" in event_types


# ---------------------------------------------------------------------------
# 7. update_quality_score with low score fires alert
# ---------------------------------------------------------------------------

def test_update_quality_score_low_score_fires_alert() -> None:
    updated_record = {"id": "rec-77", "faculty_id": "FAC-001", "quality_score": 40.0, "kpi_score": 35.0}

    with (
        patch("app.modules.teaching_quality.service.update_entity_for_tenant", return_value=updated_record),
        patch("app.modules.teaching_quality.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        from app.modules.teaching_quality.service import update_quality_score
        update_quality_score(77, {"quality_score": 40.0, "kpi_score": 35.0}, _TENANT)

    event_types = [c.kwargs["event_type"] for c in mock_pub.publish_event.call_args_list]
    assert "teaching_quality.score.updated" in event_types
    assert "teaching_quality.low_score.alert" in event_types


# ---------------------------------------------------------------------------
# 8. EventPublisher failure on create does NOT block metric creation
# ---------------------------------------------------------------------------

def test_create_quality_metric_survives_event_publisher_failure() -> None:
    record = _make_record(_GOOD_PAYLOAD)

    with (
        patch("app.modules.teaching_quality.service.list_entities_for_tenant", return_value=_ACTIVE_CONTRACT),
        patch("app.modules.teaching_quality.service.create_teaching_quality_record", return_value=record),
        patch("app.modules.teaching_quality.service.create_entity_for_tenant"),
        patch("app.modules.teaching_quality.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_pub.publish_event.side_effect = RuntimeError("broker down")
        mock_cls.return_value = mock_pub

        from app.modules.teaching_quality.service import create_quality_metric
        result = create_quality_metric(_GOOD_PAYLOAD, _TENANT)

    assert result["faculty_id"] == "FAC-001"
