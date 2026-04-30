"""W89 — facilities_work_orders: closure blocked by active high-severity security incidents.

Behavioral tests for cross-entity transition guard in update_work_order_status().
"""
from __future__ import annotations

from unittest.mock import patch

import pytest



def _make_work_order(
    id_: int = 42,
    status: str = "in_progress",
    facility_code: str = "BLDG-A",
) -> dict:
    return {
        "id": id_,
        "order_code": f"WO-{id_:03d}",
        "facility_code": facility_code,
        "title": "Repair HVAC",
        "work_type": "repair",
        "priority": "high",
        "assigned_to": "tech-1",
        "status": status,
    }



def _make_incident(
    id_: int,
    *,
    facility_code: str,
    severity: str,
    status: str,
    incident_code: str | None = None,
) -> dict:
    return {
        "id": id_,
        "incident_code": incident_code or f"INC-{id_:03d}",
        "facility_code": facility_code,
        "severity": severity,
        "status": status,
    }



def test_w89_guard_function_exists_and_callable():
    from app.modules.facilities_work_orders.service import _check_no_blocking_security_incidents

    assert callable(_check_no_blocking_security_incidents)



def test_w89_closure_and_security_constants_exist():
    from app.modules.facilities_work_orders.service import (
        _BLOCKING_SECURITY_INCIDENT_SEVERITIES,
        _BLOCKING_SECURITY_INCIDENT_STATUSES,
        _CLOSURE_STATUSES,
    )

    assert isinstance(_CLOSURE_STATUSES, frozenset)
    assert "completed" in _CLOSURE_STATUSES
    assert "cancelled" in _CLOSURE_STATUSES

    assert isinstance(_BLOCKING_SECURITY_INCIDENT_STATUSES, frozenset)
    assert "open" in _BLOCKING_SECURITY_INCIDENT_STATUSES
    assert "investigating" in _BLOCKING_SECURITY_INCIDENT_STATUSES

    assert isinstance(_BLOCKING_SECURITY_INCIDENT_SEVERITIES, frozenset)
    assert "high" in _BLOCKING_SECURITY_INCIDENT_SEVERITIES
    assert "critical" in _BLOCKING_SECURITY_INCIDENT_SEVERITIES



def test_w89_completed_blocked_when_open_high_incident_same_facility():
    from app.core.module_helpers.service_validation import DomainValidationError
    from app.modules.facilities_work_orders.schemas import WorkOrderStatusUpdateSchema
    from app.modules.facilities_work_orders.service import update_work_order_status

    order = _make_work_order(status="in_progress", facility_code="BLDG-A")
    incidents = [_make_incident(7, facility_code="BLDG-A", severity="high", status="open")]

    with patch(
        "app.modules.facilities_work_orders.service.list_entities_for_tenant",
        side_effect=lambda name, _: [order] if name == "facilities_work_orders" else incidents,
    ), patch(
        "app.modules.facilities_work_orders.service.update_entity_for_tenant"
    ) as update_mock:
        with pytest.raises(DomainValidationError, match="active high-severity security incidents"):
            update_work_order_status(
                tenant_id=1,
                order_id=42,
                request=WorkOrderStatusUpdateSchema(status="completed"),
                actor="tester",
            )

    update_mock.assert_not_called()



def test_w89_cancelled_blocked_when_investigating_critical_incident():
    from app.core.module_helpers.service_validation import DomainValidationError
    from app.modules.facilities_work_orders.schemas import WorkOrderStatusUpdateSchema
    from app.modules.facilities_work_orders.service import update_work_order_status

    order = _make_work_order(status="in_progress", facility_code="BLDG-A")
    incidents = [
        _make_incident(
            8,
            facility_code="BLDG-A",
            severity="critical",
            status="investigating",
            incident_code="INC-CRIT-8",
        )
    ]

    with patch(
        "app.modules.facilities_work_orders.service.list_entities_for_tenant",
        side_effect=lambda name, _: [order] if name == "facilities_work_orders" else incidents,
    ):
        with pytest.raises(DomainValidationError, match="INC-CRIT-8"):
            update_work_order_status(
                tenant_id=1,
                order_id=42,
                request=WorkOrderStatusUpdateSchema(status="cancelled"),
                actor="tester",
            )



