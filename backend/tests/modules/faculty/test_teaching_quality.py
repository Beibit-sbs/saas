"""Phase IV-IV1: Teaching quality analytics, brain-context, quality_drop signal."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.faculty import service as faculty_service
from tests.conftest import ADMIN_HEADERS, client as test_client


# ---------------------------------------------------------------------------
# Service-level unit tests
# ---------------------------------------------------------------------------


def test_list_teaching_quality_empty(monkeypatch) -> None:
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: [])
    result = faculty_service.list_teaching_quality(tenant_id=1)
    assert result == []


def test_list_teaching_quality_filter_by_faculty(monkeypatch) -> None:
    rows = [
        {"id": 1, "faculty_id": "FAC-01", "quality_score": 85.0, "kpi_score": 80.0, "tenant_id": "1"},
        {"id": 2, "faculty_id": "FAC-02", "quality_score": 90.0, "kpi_score": 88.0, "tenant_id": "1"},
    ]
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: rows)
    result = faculty_service.list_teaching_quality(tenant_id=1, faculty_id="FAC-01")
    assert len(result) == 1
    assert result[0]["faculty_id"] == "FAC-01"


def test_create_teaching_quality_record_good_scores_no_signal(monkeypatch) -> None:
    created = {
        "id": 10,
        "faculty_id": "FAC-01",
        "course_id": "CS101",
        "term_id": 1,
        "quality_score": 90.0,
        "kpi_score": 88.0,
        "tenant_id": "1",
    }
    monkeypatch.setattr(faculty_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.faculty.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = faculty_service.create_teaching_quality_record(
            {"faculty_id": "FAC-01", "course_id": "CS101", "term_id": 1, "quality_score": 90.0, "kpi_score": 88.0},
            tenant_id=1,
        )

    assert record["id"] == 10
    publisher.publish_event.assert_not_called()


def test_create_teaching_quality_record_low_score_fires_signal(monkeypatch) -> None:
    created = {
        "id": 11,
        "faculty_id": "FAC-02",
        "course_id": "MATH201",
        "term_id": 2,
        "quality_score": 45.0,
        "kpi_score": 50.0,
        "tenant_id": "1",
    }
    monkeypatch.setattr(faculty_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.faculty.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        record = faculty_service.create_teaching_quality_record(
            {"faculty_id": "FAC-02", "course_id": "MATH201", "term_id": 2, "quality_score": 45.0, "kpi_score": 50.0},
            tenant_id=1,
        )

    assert record["id"] == 11
    publisher.publish_event.assert_called_once()
    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "faculty.quality_drop.detected"
    assert call_kwargs["tenant_id"] == 1
    assert call_kwargs["payload_json"]["faculty_id"] == "FAC-02"


def test_create_teaching_quality_record_kpi_below_threshold_fires_signal(monkeypatch) -> None:
    created = {
        "id": 12,
        "faculty_id": "FAC-03",
        "course_id": "PHY301",
        "term_id": 1,
        "quality_score": 75.0,
        "kpi_score": 30.0,
        "tenant_id": "1",
    }
    monkeypatch.setattr(faculty_service, "create_entity_for_tenant", lambda name, payload, tid: created)

    with patch("app.modules.faculty.service.EventPublisher") as mock_pub_cls:
        publisher = MagicMock()
        mock_pub_cls.return_value = publisher
        faculty_service.create_teaching_quality_record(
            {"faculty_id": "FAC-03", "course_id": "PHY301", "term_id": 1, "quality_score": 75.0, "kpi_score": 30.0},
            tenant_id=1,
        )

    call_kwargs = publisher.publish_event.call_args.kwargs
    assert call_kwargs["payload_json"]["risk_level"] == "high"


# ---------------------------------------------------------------------------
# Brain-context tests
# ---------------------------------------------------------------------------


def test_get_faculty_brain_context_empty(monkeypatch) -> None:
    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", lambda name, tid: [])
    ctx = faculty_service.get_faculty_brain_context(tenant_id=5)
    assert ctx["module"] == "faculty"
    assert ctx["tenant_id"] == 5
    assert ctx["total_faculty"] == 0
    assert ctx["total_quality_records"] == 0
    assert ctx["risk_level"] == "low"
    assert ctx["avg_quality_score"] is None


def test_get_faculty_brain_context_with_alerts(monkeypatch) -> None:
    faculty_rows = [
        {"id": 1, "faculty_id": "FAC-01", "status": "active", "department": "CS", "tenant_id": "5"},
        {"id": 2, "faculty_id": "FAC-02", "status": "active", "department": "Math", "tenant_id": "5"},
        {"id": 3, "faculty_id": "FAC-03", "status": "inactive", "department": "CS", "tenant_id": "5"},
    ]
    quality_rows = [
        {"id": 10, "faculty_id": "FAC-01", "quality_score": 40.0, "kpi_score": 88.0, "tenant_id": "5"},
        {"id": 11, "faculty_id": "FAC-02", "quality_score": 90.0, "kpi_score": 92.0, "tenant_id": "5"},
    ]

    def fake_list(name: str, tid: int):
        if name == "faculty":
            return faculty_rows
        return quality_rows

    monkeypatch.setattr(faculty_service, "list_entities_for_tenant", fake_list)
    ctx = faculty_service.get_faculty_brain_context(tenant_id=5)
    assert ctx["total_faculty"] == 3
    assert ctx["total_quality_records"] == 2
    assert ctx["quality_alert_count"] == 1
    assert ctx["avg_quality_score"] == pytest.approx(65.0)


# ---------------------------------------------------------------------------
# HTTP endpoint tests (router level) — use conftest JWT auth + monkeypatch
# ---------------------------------------------------------------------------


def test_get_teaching_quality_list_empty_http(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.faculty.router.list_teaching_quality", lambda tenant_id, faculty_id=None: [])
    resp = test_client.get("/api/admin/org/faculty/teaching-quality", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    data = resp.json()
    assert data["records"] == []


def test_create_teaching_quality_record_via_api_http(monkeypatch: pytest.MonkeyPatch) -> None:
    created = {
        "id": 10,
        "faculty_id": "FAC-10",
        "course_id": "CS999",
        "term_id": 1,
        "quality_score": 88.0,
        "kpi_score": 91.0,
        "improvement_plan": None,
        "notes": None,
        "tenant_id": "1",
    }
    monkeypatch.setattr(
        "app.modules.faculty.router.create_teaching_quality_record",
        lambda payload, tenant_id: created,
    )
    payload = {
        "faculty_id": "FAC-10",
        "course_id": "CS999",
        "term_id": 1,
        "quality_score": 88.0,
        "kpi_score": 91.0,
    }
    resp = test_client.post(
        "/api/admin/org/faculty/teaching-quality", json=payload, headers=dict(ADMIN_HEADERS)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["record"]["faculty_id"] == "FAC-10"
    assert data["record"]["quality_score"] == 88.0


def test_faculty_brain_context_endpoint_http(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = {
        "module": "faculty",
        "tenant_id": 1,
        "total_faculty": 5,
        "by_status": {"active": 5},
        "by_department": {"CS": 3, "Math": 2},
        "total_quality_records": 10,
        "quality_alert_count": 0,
        "avg_quality_score": 82.5,
        "risk_level": "low",
    }
    monkeypatch.setattr("app.modules.faculty.router.get_faculty_brain_context", lambda tenant_id: ctx)
    resp = test_client.get("/api/admin/org/faculty/brain-context", headers=dict(ADMIN_HEADERS))
    assert resp.status_code == 200
    data = resp.json()
    assert data["module"] == "faculty"
    assert data["risk_level"] == "low"
    assert data["quality_alert_count"] == 0
