"""W150 — hr_payroll: deep domain hardening pack.

Scope:
- W125 guard: payroll cycle create blocked if no active/on_leave employees
- fail-closed on hr_employees lookup failure
- validate-before-persist for create_payroll_cycle
- router _svc pattern checks
"""
from __future__ import annotations

from pathlib import Path

import pytest

import app.modules.hr_payroll.service as svc
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.hr_payroll.schemas import PayrollCycleCreateSchema


_TENANT = 55
_CYCLE_CODE = "PAY-2026-04"


def _employee(status: str, emp_id: int = 1) -> dict:
    return {"id": emp_id, "employee_code": f"E{emp_id:03d}", "status": status}


def _cycle_payload(**overrides) -> PayrollCycleCreateSchema:
    data = {
        "cycle_code": _CYCLE_CODE,
        "period_label": "April 2026",
        "total_gross": 100000.0,
        "total_net": 85000.0,
        "employee_count": 10,
        "status": "DRAFT",
    }
    data.update(overrides)
    return PayrollCycleCreateSchema(**data)


class TestConstants:
    def test_required_statuses_type(self):
        assert isinstance(svc._PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES, frozenset)

    def test_active_allowed(self):
        assert "active" in svc._PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES

    def test_on_leave_allowed(self):
        assert "on_leave" in svc._PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES

    def test_terminated_not_allowed(self):
        assert "terminated" not in svc._PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES

    def test_offboarding_not_allowed(self):
        assert "offboarding" not in svc._PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES

    def test_onboarding_not_allowed(self):
        assert "onboarding" not in svc._PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES

    def test_set_is_nonempty(self):
        assert len(svc._PAYROLL_CREATE_REQUIRED_EMPLOYEE_STATUSES) >= 2


class TestW125GuardCore:
    def test_no_employees_blocks(self, monkeypatch):
        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", lambda e, t: [])
        with pytest.raises(DomainValidationError, match="no employees with payable status"):
            svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)

    def test_all_terminated_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda e, t: [_employee("terminated", 1), _employee("terminated", 2)],
        )
        with pytest.raises(DomainValidationError, match="ghost payroll"):
            svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)

    def test_all_offboarding_blocks(self, monkeypatch):
        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", lambda e, t: [_employee("offboarding")])
        with pytest.raises(DomainValidationError):
            svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)

    def test_all_onboarding_blocks(self, monkeypatch):
        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", lambda e, t: [_employee("onboarding")])
        with pytest.raises(DomainValidationError):
            svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)

    def test_active_passes(self, monkeypatch):
        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", lambda e, t: [_employee("active")])
        svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)

    def test_on_leave_passes(self, monkeypatch):
        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", lambda e, t: [_employee("on_leave")])
        svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)

    def test_mixed_one_active_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.list_entities_for_tenant",
            lambda e, t: [_employee("terminated"), _employee("active"), _employee("offboarding")],
        )
        svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)

    def test_error_mentions_cycle_code(self, monkeypatch):
        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", lambda e, t: [])
        with pytest.raises(DomainValidationError) as exc:
            svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)
        assert _CYCLE_CODE in str(exc.value)


class TestW125FailClosed:
    def test_lookup_runtime_error_blocks(self, monkeypatch):
        def boom(entity, tenant_id):
            raise RuntimeError("db down")

        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError, match="lookup failed"):
            svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)

    def test_lookup_connection_error_blocks(self, monkeypatch):
        def boom(entity, tenant_id):
            raise ConnectionError("timeout")

        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError):
            svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)

    def test_lookup_value_error_blocks(self, monkeypatch):
        def boom(entity, tenant_id):
            raise ValueError("bad data")

        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError):
            svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)

    def test_fail_closed_error_mentions_reason(self, monkeypatch):
        def boom(entity, tenant_id):
            raise OSError("network unreachable")

        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError) as exc:
            svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=_TENANT, cycle_code=_CYCLE_CODE)
        msg = str(exc.value)
        assert "Cannot" in msg or "lookup failed" in msg


