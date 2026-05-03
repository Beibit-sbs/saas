"""XXXIV.7 — research_ethics: 10-step loop event hardening tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.research_ethics import service as svc

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ACTIVE_CONTRACT = [{"faculty_id": "PI-001", "status": "active"}]
_ACTIVE_FACULTY = [{"faculty_id": "PI-001", "status": "active"}]

_REVIEW_PAYLOAD: dict[str, object] = {
    "principal_investigator_id": "PI-001",
    "review_type": "irb",
    "risk_level": "low",
    "status": "pending",
    "title": "Test Study",
}


def _make_entity_store(initial: list[dict] | None = None) -> list[dict]:
    return list(initial or [])


# ---------------------------------------------------------------------------
# 1. create_ethics_review publishes submission.created
# ---------------------------------------------------------------------------

def test_create_ethics_review_publishes_submission_created() -> None:
    store: list[dict] = []

    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        record = {**payload, "id": 1}
        store.append(record)
        return record

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "faculty_contracts":
            return _ACTIVE_CONTRACT
        return store

    with (
        patch("app.modules.research_ethics.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.research_ethics.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        result = svc.create_ethics_review(_REVIEW_PAYLOAD.copy(), tenant_id=1)

    assert result["id"] == 1
    event_types = [c.args[0] for c in mock_pub.publish_event.call_args_list]
    assert "research_ethics.submission.created" in event_types


# ---------------------------------------------------------------------------
# 2. High-risk review fires high_risk_flagged event
# ---------------------------------------------------------------------------

def test_create_ethics_review_high_risk_fires_high_risk_flagged() -> None:
    store: list[dict] = []

    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        record = {**payload, "id": 2}
        store.append(record)
        return record

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "faculty_contracts":
            return _ACTIVE_CONTRACT
        return store

    payload = {**_REVIEW_PAYLOAD, "risk_level": "high"}

    with (
        patch("app.modules.research_ethics.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.research_ethics.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.create_ethics_review(payload, tenant_id=1)

    event_types = [c.args[0] for c in mock_pub.publish_event.call_args_list]
    assert "research_ethics.submission.created" in event_types
    assert "research_ethics.review.high_risk_flagged" in event_types


# ---------------------------------------------------------------------------
# 3. Low-risk review does NOT fire high_risk_flagged event
# ---------------------------------------------------------------------------

def test_create_ethics_review_low_risk_no_high_risk_event() -> None:
    store: list[dict] = []

    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        record = {**payload, "id": 3}
        store.append(record)
        return record

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "faculty_contracts":
            return _ACTIVE_CONTRACT
        return store

    payload = {**_REVIEW_PAYLOAD, "risk_level": "low"}

    with (
        patch("app.modules.research_ethics.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.research_ethics.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.create_ethics_review(payload, tenant_id=1)

    event_types = [c.args[0] for c in mock_pub.publish_event.call_args_list]
    assert "research_ethics.review.high_risk_flagged" not in event_types


# ---------------------------------------------------------------------------
# 4. Action log entity created on submission
# ---------------------------------------------------------------------------

def test_create_ethics_review_creates_action_log_entity() -> None:
    created_entities: list[str] = []

    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        created_entities.append(entity_type)
        return {**payload, "id": 4}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "faculty_contracts":
            return _ACTIVE_CONTRACT
        return []

    with (
        patch("app.modules.research_ethics.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.research_ethics.service.EventPublisher"),
    ):
        svc.create_ethics_review(_REVIEW_PAYLOAD.copy(), tenant_id=1)

    assert "research_ethics_action_logs" in created_entities


# ---------------------------------------------------------------------------
# 5. Guard blocks PI with no active contract
# ---------------------------------------------------------------------------

def test_create_ethics_review_guard_blocks_terminated_pi() -> None:
    terminated_contract = [{"faculty_id": "PI-001", "status": "terminated"}]

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "faculty_contracts":
            return terminated_contract
        return []

    with (
        patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.research_ethics.service.create_entity_for_tenant"),
        patch("app.modules.research_ethics.service.EventPublisher"),
    ):
        with pytest.raises(DomainValidationError):
            svc.create_ethics_review(_REVIEW_PAYLOAD.copy(), tenant_id=1)


# ---------------------------------------------------------------------------
# 6. update_ethics_review_status approved → fires review.approved
# ---------------------------------------------------------------------------

def test_update_ethics_review_status_approved_fires_approved_event() -> None:
    from app.modules.research_ethics.schemas import EthicsReviewStatusUpdateSchema

    existing = {"id": 10, "status": "under_review",
                "principal_investigator_id": "PI-001",
                "review_type": "irb", "risk_level": "low", "tenant_id": 1}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "ethics_reviews":
            return [existing]
        if entity_type == "faculty":
            return _ACTIVE_FACULTY
        if entity_type == "faculty_contracts":
            return _ACTIVE_CONTRACT
        return []

    def _update(entity_type: str, entity_id: int, payload: dict, tenant_id: int) -> dict:
        return {**payload, "id": entity_id}

    request = EthicsReviewStatusUpdateSchema(status="approved")

    with (
        patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.research_ethics.service.update_entity_for_tenant", side_effect=_update),
        patch("app.modules.research_ethics.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.update_ethics_review_status(tenant_id=1, review_id=10, request=request)

    event_types = [c.args[0] for c in mock_pub.publish_event.call_args_list]
    assert "research_ethics.review.approved" in event_types


# ---------------------------------------------------------------------------
# 7. update_ethics_review_status rejected → fires review.rejected
# ---------------------------------------------------------------------------

def test_update_ethics_review_status_rejected_fires_rejected_event() -> None:
    from app.modules.research_ethics.schemas import EthicsReviewStatusUpdateSchema

    existing = {"id": 11, "status": "under_review",
                "principal_investigator_id": "PI-001",
                "review_type": "irb", "risk_level": "low", "tenant_id": 1}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "ethics_reviews":
            return [existing]
        return []

    def _update(entity_type: str, entity_id: int, payload: dict, tenant_id: int) -> dict:
        return {**payload, "id": entity_id}

    request = EthicsReviewStatusUpdateSchema(status="rejected")

    with (
        patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.research_ethics.service.update_entity_for_tenant", side_effect=_update),
        patch("app.modules.research_ethics.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        svc.update_ethics_review_status(tenant_id=1, review_id=11, request=request)

    event_types = [c.args[0] for c in mock_pub.publish_event.call_args_list]
    assert "research_ethics.review.rejected" in event_types


# ---------------------------------------------------------------------------
# 8. EventPublisher failure does not block submission
# ---------------------------------------------------------------------------

def test_create_ethics_review_survives_event_publisher_failure() -> None:
    def _create(entity_type: str, payload: dict, tenant_id: int) -> dict:
        return {**payload, "id": 99}

    def _list(entity_type: str, tenant_id: int) -> list[dict]:
        if entity_type == "faculty_contracts":
            return _ACTIVE_CONTRACT
        return []

    with (
        patch("app.modules.research_ethics.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.research_ethics.service.list_entities_for_tenant", side_effect=_list),
        patch("app.modules.research_ethics.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_pub.publish_event.side_effect = RuntimeError("broker down")
        mock_cls.return_value = mock_pub

        result = svc.create_ethics_review(_REVIEW_PAYLOAD.copy(), tenant_id=1)

    assert result["id"] == 99
