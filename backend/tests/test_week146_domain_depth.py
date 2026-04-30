"""W146 — campus_sla: Deep domain test pack.

Guards under test:
  W120: _check_facility_has_active_maintenance_request — facility must have an active
        (open/pending/in_progress) maintenance request before creating an SLA record.
        Fail-closed: lookup failure → DomainValidationError with __cause__.
  W59:  _SLA_PRIORITY_MAX_ACTIVE — per-priority active record count cap.
  SLA max target minutes per priority tier.
"""
from __future__ import annotations

import sys
import inspect

import pytest

sys.path.insert(0, "/home/sbs/AI/backend")

import app.modules.campus_sla.service as _svc
import app.modules.campus_sla.router as _router
from app.core.module_helpers.service_validation import DomainValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_payload(**kwargs) -> dict:
    base = {
        "facility_code": "FAC-001",
        "service_type": "hvac",
        "priority": "high",
        "target_sla_minutes": 120,
    }
    base.update(kwargs)
    return base


def _maintenance_request(facility_code: str, status: str = "open") -> dict:
    return {"facility_code": facility_code, "status": status}


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_active_maintenance_statuses_is_frozenset(self):
        assert isinstance(_svc._ACTIVE_MAINTENANCE_STATUSES, frozenset)

    def test_active_maintenance_statuses_contains_open(self):
        assert "open" in _svc._ACTIVE_MAINTENANCE_STATUSES

    def test_active_maintenance_statuses_contains_pending(self):
        assert "pending" in _svc._ACTIVE_MAINTENANCE_STATUSES

    def test_active_maintenance_statuses_contains_in_progress(self):
        assert "in_progress" in _svc._ACTIVE_MAINTENANCE_STATUSES

    def test_sla_priority_max_active_is_dict(self):
        assert isinstance(_svc._SLA_PRIORITY_MAX_ACTIVE, dict)

    def test_sla_priority_max_active_critical(self):
        assert _svc._SLA_PRIORITY_MAX_ACTIVE["critical"] == 10

    def test_sla_priority_max_active_high(self):
        assert _svc._SLA_PRIORITY_MAX_ACTIVE["high"] == 25

    def test_sla_priority_max_active_medium(self):
        assert _svc._SLA_PRIORITY_MAX_ACTIVE["medium"] == 50

    def test_sla_priority_max_active_low(self):
        assert _svc._SLA_PRIORITY_MAX_ACTIVE["low"] == 100

    def test_sla_max_target_by_priority_is_dict(self):
        assert isinstance(_svc._SLA_MAX_TARGET_BY_PRIORITY, dict)

    def test_sla_max_target_critical(self):
        assert _svc._SLA_MAX_TARGET_BY_PRIORITY["critical"] == 60

    def test_sla_max_target_high(self):
        assert _svc._SLA_MAX_TARGET_BY_PRIORITY["high"] == 240

    def test_sla_max_target_medium(self):
        assert _svc._SLA_MAX_TARGET_BY_PRIORITY["medium"] == 1440

    def test_sla_max_target_low(self):
        assert _svc._SLA_MAX_TARGET_BY_PRIORITY["low"] == 4320

    def test_active_sla_statuses_is_frozenset(self):
        assert isinstance(_svc._ACTIVE_SLA_STATUSES, frozenset)

    def test_active_sla_statuses_contains_open(self):
        assert "open" in _svc._ACTIVE_SLA_STATUSES

    def test_active_sla_statuses_contains_in_progress(self):
        assert "in_progress" in _svc._ACTIVE_SLA_STATUSES


# ---------------------------------------------------------------------------
# 2. W120 Guard — facility active maintenance request
# ---------------------------------------------------------------------------

