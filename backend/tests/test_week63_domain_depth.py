"""Week 63 domain-depth tests: faculty_performance_kpis — performance risk statuses + low score alert."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Test 1: Cap dict structure
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_kpi_period_max_active_dict_structure():
    from app.modules.faculty_performance_kpis.service import _KPI_PERIOD_MAX_ACTIVE

    assert isinstance(_KPI_PERIOD_MAX_ACTIVE, dict)
    assert len(_KPI_PERIOD_MAX_ACTIVE) >= 2
    for k, v in _KPI_PERIOD_MAX_ACTIVE.items():
        assert isinstance(k, str) and len(k) > 0
        assert isinstance(v, int) and v > 0


# ---------------------------------------------------------------------------
# Test 2: Frozenset constants for active and risk statuses
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_active_and_performance_risk_statuses_are_frozensets():
    from app.modules.faculty_performance_kpis.service import _ACTIVE_KPI_STATUSES, _PERFORMANCE_RISK_STATUSES

    assert isinstance(_ACTIVE_KPI_STATUSES, frozenset)
    assert isinstance(_PERFORMANCE_RISK_STATUSES, frozenset)
    assert len(_ACTIVE_KPI_STATUSES) >= 1
    assert len(_PERFORMANCE_RISK_STATUSES) >= 1
    assert all(isinstance(s, str) for s in _ACTIVE_KPI_STATUSES)
    assert all(isinstance(s, str) for s in _PERFORMANCE_RISK_STATUSES)


# ---------------------------------------------------------------------------
# Test 3: create_faculty_kpi raises when active cap reached
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_faculty_kpi_raises_when_active_cap_reached(monkeypatch):
    from app.modules.faculty_performance_kpis import service

    period = next(iter(service._KPI_PERIOD_MAX_ACTIVE))
    cap = service._KPI_PERIOD_MAX_ACTIVE[period]
    active_status = next(iter(service._ACTIVE_KPI_STATUSES))

    fake_kpis = [
        {"id": i, "kpi_period": period, "status": active_status, "faculty_id": f"fac_{i}"}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: fake_kpis,
    )

    from app.modules.faculty_performance_kpis.schemas import FacultyKpiCreateSchema
    request = FacultyKpiCreateSchema(
        faculty_id="fac_test",
        name="Test KPI",
        department_id="CS",
        kpi_period=period,
        teaching_score=80.0,
        research_score=70.0,
        service_score=75.0,
        overall_score=75.0,
        status=active_status,
    )

    with pytest.raises(ValueError, match="Active KPI cap"):
        service.create_faculty_kpi(tenant_id=1, request=request, actor="admin")


# ---------------------------------------------------------------------------
# Test 4: _ensure_low_performance_alert_record is idempotent + EventPublisher
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ensure_low_performance_alert_record_is_idempotent_with_event(monkeypatch):
    from app.modules.faculty_performance_kpis import service

    calls_to_create: list = []

    # Mock: existing alert already exists
    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: (
            [{"integration_source": "faculty_kpi_alert", "source_entity_id": "77"}]
            if entity == "faculty_kpi_low_performance_alerts"
            else []
        ),
    )
    monkeypatch.setattr(
        service, "create_entity_for_tenant",
        lambda entity, data, tenant_id: calls_to_create.append((entity, data)) or data,
    )

    # Mock: EventPublisher.publish_event
    mock_publisher = MagicMock()
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publisher,
    )

    service._ensure_low_performance_alert_record(
        tenant_id=1,
        kpi_id=77,
        kpi_data={
            "faculty_id": "fac_001",
            "kpi_period": "Q1",
            "overall_score": 45.0,
        },
    )

    # Alert already exists → no new create and no new event
    assert len(calls_to_create) == 0
    assert mock_publisher.call_count == 0


# ---------------------------------------------------------------------------
# Test 4b: _ensure_low_performance_alert_record creates alert when not exists
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ensure_low_performance_alert_record_creates_when_not_exists(monkeypatch):
    from app.modules.faculty_performance_kpis import service

    calls_to_create: list = []

    # Mock: no existing alerts
    monkeypatch.setattr(
        service, "list_entities_for_tenant",
        lambda entity, tenant_id: [],
    )
    monkeypatch.setattr(
        service, "create_entity_for_tenant",
        lambda entity, data, tenant_id: calls_to_create.append((entity, data)) or data,
    )

    # Mock: EventPublisher.publish_event
    mock_publisher = MagicMock()
    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        mock_publisher,
    )

    service._ensure_low_performance_alert_record(
        tenant_id=1,
        kpi_id=88,
        kpi_data={
            "faculty_id": "fac_002",
            "kpi_period": "Q2",
            "overall_score": 40.0,
        },
    )

    # Should create alert + publish event
    assert len(calls_to_create) == 1
    assert calls_to_create[0][0] == "faculty_kpi_low_performance_alerts"
    assert calls_to_create[0][1]["kpi_id"] == 88
    assert calls_to_create[0][1]["integration_source"] == "faculty_kpi_alert"
    
    # Event should be published once
    assert mock_publisher.call_count == 1
    call_kwargs = mock_publisher.call_args[1]
    assert call_kwargs["event_type"] == "campus.faculty_performance.low_score_alert_detected"
    assert call_kwargs["tenant_id"] == 1
