"""XCIX - Research Ethics Service Hardening (canonical 10-step hooks).

Verifies:
1. create_ethics_review uses canonical EventPublisher constructor and records metric.
2. update_ethics_review_status uses canonical EventPublisher constructor and records metric.
3. create_ethics_review survives outcome hook failure and still records metric.
4. update_ethics_review_status rejects invalid transition (guard fail-closed).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.research_ethics import service as svc
from app.modules.research_ethics.schemas import EthicsReviewStatusUpdateSchema

MODULE = "app.modules.research_ethics.service"


def _review(*, review_id: int = 101, status: str = "pending") -> dict[str, object]:
    return {
        "id": review_id,
        "review_code": "IRB-101",
        "project_title": "Safety Study",
        "principal_investigator_id": "PI-001",
        "review_type": "irb",
        "status": status,
        "risk_level": "low",
        "tenant_id": 1,
    }


def _active_contracts() -> list[dict[str, object]]:
    return [{"faculty_id": "PI-001", "status": "active"}]


def test_create_ethics_review_uses_canonical_event_publisher_and_metric() -> None:
    metrics: list[tuple[int, str, int]] = []

    def _capture_metric(tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    def _list(entity: str, tenant_id: int) -> list[dict[str, object]]:
        if entity == "faculty_contracts":
            return _active_contracts()
        if entity == "ethics_reviews":
            return []
        if entity == "ethics_alert_records":
            return []
        return []

    with (
        patch(f"{MODULE}.list_entities_for_tenant", side_effect=_list),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_review()),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}._metric", side_effect=_capture_metric),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        result = svc.create_ethics_review(
            {
                "review_code": "IRB-101",
                "project_title": "Safety Study",
                "principal_investigator_id": "PI-001",
                "review_type": "irb",
                "status": "pending",
                "risk_level": "low",
            },
            tenant_id=1,
            actor="admin@test.com",
        )

    assert int(result["id"]) == 101
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "research_ethics_reviews_created", 1) in metrics


def test_update_ethics_review_status_uses_canonical_event_publisher_and_metric() -> None:
    # pending → rejected is an allowed transition and fires a lifecycle event
    metrics: list[tuple[int, str, int]] = []

    def _capture_metric(tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[_review(status="pending")]),
        patch(f"{MODULE}.update_entity_for_tenant", return_value=_review(status="rejected")),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}._metric", side_effect=_capture_metric),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        result = svc.update_ethics_review_status(
            tenant_id=1,
            review_id=101,
            request=EthicsReviewStatusUpdateSchema(status="rejected"),
            actor="admin@test.com",
        )

    assert str(result["status"]).lower() == "rejected"
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "research_ethics_review_status_updates", 1) in metrics


def test_create_ethics_review_survives_outcome_failure_and_records_metric() -> None:
    metrics: list[tuple[int, str, int]] = []

    def _capture_metric(tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    def _list(entity: str, tenant_id: int) -> list[dict[str, object]]:
        if entity == "faculty_contracts":
            return _active_contracts()
        if entity == "ethics_reviews":
            return []
        if entity == "ethics_alert_records":
            return []
        return []

    with (
        patch(f"{MODULE}.list_entities_for_tenant", side_effect=_list),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_review()),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}._metric", side_effect=_capture_metric),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
    ):
        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        result = svc.create_ethics_review(
            {
                "review_code": "IRB-101",
                "project_title": "Safety Study",
                "principal_investigator_id": "PI-001",
                "review_type": "irb",
                "status": "pending",
                "risk_level": "low",
            },
            tenant_id=1,
            actor="admin@test.com",
        )

    assert int(result["id"]) == 101
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "research_ethics_reviews_created", 1) in metrics


def test_update_ethics_review_status_rejects_invalid_transition_fail_closed() -> None:
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_review(status="pending")]):
        with pytest.raises(ValueError, match="not allowed"):
            svc.update_ethics_review_status(
                tenant_id=1,
                review_id=101,
                request=EthicsReviewStatusUpdateSchema(status="approved"),
                actor="admin@test.com",
            )
