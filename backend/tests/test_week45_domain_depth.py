"""W45 domain-depth tests: courses module count-cap + retirement alert."""
from __future__ import annotations

import pytest

from app.modules.courses.service import (
    _ACTIVE_COURSE_STATUSES,
    _COURSE_STATUS_MAX_ACTIVE,
    _RETIREMENT_RISK_STATUSES,
    _ensure_retirement_alert_record,
    create_course,
)

TENANT_ID = 21


# ---------------------------------------------------------------------------
# Test 1: cap dict sanity
# ---------------------------------------------------------------------------
def test_course_status_cap_dict_structure() -> None:
    for status, cap in _COURSE_STATUS_MAX_ACTIVE.items():
        assert isinstance(cap, int) and cap > 0, f"Bad cap for {status!r}"
    assert "active" in _COURSE_STATUS_MAX_ACTIVE
    assert "draft" in _COURSE_STATUS_MAX_ACTIVE


# ---------------------------------------------------------------------------
# Test 2: active statuses and retirement risk statuses
# ---------------------------------------------------------------------------
def test_active_statuses_and_retirement_risk_statuses() -> None:
    assert isinstance(_ACTIVE_COURSE_STATUSES, frozenset)
    assert "active" in _ACTIVE_COURSE_STATUSES
    assert "draft" in _ACTIVE_COURSE_STATUSES
    assert "archived" not in _ACTIVE_COURSE_STATUSES
    assert isinstance(_RETIREMENT_RISK_STATUSES, frozenset)
    assert "inactive" in _RETIREMENT_RISK_STATUSES
    assert "archived" in _RETIREMENT_RISK_STATUSES


# ---------------------------------------------------------------------------
# Test 3: count-cap guard raises ValueError when limit reached
# ---------------------------------------------------------------------------
def test_create_course_raises_when_cap_reached(monkeypatch) -> None:
    cap = _COURSE_STATUS_MAX_ACTIVE.get("active", 500)
    existing = [
        {"course_code": f"CRS-{i}", "status": "active", "id": i, "tenant_id": str(TENANT_ID)}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        "app.modules.courses.service.list_entities_for_tenant",
        lambda entity, tid: existing if entity == "courses" else [],
    )
    monkeypatch.setattr(
        "app.modules.courses.service.create_entity_for_tenant",
        lambda entity, payload, tid: {**payload, "id": 9999, "tenant_id": str(tid)},
    )
    monkeypatch.setattr(
        "app.modules.courses.service.assert_billing_write_allowed",
        lambda *args, **kwargs: None,
    )

    payload = {
        "course_code": "CRS-OVER",
        "title": "Over Cap Course",
        "credits": 3,
        "program_id": 1,
        "status": "active",
    }

    with pytest.raises(ValueError, match="cap"):
        create_course(payload, TENANT_ID)


# ---------------------------------------------------------------------------
# Test 4: retirement alert helper is idempotent
# ---------------------------------------------------------------------------
def test_ensure_retirement_alert_record_is_idempotent(monkeypatch) -> None:
    created: list[tuple[str, dict]] = []

    existing_alerts = [
        {
            "integration_source": "courses_retirement_queue",
            "source_entity_id": "42",
            "id": 1,
            "tenant_id": str(TENANT_ID),
        }
    ]

    monkeypatch.setattr(
        "app.modules.courses.service.list_entities_for_tenant",
        lambda entity, tid: existing_alerts if entity == "course_retirement_alerts" else [],
    )
    monkeypatch.setattr(
        "app.modules.courses.service.create_entity_for_tenant",
        lambda entity, payload, tid: (
            created.append((entity, payload))
            or {**payload, "id": 99, "tenant_id": str(tid)}
        ),
    )

    _ensure_retirement_alert_record(
        tenant_id=TENANT_ID,
        course_id=42,
        course_data={"course_code": "CRS-42", "program_id": "5", "status": "archived"},
    )

    assert len(created) == 0, "Expected no new record created due to idempotency"
