"""W120 — campus_sla: Facility Active Maintenance Request Guard.

Real-world problem:
    create_sla_record() validated priority tier caps and SLA target ceilings but never
    checked whether the referenced facility_code has any active maintenance request in the
    system. Ghost SLA records for non-existent or idle facility codes inflate breach counts
    and corrupt institutional SLA compliance analytics.

Root fix:
    _check_facility_has_active_maintenance_request() — fail-closed cross-entity guard that
    validates facility_code against facilities_maintenance_requests BEFORE any persist.

Guard answers the 5 hardening questions:
1. Dangerous action      : creating a campus SLA record (feeds breach-rate compliance metrics)
2. Real-world constraint : SLA records must correspond to an actual open/pending maintenance
                           issue at the facility — no phantom SLA tracking allowed
3. External entity       : facilities_maintenance_requests
4. Validate BEFORE       : create_entity_for_tenant("campus_sla_records", ...)
5. Bad outcome prevented : Ghost SLA records inflate breach counts, corrupt compliance reports
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.campus_sla.service import (
    _ACTIVE_MAINTENANCE_STATUSES,
    _ACTIVE_SLA_STATUSES,
    _check_facility_has_active_maintenance_request,
    create_sla_record,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

ACTIVE_MAINT_REQUEST = {
    "request_code": "MR-001",
    "facility_code": "FAC-A",
    "issue_type": "plumbing",
    "severity": "high",
    "status": "open",
    "tenant_id": 1,
}
PENDING_MAINT_REQUEST = {
    "request_code": "MR-002",
    "facility_code": "FAC-B",
    "issue_type": "electrical",
    "severity": "medium",
    "status": "pending",
    "tenant_id": 1,
}
IN_PROGRESS_MAINT_REQUEST = {
    "request_code": "MR-003",
    "facility_code": "FAC-C",
    "issue_type": "hvac",
    "severity": "low",
    "status": "in_progress",
    "tenant_id": 1,
}
RESOLVED_MAINT_REQUEST = {
    "request_code": "MR-004",
    "facility_code": "FAC-D",
    "issue_type": "lighting",
    "severity": "low",
    "status": "resolved",
    "tenant_id": 1,
}
CLOSED_MAINT_REQUEST = {
    "request_code": "MR-005",
    "facility_code": "FAC-E",
    "issue_type": "cleaning",
    "severity": "low",
    "status": "closed",
    "tenant_id": 1,
}


def _make_sla_payload(
    facility_code: str = "FAC-A",
    service_type: str = "maintenance",
    target_sla_minutes: int = 120,
    priority: str = "high",
    status: str = "open",
) -> dict[str, object]:
    return {
        "service_type": service_type,
        "facility_code": facility_code,
        "target_sla_minutes": target_sla_minutes,
        "actual_minutes": None,
        "status": status,
        "priority": priority,
        "reported_at": "2026-04-29T09:00:00",
        "resolved_at": None,
        "description": "Test SLA record",
        "integration_source": None,
        "reviewer_notes": None,
    }


# ---------------------------------------------------------------------------
# TestW120Constants — sentinel values
# ---------------------------------------------------------------------------


class TestW120Constants:
    def test_active_maintenance_statuses_type(self):
        assert isinstance(_ACTIVE_MAINTENANCE_STATUSES, frozenset)

    def test_open_included(self):
        assert "open" in _ACTIVE_MAINTENANCE_STATUSES

    def test_pending_included(self):
        assert "pending" in _ACTIVE_MAINTENANCE_STATUSES

    def test_in_progress_included(self):
        assert "in_progress" in _ACTIVE_MAINTENANCE_STATUSES

    def test_resolved_excluded(self):
        assert "resolved" not in _ACTIVE_MAINTENANCE_STATUSES

    def test_closed_excluded(self):
        assert "closed" not in _ACTIVE_MAINTENANCE_STATUSES

    def test_cancelled_excluded(self):
        assert "cancelled" not in _ACTIVE_MAINTENANCE_STATUSES

    def test_active_sla_statuses_type(self):
        assert isinstance(_ACTIVE_SLA_STATUSES, frozenset)

    def test_open_in_active_sla(self):
        assert "open" in _ACTIVE_SLA_STATUSES

    def test_in_progress_in_active_sla(self):
        assert "in_progress" in _ACTIVE_SLA_STATUSES


# ---------------------------------------------------------------------------
# TestW120GuardSignature — guard raises DomainValidationError (not ValueError)
# ---------------------------------------------------------------------------


class TestW120GuardSignature:
    def test_guard_raises_domain_validation_error_for_unknown_facility(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError):
            _check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="GHOST-FAC"
            )

    def test_guard_does_not_raise_for_open_maintenance(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ACTIVE_MAINT_REQUEST],
        )
        _check_facility_has_active_maintenance_request(tenant_id=1, facility_code="FAC-A")

    def test_guard_does_not_raise_for_pending_maintenance(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [PENDING_MAINT_REQUEST],
        )
        _check_facility_has_active_maintenance_request(tenant_id=1, facility_code="FAC-B")

    def test_guard_does_not_raise_for_in_progress_maintenance(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [IN_PROGRESS_MAINT_REQUEST],
        )
        _check_facility_has_active_maintenance_request(tenant_id=1, facility_code="FAC-C")


# ---------------------------------------------------------------------------
# TestW120GuardFailures — all blocked scenarios
# ---------------------------------------------------------------------------


class TestW120GuardFailures:
    def test_no_requests_at_all_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no active maintenance request"):
            _check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-NONE"
            )

    def test_resolved_request_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [RESOLVED_MAINT_REQUEST],
        )
        with pytest.raises(DomainValidationError):
            _check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-D"
            )

    def test_closed_request_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [CLOSED_MAINT_REQUEST],
        )
        with pytest.raises(DomainValidationError):
            _check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-E"
            )

    def test_wrong_facility_code_in_request_blocks(self, monkeypatch):
        """Request exists but for different facility — guard blocks."""
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ACTIVE_MAINT_REQUEST],  # FAC-A
        )
        with pytest.raises(DomainValidationError):
            _check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-Z"
            )

    def test_case_insensitive_facility_code_match(self, monkeypatch):
        """Guard matches facility_code case-insensitively."""
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ACTIVE_MAINT_REQUEST],  # facility_code="FAC-A"
        )
        # uppercase variant should still find the match
        _check_facility_has_active_maintenance_request(tenant_id=1, facility_code="fac-a")

    def test_whitespace_trimmed_facility_code(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ACTIVE_MAINT_REQUEST],
        )
        _check_facility_has_active_maintenance_request(tenant_id=1, facility_code="  FAC-A  ")


# ---------------------------------------------------------------------------
# TestW120FailClosed — lookup failure → DomainValidationError
# ---------------------------------------------------------------------------


class TestW120FailClosed:
    def test_lookup_exception_raises_domain_validation_error(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise RuntimeError("DB unavailable")

        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError, match="lookup failed"):
            _check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-A"
            )

    def test_lookup_connection_error_raises_domain_validation_error(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise ConnectionError("network error")

        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError):
            _check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-A"
            )

    def test_lookup_never_silently_passes(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise IOError("timeout")

        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError):
            _check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-A"
            )


# ---------------------------------------------------------------------------
# TestW120CreatePath — end-to-end create_sla_record integration
# ---------------------------------------------------------------------------


class TestW120CreatePath:
    def _setup_monkeypatches(
        self, monkeypatch, maintenance_requests, existing_sla_records=None
    ):
        existing_sla_records = existing_sla_records or []
        created: dict[str, object] = {}

        def mock_list(entity_name, tenant_id):
            if entity_name == "facilities_maintenance_requests":
                return maintenance_requests
            if entity_name == "campus_sla_records":
                return existing_sla_records
            return []

        def mock_create(entity_name, payload, tenant_id):
            record = dict(payload)
            record["id"] = 42
            record["tenant_id"] = tenant_id
            created["entity_name"] = entity_name
            created["payload"] = record
            return record

        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.campus_sla.service.create_entity_for_tenant", mock_create
        )
        return created

    def test_create_succeeds_for_open_maintenance_facility(self, monkeypatch):
        created = self._setup_monkeypatches(
            monkeypatch, maintenance_requests=[ACTIVE_MAINT_REQUEST]
        )
        result = create_sla_record(_make_sla_payload(facility_code="FAC-A"), tenant_id=1)
        assert result["id"] == 42
        assert created["entity_name"] == "campus_sla_records"

    def test_create_blocked_for_resolved_maintenance_facility(self, monkeypatch):
        self._setup_monkeypatches(
            monkeypatch, maintenance_requests=[RESOLVED_MAINT_REQUEST]
        )
        with pytest.raises(DomainValidationError):
            create_sla_record(_make_sla_payload(facility_code="FAC-D"), tenant_id=1)

    def test_create_blocked_for_unknown_facility(self, monkeypatch):
        self._setup_monkeypatches(monkeypatch, maintenance_requests=[])
        with pytest.raises(DomainValidationError):
            create_sla_record(_make_sla_payload(facility_code="GHOST"), tenant_id=1)

    def test_guard_fires_before_persist(self, monkeypatch):
        """Guard must prevent create_entity_for_tenant when facility has no active request."""
        persist_calls: list[str] = []

        def mock_list(entity_name, tenant_id):
            if entity_name == "facilities_maintenance_requests":
                return []  # trigger guard failure
            return []

        def mock_create(entity_name, payload, tenant_id):
            persist_calls.append(entity_name)
            return {"id": 1}

        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.campus_sla.service.create_entity_for_tenant", mock_create
        )
        with pytest.raises(DomainValidationError):
            create_sla_record(_make_sla_payload(facility_code="GHOST"), tenant_id=1)

        assert "campus_sla_records" not in persist_calls

    def test_not_persisted_when_guard_fails(self, monkeypatch):
        created_calls: list[str] = []

        def mock_list(entity_name, tenant_id):
            if entity_name == "facilities_maintenance_requests":
                return [RESOLVED_MAINT_REQUEST]  # resolved — guard blocks
            return []

        def mock_create(entity_name, payload, tenant_id):
            created_calls.append(entity_name)
            return {"id": 1}

        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.campus_sla.service.create_entity_for_tenant", mock_create
        )
        with pytest.raises(DomainValidationError):
            create_sla_record(_make_sla_payload(facility_code="FAC-D"), tenant_id=1)

        assert created_calls == []

    def test_empty_facility_code_blocked(self, monkeypatch):
        self._setup_monkeypatches(
            monkeypatch, maintenance_requests=[ACTIVE_MAINT_REQUEST]
        )
        payload = _make_sla_payload(facility_code="")
        with pytest.raises(DomainValidationError):
            create_sla_record(payload, tenant_id=1)

    def test_none_facility_code_blocked(self, monkeypatch):
        self._setup_monkeypatches(
            monkeypatch, maintenance_requests=[ACTIVE_MAINT_REQUEST]
        )
        payload = _make_sla_payload()
        payload["facility_code"] = None
        with pytest.raises(DomainValidationError):
            create_sla_record(payload, tenant_id=1)


# ---------------------------------------------------------------------------
# TestW120PersistOrdering — guard is first, before cap guard
# ---------------------------------------------------------------------------


class TestW120PersistOrdering:
    def test_maintenance_lookup_happens_before_cap_check(self, monkeypatch):
        """Even if cap is exceeded, guard fires first (maintenance lookup before cap logic)."""
        maintenance_lookup_calls: list[str] = []

        def mock_list(entity_name, tenant_id):
            maintenance_lookup_calls.append(entity_name)
            if entity_name == "facilities_maintenance_requests":
                return []  # trigger guard failure
            return []

        def mock_create(entity_name, payload, tenant_id):
            return {"id": 1}

        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.campus_sla.service.create_entity_for_tenant", mock_create
        )
        with pytest.raises(DomainValidationError):
            create_sla_record(_make_sla_payload(), tenant_id=1)

        # The first lookup must be for maintenance requests
        assert maintenance_lookup_calls[0] == "facilities_maintenance_requests"

    def test_persist_called_once_on_success(self, monkeypatch):
        persist_calls: list[str] = []

        def mock_list(entity_name, tenant_id):
            if entity_name == "facilities_maintenance_requests":
                return [ACTIVE_MAINT_REQUEST]
            return []

        def mock_create(entity_name, payload, tenant_id):
            persist_calls.append(entity_name)
            record = dict(payload)
            record["id"] = 1
            record["tenant_id"] = tenant_id
            return record

        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.campus_sla.service.create_entity_for_tenant", mock_create
        )
        create_sla_record(_make_sla_payload(facility_code="FAC-A"), tenant_id=1)
        assert "campus_sla_records" in persist_calls


# ---------------------------------------------------------------------------
# TestW120BusinessInvariants — multi-tenant isolation and combined scenarios
# ---------------------------------------------------------------------------


class TestW120BusinessInvariants:
    def test_two_tenants_isolated(self, monkeypatch):
        """Maintenance request from tenant 1 must not satisfy tenant 2 check."""

        def mock_list(entity_name, tenant_id):
            if entity_name == "facilities_maintenance_requests" and tenant_id == 1:
                return [ACTIVE_MAINT_REQUEST]
            if entity_name == "facilities_maintenance_requests" and tenant_id == 2:
                return []
            return []

        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant", mock_list
        )
        # Tenant 1 passes
        _check_facility_has_active_maintenance_request(
            tenant_id=1, facility_code="FAC-A"
        )
        # Tenant 2 blocked
        with pytest.raises(DomainValidationError):
            _check_facility_has_active_maintenance_request(
                tenant_id=2, facility_code="FAC-A"
            )

    def test_multiple_requests_one_active_passes(self, monkeypatch):
        """Even if one request is resolved, an active one satisfies the guard."""
        requests = [
            {**RESOLVED_MAINT_REQUEST, "facility_code": "FAC-A"},
            {**ACTIVE_MAINT_REQUEST, "facility_code": "FAC-A"},
        ]
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda e, t: requests,
        )
        _check_facility_has_active_maintenance_request(tenant_id=1, facility_code="FAC-A")

    def test_all_resolved_blocks(self, monkeypatch):
        requests = [
            {**RESOLVED_MAINT_REQUEST, "facility_code": "FAC-A"},
            {**CLOSED_MAINT_REQUEST, "facility_code": "FAC-A"},
        ]
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda e, t: requests,
        )
        with pytest.raises(DomainValidationError):
            _check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-A"
            )

    def test_error_message_contains_facility_code(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        with pytest.raises(DomainValidationError, match="FAC-XYZ"):
            _check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-XYZ"
            )

    def test_fail_closed_error_message_mentions_lookup(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise Exception("DB timeout")

        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError, match="lookup failed"):
            _check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-A"
            )

    def test_pending_status_accepted(self, monkeypatch):
        """'pending' maintenance request is accepted."""
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda e, t: [{"facility_code": "FAC-P", "status": "pending", "tenant_id": 1}],
        )
        _check_facility_has_active_maintenance_request(
            tenant_id=1, facility_code="FAC-P"
        )

    def test_in_progress_status_accepted(self, monkeypatch):
        """'in_progress' maintenance request is accepted."""
        monkeypatch.setattr(
            "app.modules.campus_sla.service.list_entities_for_tenant",
            lambda e, t: [{"facility_code": "FAC-IP", "status": "in_progress", "tenant_id": 1}],
        )
        _check_facility_has_active_maintenance_request(
            tenant_id=1, facility_code="FAC-IP"
        )
