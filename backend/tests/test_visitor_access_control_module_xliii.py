"""Phase XLIII — Visitor Management + Access Control tests (20 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ─── visitor_management ───────────────────────────────────────────────────────

import app.modules.visitor_management.service as vm_svc


def _vm_mocks(existing_visits=None):
    """Return (create_mock, list_mock, pub_mock)."""
    existing = list(existing_visits or [])
    counter = {"n": 0}

    def _create(tid, table, data):
        counter["n"] += 1
        row = {"id": f"vis-{counter['n']}", **data}
        existing.append(row)
        return row

    def _list(tid, table):
        return list(existing)

    pub = MagicMock()
    pub.return_value.publish_event = MagicMock()
    return _create, _list, pub, existing


# 1) VISIT_STATES constant
def test_visit_states_constant():
    assert "REQUESTED" in vm_svc.VISIT_STATES
    assert "APPROVED" in vm_svc.VISIT_STATES
    assert "CHECKED_IN" in vm_svc.VISIT_STATES
    assert "CHECKED_OUT" in vm_svc.VISIT_STATES
    assert "EXPIRED" in vm_svc.VISIT_STATES


# 2) register_visitor success
def test_register_visitor_success():
    create, lst, pub, _ = _vm_mocks()
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        result = vm_svc.register_visitor(1, name="Alice", host_id="h1", visit_date="2025-01-01")
    assert result["status"] == "REQUESTED"
    assert "visit_id" in result


# 3) register_visitor missing name
def test_register_visitor_missing_name():
    create, lst, pub, _ = _vm_mocks()
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        with pytest.raises(ValueError, match="name"):
            vm_svc.register_visitor(1, name="", host_id="h1", visit_date="2025-01-01")


# 4) register_visitor missing host
def test_register_visitor_missing_host():
    create, lst, pub, _ = _vm_mocks()
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        with pytest.raises(ValueError, match="host_id"):
            vm_svc.register_visitor(1, name="Alice", host_id="", visit_date="2025-01-01")


# 5) register_visitor missing visit_date
def test_register_visitor_missing_date():
    create, lst, pub, _ = _vm_mocks()
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        with pytest.raises(ValueError, match="visit_date"):
            vm_svc.register_visitor(1, name="Alice", host_id="h1", visit_date="")


# 6) register_visitor invalid tenant
def test_register_visitor_invalid_tenant():
    create, lst, pub, _ = _vm_mocks()
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        with pytest.raises(ValueError, match="tenant_id"):
            vm_svc.register_visitor(0, name="Alice", host_id="h1", visit_date="2025-01-01")


# 7) approve_visit success
def test_approve_visit_success():
    existing = [{"id": "v1", "status": "REQUESTED", "host_id": "h1"}]
    create, lst, pub, _ = _vm_mocks(existing)
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        result = vm_svc.approve_visit(1, visit_id="v1")
    assert result["status"] == "APPROVED"


# 8) approve_visit wrong status
def test_approve_visit_wrong_status():
    existing = [{"id": "v1", "status": "CHECKED_IN", "host_id": "h1"}]
    create, lst, pub, _ = _vm_mocks(existing)
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        with pytest.raises(ValueError):
            vm_svc.approve_visit(1, visit_id="v1")


# 9) check_in_visitor fires visitor.arrived
def test_check_in_visitor_fires_event():
    existing = [{"id": "v1", "status": "APPROVED", "host_id": "h1"}]
    create, lst, pub, _ = _vm_mocks(existing)
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        result = vm_svc.check_in_visitor(1, visit_id="v1", badge_number="B42")
    assert result["status"] == "CHECKED_IN"
    pub.return_value.publish_event.assert_called_once()
    call_kwargs = pub.return_value.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "visitor.arrived"


# 10) check_in_visitor missing badge
def test_check_in_visitor_missing_badge():
    existing = [{"id": "v1", "status": "APPROVED"}]
    create, lst, pub, _ = _vm_mocks(existing)
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        with pytest.raises(ValueError, match="badge"):
            vm_svc.check_in_visitor(1, visit_id="v1", badge_number="")


# 11) check_out_visitor success
def test_check_out_visitor_success():
    existing = [{"id": "v1", "status": "CHECKED_IN"}]
    create, lst, pub, _ = _vm_mocks(existing)
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        result = vm_svc.check_out_visitor(1, visit_id="v1")
    assert result["status"] == "CHECKED_OUT"


# 12) expire_visit success
def test_expire_visit_success():
    existing = [{"id": "v1", "status": "REQUESTED"}]
    create, lst, pub, _ = _vm_mocks(existing)
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        result = vm_svc.expire_visit(1, visit_id="v1")
    assert result["status"] == "EXPIRED"


# 13) expire_visit blocks terminal state
def test_expire_visit_blocks_terminal():
    existing = [{"id": "v1", "status": "CHECKED_OUT"}]
    create, lst, pub, _ = _vm_mocks(existing)
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        with pytest.raises(ValueError, match="terminal"):
            vm_svc.expire_visit(1, visit_id="v1")


# 14) record_unauthorized_attempt fires event
def test_record_unauthorized_attempt_fires_event():
    create, lst, pub, _ = _vm_mocks()
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        result = vm_svc.record_unauthorized_attempt(1, visitor_name="Bob", zone="SERVER_ROOM")
    assert "log_id" in result
    pub.return_value.publish_event.assert_called_once()
    call_kwargs = pub.return_value.publish_event.call_args.kwargs
    assert call_kwargs["event_type"] == "visitor.unauthorized_attempt"


# 15) list_visits filter by status
def test_list_visits_by_status():
    existing = [
        {"id": "v1", "status": "REQUESTED"},
        {"id": "v2", "status": "APPROVED"},
    ]
    create, lst, pub, _ = _vm_mocks(existing)
    with patch("app.modules.visitor_management.service.create_entity_for_tenant", create), \
         patch("app.modules.visitor_management.service.list_entities_for_tenant", lst), \
         patch("app.modules.visitor_management.service.EventPublisher", pub):
        result = vm_svc.list_visits(1, status="REQUESTED")
    assert len(result) == 1
    assert result[0]["id"] == "v1"


# ─── access_control ───────────────────────────────────────────────────────────

import app.modules.access_control.service as ac_svc


def _ac_mocks(existing_cards=None, existing_logs=None):
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


# 16) CARD_STATES constant
def test_card_states_constant():
    assert "ACTIVE" in ac_svc.CARD_STATES
    assert "SUSPENDED" in ac_svc.CARD_STATES
    assert "REVOKED" in ac_svc.CARD_STATES


# 17) issue_card success
def test_issue_card_success():
    create, lst, pub, _, _ = _ac_mocks()
    with patch("app.modules.access_control.service.create_entity_for_tenant", create), \
         patch("app.modules.access_control.service.list_entities_for_tenant", lst), \
         patch("app.modules.access_control.service.EventPublisher", pub):
        result = ac_svc.issue_card(1, holder_id="s1", zones=["ZONE_A"])
    assert result["status"] == "ACTIVE"
    assert "card_id" in result


# 18) attempt_access granted fires access.granted
def test_attempt_access_granted():
    cards = [{"id": "c1", "status": "ACTIVE", "zones": ["ZONE_A"]}]
    create, lst, pub, _, _ = _ac_mocks(existing_cards=cards)
    with patch("app.modules.access_control.service.create_entity_for_tenant", create), \
         patch("app.modules.access_control.service.list_entities_for_tenant", lst), \
         patch("app.modules.access_control.service.EventPublisher", pub):
        result = ac_svc.attempt_access(1, card_id="c1", zone="ZONE_A")
    assert result["granted"] is True
    pub.return_value.publish_event.assert_called_once()
    assert pub.return_value.publish_event.call_args.kwargs["event_type"] == "access.granted"


# 19) attempt_access denied fires access.denied
def test_attempt_access_denied():
    cards = [{"id": "c1", "status": "ACTIVE", "zones": ["ZONE_A"]}]
    logs: list = []
    create, lst, pub, _, _ = _ac_mocks(existing_cards=cards, existing_logs=logs)
    with patch("app.modules.access_control.service.create_entity_for_tenant", create), \
         patch("app.modules.access_control.service.list_entities_for_tenant", lst), \
         patch("app.modules.access_control.service.EventPublisher", pub):
        result = ac_svc.attempt_access(1, card_id="c1", zone="ZONE_B")
    assert result["granted"] is False
    events = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "access.denied" in events


# 20) security.anomaly fires at threshold
def test_attempt_access_security_anomaly():
    cards = [{"id": "c2", "status": "ACTIVE", "zones": ["ZONE_A"]}]
    # pre-seed logs with threshold-1 denials
    threshold = ac_svc.REPEATED_DENIAL_THRESHOLD
    existing_logs = [
        {"id": f"lg-{i}", "card_id": "c2", "zone": "ZONE_B", "result": "DENIED"}
        for i in range(threshold - 1)
    ]
    create, lst, pub, _, _ = _ac_mocks(existing_cards=cards, existing_logs=existing_logs)
    with patch("app.modules.access_control.service.create_entity_for_tenant", create), \
         patch("app.modules.access_control.service.list_entities_for_tenant", lst), \
         patch("app.modules.access_control.service.EventPublisher", pub):
        ac_svc.attempt_access(1, card_id="c2", zone="ZONE_B")
    events = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "security.anomaly" in events


# 21) suspend_card fires card.suspended
def test_suspend_card_fires_event():
    cards = [{"id": "c1", "status": "ACTIVE", "zones": ["ZONE_A"]}]
    create, lst, pub, _, _ = _ac_mocks(existing_cards=cards)
    with patch("app.modules.access_control.service.create_entity_for_tenant", create), \
         patch("app.modules.access_control.service.list_entities_for_tenant", lst), \
         patch("app.modules.access_control.service.EventPublisher", pub):
        result = ac_svc.suspend_card(1, card_id="c1")
    assert result["status"] == "SUSPENDED"
    pub.return_value.publish_event.assert_called_once()
    assert pub.return_value.publish_event.call_args.kwargs["event_type"] == "card.suspended"


# 22) revoke_card success
def test_revoke_card_success():
    cards = [{"id": "c1", "status": "ACTIVE", "zones": ["ZONE_A"]}]
    create, lst, pub, _, _ = _ac_mocks(existing_cards=cards)
    with patch("app.modules.access_control.service.create_entity_for_tenant", create), \
         patch("app.modules.access_control.service.list_entities_for_tenant", lst), \
         patch("app.modules.access_control.service.EventPublisher", pub):
        result = ac_svc.revoke_card(1, card_id="c1")
    assert result["status"] == "REVOKED"


# 23) suspend_card wrong status raises
def test_suspend_card_wrong_status():
    cards = [{"id": "c1", "status": "REVOKED", "zones": []}]
    create, lst, pub, _, _ = _ac_mocks(existing_cards=cards)
    with patch("app.modules.access_control.service.create_entity_for_tenant", create), \
         patch("app.modules.access_control.service.list_entities_for_tenant", lst), \
         patch("app.modules.access_control.service.EventPublisher", pub):
        with pytest.raises(ValueError):
            ac_svc.suspend_card(1, card_id="c1")
