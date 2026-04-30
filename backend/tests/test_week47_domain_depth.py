"""W47 domain depth tests — academic_records module."""
from __future__ import annotations

import pytest

from app.modules.academic_records.service import (
    _ACADEMIC_RECORD_STATUS_MAX_ACTIVE,
    _ACTIVE_RECORD_STATUSES,
    _WITHDRAWAL_RISK_STATUSES,
    create_record,
    _ensure_withdrawal_alert_record,
)


def test_academic_record_status_cap_dict_structure():
    """Cap dict covers expected statuses with positive caps."""
    assert isinstance(_ACADEMIC_RECORD_STATUS_MAX_ACTIVE, dict)
    for key, val in _ACADEMIC_RECORD_STATUS_MAX_ACTIVE.items():
        assert isinstance(key, str)
        assert isinstance(val, int) and val > 0


def test_active_record_statuses_and_withdrawal_risk_statuses():
    """Frozensets are non-empty, disjoint, and contain expected members."""
    assert isinstance(_ACTIVE_RECORD_STATUSES, frozenset)
    assert isinstance(_WITHDRAWAL_RISK_STATUSES, frozenset)
    assert "published" in _ACTIVE_RECORD_STATUSES
    assert "pending" in _ACTIVE_RECORD_STATUSES
    assert "withdrawn" in _WITHDRAWAL_RISK_STATUSES
    assert _ACTIVE_RECORD_STATUSES.isdisjoint(_WITHDRAWAL_RISK_STATUSES)


def test_create_record_raises_when_cap_reached(monkeypatch):
    """create_record raises ValueError when active record cap is filled."""
    monkeypatch.setattr(
        "app.modules.academic_records.service._check_enrollment_exists_for_academic_record",
        lambda *a, **kw: None,
    )
    cap = _ACADEMIC_RECORD_STATUS_MAX_ACTIVE.get("pending", 300)
    fake_records = [{"status": "pending"} for _ in range(cap)]

    monkeypatch.setattr(
        "app.modules.academic_records.service.list_entities_for_tenant",
        lambda entity, tid: fake_records if entity == "academic_records" else [],
    )
    monkeypatch.setattr(
        "app.modules.academic_records.service.create_entity_for_tenant",
        lambda *a, **kw: {},
    )

    with pytest.raises(ValueError, match="cap reached"):
        create_record(
            {"student_id": 1, "course_id": 1, "grade": "A", "semester": "2026-1", "status": "pending"},
            tenant_id=1,
        )


def test_ensure_withdrawal_alert_record_is_idempotent(monkeypatch):
    """_ensure_withdrawal_alert_record does not create a duplicate if one exists."""
    existing = [
        {
            "integration_source": "academic_records_withdrawal_queue",
            "source_entity_id": "99",
        }
    ]
    created: list = []

    monkeypatch.setattr(
        "app.modules.academic_records.service.list_entities_for_tenant",
        lambda entity, tid: existing if entity == "academic_withdrawal_alerts" else [],
    )
    monkeypatch.setattr(
        "app.modules.academic_records.service.create_entity_for_tenant",
        lambda entity, payload, tid: created.append(payload) or {},
    )

    _ensure_withdrawal_alert_record(record_id=99, tenant_id=1)
    assert len(created) == 0
