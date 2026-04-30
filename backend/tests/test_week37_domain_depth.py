"""W37 domain-depth tests: communications module cap + broadcast audit."""
from __future__ import annotations

import pytest

from app.modules.communications.service import (
    _ACTIVE_MESSAGE_STATUSES,
    _LARGE_AUDIENCE_THRESHOLD,
    _MESSAGE_TYPE_MAX_ACTIVE,
    create_message,
)

TENANT_ID = 11


# ---------------------------------------------------------------------------
# Test 1: cap dict sanity
# ---------------------------------------------------------------------------
def test_message_type_cap_dict_structure() -> None:
    """All cap values must be positive integers; known types present."""
    for msg_type, cap in _MESSAGE_TYPE_MAX_ACTIVE.items():
        assert isinstance(cap, int) and cap > 0, f"Bad cap for {msg_type!r}"
    for required_key in ("announcement", "alert", "newsletter", "emergency"):
        assert required_key in _MESSAGE_TYPE_MAX_ACTIVE


# ---------------------------------------------------------------------------
# Test 2: active-status frozenset and threshold
# ---------------------------------------------------------------------------
def test_active_statuses_and_threshold() -> None:
    assert isinstance(_ACTIVE_MESSAGE_STATUSES, frozenset)
    assert "draft" in _ACTIVE_MESSAGE_STATUSES
    assert "sending" in _ACTIVE_MESSAGE_STATUSES
    assert isinstance(_LARGE_AUDIENCE_THRESHOLD, int)
    assert _LARGE_AUDIENCE_THRESHOLD > 0


# ---------------------------------------------------------------------------
# Test 3: cap guard raises ValueError when limit reached
# ---------------------------------------------------------------------------
def test_create_message_raises_when_cap_reached(monkeypatch) -> None:
    cap = _MESSAGE_TYPE_MAX_ACTIVE.get("newsletter", 3)
    active_messages = [
        {"message_type": "newsletter", "status": "draft", "id": i, "tenant_id": TENANT_ID}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        "app.modules.communications.service.list_entities_for_tenant",
        lambda entity, tid: active_messages if entity == "communication_messages" else [],
    )
    monkeypatch.setattr(
        "app.modules.communications.service.create_entity_for_tenant",
        lambda entity, payload, tid: {**payload, "id": 999, "tenant_id": tid},
    )

    with pytest.raises(ValueError, match="newsletter"):
        create_message(
            {
                "message_code": "NL-OVER",
                "title": "Newsletter overflow",
                "message_type": "newsletter",
                "target_audience": "all",
                "status": "draft",
                "recipients_count": 10,
            },
            TENANT_ID,
        )


# ---------------------------------------------------------------------------
# Test 4: broadcast audit record created for large audience
# ---------------------------------------------------------------------------
def test_create_message_triggers_broadcast_audit_for_large_audience(monkeypatch) -> None:
    created: list[tuple[str, dict]] = []

    monkeypatch.setattr(
        "app.modules.communications.service.list_entities_for_tenant",
        lambda entity, tid: [],
    )
    monkeypatch.setattr(
        "app.modules.communications.service.create_entity_for_tenant",
        lambda entity, payload, tid: (
            created.append((entity, payload))
            or {**payload, "id": 42, "tenant_id": tid}
        ),
    )

    create_message(
        {
            "message_code": "ALERT-MASS",
            "title": "Mass alert",
            "message_type": "alert",
            "target_audience": "campus",
            "status": "draft",
            "recipients_count": _LARGE_AUDIENCE_THRESHOLD + 100,
        },
        TENANT_ID,
    )

    entities_created = [e for e, _ in created]
    assert "communication_broadcast_audits" in entities_created
    audit_payloads = [p for e, p in created if e == "communication_broadcast_audits"]
    assert len(audit_payloads) == 1
    assert audit_payloads[0]["audit_status"] == "logged"
    assert audit_payloads[0]["integration_source"] == "communications_broadcast"
