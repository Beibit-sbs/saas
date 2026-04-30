"""Phase VI-VI1: Security operations module tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.security_operations import service as security_service
from tests.conftest import ADMIN_HEADERS, client as test_client


def test_list_security_incidents_empty(monkeypatch) -> None:
    monkeypatch.setattr(security_service, "list_entities_for_tenant", lambda name, tid: [])
    assert security_service.list_security_incidents(tenant_id=1) == []


def test_list_security_incidents_filter_by_severity(monkeypatch) -> None:
    rows = [
        {
            "id": 1,
            "incident_code": "INC-1",
            "facility_code": "BLDG-A",
            "category": "badge_forced_open",
            "severity": "high",
            "status": "open",
            "tenant_id": 1,
        },
        {
            "id": 2,
            "incident_code": "INC-2",
            "facility_code": "BLDG-B",
            "category": "visitor_delay",
            "severity": "low",
            "status": "closed",
            "tenant_id": 1,
        },
    ]
    monkeypatch.setattr(security_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = security_service.list_security_incidents(tenant_id=1, severity="high")
    assert len(result) == 1
    assert result[0]["incident_code"] == "INC-1"


def test_create_security_incident_high_severity_fires_signal(monkeypatch) -> None:
    created = {
        "id": 10,
        "incident_code": "INC-10",
        "facility_code": "BLDG-C",
        "category": "unauthorized_access",
        "severity": "critical",
        "status": "open",
        "reported_at": None,
        "description": None,
        "visitor_id": None,
        "access_control_event_id": "ACE-1",
        "integration_source": "acs",
        "tenant_id": 1,
    }
    monkeypatch.setattr(security_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.security_operations.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = security_service.create_security_incident(
            {
                "incident_code": "INC-10",
                "facility_code": "BLDG-C",
                "category": "unauthorized_access",
                "severity": "critical",
                "status": "open",
            },
            tenant_id=1,
        )

    assert record["id"] == 10
    publisher.publish_event.assert_called_once()
    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "campus.security_incident.detected"
    assert call_kwargs["payload_json"]["issue_type"] == "unauthorized_access"


def test_create_security_incident_low_severity_no_signal(monkeypatch) -> None:
    created = {
        "id": 11,
        "incident_code": "INC-11",
        "facility_code": "BLDG-D",
        "category": "visitor_delay",
        "severity": "low",
        "status": "open",
        "reported_at": None,
        "description": None,
        "visitor_id": None,
        "access_control_event_id": None,
        "integration_source": None,
        "tenant_id": 1,
    }
    monkeypatch.setattr(security_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.security_operations.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        security_service.create_security_incident(
            {
                "incident_code": "INC-11",
                "facility_code": "BLDG-D",
                "category": "visitor_delay",
                "severity": "low",
                "status": "open",
            },
            tenant_id=1,
        )

    publisher.publish_event.assert_not_called()


def test_get_security_operations_brain_context_high_risk(monkeypatch) -> None:
    incidents = [
        {
            "id": 1,
            "incident_code": "INC-1",
            "facility_code": "BLDG-A",
            "category": "unauthorized_access",
            "severity": "critical",
            "status": "open",
            "tenant_id": 3,
        }
    ]
    visitors = [
        {
            "id": 1,
            "visitor_name": "Alex Doe",
            "host_faculty_id": "FAC-1",
            "visit_purpose": "delivery",
            "status": "checked_in",
            "access_status": "denied",
            "badge_id": None,
            "check_in_at": None,
            "check_out_at": None,
            "access_control_event_id": "ACE-77",
            "tenant_id": 3,
        },
        {
            "id": 2,
            "visitor_name": "Sam Doe",
            "host_faculty_id": "FAC-2",
            "visit_purpose": "meeting",
            "status": "expected",
            "access_status": "denied",
            "badge_id": None,
            "check_in_at": None,
            "check_out_at": None,
            "access_control_event_id": "ACE-78",
            "tenant_id": 3,
        },
    ]

    def fake_list(name: str, tid: int) -> list[dict[str, object]]:
        if name == "security_incidents":
            return incidents
        return visitors

    monkeypatch.setattr(security_service, "list_entities_for_tenant", fake_list)
    ctx = security_service.get_security_operations_brain_context(tenant_id=3)
    assert ctx["critical_incidents"] == 1
    assert ctx["denied_access_events"] == 2
    assert ctx["risk_level"] == "high"


def test_http_list_security_incidents_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.security_operations.service.list_security_incidents",
        lambda tenant_id, severity=None, status=None: [],
    )
    resp = test_client.get("/api/admin/security-operations/incidents", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    assert resp.json()["records"] == []


def test_http_create_security_incident(monkeypatch: pytest.MonkeyPatch) -> None:
    created = {
        "id": 21,
        "incident_code": "INC-21",
        "facility_code": "BLDG-X",
        "category": "unauthorized_access",
        "severity": "high",
        "status": "open",
        "reported_at": None,
        "description": None,
        "visitor_id": None,
        "access_control_event_id": "ACE-21",
        "integration_source": "acs",
        "tenant_id": 1,
    }
    monkeypatch.setattr(
        "app.modules.security_operations.service.create_security_incident",
        lambda payload, tenant_id: created,
    )
    resp = test_client.post(
        "/api/admin/security-operations/incidents",
        json={
            "incident_code": "INC-21",
            "facility_code": "BLDG-X",
            "category": "unauthorized_access",
            "severity": "high",
            "status": "open",
        },
        headers=dict(ADMIN_HEADERS),
    )
    assert resp.status_code == 201
    assert resp.json()["record"]["incident_code"] == "INC-21"


def test_http_get_security_operations_brain_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.security_operations.service.get_security_operations_brain_context",
        lambda tenant_id: {
            "module": "security_operations",
            "tenant_id": 1,
            "total_incidents": 2,
            "open_incidents": 1,
            "critical_incidents": 1,
            "total_visitors": 3,
            "active_visitors": 1,
            "denied_access_events": 1,
            "risk_level": "high",
        },
    )
    resp = test_client.get("/api/admin/security-operations/brain-context", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    assert resp.json()["module"] == "security_operations"
    assert resp.json()["risk_level"] == "high"
