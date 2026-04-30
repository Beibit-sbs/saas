"""W43 domain-depth tests: hr_payroll module count-cap + offboarding alert."""
from __future__ import annotations

import pytest

from app.modules.hr_payroll.service import (
    _ACTIVE_EMPLOYEE_STATUSES,
    _EMPLOYEE_STATUS_MAX_ACTIVE,
    _OFFBOARDING_RISK_STATUSES,
    _ensure_offboarding_alert_record,
    create_hr_employee,
)
from app.modules.hr_payroll.schemas import HrEmployeeCreateSchema

TENANT_ID = 17


# ---------------------------------------------------------------------------
# Test 1: cap dict sanity
# ---------------------------------------------------------------------------
def test_employee_status_cap_dict_structure() -> None:
    """All cap values must be positive integers; key statuses present."""
    for status, cap in _EMPLOYEE_STATUS_MAX_ACTIVE.items():
        assert isinstance(cap, int) and cap > 0, f"Bad cap for {status!r}"
    assert "active" in _EMPLOYEE_STATUS_MAX_ACTIVE
    assert "offboarding" in _EMPLOYEE_STATUS_MAX_ACTIVE


# ---------------------------------------------------------------------------
# Test 2: active statuses and offboarding risk statuses
# ---------------------------------------------------------------------------
def test_active_statuses_and_offboarding_risk_statuses() -> None:
    assert isinstance(_ACTIVE_EMPLOYEE_STATUSES, frozenset)
    assert "active" in _ACTIVE_EMPLOYEE_STATUSES
    assert "onboarding" in _ACTIVE_EMPLOYEE_STATUSES
    assert "terminated" not in _ACTIVE_EMPLOYEE_STATUSES
    assert isinstance(_OFFBOARDING_RISK_STATUSES, frozenset)
    assert "offboarding" in _OFFBOARDING_RISK_STATUSES
    assert "terminated" in _OFFBOARDING_RISK_STATUSES


# ---------------------------------------------------------------------------
# Test 3: count-cap guard raises ValueError when limit reached
# ---------------------------------------------------------------------------
def test_create_hr_employee_raises_when_cap_reached(monkeypatch) -> None:
    cap = _EMPLOYEE_STATUS_MAX_ACTIVE.get("active", 1000)
    existing = [
        {"employee_code": f"EMP-{i}", "status": "active", "id": i, "tenant_id": str(TENANT_ID)}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        lambda entity, tid: existing if entity == "hr_employees" else [],
    )
    monkeypatch.setattr(
        "app.modules.hr_payroll.service.create_entity_for_tenant",
        lambda entity, payload, tid: {**payload, "id": 9999, "tenant_id": str(tid)},
    )
    monkeypatch.setattr(
        "app.modules.hr_payroll.service.log_admin_action",
        lambda **kwargs: None,
    )

    payload = HrEmployeeCreateSchema(
        employee_code="EMP-OVER",
        full_name="Over Flow",
        department_id="DEPT-01",
        role_title="Staff",
        status="active",
    )

    with pytest.raises(ValueError, match="cap"):
        create_hr_employee(TENANT_ID, payload, actor="admin@test")


# ---------------------------------------------------------------------------
# Test 4: offboarding alert helper is idempotent
# ---------------------------------------------------------------------------
def test_ensure_offboarding_alert_record_is_idempotent(monkeypatch) -> None:
    created: list[tuple[str, dict]] = []

    existing_alerts = [
        {
            "integration_source": "hr_offboarding_queue",
            "source_entity_id": "55",
            "id": 1,
            "tenant_id": str(TENANT_ID),
        }
    ]

    monkeypatch.setattr(
        "app.modules.hr_payroll.service.list_entities_for_tenant",
        lambda entity, tid: existing_alerts if entity == "hr_offboarding_alerts" else [],
    )
    monkeypatch.setattr(
        "app.modules.hr_payroll.service.create_entity_for_tenant",
        lambda entity, payload, tid: (
            created.append((entity, payload))
            or {**payload, "id": 99, "tenant_id": str(tid)}
        ),
    )

    _ensure_offboarding_alert_record(
        tenant_id=TENANT_ID,
        employee_id=55,
        employee_data={"employee_code": "EMP-55", "department_id": "DEPT-01", "status": "offboarding"},
    )

    assert len(created) == 0, "Expected no new record created due to idempotency"