class TestW120GuardAllowPath:
    def test_guard_passes_when_facility_has_open_request(self, monkeypatch):
        """Guard passes when facility has an open maintenance request."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [_maintenance_request("FAC-001", "open")]
            if entity == "facilities_maintenance_requests" else [],
        )
        # Should not raise
        _svc._check_facility_has_active_maintenance_request(
            tenant_id=1, facility_code="FAC-001"
        )

    def test_guard_passes_when_facility_has_pending_request(self, monkeypatch):
        """Guard passes for 'pending' status."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [_maintenance_request("FAC-002", "pending")]
            if entity == "facilities_maintenance_requests" else [],
        )
        _svc._check_facility_has_active_maintenance_request(
            tenant_id=1, facility_code="FAC-002"
        )

    def test_guard_passes_when_facility_has_in_progress_request(self, monkeypatch):
        """Guard passes for 'in_progress' status."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [_maintenance_request("FAC-003", "in_progress")]
            if entity == "facilities_maintenance_requests" else [],
        )
        _svc._check_facility_has_active_maintenance_request(
            tenant_id=1, facility_code="FAC-003"
        )

    def test_guard_case_insensitive_facility_code(self, monkeypatch):
        """Guard matches facility_code case-insensitively."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [{"facility_code": "fac-001", "status": "open"}]
            if entity == "facilities_maintenance_requests" else [],
        )
        # Should pass: "FAC-001" vs "fac-001"
        _svc._check_facility_has_active_maintenance_request(
            tenant_id=1, facility_code="FAC-001"
        )

    def test_guard_trims_whitespace_in_facility_code(self, monkeypatch):
        """Guard strips whitespace from facility_code before matching."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [{"facility_code": "FAC-001", "status": "open"}]
            if entity == "facilities_maintenance_requests" else [],
        )
        _svc._check_facility_has_active_maintenance_request(
            tenant_id=1, facility_code="  FAC-001  "
        )

    def test_guard_ignores_closed_requests_from_other_facilities(self, monkeypatch):
        """Guard ignores records for other facilities."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [
                _maintenance_request("FAC-002", "open"),
                _maintenance_request("FAC-001", "closed"),  # closed — not active
            ]
            if entity == "facilities_maintenance_requests" else [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-001"
            )
        assert "FAC-001" in str(exc_info.value)


class TestW120GuardBlockPath:
    def test_guard_blocks_when_no_requests_for_facility(self, monkeypatch):
        """Guard blocks when facility has no maintenance requests at all."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-999"
            )
        assert "FAC-999" in str(exc_info.value)

    def test_guard_blocks_when_request_is_closed(self, monkeypatch):
        """Guard blocks when facility's only maintenance request is 'closed'."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [_maintenance_request("FAC-001", "closed")]
            if entity == "facilities_maintenance_requests" else [],
        )
        with pytest.raises(DomainValidationError):
            _svc._check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-001"
            )

    def test_guard_blocks_when_request_is_completed(self, monkeypatch):
        """Guard blocks when facility's only maintenance request is 'completed'."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [_maintenance_request("FAC-001", "completed")]
            if entity == "facilities_maintenance_requests" else [],
        )
        with pytest.raises(DomainValidationError):
            _svc._check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-001"
            )

    def test_guard_fail_closed_on_lookup_exception(self, monkeypatch):
        """Fail-closed: lookup exception → DomainValidationError (NOT silenced)."""
        def boom(entity, tid):
            raise RuntimeError("DB timeout")

        monkeypatch.setattr(_svc, "list_entities_for_tenant", boom)

        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="FAC-001"
            )
        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, RuntimeError)

    def test_guard_error_message_includes_facility_code(self, monkeypatch):
        """Error message must reference the failing facility code."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_facility_has_active_maintenance_request(
                tenant_id=1, facility_code="BLDG-42"
            )
        assert "BLDG-42" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 3. W59 Guard — Priority active count cap
# ---------------------------------------------------------------------------

