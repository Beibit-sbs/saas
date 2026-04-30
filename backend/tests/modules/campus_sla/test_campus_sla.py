"""Phase VI-VI3: Campus SLA module tests."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.campus_sla import service as sla_service
from tests.conftest import ADMIN_HEADERS, client as test_client


def test_list_sla_records_empty(monkeypatch) -> None:
    monkeypatch.setattr(sla_service, "list_entities_for_tenant", lambda name, tid: [])
    assert sla_service.list_sla_records(tenant_id=1) == []


def test_list_sla_records_filter_by_status(monkeypatch) -> None:
    rows = [
        {
            "id": 1,
            "service_type": "wifi",
            "facility_code": "BLDG-A",
            "target_sla_minutes": 60,
            "actual_minutes": 30,
            "status": "resolved",
            "tenant_id": 1,
        },
        {
            "id": 2,
            "service_type": "elevator",
            "facility_code": "BLDG-B",
            "target_sla_minutes": 120,
            "actual_minutes": None,
            "status": "open",
            "tenant_id": 1,
        },
    ]
    monkeypatch.setattr(sla_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = sla_service.list_sla_records(tenant_id=1, status="open")
    assert len(result) == 1
    assert result[0]["service_type"] == "elevator"


def test_list_sla_records_filter_by_service_type(monkeypatch) -> None:
    rows = [
        {
            "id": 1,
            "service_type": "wifi",
            "facility_code": "BLDG-A",
            "target_sla_minutes": 60,
            "actual_minutes": 90,
            "status": "breached",
            "tenant_id": 1,
        },
        {
            "id": 2,
            "service_type": "hvac",
            "facility_code": "BLDG-C",
            "target_sla_minutes": 240,
            "actual_minutes": None,
            "status": "open",
            "tenant_id": 1,
        },
    ]
    monkeypatch.setattr(sla_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = sla_service.list_sla_records(tenant_id=1, service_type="wifi")
    assert len(result) == 1
    assert result[0]["id"] == 1


def test_create_sla_record_breach_fires_signal(monkeypatch) -> None:
    """When actual_minutes > target_sla_minutes the breach event is published."""
    created = {
        "id": 10,
        "service_type": "wifi",
        "facility_code": "BLDG-A",
        "target_sla_minutes": 60,
        "actual_minutes": 120,
        "status": "open",
        "reported_at": None,
        "resolved_at": None,
        "description": None,
        "integration_source": "helpdesk",
        "tenant_id": 1,
    }
    monkeypatch.setattr(
        sla_service,
        "list_entities_for_tenant",
        lambda name, tid: (
            [{"facility_code": "BLDG-A", "status": "open"}] if name == "facilities_maintenance_requests" else []
        ),
    )
    monkeypatch.setattr(sla_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.campus_sla.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = sla_service.create_sla_record(
            {
                "service_type": "wifi",
                "facility_code": "BLDG-A",
                "target_sla_minutes": 60,
                "actual_minutes": 120,
                "status": "open",
            },
            tenant_id=1,
        )

    assert record["id"] == 10
    assert record["breached"] is True
    publisher.publish_event.assert_called_once()
    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "campus.sla.breach_detected"
    assert call_kwargs["payload_json"]["service_type"] == "wifi"


def test_create_sla_record_no_breach_no_signal(monkeypatch) -> None:
    """When actual_minutes <= target_sla_minutes no event is published."""
    created = {
        "id": 11,
        "service_type": "elevator",
        "facility_code": "BLDG-B",
        "target_sla_minutes": 120,
        "actual_minutes": 60,
        "status": "resolved",
        "reported_at": None,
        "resolved_at": None,
        "description": None,
        "integration_source": None,
        "tenant_id": 2,
    }
    monkeypatch.setattr(
        sla_service,
        "list_entities_for_tenant",
        lambda name, tid: (
            [{"facility_code": "BLDG-B", "status": "open"}] if name == "facilities_maintenance_requests" else []
        ),
    )
    monkeypatch.setattr(sla_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.campus_sla.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = sla_service.create_sla_record(
            {"service_type": "elevator", "facility_code": "BLDG-B", "target_sla_minutes": 120, "actual_minutes": 60, "status": "resolved"},
            tenant_id=2,
        )

    assert record["breached"] is False
    publisher.publish_event.assert_not_called()


def test_get_campus_sla_brain_context_high_breach(monkeypatch) -> None:
    rows = [
        {"id": 1, "service_type": "wifi", "facility_code": "BLDG-A", "target_sla_minutes": 60, "actual_minutes": 180, "status": "breached", "tenant_id": 3},
        {"id": 2, "service_type": "hvac", "facility_code": "BLDG-B", "target_sla_minutes": 120, "actual_minutes": 300, "status": "open", "tenant_id": 3},
        {"id": 3, "service_type": "elevator", "facility_code": "BLDG-C", "target_sla_minutes": 60, "actual_minutes": 10, "status": "resolved", "tenant_id": 3},
    ]
    monkeypatch.setattr(sla_service, "list_entities_for_tenant", lambda name, tid: rows)
    ctx = sla_service.get_campus_sla_brain_context(tenant_id=3)
    assert ctx["total_records"] == 3
    assert ctx["breached_records"] == 2
    assert ctx["open_records"] == 1
    assert ctx["resolved_records"] == 1
    assert ctx["compliance_level"] == "low"


def test_get_campus_sla_brain_context_empty(monkeypatch) -> None:
    monkeypatch.setattr(sla_service, "list_entities_for_tenant", lambda name, tid: [])
    ctx = sla_service.get_campus_sla_brain_context(tenant_id=1)
    assert ctx["total_records"] == 0
    assert ctx["breach_rate"] == 0.0
    assert ctx["compliance_level"] == "high"


def test_http_list_sla_records_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.campus_sla.service.list_sla_records",
        lambda tenant_id, status=None, service_type=None: [],
    )
    resp = test_client.get("/api/admin/campus-sla/sla-records", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    assert resp.json()["records"] == []


def test_http_create_sla_record(monkeypatch: pytest.MonkeyPatch) -> None:
    created = {
        "id": 21,
        "service_type": "cleaning",
        "facility_code": "BLDG-Z",
        "target_sla_minutes": 480,
        "actual_minutes": 600,
        "status": "breached",
        "reported_at": None,
        "resolved_at": None,
        "description": None,
        "integration_source": None,
        "tenant_id": 1,
        "breached": True,
    }
    monkeypatch.setattr(
        "app.modules.campus_sla.service.create_sla_record",
        lambda payload, tenant_id: created,
    )
    resp = test_client.post(
        "/api/admin/campus-sla/sla-records",
        json={
            "service_type": "cleaning",
            "facility_code": "BLDG-Z",
            "target_sla_minutes": 480,
            "actual_minutes": 600,
            "status": "breached",
        },
        headers=dict(ADMIN_HEADERS),
    )
    assert resp.status_code == 201
    data = resp.json()["record"]
    assert data["id"] == 21
    assert data["breached"] is True


def test_http_brain_context(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = {
        "module": "campus_sla",
        "tenant_id": 1,
        "total_records": 5,
        "open_records": 2,
        "resolved_records": 2,
        "breached_records": 1,
        "breach_rate": 0.2,
        "compliance_level": "medium",
    }
    monkeypatch.setattr(
        "app.modules.campus_sla.service.get_campus_sla_brain_context",
        lambda tenant_id: ctx,
    )
    resp = test_client.get("/api/admin/campus-sla/brain-context", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    body = resp.json()
    assert body["module"] == "campus_sla"
    assert body["compliance_level"] == "medium"
    assert body["breached_records"] == 1
