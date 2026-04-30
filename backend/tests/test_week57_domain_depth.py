"""Week 57 domain-depth tests: student_life — disciplinary case cap + escalation alert."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Test 1: Cap dict structure
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_disciplinary_severity_max_active_dict_structure():
    from app.modules.student_life.service import _DISCIPLINARY_SEVERITY_MAX_ACTIVE

    assert isinstance(_DISCIPLINARY_SEVERITY_MAX_ACTIVE, dict)
    assert len(_DISCIPLINARY_SEVERITY_MAX_ACTIVE) >= 2
    for k, v in _DISCIPLINARY_SEVERITY_MAX_ACTIVE.items():
        assert isinstance(k, str) and len(k) > 0
        assert isinstance(v, int) and v > 0


# ---------------------------------------------------------------------------
# Test 2: Frozenset constants
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_disciplinary_statuses_and_escalation_risk_statuses_are_frozensets():
    from app.modules.student_life.service import (
        _ACTIVE_DISCIPLINARY_STATUSES,
        _DISCIPLINARY_ESCALATION_RISK_STATUSES,
    )

    assert isinstance(_ACTIVE_DISCIPLINARY_STATUSES, frozenset)
    assert isinstance(_DISCIPLINARY_ESCALATION_RISK_STATUSES, frozenset)
    assert len(_ACTIVE_DISCIPLINARY_STATUSES) >= 1
    assert len(_DISCIPLINARY_ESCALATION_RISK_STATUSES) >= 1
    assert all(isinstance(s, str) for s in _ACTIVE_DISCIPLINARY_STATUSES)
    assert all(isinstance(s, str) for s in _DISCIPLINARY_ESCALATION_RISK_STATUSES)


# ---------------------------------------------------------------------------
# Test 3: create_disciplinary_case raises when active cap reached
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_disciplinary_case_raises_when_active_cap_reached(monkeypatch):
    from app.modules.student_life import service
    from app.modules.student_life.schemas import DisciplinaryCaseCreateSchema

    severity = next(iter(service._DISCIPLINARY_SEVERITY_MAX_ACTIVE))
    cap = service._DISCIPLINARY_SEVERITY_MAX_ACTIVE[severity]
    active_status = next(iter(service._ACTIVE_DISCIPLINARY_STATUSES))

    fake_cases = [
        {"severity": severity, "status": active_status, "id": i}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: fake_cases,
    )

    request = DisciplinaryCaseCreateSchema(
        incident_code="INC-W57",
        student_id="STU-001",
        incident_type="misconduct",
        severity=severity,
        status=active_status,
    )

    with pytest.raises(ValueError, match="active disciplinary case cap reached for severity"):
        service.create_disciplinary_case(tenant_id=1, request=request, actor="test")


# ---------------------------------------------------------------------------
# Test 4: _ensure_disciplinary_escalation_alert is idempotent
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ensure_disciplinary_escalation_alert_is_idempotent(monkeypatch):
    from app.modules.student_life import service

    calls_to_create: list = []
    event_mock = MagicMock()

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: (
            [{"integration_source": "disciplinary_escalation_queue", "source_entity_id": "42"}]
            if entity == "student_life_disciplinary_escalation_alerts"
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
        service._ensure_disciplinary_escalation_alert(
            tenant_id=1,
            case_id=42,
            case_data={
                "incident_code": "INC-42",
                "student_id": "STU-001",
                "incident_type": "misconduct",
                "severity": "high",
                "status": "appealed",
            },
        )

    # Already exists → no new create, no event emitted
    assert len(calls_to_create) == 0
    event_mock.assert_not_called()
