"""W122 — facilities_work_orders: Facility Safety Incident Guard (behavioral depth).

Real-world problem:
    create_work_order() had only SLA cap + delay-queue cap guards — NO cross-entity
    check against security_incidents.  A maintenance technician could be dispatched
    (work order created) for a facility that has an active high-severity security
    incident in progress — physical safety risk.

Root fix (W122):
    Guard _check_facility_clear_for_work_order() is FIRST action in create_work_order()
    before any cap check or persist call.  Fail-closed: if security_incidents lookup
    fails → DomainValidationError (never silently allow).
    Router POST now catches (ValueError, DomainValidationError) → HTTP 422.

Guard answers the 5 hardening questions:
1. Dangerous action      : create_work_order dispatches maintenance technician to facility
2. Real-world constraint : facilities with active high-severity incidents are unsafe
3. External entity       : security_incidents
4. Validate BEFORE       : create_entity_for_tenant("facilities_work_orders", ...)
5. Bad outcome prevented : maintenance staff sent into active security incident zone
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.facilities_work_orders.schemas import WorkOrderCreateSchema
from app.modules.facilities_work_orders.service import (
    _FACILITY_BLOCKING_SEVERITIES,
    _FACILITY_SAFE_STATUSES,
    _PRIORITY_MAX_OPEN,
    _check_facility_clear_for_work_order,
    create_work_order,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

OPEN_CRITICAL_INCIDENT = {
    "id": 1,
    "incident_code": "INC-001",
    "facility_code": "FAC-A",
    "status": "open",
    "severity": "critical",
    "tenant_id": 1,
}
INVESTIGATING_HIGH_INCIDENT = {
    "id": 2,
    "incident_code": "INC-002",
    "facility_code": "FAC-A",
    "status": "investigating",
    "severity": "high",
    "tenant_id": 1,
}
RESOLVED_CRITICAL_INCIDENT = {
    "id": 3,
    "incident_code": "INC-003",
    "facility_code": "FAC-A",
    "status": "resolved",
    "severity": "critical",
    "tenant_id": 1,
}
OPEN_LOW_INCIDENT = {
    "id": 4,
    "incident_code": "INC-004",
    "facility_code": "FAC-A",
    "status": "open",
    "severity": "low",
    "tenant_id": 1,
}
OTHER_FACILITY_INCIDENT = {
    "id": 5,
    "incident_code": "INC-005",
    "facility_code": "FAC-B",
    "status": "open",
    "severity": "critical",
    "tenant_id": 1,
}


def _make_payload(
    facility_code: str = "FAC-CLEAR",
    priority: str = "medium",
    assigned_to: str | None = None,
) -> WorkOrderCreateSchema:
    return WorkOrderCreateSchema(
        order_code=f"WO-{facility_code}-001",
        facility_code=facility_code,
        title="Fix HVAC unit",
        work_type="repair",
        priority=priority,  # type: ignore[arg-type]
        status="open",
        assigned_to=assigned_to,
    )


# ---------------------------------------------------------------------------
# TestW122Constants
# ---------------------------------------------------------------------------


class TestW122Constants:
    def test_facility_safe_statuses_is_frozenset(self):
        assert isinstance(_FACILITY_SAFE_STATUSES, frozenset)

    def test_open_in_facility_safe_statuses(self):
        assert "open" in _FACILITY_SAFE_STATUSES

    def test_investigating_in_facility_safe_statuses(self):
        assert "investigating" in _FACILITY_SAFE_STATUSES

    def test_resolved_not_in_facility_safe_statuses(self):
        assert "resolved" not in _FACILITY_SAFE_STATUSES

    def test_closed_not_in_facility_safe_statuses(self):
        assert "closed" not in _FACILITY_SAFE_STATUSES

    def test_facility_blocking_severities_is_frozenset(self):
        assert isinstance(_FACILITY_BLOCKING_SEVERITIES, frozenset)

    def test_high_in_blocking_severities(self):
        assert "high" in _FACILITY_BLOCKING_SEVERITIES

    def test_critical_in_blocking_severities(self):
        assert "critical" in _FACILITY_BLOCKING_SEVERITIES

    def test_low_not_in_blocking_severities(self):
        assert "low" not in _FACILITY_BLOCKING_SEVERITIES

    def test_medium_not_in_blocking_severities(self):
        assert "medium" not in _FACILITY_BLOCKING_SEVERITIES

    def test_priority_max_open_is_dict(self):
        assert isinstance(_PRIORITY_MAX_OPEN, dict)

    def test_critical_cap_is_three(self):
        assert _PRIORITY_MAX_OPEN.get("critical") == 3


# ---------------------------------------------------------------------------
# TestW122GuardSignature
# ---------------------------------------------------------------------------


class TestW122GuardSignature:
    def test_guard_passes_for_clear_facility(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-CLEAR")

    def test_guard_passes_when_only_resolved_incidents(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [RESOLVED_CRITICAL_INCIDENT],
        )
        _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_guard_passes_when_only_low_severity_open(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [OPEN_LOW_INCIDENT],
        )
        _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_guard_raises_for_open_critical(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [OPEN_CRITICAL_INCIDENT],
        )
        with pytest.raises(DomainValidationError):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_guard_raises_for_investigating_high(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [INVESTIGATING_HIGH_INCIDENT],
        )
        with pytest.raises(DomainValidationError):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")


# ---------------------------------------------------------------------------
# TestW122GuardFailures — all blocked scenarios
# ---------------------------------------------------------------------------


class TestW122GuardFailures:
    def test_open_critical_incident_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [OPEN_CRITICAL_INCIDENT],
        )
        with pytest.raises(DomainValidationError, match="INC-001"):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_investigating_high_incident_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [INVESTIGATING_HIGH_INCIDENT],
        )
        with pytest.raises(DomainValidationError, match="INC-002"):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_multiple_blocking_incidents_listed_in_error(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [OPEN_CRITICAL_INCIDENT, INVESTIGATING_HIGH_INCIDENT],
        )
        with pytest.raises(DomainValidationError, match="INC-001"):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_empty_facility_code_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="facility_code is missing"):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="")

    def test_none_facility_code_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="facility_code is missing"):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code=None)  # type: ignore

    def test_other_facility_incident_does_not_block(self, monkeypatch):
        """Incident on FAC-B must not block work order for FAC-A."""
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [OTHER_FACILITY_INCIDENT],  # FAC-B
        )
        _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")


# ---------------------------------------------------------------------------
# TestW122FailClosed — lookup failure → DomainValidationError
# ---------------------------------------------------------------------------


class TestW122FailClosed:
    def test_runtime_error_raises_domain_validation_error(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise RuntimeError("DB unavailable")

        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError, match="security_incidents lookup failed"):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_connection_error_blocks(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise ConnectionError("network error")

        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_ioerror_blocks(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise IOError("timeout")

        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_fail_closed_error_mentions_facility_code(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise Exception("unexpected error")

        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError, match="FAC-ZONE-9"):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-ZONE-9")


# ---------------------------------------------------------------------------
# TestW122CreatePath — end-to-end create_work_order integration
# ---------------------------------------------------------------------------


class TestW122CreatePath:
    def _setup(self, monkeypatch, incidents=None, existing_orders=None):
        incidents = incidents or []
        existing_orders = existing_orders or []
        created: dict[str, object] = {}

        def mock_list(entity_name, tenant_id):
            if entity_name == "security_incidents":
                return incidents
            if entity_name == "facilities_work_orders":
                return existing_orders
            return []

        def mock_create(entity_name, payload, tenant_id):
            record = dict(payload)
            record["id"] = 55
            record["tenant_id"] = str(tenant_id)
            created["entity_name"] = entity_name
            created["payload"] = record
            return record

        def mock_log(*args, **kwargs):
            pass

        def mock_publish(*args, **kwargs):
            pass

        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.create_entity_for_tenant", mock_create
        )
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.log_admin_action", mock_log
        )
        monkeypatch.setattr(
            "app.platform.events.publisher.EventPublisher.publish_event", mock_publish
        )
        return created

    def test_create_succeeds_for_clear_facility(self, monkeypatch):
        self._setup(monkeypatch, incidents=[])
        result = create_work_order(1, _make_payload(facility_code="FAC-CLEAR"), actor="admin")
        assert result.id == 55

    def test_create_blocked_for_facility_with_active_critical_incident(self, monkeypatch):
        self._setup(monkeypatch, incidents=[OPEN_CRITICAL_INCIDENT])
        with pytest.raises(DomainValidationError):
            create_work_order(1, _make_payload(facility_code="FAC-A"), actor="admin")

    def test_create_blocked_for_facility_with_investigating_high_incident(self, monkeypatch):
        self._setup(monkeypatch, incidents=[INVESTIGATING_HIGH_INCIDENT])
        with pytest.raises(DomainValidationError):
            create_work_order(1, _make_payload(facility_code="FAC-A"), actor="admin")

    def test_guard_fires_before_cap_check(self, monkeypatch):
        """Security incident guard must fire before SLA cap checks — incidents queried first."""
        lookup_order: list[str] = []

        def mock_list(entity_name, tenant_id):
            lookup_order.append(entity_name)
            if entity_name == "security_incidents":
                return [OPEN_CRITICAL_INCIDENT]  # trigger guard failure
            return []

        def mock_create(entity_name, payload, tenant_id):
            return {"id": 1}

        def mock_log(*args, **kwargs):
            pass

        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.create_entity_for_tenant", mock_create
        )
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.log_admin_action", mock_log
        )
        with pytest.raises(DomainValidationError):
            create_work_order(1, _make_payload(facility_code="FAC-A"), actor="admin")

        assert lookup_order[0] == "security_incidents"

    def test_not_persisted_when_guard_fails(self, monkeypatch):
        created_calls: list[str] = []

        def mock_list(entity_name, tenant_id):
            if entity_name == "security_incidents":
                return [OPEN_CRITICAL_INCIDENT]
            return []

        def mock_create(entity_name, payload, tenant_id):
            created_calls.append(entity_name)
            return {"id": 1}

        def mock_log(*args, **kwargs):
            pass

        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.create_entity_for_tenant", mock_create
        )
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.log_admin_action", mock_log
        )
        with pytest.raises(DomainValidationError):
            create_work_order(1, _make_payload(facility_code="FAC-A"), actor="admin")

        assert "facilities_work_orders" not in created_calls


# ---------------------------------------------------------------------------
# TestW122BusinessInvariants — multi-tenant, combined, edge cases
# ---------------------------------------------------------------------------


class TestW122BusinessInvariants:
    def test_two_tenants_isolated(self, monkeypatch):
        """Incident for tenant 1 must not block tenant 2 if tenant 2 has none."""

        def mock_list(entity_name, tenant_id):
            if entity_name == "security_incidents" and tenant_id == 1:
                return [OPEN_CRITICAL_INCIDENT]
            return []

        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant", mock_list
        )
        # Tenant 1 — blocked
        with pytest.raises(DomainValidationError):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")
        # Tenant 2 — clear
        _check_facility_clear_for_work_order(tenant_id=2, facility_code="FAC-A")

    def test_resolved_and_open_mixed_blocks(self, monkeypatch):
        """Resolved incident + open critical → still blocked."""
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda e, t: [RESOLVED_CRITICAL_INCIDENT, OPEN_CRITICAL_INCIDENT],
        )
        with pytest.raises(DomainValidationError, match="INC-001"):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_case_insensitive_facility_match(self, monkeypatch):
        """Guard must match facility_code case-insensitively."""
        incident_upper = {**OPEN_CRITICAL_INCIDENT, "facility_code": "fac-a"}
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda e, t: [incident_upper],
        )
        with pytest.raises(DomainValidationError):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_whitespace_trimmed_facility_code(self, monkeypatch):
        """Whitespace in facility_code is trimmed before matching."""
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda e, t: [OPEN_CRITICAL_INCIDENT],
        )
        with pytest.raises(DomainValidationError):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="  FAC-A  ")

    def test_error_message_includes_facility_code(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda e, t: [OPEN_CRITICAL_INCIDENT],
        )
        with pytest.raises(DomainValidationError, match="FAC-A"):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_error_message_includes_resolve_guidance(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda e, t: [OPEN_CRITICAL_INCIDENT],
        )
        with pytest.raises(DomainValidationError, match="Resolve security incidents"):
            _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")

    def test_medium_severity_open_does_not_block(self, monkeypatch):
        """Open medium-severity incident must NOT block work order creation."""
        medium_incident = {
            "id": 10,
            "incident_code": "INC-010",
            "facility_code": "FAC-A",
            "status": "open",
            "severity": "medium",
            "tenant_id": 1,
        }
        monkeypatch.setattr(
            "app.modules.facilities_work_orders.service.list_entities_for_tenant",
            lambda e, t: [medium_incident],
        )
        _check_facility_clear_for_work_order(tenant_id=1, facility_code="FAC-A")