class TestW59PriorityCapGuard:
    def test_cap_blocks_when_at_critical_limit(self, monkeypatch):
        """W59: critical priority cap (10) is enforced."""
        critical_records = [
            {"priority": "critical", "status": "open"} for _ in range(10)
        ]

        def mock_list(entity, tid):
            if entity == "facilities_maintenance_requests":
                return [_maintenance_request("FAC-001", "open")]
            if entity == "campus_sla_records":
                return critical_records
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)

        with pytest.raises(ValueError) as exc_info:
            _svc.create_sla_record(
                _make_payload(facility_code="FAC-001", priority="critical", target_sla_minutes=30),
                tenant_id=1,
            )
        assert "critical" in str(exc_info.value)

    def test_cap_allows_below_limit(self, monkeypatch):
        """W59: below cap allows creation."""
        records_below_cap = [
            {"priority": "high", "status": "open"} for _ in range(5)
        ]

        def mock_list(entity, tid):
            if entity == "facilities_maintenance_requests":
                return [_maintenance_request("FAC-001", "open")]
            if entity == "campus_sla_records":
                return records_below_cap
            return []

        def mock_create(entity, data, tid):
            return dict(data) | {"id": "new-id"}

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", mock_create)

        result = _svc.create_sla_record(
            _make_payload(facility_code="FAC-001", priority="high", target_sla_minutes=120),
            tenant_id=1,
        )
        assert result["id"] == "new-id"

    def test_cap_counts_only_active_statuses(self, monkeypatch):
        """W59: closed/completed records are not counted against the cap."""
        mixed_records = [
            {"priority": "critical", "status": "closed"} for _ in range(15)
        ]

        def mock_list(entity, tid):
            if entity == "facilities_maintenance_requests":
                return [_maintenance_request("FAC-001", "open")]
            if entity == "campus_sla_records":
                return mixed_records
            return []

        def mock_create(entity, data, tid):
            return dict(data) | {"id": "new-id"}

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", mock_create)

        # closed records don't count → creation allowed
        result = _svc.create_sla_record(
            _make_payload(facility_code="FAC-001", priority="critical", target_sla_minutes=30),
            tenant_id=1,
        )
        assert result is not None

    def test_cap_independent_per_priority(self, monkeypatch):
        """W59: caps are independent per priority tier."""
        # 10 critical (at cap), but 0 high — high should still be allowed
        records = [{"priority": "critical", "status": "open"} for _ in range(10)]

        def mock_list(entity, tid):
            if entity == "facilities_maintenance_requests":
                return [_maintenance_request("FAC-001", "open")]
            if entity == "campus_sla_records":
                return records
            return []

        def mock_create(entity, data, tid):
            return dict(data) | {"id": "new-id"}

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", mock_create)

        # high priority not at cap → allowed
        result = _svc.create_sla_record(
            _make_payload(facility_code="FAC-001", priority="high", target_sla_minutes=120),
            tenant_id=1,
        )
        assert result is not None


# ---------------------------------------------------------------------------
# 4. SLA max target minutes guard
# ---------------------------------------------------------------------------

class TestSlaMaxTargetMinutes:
    def test_critical_max_60_enforced(self, monkeypatch):
        """SLA max target: critical priority blocked above 60 minutes."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [_maintenance_request("FAC-001", "open")]
            if entity == "facilities_maintenance_requests" else [],
        )
        with pytest.raises(ValueError) as exc_info:
            _svc.create_sla_record(
                _make_payload(facility_code="FAC-001", priority="critical", target_sla_minutes=61),
                tenant_id=1,
            )
        assert "critical" in str(exc_info.value)

    def test_high_max_240_enforced(self, monkeypatch):
        """SLA max target: high priority blocked above 240 minutes."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [_maintenance_request("FAC-001", "open")]
            if entity == "facilities_maintenance_requests" else [],
        )
        with pytest.raises(ValueError):
            _svc.create_sla_record(
                _make_payload(facility_code="FAC-001", priority="high", target_sla_minutes=241),
                tenant_id=1,
            )

    def test_critical_exactly_at_max_passes(self, monkeypatch):
        """SLA max target: critical=60 exactly at max is allowed."""
        def mock_list(entity, tid):
            if entity == "facilities_maintenance_requests":
                return [_maintenance_request("FAC-001", "open")]
            return []

        def mock_create(entity, data, tid):
            return dict(data) | {"id": "new-id"}

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", mock_create)

        result = _svc.create_sla_record(
            _make_payload(facility_code="FAC-001", priority="critical", target_sla_minutes=60),
            tenant_id=1,
        )
        assert result is not None