class TestCreateCyclePath:
    def _setup_success(self, monkeypatch, employees, existing=None):
        existing = existing or []

        def mock_list(entity, tenant_id):
            if entity == "hr_employees":
                return employees
            if entity == "hr_payroll_cycle_risk_alerts":
                return existing
            return []

        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", mock_list)
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.create_entity_for_tenant",
            lambda entity, payload, tenant_id: {
                "id": 99,
                "cycle_code": payload.get("cycle_code"),
                "period_label": payload.get("period_label"),
                "total_gross": payload.get("total_gross"),
                "total_net": payload.get("total_net"),
                "employee_count": int(payload.get("employee_count") or 1),
                "status": payload.get("status"),
            },
        )
        monkeypatch.setattr("app.modules.hr_payroll.service.log_admin_action", lambda **kwargs: None)
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.EventPublisher",
            lambda: type("EP", (), {"publish_event": lambda self, **kw: None})(),
        )

    def test_create_succeeds_with_active_employee(self, monkeypatch):
        self._setup_success(monkeypatch, employees=[_employee("active")])
        result = svc.create_payroll_cycle(_TENANT, _cycle_payload(), "actor")
        assert result.cycle_code == _CYCLE_CODE

    def test_create_succeeds_with_on_leave_employee(self, monkeypatch):
        self._setup_success(monkeypatch, employees=[_employee("on_leave")])
        result = svc.create_payroll_cycle(_TENANT, _cycle_payload(), "actor")
        assert result.cycle_code == _CYCLE_CODE

    def test_create_blocked_without_payable_employee(self, monkeypatch):
        self._setup_success(monkeypatch, employees=[_employee("terminated")])
        with pytest.raises(DomainValidationError):
            svc.create_payroll_cycle(_TENANT, _cycle_payload(), "actor")

    def test_validate_before_persist(self, monkeypatch):
        created_calls: list[str] = []

        def mock_list(entity, tenant_id):
            if entity == "hr_employees":
                return [_employee("terminated")]
            return []

        def mock_create(entity, payload, tenant_id):
            created_calls.append(entity)
            return {"id": 1}

        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", mock_list)
        monkeypatch.setattr("app.modules.hr_payroll.service.create_entity_for_tenant", mock_create)
        monkeypatch.setattr("app.modules.hr_payroll.service.log_admin_action", lambda **kwargs: None)

        with pytest.raises(DomainValidationError):
            svc.create_payroll_cycle(_TENANT, _cycle_payload(), "actor")

        assert "hr_payroll_cycles" not in created_calls

    def test_guard_called_before_persist(self, monkeypatch):
        order: list[str] = []

        def guard(*, tenant_id, cycle_code):
            order.append("guard")

        def mock_create(entity, payload, tenant_id):
            if entity == "hr_payroll_cycles":
                order.append("persist")
            # Side-effect entity (risk alert) has a different schema; we only need it not to fail.
            if entity != "hr_payroll_cycles":
                return {"id": 2}
            return {
                "id": 1,
                "cycle_code": payload["cycle_code"],
                "period_label": payload["period_label"],
                "total_gross": payload["total_gross"],
                "total_net": payload["total_net"],
                "employee_count": payload["employee_count"],
                "status": payload["status"],
            }

        monkeypatch.setattr("app.modules.hr_payroll.service._check_payable_employees_exist_for_payroll_cycle_create", guard)
        monkeypatch.setattr("app.modules.hr_payroll.service.create_entity_for_tenant", mock_create)
        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", lambda e, t: [])
        monkeypatch.setattr("app.modules.hr_payroll.service.log_admin_action", lambda **kwargs: None)
        monkeypatch.setattr(
            "app.modules.hr_payroll.service.EventPublisher",
            lambda: type("EP", (), {"publish_event": lambda self, **kw: None})(),
        )

        svc.create_payroll_cycle(_TENANT, _cycle_payload(), "actor")
        assert order == ["guard", "persist"]


class TestTenantIsolation:
    def test_guard_queries_hr_employees_for_same_tenant(self, monkeypatch):
        calls: list[tuple[str, int]] = []

        def mock_list(entity, tenant_id):
            calls.append((entity, tenant_id))
            return []

        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", mock_list)
        with pytest.raises(DomainValidationError):
            svc._check_payable_employees_exist_for_payroll_cycle_create(tenant_id=99, cycle_code="PAY-99")
        assert calls[0] == ("hr_employees", 99)

    def test_list_cycles_scoped_by_tenant(self, monkeypatch):
        calls: list[tuple[str, int]] = []

        def mock_list(entity, tenant_id):
            calls.append((entity, tenant_id))
            return []

        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", mock_list)
        svc.list_payroll_cycles(tenant_id=42)
        assert calls == [("hr_payroll_cycles", 42)]

    def test_list_hr_employees_scoped_by_tenant(self, monkeypatch):
        calls: list[tuple[str, int]] = []

        def mock_list(entity, tenant_id):
            calls.append((entity, tenant_id))
            return []

        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", mock_list)
        svc.list_hr_employees(tenant_id=88)
        assert calls == [("hr_employees", 88)]


class TestApprovalGuardW94:
    def test_w94_blocks_approval_if_no_payable(self, monkeypatch):
        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", lambda e, t: [_employee("terminated")])
        with pytest.raises(DomainValidationError):
            svc._check_active_employees_exist_for_payroll_approval(
                tenant_id=1,
                cycle_id=7,
                target_status="APPROVED",
            )

    def test_w94_surgical_non_approved_status_skips(self, monkeypatch):
        monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", lambda e, t: [])
        svc._check_active_employees_exist_for_payroll_approval(
            tenant_id=1,
            cycle_id=7,
            target_status="CALCULATING",
        )


class TestRouterStructure:
    def _router_source(self) -> str:
        return (Path(__file__).resolve().parents[1] / "app/modules/hr_payroll/router.py").read_text(encoding="utf-8")

    def test_router_uses_service_alias(self):
        source = self._router_source()
        assert "import app.modules.hr_payroll.service as _svc" in source

    def test_router_has_no_direct_service_imports(self):
        source = self._router_source()
        assert "from app.modules.hr_payroll.service import" not in source

    def test_create_payroll_cycle_maps_domain_error_to_422(self):
        source = self._router_source()
        assert "except (ValueError, DomainValidationError) as exc" in source
        assert "status_code=422" in source

    def test_create_hr_employee_maps_value_error_to_422(self):
        source = self._router_source()
        assert "def create_hr_employee_endpoint(" in source
        assert "except ValueError as exc" in source
        assert "status_code=422" in source

    def test_router_calls_use_service_alias(self):
        source = self._router_source()
        assert "_svc.create_payroll_cycle(" in source
        assert "_svc.update_payroll_cycle_status(" in source
        assert "_svc.list_hr_employees(" in source

    def test_router_has_expected_paths(self):
        from app.modules.hr_payroll import router as router_obj

        paths = {r.path for r in router_obj.router.routes}
        assert "/api/admin/hr-payroll/employees" in paths
        assert "/api/admin/hr-payroll/cycles" in paths
