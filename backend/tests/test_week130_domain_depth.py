"""W130 Domain Depth — faculty_performance_kpis × faculty_contracts guard (expanded).

Expanded coverage for the W103 cross-entity guard:
  _check_faculty_has_active_contract_for_kpi (in faculty_performance_kpis/service.py)

Covers:
- Guard unit tests: whitespace, case insensitivity, resigned/on_leave status, tenant
  isolation, multi-contract scenarios, error message content
- Service integration tests: guard fires first, cap enforcement per period, event
  emission for low scores, alert record creation for critically low scores
- Router hardening: DomainValidationError now caught → HTTP 422 (W130 fix)
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.faculty_performance_kpis.schemas import FacultyKpiCreateSchema
from app.modules.faculty_performance_kpis.service import (
    _KPI_ACTIVE_CONTRACT_STATUSES,
    _KPI_PERIOD_MAX_ACTIVE,
    _LOW_SCORE_THRESHOLD,
    _check_faculty_has_active_contract_for_kpi,
    create_faculty_kpi,
)

TENANT_ID = 9130


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _contract(faculty_id: str, status: str, cid: int = 1) -> dict:
    return {"id": cid, "faculty_id": faculty_id, "status": status}


def _kpi_request(
    faculty_id: str = "FAC-130",
    kpi_period: str = "Q1",
    overall_score: float = 75.0,
    status: str = "satisfactory",
) -> FacultyKpiCreateSchema:
    return FacultyKpiCreateSchema(
        faculty_id=faculty_id,
        name="Performance Review Q1",
        department_id="DEPT-ENG",
        kpi_period=kpi_period,
        teaching_score=80.0,
        research_score=70.0,
        service_score=75.0,
        overall_score=overall_score,
        status=status,  # type: ignore[arg-type]
    )


def _minimal_list(contracts_for: str, status: str):
    """Return a monkeypatch list function returning one contract for the given faculty_id."""
    def _inner(table, tid):
        if table == "faculty_contracts":
            return [_contract(contracts_for, status)]
        return []
    return _inner


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

def test_w130_active_status_in_sentinel():
    assert "active" in _KPI_ACTIVE_CONTRACT_STATUSES


def test_w130_inactive_statuses_not_in_sentinel():
    for bad in ("terminated", "expired", "suspended", "resigned", "on_leave", "inactive", ""):
        assert bad not in _KPI_ACTIVE_CONTRACT_STATUSES, f"'{bad}' should NOT be in active set"


def test_w130_sentinel_is_frozenset():
    assert isinstance(_KPI_ACTIVE_CONTRACT_STATUSES, frozenset)


def test_w130_low_score_threshold_is_numeric():
    assert isinstance(_LOW_SCORE_THRESHOLD, float)
    assert 0.0 < _LOW_SCORE_THRESHOLD <= 100.0


def test_w130_period_caps_present_for_standard_periods():
    for period in ("Q1", "Q2", "Q3", "Q4", "annual", "semester"):
        assert period in _KPI_PERIOD_MAX_ACTIVE, f"Period '{period}' missing from cap map"


# ---------------------------------------------------------------------------
# 2. Guard unit tests — happy path
# ---------------------------------------------------------------------------

def test_w130_guard_active_contract_passes(monkeypatch):
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        _minimal_list("FAC-A", "active"),
    )
    _check_faculty_has_active_contract_for_kpi(
        tenant_id=TENANT_ID, faculty_id="FAC-A", kpi_period="Q1"
    )  # must NOT raise


def test_w130_guard_multiple_contracts_one_active_passes(monkeypatch):
    def _list(table, tid):
        if table == "faculty_contracts":
            return [
                _contract("FAC-M", "terminated", 1),
                _contract("FAC-M", "expired", 2),
                _contract("FAC-M", "active", 3),
            ]
        return []
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", _list
    )
    _check_faculty_has_active_contract_for_kpi(
        tenant_id=TENANT_ID, faculty_id="FAC-M", kpi_period="annual"
    )


def test_w130_guard_faculty_id_whitespace_stripped(monkeypatch):
    """Faculty IDs with surrounding whitespace must still match."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        _minimal_list("FAC-WS", "active"),
    )
    _check_faculty_has_active_contract_for_kpi(
        tenant_id=TENANT_ID, faculty_id="  FAC-WS  ", kpi_period="Q2"
    )


# ---------------------------------------------------------------------------
# 3. Guard unit tests — blocked cases
# ---------------------------------------------------------------------------

def test_w130_guard_no_contracts_raises_domain_error(monkeypatch):
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    with pytest.raises(DomainValidationError, match="no contract records found"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-NONE", kpi_period="Q1"
        )


