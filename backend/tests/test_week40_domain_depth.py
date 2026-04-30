"""W40 domain-depth tests: advising module cap + personal-support alert."""
from __future__ import annotations

import pytest

from app.modules.advising.service import (
    _ACTIVE_SESSION_STATUSES,
    _HIGH_FREQUENCY_SESSION_TYPES,
    _SESSION_TYPE_MAX_ACTIVE,
    create_advising_session,
)
from app.modules.advising.schemas import AdvisingSessionCreateSchema

TENANT_ID = 14


# ---------------------------------------------------------------------------
# Test 1: cap dict sanity
# ---------------------------------------------------------------------------
def test_session_type_cap_dict_structure() -> None:
    """All cap values must be positive integers; known types present."""
    for session_type, cap in _SESSION_TYPE_MAX_ACTIVE.items():
        assert isinstance(cap, int) and cap > 0, f"Bad cap for {session_type!r}"
    for required_key in ("academic", "career", "personal", "mentoring"):
        assert required_key in _SESSION_TYPE_MAX_ACTIVE


# ---------------------------------------------------------------------------
# Test 2: active-status frozenset and high-frequency types
# ---------------------------------------------------------------------------
def test_active_statuses_and_high_frequency_types() -> None:
    assert isinstance(_ACTIVE_SESSION_STATUSES, frozenset)
    assert "scheduled" in _ACTIVE_SESSION_STATUSES
    assert isinstance(_HIGH_FREQUENCY_SESSION_TYPES, frozenset)
    assert "personal" in _HIGH_FREQUENCY_SESSION_TYPES


# ---------------------------------------------------------------------------
# Test 3: cap guard raises ValueError when limit reached
# ---------------------------------------------------------------------------
def test_create_advising_session_raises_when_cap_reached(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.modules.advising.service._check_advisor_is_active_faculty_for_advising",
        lambda *a, **kw: None,
    )
    monkeypatch.setattr(
        "app.modules.advising.service._check_student_has_active_enrollment_for_advising",
        lambda *a, **kw: None,
    )
    cap = _SESSION_TYPE_MAX_ACTIVE.get("career", 80)
    existing_sessions = [
        {"session_type": "career", "status": "scheduled", "id": i, "tenant_id": str(TENANT_ID)}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        "app.modules.advising.service.list_entities_for_tenant",
        lambda entity, tid: existing_sessions if entity == "advising_sessions" else [],
    )
    monkeypatch.setattr(
        "app.modules.advising.service.create_entity_for_tenant",
        lambda entity, payload, tid: {**payload, "id": 999, "tenant_id": str(tid)},
    )
    monkeypatch.setattr(
        "app.modules.advising.service.log_admin_action",
        lambda **kwargs: None,
    )

    payload = AdvisingSessionCreateSchema(
        student_id=1,
        advisor_id="ADV-OVER",
        session_type="career",
    )

    with pytest.raises(ValueError, match="career"):
        create_advising_session(TENANT_ID, payload, actor="admin@test")


# ---------------------------------------------------------------------------
# Test 4: personal-support alert created for personal session type
# ---------------------------------------------------------------------------
def test_create_advising_session_triggers_support_alert_for_personal(monkeypatch) -> None:
    created: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        "app.modules.advising.service._check_advisor_is_active_faculty_for_advising",
        lambda *a, **kw: None,
    )
    monkeypatch.setattr(
        "app.modules.advising.service._check_student_has_active_enrollment_for_advising",
        lambda *a, **kw: None,
    )

    monkeypatch.setattr(
        "app.modules.advising.service.list_entities_for_tenant",
        lambda entity, tid: [],
    )
    monkeypatch.setattr(
        "app.modules.advising.service.create_entity_for_tenant",
        lambda entity, payload, tid: (
            created.append((entity, payload))
            or {**payload, "id": 88, "tenant_id": str(tid)}
        ),
    )
    monkeypatch.setattr(
        "app.modules.advising.service.log_admin_action",
        lambda **kwargs: None,
    )

    payload = AdvisingSessionCreateSchema(
        student_id=3,
        advisor_id="ADV-PERSONAL",
        session_type="personal",
    )

    create_advising_session(TENANT_ID, payload, actor="admin@test")

    entities_created = [e for e, _ in created]
    assert "advising_support_alerts" in entities_created
    alert_payloads = [p for e, p in created if e == "advising_support_alerts"]
    assert len(alert_payloads) == 1
    assert alert_payloads[0]["alert_status"] == "open"
    assert alert_payloads[0]["integration_source"] == "advising_support"
