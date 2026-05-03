"""LXXXVI — Scholarship service hardening tests.

Focus:
1) Persist alert projection before event publication.
2) Fire-and-forget event publication (no rollback of persisted side effects).
3) Idempotent alert creation for repeated checks.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.modules.scholarship import service as svc


def _at_risk_payload() -> dict[str, object]:
    return {
        "award_code": "AWD-001",
        "student_id": "STU-1",
        "scholarship_type": "merit",
        "status": "active",
        "amount": 1000.0,
        "gpa_threshold": 3.0,
        "current_gpa": 2.2,
    }


def test_create_scholarship_award_at_risk_persists_alert_then_emits_event() -> None:
    created_entities: list[str] = []

    def _create(entity_type: str, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
        created_entities.append(entity_type)
        if entity_type == "scholarship_awards":
            return {"id": 11, **payload}
        return {"id": 21, **payload}

    with (
        patch("app.modules.scholarship.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.scholarship.service.list_entities_for_tenant", return_value=[]),
        patch("app.modules.scholarship.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_cls.return_value = mock_pub

        result = svc.create_scholarship_award(_at_risk_payload(), tenant_id=1)

    assert result["at_risk"] is True
    assert created_entities == ["scholarship_awards", "scholarship_revocation_alerts"]
    mock_pub.publish_event.assert_called()


def test_create_scholarship_award_survives_event_failure_with_persisted_alert() -> None:
    created_entities: list[str] = []

    def _create(entity_type: str, payload: dict[str, object], tenant_id: int) -> dict[str, object]:
        created_entities.append(entity_type)
        if entity_type == "scholarship_awards":
            return {"id": 31, **payload}
        return {"id": 41, **payload}

    with (
        patch("app.modules.scholarship.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.scholarship.service.list_entities_for_tenant", return_value=[]),
        patch("app.modules.scholarship.service.EventPublisher") as mock_cls,
    ):
        mock_pub = MagicMock()
        mock_pub.publish_event.side_effect = RuntimeError("broker down")
        mock_cls.return_value = mock_pub

        result = svc.create_scholarship_award(_at_risk_payload(), tenant_id=1)

    assert result["id"] == 31
    assert result["at_risk"] is True
    assert "scholarship_revocation_alerts" in created_entities


def test_ensure_revocation_alert_record_idempotent_when_existing() -> None:
    existing = [
        {
            "integration_source": "scholarship_revocation_queue",
            "source_entity_id": "99",
        }
    ]

    with (
        patch("app.modules.scholarship.service.list_entities_for_tenant", return_value=existing),
        patch("app.modules.scholarship.service.create_entity_for_tenant") as mock_create,
        patch("app.modules.scholarship.service.EventPublisher") as mock_cls,
    ):
        svc._ensure_revocation_alert_record(award_id=99, tenant_id=1)

    mock_create.assert_not_called()
    mock_cls.assert_not_called()


def test_create_scholarship_award_non_risk_does_not_emit_or_create_alert() -> None:
    payload = _at_risk_payload()
    payload["current_gpa"] = 3.5

    with (
        patch(
            "app.modules.scholarship.service.create_entity_for_tenant",
            return_value={"id": 51, **payload},
        ) as mock_create,
        patch("app.modules.scholarship.service.list_entities_for_tenant", return_value=[]),
        patch("app.modules.scholarship.service.EventPublisher") as mock_cls,
    ):
        result = svc.create_scholarship_award(payload, tenant_id=1)

    assert result["at_risk"] is False
    mock_cls.assert_not_called()
    mock_create.assert_called_once_with("scholarship_awards", payload, 1)
