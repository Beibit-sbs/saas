"""Phase C — Courses Service Hardening (canonical 10-step loop)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.modules.courses import service as svc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_course(course_id: int = 1, status: str = "active") -> dict:
    return {
        "id": course_id,
        "course_code": "CS101",
        "title": "Intro",
        "credits": 3,
        "program_id": 10,
        "status": status,
        "tenant_id": "1",
    }


# ---------------------------------------------------------------------------
# Test 1: create_course fires courses.course.created event + metric
# (EventPublisher is lazy-imported inside _fire — patch _fire directly)
# ---------------------------------------------------------------------------

def test_create_course_uses_canonical_event_publisher_and_metric(monkeypatch):
    """create_course must fire courses.course.created event and record metric."""
    monkeypatch.setattr(svc, "assert_billing_write_allowed", lambda *a, **kw: None)
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda *a, **kw: [])
    monkeypatch.setattr(svc, "create_entity_for_tenant", lambda name, payload, tid: _make_course(1, "active"))
    monkeypatch.setattr(svc, "_record_outcome", MagicMock())
    monkeypatch.setattr(svc, "_audit", MagicMock())

    fired: list[dict] = []

    def fake_fire(tenant_id, event_type, aggregate_type, aggregate_id, payload_json):
        fired.append({"tenant_id": tenant_id, "event_type": event_type})

    monkeypatch.setattr(svc, "_fire", fake_fire)

    metrics: list = []
    monkeypatch.setattr(svc, "_metric", lambda tid, name, val=1: metrics.append((tid, name, val)))

    svc.create_course(
        {"status": "active", "course_code": "CS101", "title": "T", "credits": 3, "program_id": 10},
        1,
        actor="admin@test",
    )

    assert any(f["event_type"] == "courses.course.created" for f in fired)
    assert any(f["tenant_id"] == 1 for f in fired)
    assert any(name == "courses_created" for _, name, _ in metrics)


# ---------------------------------------------------------------------------
# Test 2: update_course with risk status fires event + metric
# ---------------------------------------------------------------------------

def test_update_course_risk_status_fires_event_and_metric(monkeypatch):
    """update_course with inactive/archived status fires courses.status.risk_detected + metric."""
    monkeypatch.setattr(svc, "assert_billing_write_allowed", lambda *a, **kw: None)
    monkeypatch.setattr(
        svc, "update_entity_for_tenant",
        lambda name, cid, payload, tid: _make_course(cid, "inactive"),
    )
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda *a, **kw: [])
    monkeypatch.setattr(svc, "create_entity_for_tenant", lambda *a, **kw: {})
    monkeypatch.setattr(svc, "_record_outcome", MagicMock())
    monkeypatch.setattr(svc, "_audit", MagicMock())

    fired: list[dict] = []

    def fake_fire(tenant_id, event_type, aggregate_type, aggregate_id, payload_json):
        fired.append({"event_type": event_type})

    monkeypatch.setattr(svc, "_fire", fake_fire)

    metrics: list = []
    monkeypatch.setattr(svc, "_metric", lambda tid, name, val=1: metrics.append((tid, name, val)))

    svc.update_course(5, {"status": "inactive"}, 1, actor="admin@test")

    assert any(f["event_type"] == "courses.status.risk_detected" for f in fired)
    assert any(name == "courses_updated" for _, name, _ in metrics)


# ---------------------------------------------------------------------------
# Test 3: create_course survives outcome failure and still records metric
# _record_outcome has try/except — simulate brain down via raised exception
# ---------------------------------------------------------------------------

def test_create_course_survives_outcome_failure_and_records_metric(monkeypatch):
    """Brain down must not prevent create_course from completing or recording metric."""
    monkeypatch.setattr(svc, "assert_billing_write_allowed", lambda *a, **kw: None)
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda *a, **kw: [])
    monkeypatch.setattr(svc, "create_entity_for_tenant", lambda *a, **kw: _make_course(2))
    monkeypatch.setattr(svc, "_audit", MagicMock())

    fired_events: list = []

    def fake_fire(tenant_id, event_type, aggregate_type, aggregate_id, payload_json):
        fired_events.append(event_type)

    monkeypatch.setattr(svc, "_fire", fake_fire)

    metrics: list = []
    monkeypatch.setattr(svc, "_metric", lambda tid, name, val=1: metrics.append((tid, name, val)))

    # Simulate brain down: brain_core_service.record_dispatch_outcome raises inside _record_outcome
    # _record_outcome has try/except so create_course must NOT raise
    mock_brain = MagicMock()
    mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")

    with patch("app.modules.brain_core.service.brain_core_service", mock_brain):
        result = svc.create_course(
            {"status": "active", "course_code": "CS102", "title": "T", "credits": 3, "program_id": 10},
            1,
        )

    assert result["id"] == 2
    assert "courses.course.created" in fired_events
    assert any(name == "courses_created" for _, name, _ in metrics)


# ---------------------------------------------------------------------------
# Test 4: create_course cap guard is fail-closed
# ---------------------------------------------------------------------------

def test_create_course_cap_guard_fail_closed(monkeypatch):
    """create_course must raise ValueError when active course cap is exceeded."""
    monkeypatch.setattr(svc, "assert_billing_write_allowed", lambda *a, **kw: None)
    # 500 active courses already
    many_active = [{"id": i, "status": "active"} for i in range(500)]
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda *a, **kw: many_active)

    with pytest.raises(ValueError, match="cap"):
        svc.create_course({"status": "active", "course_code": "CSX", "title": "T", "credits": 3, "program_id": 10}, 1)
