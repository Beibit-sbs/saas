"""Phase IV-IV2: Proctoring module — exam supervision, violation_detected signal."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.faculty import service as faculty_service
from tests.conftest import ADMIN_HEADERS, client as test_client


# ---------------------------------------------------------------------------
# Service-level unit tests
# ---------------------------------------------------------------------------


def test_list_proctoring_records_empty(monkeypatch) -> None:
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: [])
    result = faculty_service.list_proctoring_records(tenant_id=1)
    assert result == []


def test_list_proctoring_records_filter_by_faculty(monkeypatch) -> None:
    rows = [
        {"id": 1, "exam_id": "EXAM-01", "faculty_id": "FAC-01", "severity": "high", "status": "open", "tenant_id": "1"},
        {"id": 2, "exam_id": "EXAM-01", "faculty_id": "FAC-02", "severity": "low", "status": "open", "tenant_id": "1"},
    ]
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = faculty_service.list_proctoring_records(tenant_id=1, faculty_id="FAC-01")
    assert len(result) == 1
    assert result[0]["faculty_id"] == "FAC-01"


def test_list_proctoring_records_filter_by_exam(monkeypatch) -> None:
    rows = [
        {"id": 1, "exam_id": "EXAM-01", "faculty_id": "FAC-01", "severity": "medium", "status": "open", "tenant_id": "1"},
        {"id": 2, "exam_id": "EXAM-02", "faculty_id": "FAC-01", "severity": "high", "status": "open", "tenant_id": "1"},
    ]
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = faculty_service.list_proctoring_records(tenant_id=1, exam_id="EXAM-02")
    assert len(result) == 1
    assert result[0]["exam_id"] == "EXAM-02"


def test_create_proctoring_record_low_severity_no_signal(monkeypatch) -> None:
    created = {
        "id": 10,
        "exam_id": "EXAM-01",
        "faculty_id": "FAC-01",
        "room_id": "R101",
        "violation_type": "minor_disruption",
        "severity": "low",
        "student_id": "STU-01",
        "notes": None,
        "status": "open",
        "tenant_id": "1",
    }
    monkeypatch.setattr(faculty_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.faculty.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = faculty_service.create_proctoring_record(
            {"exam_id": "EXAM-01", "faculty_id": "FAC-01", "violation_type": "minor_disruption", "severity": "low", "status": "open"},
            tenant_id=1,
        )

    assert record["id"] == 10
    publisher.publish_event.assert_not_called()


def test_create_proctoring_record_high_severity_fires_signal(monkeypatch) -> None:
    created = {
        "id": 11,
        "exam_id": "EXAM-02",
        "faculty_id": "FAC-02",
        "room_id": "R202",
        "violation_type": "cheating_suspected",
        "severity": "high",
        "student_id": "STU-02",
        "notes": "Caught with unauthorized notes",
        "status": "open",
        "tenant_id": "1",
    }
    monkeypatch.setattr(faculty_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.faculty.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = faculty_service.create_proctoring_record(
            {"exam_id": "EXAM-02", "faculty_id": "FAC-02", "violation_type": "cheating_suspected", "severity": "high", "status": "open"},
            tenant_id=1,
        )

    assert record["id"] == 11
    publisher.publish_event.assert_called_once()
    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "faculty.proctoring.violation_detected"
    assert call_kwargs["tenant_id"] == 1
    assert call_kwargs["payload_json"]["faculty_id"] == "FAC-02"
    assert call_kwargs["payload_json"]["severity"] == "high"
    assert call_kwargs["payload_json"]["violation_type"] == "cheating_suspected"


def test_create_proctoring_record_medium_severity_no_signal(monkeypatch) -> None:
    """Medium severity should NOT fire the brain signal (only high triggers it)."""
    created = {
        "id": 12,
        "exam_id": "EXAM-03",
        "faculty_id": "FAC-03",
        "room_id": None,
        "violation_type": "unauthorized_material",
        "severity": "medium",
        "student_id": None,
        "notes": None,
        "status": "open",
        "tenant_id": "1",
    }
    monkeypatch.setattr(faculty_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.faculty.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        faculty_service.create_proctoring_record(
            {"exam_id": "EXAM-03", "faculty_id": "FAC-03", "violation_type": "unauthorized_material", "severity": "medium", "status": "open"},
            tenant_id=1,
        )

    publisher.publish_event.assert_not_called()


# ---------------------------------------------------------------------------
# Proctoring brain-context tests
# ---------------------------------------------------------------------------


def test_get_proctoring_brain_context_empty(monkeypatch) -> None:
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: [])
    ctx = faculty_service.get_proctoring_brain_context(tenant_id=7)
    assert ctx["module"] == "proctoring"
    assert ctx["tenant_id"] == 7
    assert ctx["total_records"] == 0
    assert ctx["open_violations"] == 0
    assert ctx["high_severity_count"] == 0
    assert ctx["risk_level"] == "low"


def test_get_proctoring_brain_context_high_risk(monkeypatch) -> None:
    rows = [
        {"id": 1, "exam_id": "EXAM-01", "faculty_id": "FAC-01", "severity": "high", "status": "open", "violation_type": "cheating_suspected", "tenant_id": "7"},
        {"id": 2, "exam_id": "EXAM-01", "faculty_id": "FAC-01", "severity": "high", "status": "open", "violation_type": "cheating_suspected", "tenant_id": "7"},
        {"id": 3, "exam_id": "EXAM-02", "faculty_id": "FAC-02", "severity": "low", "status": "resolved", "violation_type": "disruption", "tenant_id": "7"},
    ]
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: rows)
    ctx = faculty_service.get_proctoring_brain_context(tenant_id=7)
    assert ctx["total_records"] == 3
    assert ctx["open_violations"] == 2
    assert ctx["high_severity_count"] == 2
    assert ctx["risk_level"] == "high"


# ---------------------------------------------------------------------------
# HTTP endpoint tests (router level)
# ---------------------------------------------------------------------------


def test_get_proctoring_list_empty_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.modules.faculty.router.list_proctoring_records",
        lambda tenant_id, faculty_id=None, exam_id=None: [],
    )
    resp = test_client.get("/api/admin/org/faculty/proctoring", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    assert resp.json()["records"] == []


def test_create_proctoring_record_via_api_http(monkeypatch: pytest.MonkeyPatch) -> None:
    created = {
        "id": 20,
        "exam_id": "EXAM-10",
        "faculty_id": "FAC-10",
        "room_id": "R300",
        "violation_type": "cheating_suspected",
        "severity": "high",
        "student_id": "STU-99",
        "notes": None,
        "status": "open",
        "tenant_id": "1",
    }
    monkeypatch.setattr(
        "app.modules.faculty.router.create_proctoring_record",
        lambda payload, tenant_id: created,
    )
    payload = {
        "exam_id": "EXAM-10",
        "faculty_id": "FAC-10",
        "room_id": "R300",
        "violation_type": "cheating_suspected",
        "severity": "high",
        "status": "open",
    }
    resp = test_client.post("/api/admin/org/faculty/proctoring", json=payload, headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    data = resp.json()
    assert data["record"]["exam_id"] == "EXAM-10"
    assert data["record"]["severity"] == "high"


def test_proctoring_brain_context_endpoint_http(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = {
        "module": "proctoring",
        "tenant_id": 1,
        "total_records": 10,
        "open_violations": 3,
        "by_severity": {"high": 3, "medium": 2, "low": 5},
        "by_violation_type": {"cheating_suspected": 5, "disruption": 5},
        "high_severity_count": 3,
        "risk_level": "medium",
    }
    monkeypatch.setattr("app.modules.faculty.router.get_proctoring_brain_context", lambda tenant_id: ctx)
    resp = test_client.get("/api/admin/org/faculty/proctoring/brain-context", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    data = resp.json()
    assert data["module"] == "proctoring"
    assert data["risk_level"] == "medium"
    assert data["high_severity_count"] == 3
