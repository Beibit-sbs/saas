"""W38 domain-depth tests: faculty_performance_kpis module cap + low-score alert."""
from __future__ import annotations

import pytest

from app.modules.faculty_performance_kpis.service import (
    _ACTIVE_KPI_STATUSES,
    _KPI_PERIOD_MAX_ACTIVE,
    _LOW_SCORE_THRESHOLD,
    create_faculty_kpi,
)
from app.modules.faculty_performance_kpis.schemas import FacultyKpiCreateSchema

TENANT_ID = 12


# ---------------------------------------------------------------------------
# Test 1: cap dict sanity
# ---------------------------------------------------------------------------
def test_kpi_period_cap_dict_structure() -> None:
    """All cap values must be positive integers; known periods present."""
    for period, cap in _KPI_PERIOD_MAX_ACTIVE.items():
        assert isinstance(cap, int) and cap > 0, f"Bad cap for {period!r}"
    for required_key in ("Q1", "Q2", "annual", "semester"):
        assert required_key in _KPI_PERIOD_MAX_ACTIVE


# ---------------------------------------------------------------------------
# Test 2: active-status frozenset and low-score threshold
# ---------------------------------------------------------------------------
def test_active_statuses_and_low_score_threshold() -> None:
    assert isinstance(_ACTIVE_KPI_STATUSES, frozenset)
    assert "satisfactory" in _ACTIVE_KPI_STATUSES
    assert "on_probation" in _ACTIVE_KPI_STATUSES
    assert isinstance(_LOW_SCORE_THRESHOLD, float)
    assert _LOW_SCORE_THRESHOLD > 0


# ---------------------------------------------------------------------------
# Test 3: cap guard raises ValueError when limit reached
# ---------------------------------------------------------------------------
def test_create_faculty_kpi_raises_when_cap_reached(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service._check_faculty_has_active_contract_for_kpi",
        lambda *a, **kw: None,
    )
    cap = _KPI_PERIOD_MAX_ACTIVE.get("Q1", 50)
    existing_kpis = [
        {"kpi_period": "Q1", "status": "satisfactory", "id": i, "tenant_id": TENANT_ID}
        for i in range(cap)
    ]

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda entity, tid: existing_kpis if entity == "faculty_performance_kpis" else [],
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant",
        lambda entity, payload, tid: {**payload, "id": 999, "tenant_id": str(tid)},
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.log_admin_action",
        lambda **kwargs: None,
    )

    payload = FacultyKpiCreateSchema(
        faculty_id="F-OVER",
        name="Overflow KPI",
        department_id="cs",
        kpi_period="Q1",
        teaching_score=80.0,
        research_score=80.0,
        service_score=80.0,
        overall_score=80.0,
        status="satisfactory",
    )

    with pytest.raises(ValueError, match="Q1"):
        create_faculty_kpi(TENANT_ID, payload, actor="admin@test")


# ---------------------------------------------------------------------------
# Test 4: low-score alert record created for overall_score below threshold
# ---------------------------------------------------------------------------
def test_create_faculty_kpi_triggers_low_performance_alert(monkeypatch) -> None:
    created: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service._check_faculty_has_active_contract_for_kpi",
        lambda *a, **kw: None,
    )

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda entity, tid: [],
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant",
        lambda entity, payload, tid: (
            created.append((entity, payload))
            or {**payload, "id": 55, "tenant_id": str(tid)}
        ),
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.log_admin_action",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.EventPublisher",
        lambda: type("EP", (), {"publish_event": lambda self, **kw: None})(),
    )

    low_score = _LOW_SCORE_THRESHOLD - 10.0
    payload = FacultyKpiCreateSchema(
        faculty_id="F-LOW",
        name="Low KPI",
        department_id="math",
        kpi_period="annual",
        teaching_score=30.0,
        research_score=35.0,
        service_score=40.0,
        overall_score=low_score,
        status="on_probation",
    )

    create_faculty_kpi(TENANT_ID, payload, actor="admin@test")

    entities_created = [e for e, _ in created]
    assert "faculty_kpi_low_performance_alerts" in entities_created
    alert_payloads = [p for e, p in created if e == "faculty_kpi_low_performance_alerts"]
    assert len(alert_payloads) == 1
    assert alert_payloads[0]["alert_status"] == "open"
    assert alert_payloads[0]["integration_source"] == "faculty_kpi_alert"