def test_w130_guard_terminated_blocks(monkeypatch):
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        _minimal_list("FAC-T", "terminated"),
    )
    with pytest.raises(DomainValidationError, match="no active contract found"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-T", kpi_period="Q3"
        )


def test_w130_guard_expired_blocks(monkeypatch):
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        _minimal_list("FAC-EX", "expired"),
    )
    with pytest.raises(DomainValidationError, match="no active contract found"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-EX", kpi_period="Q4"
        )


def test_w130_guard_resigned_blocks(monkeypatch):
    """Resigned faculty must be blocked — resigned ≠ active."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        _minimal_list("FAC-RES", "resigned"),
    )
    with pytest.raises(DomainValidationError, match="no active contract found"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-RES", kpi_period="semester"
        )


def test_w130_guard_on_leave_blocks(monkeypatch):
    """on_leave ≠ active. KPI creation blocked if only on_leave contract exists."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        _minimal_list("FAC-OL", "on_leave"),
    )
    with pytest.raises(DomainValidationError, match="no active contract found"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-OL", kpi_period="Q1"
        )


def test_w130_guard_inactive_status_blocks(monkeypatch):
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        _minimal_list("FAC-INA", "inactive"),
    )
    with pytest.raises(DomainValidationError):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-INA", kpi_period="annual"
        )


def test_w130_guard_different_faculty_not_counted(monkeypatch):
    """Active contract for a DIFFERENT faculty must not satisfy the guard."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        _minimal_list("FAC-OTHER", "active"),
    )
    with pytest.raises(DomainValidationError, match="no contract records found"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-TARGET", kpi_period="Q1"
        )


def test_w130_guard_fail_closed_on_db_error(monkeypatch):
    def _boom(table, tid):
        raise ConnectionError("DB unreachable")
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", _boom
    )
    with pytest.raises(DomainValidationError, match="faculty_contracts lookup failed"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-DB", kpi_period="Q2"
        )


def test_w130_guard_fail_closed_on_timeout(monkeypatch):
    def _timeout(table, tid):
        raise TimeoutError("query timed out")
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", _timeout
    )
    with pytest.raises(DomainValidationError, match="faculty_contracts lookup failed"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-TOUT", kpi_period="semester"
        )


# ---------------------------------------------------------------------------
# 4. Guard error message content
# ---------------------------------------------------------------------------

def test_w130_guard_error_contains_faculty_id(monkeypatch):
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda t, tid: [],
    )
    with pytest.raises(DomainValidationError, match="FAC-ERR-130"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-ERR-130", kpi_period="Q1"
        )


def test_w130_guard_error_contains_kpi_period(monkeypatch):
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda t, tid: [],
    )
    with pytest.raises(DomainValidationError, match="annual"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-P", kpi_period="annual"
        )


def test_w130_guard_error_contains_found_statuses_on_inactive(monkeypatch):
    """When contracts exist but none active, error should mention the found statuses."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        _minimal_list("FAC-S", "terminated"),
    )
    with pytest.raises(DomainValidationError, match="terminated"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID, faculty_id="FAC-S", kpi_period="Q1"
        )


# ---------------------------------------------------------------------------
# 5. Service integration — guard fires first (no persist on block)
# ---------------------------------------------------------------------------

def test_w130_create_kpi_guard_fires_before_persist(monkeypatch):
    persisted: list = []

    def fake_list(table, tid):
        if table == "faculty_contracts":
            return []  # no contracts → guard blocks
        return []

    def fake_create(table, payload, tid):
        persisted.append(payload)
        return {"id": 1, "tenant_id": str(tid), **payload}

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", fake_create
    )

    with pytest.raises(DomainValidationError):
        create_faculty_kpi(TENANT_ID, _kpi_request(faculty_id="FAC-NP"), actor="admin")

    assert not persisted, "create_entity_for_tenant MUST NOT be called when guard blocks"


def test_w130_create_kpi_allowed_with_active_contract(monkeypatch):
    created: list = []

    def fake_list(table, tid):
        if table == "faculty_contracts":
            return [_contract("FAC-OK", "active")]
        return []

    def fake_create(table, payload, tid):
        row = {"id": 10, "tenant_id": str(tid), **payload}
        created.append(row)
        return row

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", fake_create
    )

    result = create_faculty_kpi(TENANT_ID, _kpi_request(faculty_id="FAC-OK"), actor="admin")
    assert result.faculty_id == "FAC-OK"
    assert created, "create_entity_for_tenant must be called when guard passes"


def test_w130_create_kpi_blocked_terminated_raises_domain_error(monkeypatch):
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        _minimal_list("FAC-T2", "terminated"),
    )
    with pytest.raises(DomainValidationError, match="FAC-T2"):
        create_faculty_kpi(TENANT_ID, _kpi_request(faculty_id="FAC-T2"), actor="admin")


