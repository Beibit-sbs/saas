"""W66 domain-depth tests: hr_payroll — payroll cycle risk cap + alert + event."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# 1. Cap dict structure
# ---------------------------------------------------------------------------

def test_w66_employee_status_max_active_dict_structure() -> None:
    from app.modules.hr_payroll.service import _EMPLOYEE_STATUS_MAX_ACTIVE

    assert isinstance(_EMPLOYEE_STATUS_MAX_ACTIVE, dict)
    assert len(_EMPLOYEE_STATUS_MAX_ACTIVE) >= 4
    for status, cap in _EMPLOYEE_STATUS_MAX_ACTIVE.items():
        assert isinstance(status, str) and len(status) > 0
        assert isinstance(cap, int) and cap > 0


# ---------------------------------------------------------------------------
# 2. Frozensets present and correct types
# ---------------------------------------------------------------------------

def test_w66_payroll_cycle_risk_statuses_frozenset() -> None:
    from app.modules.hr_payroll.service import (
        _OFFBOARDING_RISK_STATUSES,
        _PAYROLL_CYCLE_RISK_STATUSES,
    )

    assert isinstance(_OFFBOARDING_RISK_STATUSES, frozenset)
    assert isinstance(_PAYROLL_CYCLE_RISK_STATUSES, frozenset)
    assert len(_PAYROLL_CYCLE_RISK_STATUSES) >= 1
    assert all(isinstance(s, str) for s in _PAYROLL_CYCLE_RISK_STATUSES)


# ---------------------------------------------------------------------------
# 3. Cap guard raises ValueError when active employees exceed cap
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w66_cap_guard_raises_when_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.hr_payroll import service as svc
    from app.modules.hr_payroll.schemas import HrEmployeeCreateSchema

    cap = svc._EMPLOYEE_STATUS_MAX_ACTIVE["onboarding"]
    fake_rows = [
        {"status": "onboarding"}
        for _ in range(cap)
    ]
    monkeypatch.setattr(svc, "list_entities_for_tenant", lambda entity, tid: fake_rows)

    payload = HrEmployeeCreateSchema(
        employee_code="EMP-99",
        full_name="Test Employee",
        department_id="DEPT-1",
        role_title="Engineer",
        status="onboarding",
    )
    with pytest.raises(ValueError, match="cap"):
        svc.create_hr_employee(tenant_id=1, request=payload, actor="test")


# ---------------------------------------------------------------------------
# 4. Idempotent payroll cycle risk alert + event fired on first call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w66_payroll_cycle_risk_alert_idempotent_creates_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.hr_payroll import service as svc

    created_entities: list[str] = []
    mock_publish = MagicMock()

    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publish,
    )

    def fake_list(entity: str, tenant_id: int) -> list[dict]:
        return []

    def fake_create(entity: str, data: dict, tenant_id: int) -> dict:
        created_entities.append(entity)
        return {**data, "id": 88}

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    svc._ensure_payroll_cycle_risk_alert_record(
        tenant_id=1,
        cycle_id=42,
        cycle_data={"cycle_code": "CYC-001", "period_label": "2026-04", "employee_count": 120},
    )

    assert "hr_payroll_cycle_risk_alerts" in created_entities
    mock_publish.assert_called_once()
    call_kwargs = mock_publish.call_args.kwargs
    assert call_kwargs["event_type"] == "campus.hr.payroll_cycle_risk_detected"
    assert call_kwargs["tenant_id"] == 1


# ---------------------------------------------------------------------------
# 5. Idempotent: no duplicate created when record already exists
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_w66_payroll_cycle_risk_alert_skips_if_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.hr_payroll import service as svc

    mock_publish = MagicMock()
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publish,
    )

    def fake_list(entity: str, tenant_id: int) -> list[dict]:
        if entity == "hr_payroll_cycle_risk_alerts":
            return [
                {
                    "integration_source": "payroll_cycle_risk",
                    "source_entity_id": "42",
                }
            ]
        return []

    created_entities: list[str] = []

    def fake_create(entity: str, data: dict, tenant_id: int) -> dict:
        created_entities.append(entity)
        return {**data, "id": 10}

    monkeypatch.setattr(svc, "list_entities_for_tenant", fake_list)
    monkeypatch.setattr(svc, "create_entity_for_tenant", fake_create)

    svc._ensure_payroll_cycle_risk_alert_record(
        tenant_id=1,
        cycle_id=42,
        cycle_data={"cycle_code": "CYC-001", "period_label": "2026-04", "employee_count": 120},
    )

    assert "hr_payroll_cycle_risk_alerts" not in created_entities
    mock_publish.assert_not_called()
