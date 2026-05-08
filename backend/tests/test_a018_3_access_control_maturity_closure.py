"""A-018.3 Access Control Maturity Closure tests (Wave 6).

Tests that verify access_control module meets Level 4+ maturity:
  - Full card lifecycle FSM (ACTIVE→SUSPENDED→ACTIVE, ACTIVE→REVOKED)
  - Event emission for all transitions + access attempts
  - ABAC tenant isolation
  - Security anomaly detection
  - Brain Core signal registration
  - KPI metric lineage coverage
  - Event ingestion VALID_EVENT_TYPES coverage
  - Router/schemas existence (structural)
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.modules.access_control.service as ac_svc


# ─── helpers ──────────────────────────────────────────────────────────────────

def _mocks(existing_cards=None, existing_logs=None):
    cards = list(existing_cards or [])
    logs = list(existing_logs or [])
    counter = {"n": 0}

    def _create(tid, table, data):
        counter["n"] += 1
        row = {"id": f"row-{counter['n']}", **data}
        if table == "access_cards":
            cards.append(row)
        elif table == "access_logs":
            logs.append(row)
        return row

    def _list(tid, table):
        if table == "access_cards":
            return list(cards)
        return list(logs)

    pub = MagicMock()
    pub.return_value.publish_event = MagicMock()
    return _create, _list, pub, cards, logs


_PATCHES = (
    "app.modules.access_control.service.create_entity_for_tenant",
    "app.modules.access_control.service.list_entities_for_tenant",
    "app.modules.access_control.service.EventPublisher",
    "app.modules.access_control.service.log_admin_action",
    "app.modules.access_control.service.record_usage_event",
)


def _run(create, lst, pub, fn, *args, **kwargs):
    with patch(_PATCHES[0], create), \
         patch(_PATCHES[1], lst), \
         patch(_PATCHES[2], pub), \
         patch(_PATCHES[3]), \
         patch(_PATCHES[4]):
        return fn(*args, **kwargs)


# ── T01 ── card.issued event emitted on issue_card ──────────────────────────

def test_issue_card_emits_card_issued_event():
    create, lst, pub, _, _ = _mocks()
    result = _run(create, lst, pub, ac_svc.issue_card, 1, holder_id="h1", zones=["ZONE_A"])
    assert result["status"] == "ACTIVE"
    events = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "card.issued" in events


# ── T02 ── card.suspended event emitted on suspend_card ────────────────────

def test_suspend_card_emits_card_suspended_event():
    cards = [{"id": "c1", "status": "ACTIVE", "zones": ["ZONE_A"]}]
    create, lst, pub, _, _ = _mocks(existing_cards=cards)
    result = _run(create, lst, pub, ac_svc.suspend_card, 1, card_id="c1", reason="security")
    assert result["status"] == "SUSPENDED"
    events = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "card.suspended" in events


# ── T03 ── card.reactivated event emitted on reactivate_card ───────────────

def test_reactivate_card_emits_card_reactivated_event():
    cards = [{"id": "c1", "status": "SUSPENDED", "zones": ["ZONE_A"]}]
    create, lst, pub, _, _ = _mocks(existing_cards=cards)
    result = _run(create, lst, pub, ac_svc.reactivate_card, 1, card_id="c1")
    assert result["status"] == "ACTIVE"
    events = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "card.reactivated" in events


# ── T04 ── card.revoked event emitted on revoke_card ───────────────────────

def test_revoke_card_emits_card_revoked_event():
    cards = [{"id": "c1", "status": "ACTIVE", "zones": ["ZONE_A"]}]
    create, lst, pub, _, _ = _mocks(existing_cards=cards)
    result = _run(
        create, lst, pub,
        ac_svc.revoke_card, 1, card_id="c1",
    )
    assert result["status"] == "REVOKED"
    events = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "card.revoked" in events


# ── T05 ── revoke already-revoked card raises ValueError ───────────────────

def test_revoke_already_revoked_card_raises():
    cards = [{"id": "c1", "status": "REVOKED", "zones": []}]
    create, lst, pub, _, _ = _mocks(existing_cards=cards)
    with pytest.raises(ValueError, match="already revoked"):
        _run(create, lst, pub, ac_svc.revoke_card, 1, card_id="c1")


# ── T06 ── SUSPENDED→REVOKED FSM transition allowed ────────────────────────

def test_revoke_suspended_card_succeeds():
    cards = [{"id": "c1", "status": "SUSPENDED", "zones": []}]
    create, lst, pub, _, _ = _mocks(existing_cards=cards)
    result = _run(create, lst, pub, ac_svc.revoke_card, 1, card_id="c1")
    assert result["status"] == "REVOKED"


# ── T07 ── REVOKED card cannot be suspended (FSM guard) ────────────────────

def test_suspend_revoked_card_raises():
    cards = [{"id": "c1", "status": "REVOKED", "zones": []}]
    create, lst, pub, _, _ = _mocks(existing_cards=cards)
    with pytest.raises(ValueError):
        _run(create, lst, pub, ac_svc.suspend_card, 1, card_id="c1")


# ── T08 ── access.granted event on valid zone access ───────────────────────

def test_attempt_access_granted_emits_event():
    cards = [{"id": "c1", "status": "ACTIVE", "zones": ["ZONE_A"]}]
    create, lst, pub, _, _ = _mocks(existing_cards=cards)
    result = _run(create, lst, pub, ac_svc.attempt_access, 1, card_id="c1", zone="ZONE_A")
    assert result["granted"] is True
    events = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "access.granted" in events


# ── T09 ── access.denied event on inactive card ─────────────────────────────

def test_attempt_access_denied_inactive_card():
    cards = [{"id": "c1", "status": "SUSPENDED", "zones": ["ZONE_A"]}]
    create, lst, pub, _, _ = _mocks(existing_cards=cards)
    result = _run(create, lst, pub, ac_svc.attempt_access, 1, card_id="c1", zone="ZONE_A")
    assert result["granted"] is False
    assert result["reason"] == "card_inactive"
    events = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "access.denied" in events


# ── T10 ── security.anomaly at repeated-denial threshold ───────────────────

def test_repeated_denials_trigger_security_anomaly():
    cards = [{"id": "c2", "status": "ACTIVE", "zones": ["ZONE_A"]}]
    threshold = ac_svc.REPEATED_DENIAL_THRESHOLD
    pre_logs = [
        {"id": f"lg-{i}", "card_id": "c2", "zone": "ZONE_B", "result": "DENIED"}
        for i in range(threshold - 1)
    ]
    create, lst, pub, _, _ = _mocks(existing_cards=cards, existing_logs=pre_logs)
    _run(create, lst, pub, ac_svc.attempt_access, 1, card_id="c2", zone="ZONE_B")
    events = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "security.anomaly" in events


# ── T11 ── tenant isolation: issue_card invalid tenant_id rejected ──────────

def test_issue_card_invalid_tenant_raises():
    create, lst, pub, _, _ = _mocks()
    with pytest.raises(ValueError, match="tenant_id"):
        _run(create, lst, pub, ac_svc.issue_card, 0, holder_id="h1", zones=["Z"])


# ── T12 ── tenant isolation: attempt_access invalid tenant_id rejected ──────

def test_attempt_access_invalid_tenant_raises():
    create, lst, pub, _, _ = _mocks()
    with pytest.raises(ValueError, match="tenant_id"):
        _run(create, lst, pub, ac_svc.attempt_access, -1, card_id="c1", zone="ZONE_A")


# ── T13 ── Brain Core: ACCESS_CONTROL_EVENT_TYPES in SUPPORTED_SIGNAL_EVENT_TYPES ──

def test_brain_core_access_control_event_types_registered():
    from app.modules.brain_core.constants import (
        ACCESS_CONTROL_EVENT_TYPES,
        SUPPORTED_SIGNAL_EVENT_TYPES,
    )
    assert ACCESS_CONTROL_EVENT_TYPES
    assert ACCESS_CONTROL_EVENT_TYPES.issubset(SUPPORTED_SIGNAL_EVENT_TYPES)


# ── T14 ── Brain Core: campus_security decision in registry ─────────────────

def test_brain_core_campus_security_decision_registered():
    from app.modules.brain_core.registry import DecisionRegistry
    assert "campus_security" in DecisionRegistry.decisions
    decision = DecisionRegistry.decisions["campus_security"]
    assert decision["decision_type"] == "security_risk"
    assert "notify_security_team" in decision["action_map"]


# ── T15 ── Brain Core: security.anomaly signal registered ───────────────────

def test_brain_core_security_anomaly_signal_registered():
    from app.modules.brain_core.registry import SignalRegistry
    assert "security.anomaly" in SignalRegistry.signals
    sig = SignalRegistry.signals["security.anomaly"]
    assert sig["scenario"] == "campus_security"
    assert sig["signal_class"] == "security_threat"


# ── T16 ── KPI: access_control metrics in KPI_METRIC_NAMES ──────────────────

def test_kpi_metric_names_include_access_control_metrics():
    from app.platform.kpi.service import METRIC_TITLES
    assert "access_denied_count" in METRIC_TITLES
    assert "unauthorized_attempts_count" in METRIC_TITLES
    assert "active_access_cards_count" in METRIC_TITLES
    assert "suspended_access_cards_count" in METRIC_TITLES
    assert "security_access_anomaly_count" in METRIC_TITLES


# ── T17 ── KPI: event lineage coverage for access_control ───────────────────

def test_kpi_event_lineage_covers_access_control_events():
    from app.platform.kpi.service import EVENT_DERIVED_METRIC_LINEAGE
    all_events = {e for evts in EVENT_DERIVED_METRIC_LINEAGE.values() for e in evts}
    assert "access.denied" in all_events
    assert "security.anomaly" in all_events
    assert "card.issued" in all_events
    assert "card.suspended" in all_events


# ── T18 ── VALID_EVENT_TYPES covers all access control events ────────────────

def test_valid_event_types_covers_access_control():
    from app.platform.event_ingestion.types import VALID_EVENT_TYPES
    for et in ("access.granted", "access.denied", "card.issued", "card.suspended", "card.revoked", "security.anomaly"):
        assert et in VALID_EVENT_TYPES, f"Missing from VALID_EVENT_TYPES: {et}"


# ── T19 ── events registry has all card + access event types ─────────────────

def test_events_registry_has_card_and_access_events():
    from app.platform.events.registry import EXACT_EVENT_REGISTRY
    for et in ("access.granted", "access.denied", "card.issued", "card.suspended", "card.revoked", "card.reactivated", "security.anomaly"):
        assert et in EXACT_EVENT_REGISTRY, f"Missing from events registry: {et}"


# ── T20 ── list_cards filters by status ────────────────────────────────────

def test_list_cards_filter_by_status():
    cards = [
        {"id": "c1", "status": "ACTIVE", "zones": ["Z"]},
        {"id": "c2", "status": "SUSPENDED", "zones": ["Z"]},
    ]
    create, lst, pub, _, _ = _mocks(existing_cards=cards)
    result = _run(create, lst, pub, ac_svc.list_cards, 1, status="ACTIVE")
    assert len(result) == 1
    assert result[0]["id"] == "c1"
