"""W73 domain-depth tests: hr_payroll employee lifecycle transition guard."""
from __future__ import annotations

import pytest

from app.modules.hr_payroll.schemas import HrEmployeeStatusUpdateSchema
from app.modules.hr_payroll.service import (
    _ALLOWED_EMPLOYEE_STATUS_TRANSITIONS,
    update_hr_employee_status,
)


def test_w73_allowed_employee_status_transition_succeeds(monkeypatch):
    rows = [{
        "id": 5,
        "status": "active",
        "employee_code": "E-5",
        "full_name": "Employee Five",
        "department_id": "DEPT-1",
        "role_title": "Lecturer",
    }]

    def mock_list(entity_name, tenant_id):
        assert entity_name == "hr_employees"
        return rows

    def mock_update(entity_name, employee_id, payload, tenant_id):
        assert payload["status"] == "on_leave"
        return {**payload, "id": employee_id, "tenant_id": str(tenant_id)}

    monkeypatch.setattr("app.modules.hr_payroll.service.list_entities_for_tenant", mock_list)
    monkeypatch.setattr("app.modules.hr_payroll.service.update_entity_for_tenant", mock_update)
    monkeypatch.setattr("app.modules.hr_payroll.service.log_admin_action", lambda **kwargs: None)

    result = update_hr_employee_status(
        tenant_id=1,
        employee_id=5,
        request=HrEmployeeStatusUpdateSchema(status="on_leave"),
        actor="hr@example.com",
    )

    assert result.status == "on_leave"


def test_w73_invalid_employee_status_transition_blocked(monkeypatch):
    rows = [{
        "id": 6,
        "status": "terminated",
        "employee_code": "E-6",
        "full_name": "Employee Six",
        "department_id": "DEPT-1",
        "role_title": "Lecturer",
    }]

    monkeypatch.setattr(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        lambda entity_name, tenant_id: rows,
    )

    with pytest.raises(ValueError, match="Invalid employee status transition"):
        update_hr_employee_status(
            tenant_id=1,
            employee_id=6,
            request=HrEmployeeStatusUpdateSchema(status="active"),
            actor="hr@example.com",
        )


def test_w73_missing_employee_raises_explicit_not_found(monkeypatch):
    monkeypatch.setattr(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        lambda entity_name, tenant_id: [],
    )

    with pytest.raises(LookupError, match="Employee not found"):
        update_hr_employee_status(
            tenant_id=1,
            employee_id=404,
            request=HrEmployeeStatusUpdateSchema(status="on_leave"),
            actor="hr@example.com",
        )


def test_w73_noop_transition_allowed(monkeypatch):
    rows = [{
        "id": 7,
        "status": "active",
        "employee_code": "E-7",
        "full_name": "Employee Seven",
        "department_id": "DEPT-2",
        "role_title": "Advisor",
    }]

    monkeypatch.setattr(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        lambda entity_name, tenant_id: rows,
    )
    monkeypatch.setattr(
        "app.modules.hr_payroll.service.update_entity_for_tenant",
        lambda entity_name, employee_id, payload, tenant_id: {**payload, "id": employee_id, "tenant_id": str(tenant_id)},
    )
    monkeypatch.setattr("app.modules.hr_payroll.service.log_admin_action", lambda **kwargs: None)

    result = update_hr_employee_status(
        tenant_id=1,
        employee_id=7,
        request=HrEmployeeStatusUpdateSchema(status="active"),
        actor="hr@example.com",
    )

    assert result.status == "active"


def test_w73_terminated_is_terminal_state():
    assert _ALLOWED_EMPLOYEE_STATUS_TRANSITIONS["terminated"] == frozenset()
