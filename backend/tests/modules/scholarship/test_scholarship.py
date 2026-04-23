"""Phase VIII-1: Scholarship module tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.scholarship import service as sc_service
from tests.conftest import ADMIN_HEADERS, client as test_client


def test_list_scholarship_applications_empty(monkeypatch) -> None:
    monkeypatch.setattr(sc_service, "list_entities_for_tenant", lambda name, tid: [])
    assert sc_service.list_scholarship_applications(tenant_id=1) == []


def test_list_scholarship_applications_filter_by_status(monkeypatch) -> None:
    rows = [
        {"id": 1, "application_code": "APP-001", "student_id": "STU-1", "scholarship_type": "merit", "status": "pending", "gpa": 3.8, "requested_amount": 5000.0, "tenant_id": 1},
        {"id": 2, "application_code": "APP-002", "student_id": "STU-2", "scholarship_type": "need", "status": "approved", "gpa": 3.2, "requested_amount": 3000.0, "tenant_id": 1},
    ]
    monkeypatch.setattr(sc_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = sc_service.list_scholarship_applications(tenant_id=1, status="pending")
    assert len(result) == 1
    assert result[0]["application_code"] == "APP-001"


def test_list_scholarship_applications_filter_by_type(monkeypatch) -> None:
    rows = [
        {"id": 1, "application_code": "APP-001", "student_id": "STU-1", "scholarship_type": "merit", "status": "pending", "gpa": 3.8, "requested_amount": 5000.0, "tenant_id": 1},
        {"id": 2, "application_code": "APP-002", "student_id": "STU-2", "scholarship_type": "need", "status": "approved", "gpa": 3.2, "requested_amount": 3000.0, "tenant_id": 1},
    ]
    monkeypatch.setattr(sc_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = sc_service.list_scholarship_applications(tenant_id=1, scholarship_type="need")
    assert len(result) == 1
    assert result[0]["application_code"] == "APP-002"


def test_is_award_at_risk_by_gpa(monkeypatch) -> None:
    row = {"current_gpa": 2.0, "gpa_threshold": 2.5, "status": "active"}
    assert sc_service._is_award_at_risk(row) is True


def test_is_award_at_risk_by_status(monkeypatch) -> None:
    row = {"current_gpa": 3.0, "gpa_threshold": 2.5, "status": "at_risk"}
    assert sc_service._is_award_at_risk(row) is True


def test_is_award_not_at_risk(monkeypatch) -> None:
    row = {"current_gpa": 3.0, "gpa_threshold": 2.5, "status": "active"}
    assert sc_service._is_award_at_risk(row) is False


def test_create_scholarship_award_at_risk_fires_signal(monkeypatch) -> None:
    payload = {
        "award_code": "AWD-001",
        "student_id": "STU-1",
        "scholarship_type": "merit",
        "status": "active",
        "amount": 5000.0,
        "gpa_threshold": 2.5,
        "current_gpa": 2.0,
    }
    created = {"id": 10, "award_code": "AWD-001", "student_id": "STU-1", "current_gpa": 2.0, "gpa_threshold": 2.5, "status": "active", "tenant_id": 1}
    monkeypatch.setattr(sc_service, "create_entity_for_tenant", lambda name, p, tid: created)

    with patch("app.modules.scholarship.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        result = sc_service.create_scholarship_award(payload, tenant_id=1)

    assert result["at_risk"] is True
    publisher.publish_event.assert_called_once()
    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "scholarship.award.at_risk_detected"
    assert call_kwargs["payload_json"]["award_code"] == "AWD-001"


def test_create_scholarship_award_healthy_no_signal(monkeypatch) -> None:
    payload = {
        "award_code": "AWD-002",
        "student_id": "STU-2",
        "scholarship_type": "merit",
        "status": "active",
        "amount": 5000.0,
        "gpa_threshold": 2.5,
        "current_gpa": 3.8,
    }
    created = {"id": 11, "award_code": "AWD-002", "student_id": "STU-2", "current_gpa": 3.8, "gpa_threshold": 2.5, "status": "active", "tenant_id": 1}
    monkeypatch.setattr(sc_service, "create_entity_for_tenant", lambda name, p, tid: created)

    with patch("app.modules.scholarship.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        result = sc_service.create_scholarship_award(payload, tenant_id=1)

    assert result["at_risk"] is False
    publisher.publish_event.assert_not_called()


def test_get_scholarship_brain_context_healthy(monkeypatch) -> None:
    applications = [
        {"id": 1, "status": "approved", "tenant_id": 1},
        {"id": 2, "status": "approved", "tenant_id": 1},
    ]
    awards = [
        {"id": 1, "current_gpa": 3.5, "gpa_threshold": 2.5, "status": "active"},
        {"id": 2, "current_gpa": 3.2, "gpa_threshold": 2.5, "status": "active"},
    ]

    def fake_list(name: str, tid: int) -> list:
        if name == "scholarship_applications":
            return applications
        return awards

    monkeypatch.setattr(sc_service, "list_entities_for_tenant", fake_list)
    ctx = sc_service.get_scholarship_brain_context(tenant_id=1)
    assert ctx["retention_health"] == "healthy"
    assert ctx["at_risk_rate"] == 0.0


def test_get_scholarship_brain_context_critical(monkeypatch) -> None:
    applications = [{"id": 1, "status": "pending", "tenant_id": 1}]
    awards = [
        {"id": 1, "current_gpa": 2.0, "gpa_threshold": 2.5, "status": "active"},
        {"id": 2, "current_gpa": 2.1, "gpa_threshold": 2.5, "status": "active"},
        {"id": 3, "current_gpa": 3.5, "gpa_threshold": 2.5, "status": "active"},
        {"id": 4, "current_gpa": 3.8, "gpa_threshold": 2.5, "status": "active"},
    ]

    def fake_list(name: str, tid: int) -> list:
        if name == "scholarship_applications":
            return applications
        return awards

    monkeypatch.setattr(sc_service, "list_entities_for_tenant", fake_list)
    ctx = sc_service.get_scholarship_brain_context(tenant_id=1)
    assert ctx["retention_health"] == "critical"
    assert ctx["at_risk_awards"] == 2
