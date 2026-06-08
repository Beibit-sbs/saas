"""Phase IV-IV3: Office hours module — scheduling, availability, no_show_detected signal."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.faculty import service as faculty_service


@pytest.fixture(scope="module")
def test_client():
    from tests import conftest as test_conftest

    return test_conftest.client


@pytest.fixture(scope="module")
def admin_headers() -> dict[str, str]:
    from tests import conftest as test_conftest

    return dict(test_conftest.ADMIN_HEADERS)


# ---------------------------------------------------------------------------
# Service-level unit tests
# ---------------------------------------------------------------------------


def test_list_office_hours_empty(monkeypatch) -> None:
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: [])
    result = faculty_service.list_office_hours(tenant_id=1)
    assert result == []


def test_list_office_hours_filter_by_faculty(monkeypatch) -> None:
    rows = [
        {"id": 1, "faculty_id": "FAC-01", "scheduled_at": "2026-06-01T10:00", "duration_minutes": 60, "status": "scheduled", "no_show": False, "tenant_id": "1"},
        {"id": 2, "faculty_id": "FAC-02", "scheduled_at": "2026-06-01T11:00", "duration_minutes": 30, "status": "scheduled", "no_show": False, "tenant_id": "1"},
    ]
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = faculty_service.list_office_hours(tenant_id=1, faculty_id="FAC-01")
    assert len(result) == 1
    assert result[0]["faculty_id"] == "FAC-01"


def test_list_office_hours_no_filter_returns_all(monkeypatch) -> None:
    rows = [
        {"id": 1, "faculty_id": "FAC-01", "scheduled_at": "2026-06-01T10:00", "duration_minutes": 60, "status": "scheduled", "no_show": False, "tenant_id": "1"},
        {"id": 2, "faculty_id": "FAC-02", "scheduled_at": "2026-06-01T11:00", "duration_minutes": 30, "status": "completed", "no_show": False, "tenant_id": "1"},
    ]
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = faculty_service.list_office_hours(tenant_id=1)
    assert len(result) == 2


def test_create_office_hours_no_show_false_no_signal(monkeypatch) -> None:
    created = {
        "id": 10,
        "faculty_id": "FAC-01",
        "scheduled_at": "2026-06-01T10:00",
        "duration_minutes": 60,
        "location": "Room 101",
        "status": "scheduled",
        "student_id": "STU-01",
        "notes": None,
        "no_show": False,
        "tenant_id": "1",
    }
    monkeypatch.setattr(faculty_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.faculty.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = faculty_service.create_office_hours_record(
            {"faculty_id": "FAC-01", "scheduled_at": "2026-06-01T10:00", "duration_minutes": 60, "status": "scheduled", "no_show": False},
            tenant_id=1,
        )

    assert record["id"] == 10
    publisher.publish_event.assert_not_called()


def test_create_office_hours_no_show_true_fires_signal(monkeypatch) -> None:
    created = {
        "id": 11,
        "faculty_id": "FAC-02",
        "scheduled_at": "2026-06-02T14:00",
        "duration_minutes": 60,
        "location": "Room 202",
        "status": "no_show",
        "student_id": "STU-02",
        "notes": "Student did not attend",
        "no_show": True,
        "tenant_id": "1",
    }
    monkeypatch.setattr(faculty_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.faculty.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = faculty_service.create_office_hours_record(
            {"faculty_id": "FAC-02", "scheduled_at": "2026-06-02T14:00", "duration_minutes": 60, "status": "no_show", "no_show": True},
            tenant_id=1,
        )

    assert record["id"] == 11
    publisher.publish_event.assert_called_once()
    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "faculty.office_hours.no_show_detected"
    assert call_kwargs["tenant_id"] == 1
    assert call_kwargs["payload_json"]["faculty_id"] == "FAC-02"
    assert call_kwargs["payload_json"]["no_show"] is True


def test_create_office_hours_completed_no_signal(monkeypatch) -> None:
    """Completed office hours should NOT fire the brain signal."""
    created = {
        "id": 12,
        "faculty_id": "FAC-03",
        "scheduled_at": "2026-06-03T09:00",
        "duration_minutes": 45,
        "location": None,
        "status": "completed",
        "student_id": "STU-03",
        "notes": None,
        "no_show": False,
        "tenant_id": "1",
    }
    monkeypatch.setattr(faculty_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.faculty.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        faculty_service.create_office_hours_record(
            {"faculty_id": "FAC-03", "scheduled_at": "2026-06-03T09:00", "duration_minutes": 45, "status": "completed", "no_show": False},
            tenant_id=1,
        )

    publisher.publish_event.assert_not_called()


# ---------------------------------------------------------------------------
# Brain-context unit tests
# ---------------------------------------------------------------------------


def test_get_office_hours_brain_context_empty(monkeypatch) -> None:
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: [])
    ctx = faculty_service.get_office_hours_brain_context(tenant_id=7)
    assert ctx["module"] == "office_hours"
    assert ctx["tenant_id"] == 7
    assert ctx["total_records"] == 0
    assert ctx["no_show_count"] == 0
    assert ctx["no_show_rate"] == 0.0
    assert ctx["risk_level"] == "low"


def test_get_office_hours_brain_context_high_risk(monkeypatch) -> None:
    rows = [
        {"id": 1, "faculty_id": "FAC-01", "scheduled_at": "2026-06-01T10:00", "duration_minutes": 60, "status": "no_show", "no_show": True, "tenant_id": "7"},
        {"id": 2, "faculty_id": "FAC-01", "scheduled_at": "2026-06-02T10:00", "duration_minutes": 60, "status": "no_show", "no_show": True, "tenant_id": "7"},
        {"id": 3, "faculty_id": "FAC-01", "scheduled_at": "2026-06-03T10:00", "duration_minutes": 60, "status": "no_show", "no_show": True, "tenant_id": "7"},
        {"id": 4, "faculty_id": "FAC-02", "scheduled_at": "2026-06-04T11:00", "duration_minutes": 30, "status": "completed", "no_show": False, "tenant_id": "7"},
    ]
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: rows)
    ctx = faculty_service.get_office_hours_brain_context(tenant_id=7)
    assert ctx["total_records"] == 4
    assert ctx["no_show_count"] == 3
    assert ctx["no_show_rate"] == 0.75
    assert ctx["risk_level"] == "high"


# ---------------------------------------------------------------------------
# HTTP endpoint tests (router level)
# ---------------------------------------------------------------------------


def test_get_office_hours_list_empty_http(monkeypatch: pytest.MonkeyPatch, test_client, admin_headers) -> None:
    monkeypatch.setattr(
        "app.modules.faculty.router.list_office_hours",
        lambda tenant_id, faculty_id=None: [],
    )
    resp = test_client.get("/api/admin/org/faculty/office-hours", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["records"] == []


def test_create_office_hours_via_api_http(monkeypatch: pytest.MonkeyPatch, test_client, admin_headers) -> None:
    created = {
        "id": 20,
        "faculty_id": "FAC-10",
        "scheduled_at": "2026-07-01T09:00",
        "duration_minutes": 60,
        "location": "Office 5A",
        "status": "scheduled",
        "student_id": "STU-99",
        "notes": None,
        "no_show": False,
        "tenant_id": "1",
    }
    monkeypatch.setattr(
        "app.modules.faculty.router.create_office_hours_record",
        lambda payload, tenant_id: created,
    )
    payload = {
        "faculty_id": "FAC-10",
        "scheduled_at": "2026-07-01T09:00",
        "duration_minutes": 60,
        "location": "Office 5A",
        "status": "scheduled",
        "student_id": "STU-99",
        "no_show": False,
    }
    resp = test_client.post("/api/admin/org/faculty/office-hours", json=payload, headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["record"]["id"] == 20
    assert body["record"]["faculty_id"] == "FAC-10"


def test_get_office_hours_brain_context_http(monkeypatch: pytest.MonkeyPatch, test_client, admin_headers) -> None:
    ctx = {
        "module": "office_hours",
        "tenant_id": 1,
        "total_records": 5,
        "no_show_count": 2,
        "no_show_rate": 0.4,
        "by_status": {"scheduled": 3, "no_show": 2},
        "risk_level": "high",
    }
    monkeypatch.setattr(
        "app.modules.faculty.router.get_office_hours_brain_context",
        lambda tenant_id: ctx,
    )
    resp = test_client.get("/api/admin/org/faculty/office-hours/brain-context", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["module"] == "office_hours"
    assert body["no_show_count"] == 2
    assert body["risk_level"] == "high"
