"""W103 — Faculty KPI Active Contract Guard.

Cross-entity invariant: faculty_performance_kpis × faculty_contracts.

A faculty KPI record may only be created for a faculty member with an active
employment contract. Creating a KPI for a non-contracted or terminated faculty
member generates phantom Brain Core performance signals that corrupt HR analytics
and may trigger automated decisions for non-employees.

Guard location: faculty_performance_kpis/service.py ::
    _check_faculty_has_active_contract_for_kpi  (called BEFORE create_entity_for_tenant)
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.faculty_performance_kpis.service import (
    _KPI_ACTIVE_CONTRACT_STATUSES,
    _check_faculty_has_active_contract_for_kpi,
    create_faculty_kpi,
)
from app.modules.faculty_performance_kpis.schemas import FacultyKpiCreateSchema

TENANT_ID = 9003

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _contract(faculty_id: str, status: str, contract_id: int = 1) -> dict:
    return {"id": contract_id, "faculty_id": faculty_id, "status": status}


def _kpi_request(
    faculty_id: str = "FAC-001",
    kpi_period: str = "Q1",
    overall_score: float = 75.0,
) -> FacultyKpiCreateSchema:
    return FacultyKpiCreateSchema(
        faculty_id=faculty_id,
        name="Teaching Excellence",
        department_id="DEPT-CS",
        kpi_period=kpi_period,
        teaching_score=80.0,
        research_score=70.0,
        service_score=75.0,
        overall_score=overall_score,
        status="satisfactory",
    )


# ---------------------------------------------------------------------------
# Constants smoke tests
# ---------------------------------------------------------------------------

def test_constants_active_contract_statuses():
    assert "active" in _KPI_ACTIVE_CONTRACT_STATUSES


def test_constants_terminated_not_active():
    assert "terminated" not in _KPI_ACTIVE_CONTRACT_STATUSES
    assert "expired" not in _KPI_ACTIVE_CONTRACT_STATUSES
    assert "suspended" not in _KPI_ACTIVE_CONTRACT_STATUSES


# ---------------------------------------------------------------------------
# Guard unit tests — direct _check_ function
# ---------------------------------------------------------------------------

def test_guard_active_contract_passes(monkeypatch):
    """Faculty with active contract → no raise."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda table, tid: [_contract("FAC-001", "active")] if table == "faculty_contracts" else [],
    )
    _check_faculty_has_active_contract_for_kpi(
        tenant_id=TENANT_ID,
        faculty_id="FAC-001",
        kpi_period="Q1",
    )


def test_guard_no_contracts_at_all_blocks(monkeypatch):
    """Faculty with no contract records at all → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    with pytest.raises(DomainValidationError, match="no contract records found"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID,
            faculty_id="FAC-404",
            kpi_period="Q2",
        )


def test_guard_terminated_contract_blocks(monkeypatch):
    """Faculty with only terminated contract → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda table, tid: [_contract("FAC-002", "terminated")] if table == "faculty_contracts" else [],
    )
    with pytest.raises(DomainValidationError, match="no active contract found"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID,
            faculty_id="FAC-002",
            kpi_period="Q3",
        )


def test_guard_expired_contract_blocks(monkeypatch):
    """Faculty with only expired contract → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda table, tid: [_contract("FAC-003", "expired")] if table == "faculty_contracts" else [],
    )
    with pytest.raises(DomainValidationError, match="no active contract found"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID,
            faculty_id="FAC-003",
            kpi_period="annual",
        )


def test_guard_suspended_contract_blocks(monkeypatch):
    """Faculty with only suspended contract → DomainValidationError."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda table, tid: [_contract("FAC-004", "suspended")] if table == "faculty_contracts" else [],
    )
    with pytest.raises(DomainValidationError, match="no active contract found"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID,
            faculty_id="FAC-004",
            kpi_period="semester",
        )


def test_guard_mixed_contracts_one_active_passes(monkeypatch):
    """Faculty with terminated + active contract → allowed (surgical)."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda table, tid: (
            [_contract("FAC-005", "terminated", 1), _contract("FAC-005", "active", 2)]
            if table == "faculty_contracts" else []
        ),
    )
    # Must not raise
    _check_faculty_has_active_contract_for_kpi(
        tenant_id=TENANT_ID,
        faculty_id="FAC-005",
        kpi_period="Q4",
    )


def test_guard_different_faculty_contract_does_not_count(monkeypatch):
    """Active contract for a different faculty_id must NOT satisfy the guard."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda table, tid: [_contract("FAC-OTHER", "active")] if table == "faculty_contracts" else [],
    )
    with pytest.raises(DomainValidationError, match="no contract records found"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID,
            faculty_id="FAC-006",
            kpi_period="Q1",
        )


def test_guard_fail_closed_on_query_error(monkeypatch):
    """If faculty_contracts lookup raises, guard must raise DomainValidationError (fail-closed)."""
    def boom(table, tid):
        raise RuntimeError("DB timeout")

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        boom,
    )
    with pytest.raises(DomainValidationError, match="faculty_contracts lookup failed"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID,
            faculty_id="FAC-007",
            kpi_period="Q1",
        )


# ---------------------------------------------------------------------------
# Integration tests — full create_faculty_kpi pathway
# ---------------------------------------------------------------------------

def test_create_kpi_blocked_when_no_active_contract(monkeypatch):
    """create_faculty_kpi must raise DomainValidationError when faculty has no active contract."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda table, tid: (
            [_contract("FAC-NE", "terminated")] if table == "faculty_contracts" else []
        ),
    )
    with pytest.raises(DomainValidationError, match="FAC-NE"):
        create_faculty_kpi(TENANT_ID, _kpi_request(faculty_id="FAC-NE"), actor="admin")


def test_create_kpi_allowed_when_active_contract_exists(monkeypatch):
    """create_faculty_kpi must succeed when faculty has an active contract."""
    created_rows: list[dict] = []

    def fake_list(table, tid):
        if table == "faculty_contracts":
            return [_contract("FAC-OK", "active")]
        return []

    def fake_create(table, payload, tid):
        row = {"id": 1, "tenant_id": str(tid), **payload}
        created_rows.append(row)
        return row

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", fake_create
    )

    result = create_faculty_kpi(TENANT_ID, _kpi_request(faculty_id="FAC-OK"), actor="admin")
    assert result.faculty_id == "FAC-OK"
    assert created_rows, "create_entity_for_tenant must have been called"


def test_create_kpi_guard_fires_before_persist(monkeypatch):
    """Guard must fire BEFORE create_entity_for_tenant — no record created on block."""
    persisted: list[dict] = []

    def fake_list(table, tid):
        return []  # no contracts

    def fake_create(table, payload, tid):
        persisted.append(payload)
        return {"id": 99, **payload}

    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", fake_list
    )
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", fake_create
    )

    with pytest.raises(DomainValidationError):
        create_faculty_kpi(TENANT_ID, _kpi_request(faculty_id="FAC-NP"), actor="admin")

    assert not persisted, "create_entity_for_tenant must NOT be called when guard blocks"


def test_create_kpi_no_contract_error_message_includes_faculty_id(monkeypatch):
    """Error message must clearly identify the faculty_id that failed the guard."""
    monkeypatch.setattr(
        "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
        lambda table, tid: [],
    )
    with pytest.raises(DomainValidationError, match="FAC-ERR-ID"):
        _check_faculty_has_active_contract_for_kpi(
            tenant_id=TENANT_ID,
            faculty_id="FAC-ERR-ID",
            kpi_period="Q1",
        )
