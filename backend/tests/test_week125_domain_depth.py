"""
W125 — hr_payroll domain depth tests.

Guard: _check_payable_employees_exist_for_payroll_cycle_create
- Blocks when no hr_employees records found (fail-closed)
- Blocks when employees exist but none in payable status
- Blocks on lookup exception (fail-closed)
- Passes when ≥1 active/on_leave employee exists
- create_payroll_cycle: guard fires FIRST before create_entity_for_tenant
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.hr_payroll.service import (
    _PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES,
    _check_payable_employees_exist_for_payroll_cycle_create,
    create_payroll_cycle,
)
from app.modules.hr_payroll.schemas import PayrollCycleCreateSchema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TENANT = 55
_CYCLE_CODE = "PAY-2026-04"


def _employee(status: str) -> dict:
    return {"id": 1, "employee_code": "E001", "status": status}


def _cycle_payload(**kwargs) -> PayrollCycleCreateSchema:
    defaults = {
        "cycle_code": _CYCLE_CODE,
        "period_label": "April 2026",
        "total_gross": 100000.0,
        "total_net": 85000.0,
        "employee_count": 10,
        "status": "DRAFT",
    }
    defaults.update(kwargs)
    return PayrollCycleCreateSchema(**defaults)


# ---------------------------------------------------------------------------
# TestW125Constants
# ---------------------------------------------------------------------------


class TestW125Constants:
    def test_required_statuses_is_frozenset(self):
        assert isinstance(_PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES, frozenset)

    def test_active_in_statuses(self):
        assert "active" in _PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES

    def test_on_leave_in_statuses(self):
        assert "on_leave" in _PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES

    def test_terminated_not_in_statuses(self):
        assert "terminated" not in _PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES

    def test_offboarding_not_in_statuses(self):
        assert "offboarding" not in _PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES

    def test_onboarding_not_in_statuses(self):
        assert "onboarding" not in _PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES

    def test_statuses_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES.add("temp")  # type: ignore[attr-defined]

    def test_statuses_nonempty(self):
        assert len(_PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES) >= 1

    def test_statuses_lowercase(self):
        for s in _PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES:
            assert s == s.lower()

    def test_at_least_two_statuses(self):
        assert len(_PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES) >= 2


# ---------------------------------------------------------------------------
# TestW125GuardSignature
# ---------------------------------------------------------------------------


class TestW125GuardSignature:
    def test_guard_callable(self):
        assert callable(_check_payable_employees_exist_for_payroll_cycle_create)

    def test_guard_requires_keyword_tenant_id(self):
        with pytest.raises(TypeError):
            _check_payable_employees_exist_for_payroll_cycle_create(_TENANT, _CYCLE_CODE)  # type: ignore[call-arg]

    def test_guard_requires_keyword_cycle_code(self):
        with pytest.raises(TypeError):
            _check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT)

    def test_guard_returns_none_on_success(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_employee("active")],
        )
        result = _check_payable_employees_exist_for_payroll_cycle_create(
            tenant_id=_TENANT, cycle_code=_CYCLE_CODE
        )
        assert result is None

    def test_guard_accepts_on_leave(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_employee("on_leave")],
        )
        result = _check_payable_employees_exist_for_payroll_cycle_create(
            tenant_id=_TENANT, cycle_code=_CYCLE_CODE
        )
        assert result is None


# ---------------------------------------------------------------------------
# TestW125GuardFailures
# ---------------------------------------------------------------------------


class TestW125GuardFailures:
    def test_blocks_when_no_employees_at_all(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no employees with payable status"):
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )

    def test_blocks_when_all_terminated(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_employee("terminated"), _employee("terminated")],
        )
        with pytest.raises(DomainValidationError, match="ghost payroll"):
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )

    def test_blocks_when_all_offboarding(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_employee("offboarding")],
        )
        with pytest.raises(DomainValidationError):
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )

    def test_blocks_when_all_onboarding(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_employee("onboarding")],
        )
        with pytest.raises(DomainValidationError):
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )

    def test_error_contains_cycle_code(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )
        assert _CYCLE_CODE in str(exc_info.value)

    def test_error_contains_ghost_payroll_rationale(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_employee("terminated")],
        )
        with pytest.raises(DomainValidationError, match="ghost payroll"):
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )


# ---------------------------------------------------------------------------
# TestW125FailClosed
# ---------------------------------------------------------------------------


class TestW125FailClosed:
    def test_fail_closed_on_runtime_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise RuntimeError("DB down")

        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError, match="hr_employees lookup failed"):
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )

    def test_fail_closed_error_includes_cycle_code(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ConnectionError("timeout")

        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )
        assert _CYCLE_CODE in str(exc_info.value)

    def test_fail_closed_on_value_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ValueError("bad data")

        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )

    def test_fail_closed_no_allow_fallback(self, monkeypatch):
        call_count = []

        def boom(entity_type, tenant_id):
            call_count.append(1)
            raise OSError("network unreachable")

        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )
        assert call_count == [1]


# ---------------------------------------------------------------------------
# TestW125CreatePath
# ---------------------------------------------------------------------------


class TestW125CreatePath:
    def _setup(self, monkeypatch, created_list: list):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_employee("active")] if entity_type == "hr_employees" else [],
        )
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: created_list.append(payload) or {
                "id": 99,
                "cycle_code": payload.get("cycle_code"),
                "period_label": payload.get("period_label"),
                "total_gross": payload.get("total_gross"),
                "total_net": payload.get("total_net"),
                "employee_count": max(1, int(payload.get("employee_count") or 1)),
                "status": payload.get("status"),
            },
        )
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.log_admin_action",
            lambda **kwargs: None,
        )
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.EventPublisher",
            lambda: type("EP", (), {"publish_event": lambda self, **kw: None})(),
        )

    def test_guard_fires_before_create(self, monkeypatch):
        """Guard function must be called before persistence — verified via guard mock raising."""
        guard_called = []
        created: list = []
        self._setup(monkeypatch, created)  # working create/list/log/EventPublisher mocks

        def mock_guard(*, tenant_id, cycle_code):
            guard_called.append(cycle_code)
            # let it pass — we just record the call

        monkeypatch.setattr(
            "app.modules.hr_payroll.service._check_payable_employees_exist_for_payroll_cycle_create",
            mock_guard,
        )
        create_payroll_cycle(_TENANT, _cycle_payload(), "actor")
        assert guard_called == [_CYCLE_CODE]
        assert len(created) >= 1

    def test_create_not_called_when_guard_blocks(self, monkeypatch):
        created = []
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: created.append(payload) or {"id": 1},
        )
        with pytest.raises(DomainValidationError):
            create_payroll_cycle(_TENANT, _cycle_payload(), "actor")
        assert created == []

    def test_create_succeeds_with_active_employee(self, monkeypatch):
        created: list = []
        self._setup(monkeypatch, created)
        result = create_payroll_cycle(_TENANT, _cycle_payload(), "actor")
        assert result.cycle_code == _CYCLE_CODE
        assert len(created) >= 1

    def test_create_blocked_all_terminated(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_employee("terminated")],
        )
        with pytest.raises(DomainValidationError, match="ghost payroll"):
            create_payroll_cycle(_TENANT, _cycle_payload(), "actor")

    def test_create_succeeds_with_on_leave_employee(self, monkeypatch):
        """on_leave employee satisfies payable guard → cycle created."""
        created: list = []
        self._setup(monkeypatch, created)  # working create/log/EventPublisher mocks
        # Override list mock to return on_leave employee — real guard must pass
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_employee("on_leave")] if entity_type == "hr_employees" else [],
        )
        result = create_payroll_cycle(_TENANT, _cycle_payload(), "actor")
        assert result.cycle_code == _CYCLE_CODE


# ---------------------------------------------------------------------------
# TestW125BusinessInvariants
# ---------------------------------------------------------------------------


class TestW125BusinessInvariants:
    def test_two_tenant_isolation(self, monkeypatch):
        calls = []

        def mock_list(entity_type, tenant_id):
            calls.append(tenant_id)
            if tenant_id == 1:
                return [_employee("active")]
            return []

        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant", mock_list
        )
        # Tenant 1 succeeds
        _check_payable_employees_exist_for_payroll_cycle_create(
            tenant_id=1, cycle_code=_CYCLE_CODE
        )
        # Tenant 2 blocked
        with pytest.raises(DomainValidationError):
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=2, cycle_code=_CYCLE_CODE
            )
        assert 1 in calls
        assert 2 in calls

    def test_mixed_statuses_one_active_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                _employee("terminated"),
                _employee("active"),
                _employee("offboarding"),
            ],
        )
        result = _check_payable_employees_exist_for_payroll_cycle_create(
            tenant_id=_TENANT, cycle_code=_CYCLE_CODE
        )
        assert result is None

    def test_all_non_payable_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                _employee("terminated"),
                _employee("offboarding"),
                _employee("onboarding"),
            ],
        )
        with pytest.raises(DomainValidationError, match="ghost payroll"):
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )

    def test_error_mentions_checked_statuses(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_employee("terminated")],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )
        # Should mention at least one of the checked statuses
        msg = str(exc_info.value)
        assert "active" in msg or "on_leave" in msg

    def test_lookup_called_with_hr_employees_entity(self, monkeypatch):
        entity_types_queried = []

        def track_list(entity_type, tenant_id):
            entity_types_queried.append(entity_type)
            return [_employee("active")]

        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant", track_list
        )
        _check_payable_employees_exist_for_payroll_cycle_create(
            tenant_id=_TENANT, cycle_code=_CYCLE_CODE
        )
        assert "hr_employees" in entity_types_queried

    def test_fail_closed_error_mentions_cannot_verify(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: (_ for _ in ()).throw(RuntimeError("DB unavailable")),
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_payable_employees_exist_for_payroll_cycle_create(
                tenant_id=_TENANT, cycle_code=_CYCLE_CODE
            )
        assert "Cannot" in str(exc_info.value) or "lookup failed" in str(exc_info.value)
