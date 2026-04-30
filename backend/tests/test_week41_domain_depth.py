"""W41 domain-depth tests: thesis module count-cap + overdue alert on under_review."""
from __future__ import annotations

import pytest

from app.modules.thesis.service import (
    _ACTIVE_THESIS_STATUSES,
    _HIGH_RISK_THESIS_STATUSES,
    _THESIS_STATUS_MAX_ACTIVE,
    _ensure_overdue_alert_record,
    create_thesis_record,
)
from app.modules.thesis.schemas import ThesisCreateSchema

TENANT_ID = 15


# ---------------------------------------------------------------------------
# Test 1: cap dict sanity
# ---------------------------------------------------------------------------
def test_thesis_status_cap_dict_structure() -> None:
    """All cap values must be positive integers; key statuses present."""
    for status, cap in _THESIS_STATUS_MAX_ACTIVE.items():
        assert isinstance(cap, int) and cap > 0, f"Bad cap for {status!r}"
    assert "draft" in _THESIS_STATUS_MAX_ACTIVE


# ---------------------------------------------------------------------------
# Test 2: active-status frozenset and high-risk statuses
# ---------------------------------------------------------------------------
def test_active_statuses_and_high_risk_statuses() -> None:
    assert isinstance(_ACTIVE_THESIS_STATUSES, frozenset)
    assert "draft" in _ACTIVE_THESIS_STATUSES
    assert "under_review" in _ACTIVE_THESIS_STATUSES
    assert isinstance(_HIGH_RISK_THESIS_STATUSES, frozenset)
    assert "under_review" in _HIGH_RISK_THESIS_STATUSES


# ---------------------------------------------------------------------------
# Test 3: count-cap guard raises ValueError when limit reached
# ---------------------------------------------------------------------------
def test_create_thesis_raises_when_cap_reached(monkeypatch) -> None:
    cap = _THESIS_STATUS_MAX_ACTIVE.get("draft", 200)
    existing_theses = [
        {"thesis_code": f"TH-{i}", "status": "draft", "id": i, "tenant_id": str(TENANT_ID)}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        "app.modules.thesis.service.list_entities_for_tenant",
        lambda entity, tid: existing_theses if entity == "thesis_records" else [],
    )
    monkeypatch.setattr(
        "app.modules.thesis.service.create_entity_for_tenant",
        lambda entity, payload, tid: {**payload, "id": 9999, "tenant_id": str(tid)},
    )
    monkeypatch.setattr(
        "app.modules.thesis.service.log_admin_action",
        lambda **kwargs: None,
    )

    payload = ThesisCreateSchema(
        thesis_code="TH-OVER",
        student_id=1,
        title="Overflow thesis title",
    )

    with pytest.raises(ValueError, match="cap"):
        create_thesis_record(TENANT_ID, payload, actor="admin@test")


# ---------------------------------------------------------------------------
# Test 4: overdue alert idempotent helper deduplicates correctly
# ---------------------------------------------------------------------------
def test_ensure_overdue_alert_record_is_idempotent(monkeypatch) -> None:
    created: list[tuple[str, dict]] = []

    existing_alerts = [
        {
            "integration_source": "thesis_review_queue",
            "source_entity_id": "42",
            "id": 1,
            "tenant_id": str(TENANT_ID),
        }
    ]

    monkeypatch.setattr(
        "app.modules.thesis.service.list_entities_for_tenant",
        lambda entity, tid: existing_alerts if entity == "thesis_overdue_alerts" else [],
    )
    monkeypatch.setattr(
        "app.modules.thesis.service.create_entity_for_tenant",
        lambda entity, payload, tid: (
            created.append((entity, payload))
            or {**payload, "id": 99, "tenant_id": str(tid)}
        ),
    )

    # Call twice — second call should be a no-op due to idempotency check
    _ensure_overdue_alert_record(
        tenant_id=TENANT_ID,
        thesis_id=42,
        thesis_data={"thesis_code": "TH-42", "student_id": 5, "current_status": "under_review"},
    )

    assert len(created) == 0, "Expected no new record created due to idempotency"
