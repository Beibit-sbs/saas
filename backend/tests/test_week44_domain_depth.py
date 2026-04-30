"""W44 domain-depth tests: programs module count-cap + sunset alert."""
from __future__ import annotations

import pytest

from app.modules.programs.service import (
    _ACTIVE_PROGRAM_STATUSES,
    _PROGRAM_DEGREE_TYPE_MAX_ACTIVE,
    _SUNSET_RISK_STATUSES,
    _ensure_sunset_alert_record,
    create_program,
)

TENANT_ID = 19


# ---------------------------------------------------------------------------
# Test 1: cap dict sanity
# ---------------------------------------------------------------------------
def test_program_degree_type_cap_dict_structure() -> None:
    for degree_type, cap in _PROGRAM_DEGREE_TYPE_MAX_ACTIVE.items():
        assert isinstance(cap, int) and cap > 0, f"Bad cap for {degree_type!r}"
    assert "bachelor" in _PROGRAM_DEGREE_TYPE_MAX_ACTIVE
    assert "doctorate" in _PROGRAM_DEGREE_TYPE_MAX_ACTIVE


# ---------------------------------------------------------------------------
# Test 2: active statuses and sunset risk statuses
# ---------------------------------------------------------------------------
def test_active_statuses_and_sunset_risk_statuses() -> None:
    assert isinstance(_ACTIVE_PROGRAM_STATUSES, frozenset)
    assert "active" in _ACTIVE_PROGRAM_STATUSES
    assert "draft" in _ACTIVE_PROGRAM_STATUSES
    assert "archived" not in _ACTIVE_PROGRAM_STATUSES
    assert isinstance(_SUNSET_RISK_STATUSES, frozenset)
    assert "inactive" in _SUNSET_RISK_STATUSES
    assert "archived" in _SUNSET_RISK_STATUSES


# ---------------------------------------------------------------------------
# Test 3: count-cap guard raises ValueError when limit reached
# ---------------------------------------------------------------------------
def test_create_program_raises_when_cap_reached(monkeypatch) -> None:
    cap = _PROGRAM_DEGREE_TYPE_MAX_ACTIVE.get("doctorate", 20)
    existing = [
        {"program_code": f"PHD-{i}", "degree_type": "doctorate", "status": "active", "id": i, "tenant_id": str(TENANT_ID)}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        "app.modules.programs.service.list_entities_for_tenant",
        lambda entity, tid: existing if entity == "programs" else [],
    )
    monkeypatch.setattr(
        "app.modules.programs.service.create_entity_for_tenant",
        lambda entity, payload, tid: {**payload, "id": 9999, "tenant_id": str(tid)},
    )

    payload = {
        "program_code": "PHD-OVER",
        "title": "Over Cap Doctorate",
        "degree_type": "doctorate",
        "faculty": "Faculty of Science",
        "status": "active",
    }

    with pytest.raises(ValueError, match="cap"):
        create_program(payload, TENANT_ID)


# ---------------------------------------------------------------------------
# Test 4: sunset alert helper is idempotent
# ---------------------------------------------------------------------------
def test_ensure_sunset_alert_record_is_idempotent(monkeypatch) -> None:
    created: list[tuple[str, dict]] = []

    existing_alerts = [
        {
            "integration_source": "programs_sunset_queue",
            "source_entity_id": "77",
            "id": 1,
            "tenant_id": str(TENANT_ID),
        }
    ]

    monkeypatch.setattr(
        "app.modules.programs.service.list_entities_for_tenant",
        lambda entity, tid: existing_alerts if entity == "program_sunset_alerts" else [],
    )
    monkeypatch.setattr(
        "app.modules.programs.service.create_entity_for_tenant",
        lambda entity, payload, tid: (
            created.append((entity, payload))
            or {**payload, "id": 99, "tenant_id": str(tid)}
        ),
    )

    _ensure_sunset_alert_record(
        tenant_id=TENANT_ID,
        program_id=77,
        program_data={"program_code": "PHD-77", "degree_type": "doctorate", "status": "archived"},
    )

    assert len(created) == 0, "Expected no new record created due to idempotency"