# ---------------------------------------------------------------------------
# 5. Tenant isolation
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    def test_maintenance_lookup_uses_correct_tenant_id(self, monkeypatch):
        """Guard passes tenant_id to list_entities_for_tenant, ensuring isolation."""
        observed = {}

        def tracking_list(entity, tid):
            observed[entity] = tid
            if entity == "facilities_maintenance_requests":
                return [_maintenance_request("FAC-001", "open")]
            return []

        def mock_create(entity, data, tid):
            return dict(data) | {"id": "x"}

        monkeypatch.setattr(_svc, "list_entities_for_tenant", tracking_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", mock_create)

        _svc.create_sla_record(_make_payload(facility_code="FAC-001"), tenant_id=42)

        assert observed.get("facilities_maintenance_requests") == 42

    def test_sla_records_lookup_uses_correct_tenant_id(self, monkeypatch):
        """SLA record cap lookup uses the correct tenant_id."""
        observed = {}

        def tracking_list(entity, tid):
            observed[entity] = tid
            if entity == "facilities_maintenance_requests":
                return [_maintenance_request("FAC-001", "open")]
            return []

        def mock_create(entity, data, tid):
            return dict(data) | {"id": "x"}

        monkeypatch.setattr(_svc, "list_entities_for_tenant", tracking_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", mock_create)

        _svc.create_sla_record(_make_payload(facility_code="FAC-001"), tenant_id=99)

        assert observed.get("campus_sla_records") == 99


# ---------------------------------------------------------------------------
# 6. facility_code validation
# ---------------------------------------------------------------------------

class TestFacilityCodeValidation:
    def test_empty_facility_code_raises(self, monkeypatch):
        """Empty facility_code raises DomainValidationError before guard fires."""
        monkeypatch.setattr(
            _svc, "list_entities_for_tenant", lambda entity, tid: []
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _svc.create_sla_record(_make_payload(facility_code=""), tenant_id=1)
        assert "facility_code" in str(exc_info.value)

    def test_none_facility_code_raises(self, monkeypatch):
        """None facility_code raises DomainValidationError."""
        monkeypatch.setattr(
            _svc, "list_entities_for_tenant", lambda entity, tid: []
        )
        with pytest.raises(DomainValidationError):
            _svc.create_sla_record(_make_payload(facility_code=None), tenant_id=1)


# ---------------------------------------------------------------------------
# 7. Router structure
# ---------------------------------------------------------------------------

class TestRouterStructure:
    def test_router_uses_svc_import_pattern(self):
        """Router must use 'import ... as _svc' pattern for testability."""
        src = inspect.getsource(_router)
        assert "import app.modules.campus_sla.service as _svc" in src

    def test_router_imports_domain_validation_error(self):
        """Router must import DomainValidationError for 422 mapping."""
        src = inspect.getsource(_router)
        assert "DomainValidationError" in src

    def test_router_has_3_routes(self):
        """Router must have exactly 3 routes: list, create, brain-context."""
        assert len(_router.router.routes) == 3

    def test_create_endpoint_catches_value_error(self):
        """POST /sla-records catches ValueError → 422."""
        src = inspect.getsource(_router.create_sla_record_endpoint)
        assert "ValueError" in src

    def test_create_endpoint_catches_domain_validation_error(self):
        """POST /sla-records catches DomainValidationError → 422."""
        src = inspect.getsource(_router.create_sla_record_endpoint)
        assert "DomainValidationError" in src

    def test_create_endpoint_raises_http_422(self):
        """POST /sla-records raises HTTPException with status_code=422."""
        src = inspect.getsource(_router.create_sla_record_endpoint)
        assert "422" in src

    def test_list_endpoint_uses_svc(self):
        """GET /sla-records calls _svc.list_sla_records."""
        src = inspect.getsource(_router.list_sla_records_endpoint)
        assert "_svc.list_sla_records" in src

    def test_brain_context_endpoint_uses_svc(self):
        """GET /brain-context calls _svc.get_campus_sla_brain_context."""
        src = inspect.getsource(_router.get_campus_sla_brain_context_endpoint)
        assert "_svc.get_campus_sla_brain_context" in src


# ---------------------------------------------------------------------------
# 8. Error handling end-to-end
# ---------------------------------------------------------------------------

class TestErrorHandlingEndToEnd:
    def test_w120_violation_propagates_as_domain_validation_error(self, monkeypatch):
        """W120 guard violation raises DomainValidationError from create_sla_record."""
        monkeypatch.setattr(
            _svc, "list_entities_for_tenant", lambda entity, tid: []
        )
        with pytest.raises(DomainValidationError):
            _svc.create_sla_record(_make_payload(facility_code="FAC-999"), tenant_id=1)

    def test_w59_violation_propagates_as_value_error(self, monkeypatch):
        """W59 cap violation raises ValueError from create_sla_record."""
        at_cap = [{"priority": "critical", "status": "open"} for _ in range(10)]

        def mock_list(entity, tid):
            if entity == "facilities_maintenance_requests":
                return [_maintenance_request("FAC-001", "open")]
            if entity == "campus_sla_records":
                return at_cap
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)

        with pytest.raises(ValueError):
            _svc.create_sla_record(
                _make_payload(facility_code="FAC-001", priority="critical", target_sla_minutes=30),
                tenant_id=1,
            )

    def test_target_minutes_violation_propagates_as_value_error(self, monkeypatch):
        """SLA max target violation raises ValueError."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [_maintenance_request("FAC-001", "open")]
            if entity == "facilities_maintenance_requests" else [],
        )
        with pytest.raises(ValueError):
            _svc.create_sla_record(
                _make_payload(facility_code="FAC-001", priority="critical", target_sla_minutes=999),
                tenant_id=1,
            )
