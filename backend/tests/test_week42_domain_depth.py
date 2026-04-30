"""W42 domain-depth tests: accreditation module count-cap + high-risk alert."""
from __future__ import annotations

import pytest

from app.modules.accreditation.service import (
    _ACCREDITATION_TYPE_MAX_ACTIVE,
    _ACTIVE_ACCREDITATION_STATUSES,
    _HIGH_RISK_LEVELS,
    _ensure_high_risk_alert_record,
    create_accreditation_record,
)
from app.modules.accreditation.schemas import AccreditationCreateSchema

TENANT_ID = 16


# ---------------------------------------------------------------------------
# Test 1: cap dict sanity
# ---------------------------------------------------------------------------
def test_accreditation_type_cap_dict_structure() -> None:
    """All cap values must be positive integers; all standard types present."""
    expected_types = {"institutional", "programmatic", "curriculum", "faculty_qualifications", "learning_outcomes"}
    for t in expected_types:
        assert t in _ACCREDITATION_TYPE_MAX_ACTIVE, f"Missing cap for {t!r}"
        assert isinstance(_ACCREDITATION_TYPE_MAX_ACTIVE[t], int) and _ACCREDITATION_TYPE_MAX_ACTIVE[t] > 0


# ---------------------------------------------------------------------------
# Test 2: active statuses frozenset and high-risk levels
# ---------------------------------------------------------------------------
def test_active_statuses_and_high_risk_levels() -> None:
    assert isinstance(_ACTIVE_ACCREDITATION_STATUSES, frozenset)
    assert "draft" in _ACTIVE_ACCREDITATION_STATUSES
    assert "under_review" in _ACTIVE_ACCREDITATION_STATUSES
    assert "compliant" not in _ACTIVE_ACCREDITATION_STATUSES
    assert isinstance(_HIGH_RISK_LEVELS, frozenset)
    assert "high" in _HIGH_RISK_LEVELS
    assert "low" not in _HIGH_RISK_LEVELS


# ---------------------------------------------------------------------------
# Test 3: count-cap guard raises ValueError when limit reached
# ---------------------------------------------------------------------------
def test_create_accreditation_raises_when_cap_reached(monkeypatch) -> None:
    cap = _ACCREDITATION_TYPE_MAX_ACTIVE["institutional"]
    existing = [
        {
            "standard_code": f"STD-{i}",
            "standard_type": "institutional",
            "status": "draft",
            "review_cycle_year": 2025,
            "id": i,
            "tenant_id": str(TENANT_ID),
        }
        for i in range(cap)
    ]

    monkeypatch.setattr(
        "app.modules.accreditation.service.list_entities_for_tenant",
        lambda entity, tid: existing if entity == "accreditation_records" else [],
    )
    monkeypatch.setattr(
        "app.modules.accreditation.service.create_entity_for_tenant",
        lambda entity, payload, tid: {**payload, "id": 9999, "tenant_id": str(tid)},
    )
    monkeypatch.setattr(
        "app.modules.accreditation.service.log_admin_action",
        lambda **kwargs: None,
    )

    payload = AccreditationCreateSchema(
        standard_code="STD-OVER",
        standard_type="institutional",
        title="Overflow accreditation title",
        owner_department="QA Dept",
        review_cycle_year=2025,
        risk_level="low",
    )

    with pytest.raises(ValueError, match="cap"):
        create_accreditation_record(TENANT_ID, payload, actor="admin@test")


# ---------------------------------------------------------------------------
# Test 4: high-risk alert helper is idempotent
# ---------------------------------------------------------------------------
def test_ensure_high_risk_alert_record_is_idempotent(monkeypatch) -> None:
    created: list[tuple[str, dict]] = []

    existing_alerts = [
        {
            "integration_source": "accreditation_risk_queue",
            "source_entity_id": "77",
            "id": 1,
            "tenant_id": str(TENANT_ID),
        }
    ]

    monkeypatch.setattr(
        "app.modules.accreditation.service.list_entities_for_tenant",
        lambda entity, tid: existing_alerts if entity == "accreditation_risk_alerts" else [],
    )
    monkeypatch.setattr(
        "app.modules.accreditation.service.create_entity_for_tenant",
        lambda entity, payload, tid: (
            created.append((entity, payload))
            or {**payload, "id": 99, "tenant_id": str(tid)}
        ),
    )

    _ensure_high_risk_alert_record(
        tenant_id=TENANT_ID,
        record_id=77,
        record_data={
            "standard_code": "STD-77",
            "standard_type": "programmatic",
            "owner_department": "Dept A",
            "risk_level": "high",
        },
    )

    assert len(created) == 0, "Expected no new record created due to idempotency"