def test_w89_completed_allowed_when_incident_low_severity():
    from app.modules.facilities_work_orders.schemas import WorkOrderStatusUpdateSchema
    from app.modules.facilities_work_orders.service import update_work_order_status

    order = _make_work_order(status="in_progress", facility_code="BLDG-A")
    incidents = [_make_incident(9, facility_code="BLDG-A", severity="low", status="open")]

    with patch(
        "app.modules.facilities_work_orders.service.list_entities_for_tenant",
        side_effect=lambda name, _: [order] if name == "facilities_work_orders" else incidents,
    ), patch(
        "app.modules.facilities_work_orders.service.update_entity_for_tenant",
        side_effect=lambda *_args, **_kwargs: {**order, "status": "completed"},
    ), patch("app.modules.facilities_work_orders.service._emit_audit"):
        updated = update_work_order_status(
            tenant_id=1,
            order_id=42,
            request=WorkOrderStatusUpdateSchema(status="completed"),
            actor="tester",
        )

    assert updated is not None
    assert updated.status == "completed"



def test_w89_completed_allowed_when_blocking_incident_in_other_facility():
    from app.modules.facilities_work_orders.schemas import WorkOrderStatusUpdateSchema
    from app.modules.facilities_work_orders.service import update_work_order_status

    order = _make_work_order(status="in_progress", facility_code="BLDG-A")
    incidents = [_make_incident(10, facility_code="BLDG-B", severity="critical", status="open")]

    with patch(
        "app.modules.facilities_work_orders.service.list_entities_for_tenant",
        side_effect=lambda name, _: [order] if name == "facilities_work_orders" else incidents,
    ), patch(
        "app.modules.facilities_work_orders.service.update_entity_for_tenant",
        side_effect=lambda *_args, **_kwargs: {**order, "status": "completed"},
    ), patch("app.modules.facilities_work_orders.service._emit_audit"):
        updated = update_work_order_status(
            tenant_id=1,
            order_id=42,
            request=WorkOrderStatusUpdateSchema(status="completed"),
            actor="tester",
        )

    assert updated is not None
    assert updated.status == "completed"



def test_w89_non_closure_transition_skips_security_incident_query():
    from app.modules.facilities_work_orders.schemas import WorkOrderStatusUpdateSchema
    from app.modules.facilities_work_orders.service import update_work_order_status

    order = _make_work_order(status="open", facility_code="BLDG-A")

    call_log: list[str] = []

    def _list_entities(name: str, _tenant_id: int):
        call_log.append(name)
        if name == "facilities_work_orders":
            return [order]
        if name == "security_incidents":
            raise AssertionError("security_incidents must not be queried for non-closure transition")
        return []

    with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant", side_effect=_list_entities), patch(
        "app.modules.facilities_work_orders.service.update_entity_for_tenant",
        side_effect=lambda *_args, **_kwargs: {**order, "status": "in_progress"},
    ), patch("app.modules.facilities_work_orders.service._emit_audit"):
        updated = update_work_order_status(
            tenant_id=1,
            order_id=42,
            request=WorkOrderStatusUpdateSchema(status="in_progress"),
            actor="tester",
        )

    assert updated is not None
    assert updated.status == "in_progress"
    assert call_log.count("facilities_work_orders") == 1



def test_w89_no_silent_fallback_when_incident_query_fails():
    from app.core.module_helpers.service_validation import DomainValidationError
    from app.modules.facilities_work_orders.schemas import WorkOrderStatusUpdateSchema
    from app.modules.facilities_work_orders.service import update_work_order_status

    order = _make_work_order(status="in_progress", facility_code="BLDG-A")

    def _list_entities(name: str, _tenant_id: int):
        if name == "facilities_work_orders":
            return [order]
        if name == "security_incidents":
            raise RuntimeError("DB down")
        return []

    with patch("app.modules.facilities_work_orders.service.list_entities_for_tenant", side_effect=_list_entities):
        with pytest.raises(DomainValidationError, match="query failed"):
            update_work_order_status(
                tenant_id=1,
                order_id=42,
                request=WorkOrderStatusUpdateSchema(status="completed"),
                actor="tester",
            )



def test_w89_closure_blocked_when_facility_code_missing():
    from app.core.module_helpers.service_validation import DomainValidationError
    from app.modules.facilities_work_orders.schemas import WorkOrderStatusUpdateSchema
    from app.modules.facilities_work_orders.service import update_work_order_status

    order = _make_work_order(status="in_progress", facility_code="")

    with patch(
        "app.modules.facilities_work_orders.service.list_entities_for_tenant",
        side_effect=lambda name, _: [order] if name == "facilities_work_orders" else [],
    ):
        with pytest.raises(DomainValidationError, match="facility_code is missing"):
            update_work_order_status(
                tenant_id=1,
                order_id=42,
                request=WorkOrderStatusUpdateSchema(status="completed"),
                actor="tester",
            )
