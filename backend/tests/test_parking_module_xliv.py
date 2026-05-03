"""Phase XLIV — Parking Module tests (15 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.modules.parking.service as pk


def _mocks(lots=None, permits=None, sessions=None, violations=None):
    lots = list(lots or [])
    permits = list(permits or [])
    sessions = list(sessions or [])
    violations = list(violations or [])
    counter = {"n": 0}

    def _create(tid, table, data):
        counter["n"] += 1
        row = {"id": f"row-{counter['n']}", **data}
        if table == "parking_lots":
            lots.append(row)
        elif table == "parking_permits":
            permits.append(row)
        elif table == "parking_sessions":
            sessions.append(row)
        elif table == "parking_violations":
            violations.append(row)
        return row

    def _list(tid, table):
        if table == "parking_lots":
            return list(lots)
        if table == "parking_permits":
            return list(permits)
        if table == "parking_sessions":
            return list(sessions)
        if table == "parking_violations":
            return list(violations)
        return []

    pub = MagicMock()
    pub.return_value.publish_event = MagicMock()
    return _create, _list, pub, lots, permits, sessions, violations


# 1) PERMIT_STATES constant
def test_permit_states():
    assert {"PENDING", "ACTIVE", "EXPIRED", "REVOKED"} == pk.PERMIT_STATES


# 2) SESSION_STATES constant
def test_session_states():
    assert {"OPEN", "CLOSED"} == pk.SESSION_STATES


# 3) create_lot success
def test_create_lot_success():
    create, lst, pub, _, _, _, _ = _mocks()
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        result = pk.create_lot(1, name="Lot A", capacity=50)
    assert result["name"] == "Lot A"
    assert result["capacity"] == 50


# 4) create_lot missing name
def test_create_lot_missing_name():
    create, lst, pub, _, _, _, _ = _mocks()
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        with pytest.raises(ValueError, match="name"):
            pk.create_lot(1, name="", capacity=50)


# 5) create_lot zero capacity
def test_create_lot_zero_capacity():
    create, lst, pub, _, _, _, _ = _mocks()
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        with pytest.raises(ValueError, match="capacity"):
            pk.create_lot(1, name="X", capacity=0)


# 6) apply_permit success → PENDING
def test_apply_permit_success():
    create, lst, pub, _, _, _, _ = _mocks()
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        result = pk.apply_permit(1, holder_id="s1", lot_id="l1", vehicle_plate="AB1234",
                                 valid_from="2025-01-01", valid_until="2025-12-31")
    assert result["status"] == "PENDING"


# 7) apply_permit missing plate
def test_apply_permit_missing_plate():
    create, lst, pub, _, _, _, _ = _mocks()
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        with pytest.raises(ValueError, match="vehicle_plate"):
            pk.apply_permit(1, holder_id="s1", lot_id="l1", vehicle_plate="",
                            valid_from="2025-01-01", valid_until="2025-12-31")


# 8) approve_permit fires parking.permit_issued
def test_approve_permit_fires_event():
    permits = [{"id": "p1", "status": "PENDING", "holder_id": "s1"}]
    create, lst, pub, _, _, _, _ = _mocks(permits=permits)
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        result = pk.approve_permit(1, permit_id="p1")
    assert result["status"] == "ACTIVE"
    pub.return_value.publish_event.assert_called_once()
    assert pub.return_value.publish_event.call_args.kwargs["event_type"] == "parking.permit_issued"


# 9) revoke_permit success
def test_revoke_permit_success():
    permits = [{"id": "p1", "status": "ACTIVE", "holder_id": "s1"}]
    create, lst, pub, _, _, _, _ = _mocks(permits=permits)
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        result = pk.revoke_permit(1, permit_id="p1")
    assert result["status"] == "REVOKED"


# 10) revoke_permit already revoked raises
def test_revoke_permit_already_revoked():
    permits = [{"id": "p1", "status": "REVOKED", "holder_id": "s1"}]
    create, lst, pub, _, _, _, _ = _mocks(permits=permits)
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        with pytest.raises(ValueError, match="revoked"):
            pk.revoke_permit(1, permit_id="p1")


# 11) open_session success
def test_open_session_success():
    lots = [{"id": "l1", "capacity": 10}]
    permits = [{"id": "p1", "status": "ACTIVE", "lot_id": "l1"}]
    create, lst, pub, _, _, _, _ = _mocks(lots=lots, permits=permits)
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        result = pk.open_session(1, permit_id="p1", lot_id="l1")
    assert result["status"] == "OPEN"


# 12) open_session inactive permit raises
def test_open_session_inactive_permit():
    permits = [{"id": "p1", "status": "PENDING", "lot_id": "l1"}]
    create, lst, pub, _, _, _, _ = _mocks(permits=permits)
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        with pytest.raises(ValueError, match="ACTIVE"):
            pk.open_session(1, permit_id="p1", lot_id="l1")


# 13) lot_full fires event at 100% occupancy
def test_lot_full_event():
    lots = [{"id": "l1", "capacity": 1}]
    permits = [{"id": "p1", "status": "ACTIVE", "lot_id": "l1"}]
    # pre-seed 1 open session (lot capacity=1, adding another → 2/1 → full)
    existing_sessions = [{"id": "s0", "lot_id": "l1", "status": "OPEN"}]
    create, lst, pub, _, _, _, _ = _mocks(lots=lots, permits=permits, sessions=existing_sessions)
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        pk.open_session(1, permit_id="p1", lot_id="l1")
    events = [c.kwargs["event_type"] for c in pub.return_value.publish_event.call_args_list]
    assert "parking.lot_full" in events


# 14) close_session success
def test_close_session_success():
    sessions = [{"id": "s1", "status": "OPEN", "lot_id": "l1"}]
    create, lst, pub, _, _, _, _ = _mocks(sessions=sessions)
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        result = pk.close_session(1, session_id="s1")
    assert result["status"] == "CLOSED"


# 15) record_violation fires parking.violation_recorded
def test_record_violation_fires_event():
    create, lst, pub, _, _, _, _ = _mocks()
    with patch("app.modules.parking.service.create_entity_for_tenant", create), \
         patch("app.modules.parking.service.list_entities_for_tenant", lst), \
         patch("app.modules.parking.service.EventPublisher", pub):
        result = pk.record_violation(1, vehicle_plate="XY9999", lot_id="l1",
                                     violation_type="NO_PERMIT", fine_amount=50.0)
    assert "violation_id" in result
    pub.return_value.publish_event.assert_called_once()
    assert pub.return_value.publish_event.call_args.kwargs["event_type"] == "parking.violation_recorded"
