"""Phase XCI — AI Admissions Scoring service hardening tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.modules.ai_admissions_scoring import service as svc


def _scoring() -> dict:
    return {
        "id": "score-1",
        "application_id": "app-1",
        "gpa": 3.8,
        "test_score": 95,
        "essay_length": 2500,
        "score": None,
        "status": "PENDING",
        "tenant_id": 7,
    }


def test_submit_for_scoring_persists_before_event() -> None:
    """Verify persistence happens before event is fired."""
    call_order: list[str] = []

    def mock_create(*args: object, **kwargs: object) -> dict:  # type: ignore[no-untyped-def]
        call_order.append("persist")
        return {"id": "score-1", **_scoring()}

    captured_event: dict[str, object] = {}

    class _Publisher:
        def publish_event(self, **kwargs: object) -> None:  # type: ignore[no-untyped-def]
            call_order.append("event")
            captured_event.update(kwargs)

    with (
        patch(
            "app.modules.ai_admissions_scoring.service.create_entity_for_tenant",
            side_effect=mock_create,
        ),
        patch("app.modules.ai_admissions_scoring.service.EventPublisher", _Publisher),
    ):
        result = svc.submit_for_scoring(
            7,
            application_id="app-1",
            gpa=3.8,
            test_score=95,
            essay_length=2500,
        )

    assert result["scoring_id"] == "score-1"
    assert call_order == ["persist", "event"]
    assert captured_event["aggregate_type"] == "admissions_scoring"
    assert captured_event["aggregate_id"] == "score-1"


def test_submit_for_scoring_survives_publish_failure() -> None:
    """Verify function succeeds even if event publishing fails."""

    class _Publisher:
        def publish_event(self, **kwargs: object) -> None:  # type: ignore[no-untyped-def]
            raise RuntimeError("broker down")

    with (
        patch(
            "app.modules.ai_admissions_scoring.service.create_entity_for_tenant",
            return_value={**_scoring(), "id": "score-2"},
        ) as mock_create,
        patch("app.modules.ai_admissions_scoring.service.EventPublisher", _Publisher),
    ):
        result = svc.submit_for_scoring(
            7,
            application_id="app-1",
            gpa=3.8,
            test_score=95,
            essay_length=2500,
        )

    assert result["scoring_id"] == "score-2"
    assert result["status"] == "PENDING"


def test_generate_score_uses_canonical_tenant_api_and_persists() -> None:
    """Verify canonical positional args and event firing with aggregate_id."""
    mock_create = MagicMock()
    mock_list = MagicMock(return_value=[_scoring()])
    captured_calls: dict = {}

    class _Publisher:
        def publish_event(self, **kwargs: object) -> None:  # type: ignore[no-untyped-def]
            captured_calls["publish"] = kwargs

    with (
        patch(
            "app.modules.ai_admissions_scoring.service.create_entity_for_tenant",
            mock_create,
        ),
        patch(
            "app.modules.ai_admissions_scoring.service.list_entities_for_tenant",
            mock_list,
        ) as mock_list_ref,
        patch("app.modules.ai_admissions_scoring.service.EventPublisher", _Publisher),
    ):
        result = svc.generate_score(7, scoring_id="score-1")

    assert result["scoring_id"] == "score-1"
    assert result["status"] == "SCORED"
    mock_list_ref.assert_called_once_with("admissions_scorings", 7)
    assert "publish" in captured_calls
    assert captured_calls["publish"]["aggregate_type"] == "admissions_scoring"
    assert captured_calls["publish"]["aggregate_id"] == "score-1"


def test_approve_scoring_outcome_failure_does_not_rollback_status() -> None:
    """Verify status persists even if brain outcome recording fails."""
    scoring_data = _scoring()
    scoring_data["status"] = "SCORED"

    class _BrainCore:
        def record_dispatch_outcome(self, *args: object, **kwargs: object) -> dict:  # type: ignore[no-untyped-def]
            raise RuntimeError("brain unavailable")

    with (
        patch(
            "app.modules.ai_admissions_scoring.service.list_entities_for_tenant",
            return_value=[scoring_data],
        ),
        patch("app.modules.ai_admissions_scoring.service.EventPublisher"),
        patch("app.modules.brain_core.service.brain_core_service", _BrainCore()),
    ):
        result = svc.approve_scoring(7, scoring_id="score-1")

    assert result["scoring_id"] == "score-1"
    assert result["status"] == "APPROVED"
    assert scoring_data["status"] == "APPROVED"
