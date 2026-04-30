"""Week 59 domain-depth tests: campus_sla — priority active cap + breach risk alert."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Test 1: Cap dict structure
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_sla_priority_max_active_dict_structure():
    from app.modules.campus_sla.service import _SLA_PRIORITY_MAX_ACTIVE

    assert isinstance(_SLA_PRIORITY_MAX_ACTIVE, dict)
    assert len(_SLA_PRIORITY_MAX_ACTIVE) >= 2
    for k, v in _SLA_PRIORITY_MAX_ACTIVE.items():
        assert isinstance(k, str) and len(k) > 0
        assert isinstance(v, int) and v > 0


# ---------------------------------------------------------------------------
# Test 2: Frozenset constants
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_active_sla_statuses_and_breach_risk_statuses_are_frozensets():
    from app.modules.campus_sla.service import _ACTIVE_SLA_STATUSES, _BREACH_RISK_STATUSES

    assert isinstance(_ACTIVE_SLA_STATUSES, frozenset)
    assert isinstance(_BREACH_RISK_STATUSES, frozenset)
    assert len(_ACTIVE_SLA_STATUSES) >= 1
    assert len(_BREACH_RISK_STATUSES) >= 1
    assert all(isinstance(s, str) for s in _ACTIVE_SLA_STATUSES)
    assert all(isinstance(s, str) for s in _BREACH_RISK_STATUSES)


# ---------------------------------------------------------------------------
# Test 3: create_sla_record raises when active cap reached
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_sla_record_raises_when_active_cap_reached(monkeypatch):
    from app.modules.campus_sla import service
    monkeypatch.setattr(service, "_check_facility_has_active_maintenance_request", lambda *a, **kw: None)

    priority = next(iter(service._SLA_PRIORITY_MAX_ACTIVE))
    cap = service._SLA_PRIORITY_MAX_ACTIVE[priority]
    active_status = next(iter(service._ACTIVE_SLA_STATUSES))

    fake_records = [
        {"priority": priority, "status": active_status, "id": i}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: fake_records,
    )

    payload = {
        "service_type": "it_support",
        "facility_code": "FAC-001",
        "target_sla_minutes": 60,
        "priority": priority,
        "status": active_status,
    }

    with pytest.raises(ValueError, match="active SLA record cap reached"):
        service.create_sla_record(payload=payload, tenant_id=1)


# ---------------------------------------------------------------------------
# Test 4: _ensure_sla_breach_risk_alert is idempotent
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ensure_sla_breach_risk_alert_is_idempotent(monkeypatch):
    from app.modules.campus_sla import service

    calls_to_create: list = []
    event_mock = MagicMock()

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: (
            [{"integration_source": "campus_sla_breach_queue", "source_entity_id": "55"}]
            if entity == "campus_sla_breach_risk_alerts"
            else []
        ),
    )
    monkeypatch.setattr(
        service, "create_entity_for_tenant",
        lambda entity, data, tenant_id: calls_to_create.append((entity, data)) or data,
    )

    with patch(
        "app.platform.events.publisher.EventPublisher.publish_event",
        event_mock,
    ):
        service._ensure_sla_breach_risk_alert(
            tenant_id=1,
            record_id="55",
            record_data={
                "service_type": "it_support",
                "facility_code": "FAC-001",
                "priority": "critical",
            },
        )

    # Already exists → no new create, no event
    assert len(calls_to_create) == 0
    event_mock.assert_not_called()
