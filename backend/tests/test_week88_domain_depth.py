"""W88 — budget_planning: Duplicate Approved Plan Guard (uniqueness per dept + fiscal_year).

Tests verify:
1. Guard function is importable and callable
2. Constant _APPROVAL_UNIQUENESS_STATUSES exists and contains 'approved'
3. Blocked when another approved plan exists for same (department_id, fiscal_year)
4. Allowed when no other approved plan for the same dept/fiscal_year
5. Allowed when another approved plan exists for DIFFERENT fiscal_year (surgical)
6. Allowed when another approved plan exists for DIFFERENT department (surgical)
7. Error message names plan_id, department, fiscal_year, and conflict reason
8. Blocked when query fails (NO SILENT FALLBACK — HARDENING)
9. Allowed when department_id is empty/None (guard skips — no dept = no constraint)
"""
from __future__ import annotations

import pytest
from unittest.mock import patch


def _make_plan(
    id_: int,
    status: str,
    department_id: str = "engineering",
    fiscal_year: int = 2026,
) -> dict:
    return {
        "id": id_,
        "status": status,
        "department_id": department_id,
        "fiscal_year": fiscal_year,
        "total_amount": 100000.0,
    }


# ── 1. Guard function exists and is callable ────────────────────────────────
def test_w88_guard_function_exists_and_callable():
    from app.modules.budget_planning.service import _check_no_duplicate_approved_plan
    assert callable(_check_no_duplicate_approved_plan)


# ── 2. Constant _APPROVAL_UNIQUENESS_STATUSES has 'approved' ────────────────
def test_w88_approval_uniqueness_statuses_constant_exists():
    from app.modules.budget_planning.service import _APPROVAL_UNIQUENESS_STATUSES
    assert isinstance(_APPROVAL_UNIQUENESS_STATUSES, frozenset), (
        "_APPROVAL_UNIQUENESS_STATUSES must be a frozenset"
    )
    assert "approved" in _APPROVAL_UNIQUENESS_STATUSES


# ── 3. Blocked: duplicate approved plan for same (dept, fiscal_year) ─────────
def test_w88_blocked_when_duplicate_approved_plan_same_dept_and_year():
    from app.modules.budget_planning.service import _check_no_duplicate_approved_plan
    from app.core.module_helpers.service_validation import DomainValidationError

    # plan_id=99 being approved; plan_id=42 already approved for same dept+year
    existing = [
        _make_plan(42, "approved", department_id="engineering", fiscal_year=2026),
        _make_plan(99, "submitted", department_id="engineering", fiscal_year=2026),
    ]
    with patch(
        "app.modules.budget_planning.service.list_entities_for_tenant",
        return_value=existing,
    ):
        with pytest.raises(DomainValidationError, match="already has an approved budget plan"):
            _check_no_duplicate_approved_plan(
                tenant_id=1,
                plan_id=99,
                department_id="engineering",
                fiscal_year=2026,
            )


# ── 4. Allowed: no other approved plan for the dept/year ─────────────────────
def test_w88_allowed_when_no_conflicting_approved_plan():
    from app.modules.budget_planning.service import _check_no_duplicate_approved_plan

    existing = [
        _make_plan(99, "submitted", department_id="engineering", fiscal_year=2026),
    ]
    with patch(
        "app.modules.budget_planning.service.list_entities_for_tenant",
        return_value=existing,
    ):
        # Should not raise
        _check_no_duplicate_approved_plan(
            tenant_id=1,
            plan_id=99,
            department_id="engineering",
            fiscal_year=2026,
        )


# ── 5. Allowed: approved plan exists for DIFFERENT fiscal_year (surgical) ────
def test_w88_allowed_when_approved_plan_different_fiscal_year():
    from app.modules.budget_planning.service import _check_no_duplicate_approved_plan

    # plan_id=42 approved for 2025 — not a conflict for 2026
    existing = [
        _make_plan(42, "approved", department_id="engineering", fiscal_year=2025),
        _make_plan(99, "submitted", department_id="engineering", fiscal_year=2026),
    ]
    with patch(
        "app.modules.budget_planning.service.list_entities_for_tenant",
        return_value=existing,
    ):
        _check_no_duplicate_approved_plan(
            tenant_id=1,
            plan_id=99,
            department_id="engineering",
            fiscal_year=2026,
        )


# ── 6. Allowed: approved plan exists for DIFFERENT department (surgical) ─────
def test_w88_allowed_when_approved_plan_different_department():
    from app.modules.budget_planning.service import _check_no_duplicate_approved_plan

    # plan_id=42 approved for "finance" — not a conflict for "engineering"
    existing = [
        _make_plan(42, "approved", department_id="finance", fiscal_year=2026),
        _make_plan(99, "submitted", department_id="engineering", fiscal_year=2026),
    ]
    with patch(
        "app.modules.budget_planning.service.list_entities_for_tenant",
        return_value=existing,
    ):
        _check_no_duplicate_approved_plan(
            tenant_id=1,
            plan_id=99,
            department_id="engineering",
            fiscal_year=2026,
        )


# ── 7. Error message contains plan_id, dept, fiscal_year, conflict reason ────
def test_w88_error_message_contains_dept_fiscal_year_and_conflict():
    from app.modules.budget_planning.service import _check_no_duplicate_approved_plan
    from app.core.module_helpers.service_validation import DomainValidationError

    existing = [
        _make_plan(42, "approved", department_id="engineering", fiscal_year=2026),
        _make_plan(99, "submitted", department_id="engineering", fiscal_year=2026),
    ]
    with patch(
        "app.modules.budget_planning.service.list_entities_for_tenant",
        return_value=existing,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_no_duplicate_approved_plan(
                tenant_id=1,
                plan_id=99,
                department_id="engineering",
                fiscal_year=2026,
            )
        msg = str(exc_info.value)
        assert "99" in msg, "Error must name the plan being approved"
        assert "engineering" in msg, "Error must name the department"
        assert "2026" in msg, "Error must name the fiscal_year"
        assert "cost center" in msg.lower() or "conflicting" in msg.lower() or "ambiguous" in msg.lower(), (
            "Error must explain the business rationale"
        )


# ── 8. NO SILENT FALLBACK: query error → DomainValidationError ──────────────
def test_w88_no_silent_fallback_when_query_fails():
    from app.modules.budget_planning.service import _check_no_duplicate_approved_plan
    from app.core.module_helpers.service_validation import DomainValidationError

    with patch(
        "app.modules.budget_planning.service.list_entities_for_tenant",
        side_effect=RuntimeError("DB connection lost"),
    ):
        with pytest.raises(DomainValidationError, match="query failed"):
            _check_no_duplicate_approved_plan(
                tenant_id=1,
                plan_id=99,
                department_id="engineering",
                fiscal_year=2026,
            )


# ── 9. Allowed: department_id is empty — guard skips (no dept = no constraint) ──
def test_w88_guard_skips_when_department_id_is_empty():
    from app.modules.budget_planning.service import _check_no_duplicate_approved_plan

    # Even with another "approved" plan with empty dept, no conflict raised
    existing = [
        _make_plan(42, "approved", department_id="", fiscal_year=2026),
        _make_plan(99, "submitted", department_id="", fiscal_year=2026),
    ]
    with patch(
        "app.modules.budget_planning.service.list_entities_for_tenant",
        return_value=existing,
    ):
        # dept_str is "" → guard skips (no dept set on the record being approved)
        _check_no_duplicate_approved_plan(
            tenant_id=1,
            plan_id=99,
            department_id="",  # empty — no constraint
            fiscal_year=2026,
        )