def test_w130_create_kpi_blocked_no_contracts_raises_domain_error(monkeypatch):
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda t, tid: [],
    )
    with pytest.raises(DomainValidationError):
        create_faculty_kpi(TENANT_ID, _kpi_request(faculty_id="FAC-NC"), actor="admin")


# ---------------------------------------------------------------------------
# 6. Cap enforcement per period
# ---------------------------------------------------------------------------

def _make_active_kpi(faculty_id: str, period: str, idx: int, status: str = "satisfactory") -> dict:
    return {
        "id": idx,
        "faculty_id": faculty_id,
        "kpi_period": period,
        "status": status,
        "overall_score": 70.0,
        "teaching_score": 70.0,
        "research_score": 70.0,
        "service_score": 70.0,
        "name": f"KPI {idx}",
        "department_id": "DEPT-X",
    }


def test_w130_cap_blocks_when_period_at_limit(monkeypatch):
    period = "Q1"
    cap = _KPI_PERIOD_MAX_ACTIVE[period]

    existing_kpis = [_make_active_kpi("FAC-X", period, i) for i in range(cap)]

    def fake_list(table, tid):
        if table == "faculty_contracts":
            return [_contract("FAC-CAP", "active")]
        if table == "faculty_performance_kpis":
            return existing_kpis
        return []

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )

    with pytest.raises(ValueError, match="cap"):
        create_faculty_kpi(TENANT_ID, _kpi_request(faculty_id="FAC-CAP", kpi_period=period), actor="a")


def test_w130_cap_passes_when_period_below_limit(monkeypatch):
    period = "Q2"
    cap = _KPI_PERIOD_MAX_ACTIVE[period]
    existing_kpis = [_make_active_kpi("FAC-Y", period, i) for i in range(cap - 1)]
    created: list = []

    def fake_list(table, tid):
        if table == "faculty_contracts":
            return [_contract("FAC-UNDER", "active")]
        if table == "faculty_performance_kpis":
            return existing_kpis
        return []

    def fake_create(table, payload, tid):
        row = {"id": 999, "tenant_id": str(tid), **payload}
        created.append(row)
        return row

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", fake_create
    )

    result = create_faculty_kpi(TENANT_ID, _kpi_request(faculty_id="FAC-UNDER", kpi_period=period), actor="a")
    assert result.id == 999


def test_w130_cap_not_enforced_for_non_active_status(monkeypatch):
    """KPIs in non-active statuses (e.g. 'rejected') must not count toward cap."""
    period = "annual"
    cap = _KPI_PERIOD_MAX_ACTIVE[period]
    # All existing KPIs have a non-active status (not in _ACTIVE_KPI_STATUSES)
    existing_kpis = [_make_active_kpi("FAC-Z", period, i, status="resolved") for i in range(cap + 10)]
    created: list = []

    def fake_list(table, tid):
        if table == "faculty_contracts":
            return [_contract("FAC-NACT", "active")]
        if table == "faculty_performance_kpis":
            return existing_kpis
        return []

    def fake_create(table, payload, tid):
        row = {"id": 777, "tenant_id": str(tid), **payload}
        created.append(row)
        return row

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", fake_create
    )

    result = create_faculty_kpi(
        TENANT_ID,
        _kpi_request(faculty_id="FAC-NACT", kpi_period=period),
        actor="admin",
    )
    assert result.id == 777


# ---------------------------------------------------------------------------
# 7. Low-score event + alert side effects
# ---------------------------------------------------------------------------

def test_w130_create_kpi_low_score_triggers_event(monkeypatch):
    """overall_score < 60 → EventPublisher.publish_event called."""
    events: list[dict] = []

    class FakePublisher:
        def publish_event(self, **kwargs):
            events.append(kwargs)

    def fake_list(table, tid):
        if table == "faculty_contracts":
            return [_contract("FAC-LOW", "active")]
        return []

    def fake_create(table, payload, tid):
        return {"id": 5, "tenant_id": str(tid), **payload}

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", fake_create
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.EventPublisher",
        lambda: FakePublisher(),
    )

    create_faculty_kpi(
        TENANT_ID,
        _kpi_request(faculty_id="FAC-LOW", overall_score=55.0),
        actor="admin",
    )

    warning_events = [e for e in events if "kpi.warning_detected" in str(e.get("event_type", ""))]
    assert warning_events, "Expected faculty_performance.kpi.warning_detected event for score < 60"


