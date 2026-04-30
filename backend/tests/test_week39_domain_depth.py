"""W39 domain-depth tests: financial_aid module count-cap + high-value watch."""
from __future__ import annotations

import pytest

from app.modules.financial_aid.service import (
    _ACTIVE_AID_STATUSES,
    _AID_TYPE_MAX_ACTIVE,
    _HIGH_VALUE_AID_THRESHOLD,
    create_financial_aid_record,
)
from app.modules.financial_aid.schemas import FinancialAidRecordCreateSchema

TENANT_ID = 13


# ---------------------------------------------------------------------------
# Test 1: cap dict sanity
# ---------------------------------------------------------------------------
def test_aid_type_cap_dict_structure() -> None:
    """All count-cap values must be positive integers; known types present."""
    for aid_type, cap in _AID_TYPE_MAX_ACTIVE.items():
        assert isinstance(cap, int) and cap > 0, f"Bad cap for {aid_type!r}"
    for required_key in ("scholarship", "grant", "tuition_discount", "stipend"):
        assert required_key in _AID_TYPE_MAX_ACTIVE


# ---------------------------------------------------------------------------
# Test 2: active-status frozenset and high-value thresholds
# ---------------------------------------------------------------------------
def test_active_statuses_and_high_value_threshold() -> None:
    assert isinstance(_ACTIVE_AID_STATUSES, frozenset)
    assert "pending" in _ACTIVE_AID_STATUSES
    assert "approved" in _ACTIVE_AID_STATUSES
    assert isinstance(_HIGH_VALUE_AID_THRESHOLD, dict)
    for val in _HIGH_VALUE_AID_THRESHOLD.values():
        assert isinstance(val, float) and val > 0


# ---------------------------------------------------------------------------
# Test 3: count-cap guard raises ValueError when limit reached
# ---------------------------------------------------------------------------
def test_create_financial_aid_raises_when_cap_reached(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.modules.financial_aid.service._check_student_enrollment_for_aid_creation",
        lambda *a, **kw: None,
    )
    cap = _AID_TYPE_MAX_ACTIVE.get("stipend", 300)
    existing_records = [
        {"aid_type": "stipend", "status": "pending", "id": i, "tenant_id": str(TENANT_ID)}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        "app.modules.financial_aid.service.list_entities_for_tenant",
        lambda entity, tid: existing_records if entity == "financial_aid_records" else [],
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service.create_entity_for_tenant",
        lambda entity, payload, tid: {**payload, "id": 999, "tenant_id": str(tid)},
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service.log_admin_action",
        lambda **kwargs: None,
    )

    payload = FinancialAidRecordCreateSchema(
        student_id=1,
        aid_type="stipend",
        amount=500.0,
        currency="USD",
        term="2026-Q1",
    )

    with pytest.raises(ValueError, match="stipend"):
        create_financial_aid_record(TENANT_ID, payload, actor="admin@test")


# ---------------------------------------------------------------------------
# Test 4: high-value watch record created when amount >= threshold
# ---------------------------------------------------------------------------
def test_create_financial_aid_triggers_disbursement_watch(monkeypatch) -> None:
    created: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        "app.modules.financial_aid.service._check_student_enrollment_for_aid_creation",
        lambda *a, **kw: None,
    )

    monkeypatch.setattr(
        "app.modules.financial_aid.service.list_entities_for_tenant",
        lambda entity, tid: [],
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service.create_entity_for_tenant",
        lambda entity, payload, tid: (
            created.append((entity, payload))
            or {**payload, "id": 77, "tenant_id": str(tid)}
        ),
    )
    monkeypatch.setattr(
        "app.modules.financial_aid.service.log_admin_action",
        lambda **kwargs: None,
    )

    threshold = _HIGH_VALUE_AID_THRESHOLD.get("grant", 10_000.0)
    payload = FinancialAidRecordCreateSchema(
        student_id=2,
        aid_type="grant",
        amount=threshold + 1000.0,
        currency="USD",
        term="2026-Q2",
    )

    create_financial_aid_record(TENANT_ID, payload, actor="admin@test")

    entities_created = [e for e, _ in created]
    assert "financial_aid_disbursement_watches" in entities_created
    watch_payloads = [p for e, p in created if e == "financial_aid_disbursement_watches"]
    assert len(watch_payloads) == 1
    assert watch_payloads[0]["watch_status"] == "active"
    assert watch_payloads[0]["integration_source"] == "financial_aid_watch"