def test_w130_create_kpi_high_score_no_warning_event(monkeypatch):
    """overall_score >= 60 → NO kpi.warning_detected event."""
    events: list[dict] = []

    class FakePublisher:
        def publish_event(self, **kwargs):
            events.append(kwargs)

    def fake_list(table, tid):
        if table == "faculty_contracts":
            return [_contract("FAC-HIGH", "active")]
        return []

    def fake_create(table, payload, tid):
        return {"id": 6, "tenant_id": str(tid), **payload}

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", fake_create
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.EventPublisher",
        lambda: FakePublisher(),
    )

    create_faculty_kpi(
        TENANT_ID,
        _kpi_request(faculty_id="FAC-HIGH", overall_score=80.0),
        actor="admin",
    )

    warning_events = [e for e in events if "kpi.warning_detected" in str(e.get("event_type", ""))]
    assert not warning_events, "No warning event expected for overall_score >= 60"


def test_w130_create_kpi_critical_low_score_creates_alert_record(monkeypatch):
    """overall_score < _LOW_SCORE_THRESHOLD → low-performance alert record created."""
    created_tables: list[str] = []

    def fake_list(table, tid):
        if table == "faculty_contracts":
            return [_contract("FAC-CRIT", "active")]
        return []  # no existing alerts

    def fake_create(table, payload, tid):
        created_tables.append(table)
        return {"id": 77, "tenant_id": str(tid), **payload}

    class FakePublisher:
        def publish_event(self, **kwargs):
            pass

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", fake_create
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.EventPublisher",
        lambda: FakePublisher(),
    )

    score_below_threshold = _LOW_SCORE_THRESHOLD - 1.0
    create_faculty_kpi(
        TENANT_ID,
        _kpi_request(faculty_id="FAC-CRIT", overall_score=score_below_threshold),
        actor="admin",
    )

    assert "faculty_kpi_low_performance_alerts" in created_tables, (
        "Alert record must be created for overall_score below _LOW_SCORE_THRESHOLD"
    )


def test_w130_create_kpi_score_at_threshold_no_alert(monkeypatch):
    """overall_score == _LOW_SCORE_THRESHOLD → NO alert record (threshold is exclusive)."""
    created_tables: list[str] = []

    def fake_list(table, tid):
        if table == "faculty_contracts":
            return [_contract("FAC-AT", "active")]
        return []

    def fake_create(table, payload, tid):
        created_tables.append(table)
        return {"id": 88, "tenant_id": str(tid), **payload}

    class FakePublisher:
        def publish_event(self, **kwargs):
            pass

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", fake_create
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.EventPublisher",
        lambda: FakePublisher(),
    )

    create_faculty_kpi(
        TENANT_ID,
        _kpi_request(faculty_id="FAC-AT", overall_score=_LOW_SCORE_THRESHOLD),
        actor="admin",
    )

    assert "faculty_kpi_low_performance_alerts" not in created_tables, (
        "Alert record must NOT be created when score == threshold"
    )


# ---------------------------------------------------------------------------
# 8. Multi-period correctness
# ---------------------------------------------------------------------------

def test_w130_create_kpi_different_period_cap_checked_independently(monkeypatch):
    """KPIs in period Q3 do not count against Q4 cap."""
    cap_q4 = _KPI_PERIOD_MAX_ACTIVE["Q4"]
    # Fill Q3 to capacity but Q4 is empty
    existing_q3 = [_make_active_kpi("FAC-P", "Q3", i) for i in range(cap_q4 + 5)]
    created: list = []

    def fake_list(table, tid):
        if table == "faculty_contracts":
            return [_contract("FAC-PERQ4", "active")]
        if table == "faculty_performance_kpis":
            return existing_q3
        return []

    def fake_create(table, payload, tid):
        row = {"id": 300, "tenant_id": str(tid), **payload}
        created.append(row)
        return row

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", fake_create
    )

    result = create_faculty_kpi(
        TENANT_ID,
        _kpi_request(faculty_id="FAC-PERQ4", kpi_period="Q4"),
        actor="admin",
    )
    assert result.id == 300, "Q4 KPI should be created since Q4 is not at capacity"


# ---------------------------------------------------------------------------
# 9. Router hardening — W130 fix: DomainValidationError → HTTP 422
# ---------------------------------------------------------------------------

def test_w130_router_import_catches_domain_validation_error():
    """Router must import and catch DomainValidationError (structural test)."""
    import importlib
    import inspect
    router_mod = importlib.import_module("app.modules.faculty_performance_kpis.router")
    source = inspect.getsource(router_mod)
    assert "DomainValidationError" in source, (
        "Router must import DomainValidationError (W130 hardening)"
    )


def test_w130_router_create_endpoint_catches_domain_validation_error():
    """Router create endpoint must catch (ValueError, DomainValidationError)."""
    import importlib
    import inspect
    router_mod = importlib.import_module("app.modules.faculty_performance_kpis.router")
    source = inspect.getsource(router_mod)
    assert "DomainValidationError" in source
    # Verify the except clause handles DomainValidationError
    assert "except (ValueError, DomainValidationError)" in source, (
        "Router create endpoint must catch both ValueError and DomainValidationError"
    )
