"""W113 — Budget Planning × Budget Plans cross-entity guard.

Business invariant: A budget allocation may ONLY be created when the
referenced budget plan is in 'approved' status. Allocating funds against
draft, submitted, or rejected plans creates unauthorized financial commitments
without proper organizational sign-off.

Guard: _check_budget_plan_approved_for_allocation() — BEFORE create_entity_for_tenant()
Fail-closed: if budget_plan lookup raises any exception → DomainValidationError.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError

PLAN_ID = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plan(plan_id: int, status: str, dept: str = "FINANCE", year: int = 2026) -> dict:
    return {
        "id": plan_id,
        "department_id": dept,
        "fiscal_year": year,
        "total_amount": 500_000.0,
        "currency": "USD",
        "status": status,
    }


def _make_allocation_payload(
    plan_id: int = PLAN_ID,
    category: str = "equipment",
    allocated_amount: float = 10_000.0,
) -> dict:
    return {
        "plan_id": plan_id,
        "category": category,
        "allocated_amount": allocated_amount,
        "spent_amount": 0.0,
        "currency": "USD",
        "notes": None,
    }


def _fake_create_entity(entity_type, data, tenant_id):
    return {"id": 99, **data}


# ===========================================================================
# GROUP 1 — Guard constant correctness
# ===========================================================================

class TestApprovedPlanConstant:
    def test_constant_exists(self):
        import app.modules.budget_planning.service as svc
        assert hasattr(svc, "_APPROVED_PLAN_STATUS_FOR_ALLOCATION")

    def test_constant_is_frozenset(self):
        import app.modules.budget_planning.service as svc
        assert isinstance(svc._APPROVED_PLAN_STATUS_FOR_ALLOCATION, frozenset)

    def test_approved_in_constant(self):
        import app.modules.budget_planning.service as svc
        assert "approved" in svc._APPROVED_PLAN_STATUS_FOR_ALLOCATION

    def test_draft_not_in_constant(self):
        import app.modules.budget_planning.service as svc
        assert "draft" not in svc._APPROVED_PLAN_STATUS_FOR_ALLOCATION

    def test_submitted_not_in_constant(self):
        import app.modules.budget_planning.service as svc
        assert "submitted" not in svc._APPROVED_PLAN_STATUS_FOR_ALLOCATION

    def test_rejected_not_in_constant(self):
        import app.modules.budget_planning.service as svc
        assert "rejected" not in svc._APPROVED_PLAN_STATUS_FOR_ALLOCATION

    def test_constant_has_exactly_one_status(self):
        import app.modules.budget_planning.service as svc
        # Only 'approved' should be valid for allocation
        assert len(svc._APPROVED_PLAN_STATUS_FOR_ALLOCATION) == 1


# ===========================================================================
# GROUP 2 — Guard function exists and is wired BEFORE persist
# ===========================================================================

class TestGuardFunctionExists:
    def test_guard_function_exists(self):
        import app.modules.budget_planning.service as svc
        assert hasattr(svc, "_check_budget_plan_approved_for_allocation")

    def test_guard_function_is_callable(self):
        import app.modules.budget_planning.service as svc
        assert callable(svc._check_budget_plan_approved_for_allocation)

    def test_guard_fires_before_persist(self):
        """Guard must be invoked before create_entity_for_tenant."""
        import app.modules.budget_planning.service as svc_mod
        call_order: list[str] = []

        def fake_guard(*, tenant_id, plan_id):
            call_order.append("guard")

        def fake_create(entity_type, data, tenant_id):
            call_order.append("persist")
            return {"id": 1, **data}

        def fake_list(entity_type, tenant_id):
            if entity_type == "budget_plans":
                return [_make_plan(PLAN_ID, "approved")]
            return []

        with (
            patch.object(svc_mod, "_check_budget_plan_approved_for_allocation", fake_guard),
            patch("app.modules.budget_planning.service.create_entity_for_tenant", side_effect=fake_create),
            patch("app.modules.budget_planning.service.list_entities_for_tenant", side_effect=fake_list),
        ):
            svc_mod.create_budget_allocation(_make_allocation_payload(), 1)

        assert call_order[0] == "guard", f"Guard must fire first; got: {call_order}"
        assert "persist" in call_order


# ===========================================================================
# GROUP 3 — Guard blocks: plan not found
# ===========================================================================

class TestGuardBlocksPlanNotFound:
    def _run_guard(self, plans: list[dict], plan_id: int = PLAN_ID):
        import app.modules.budget_planning.service as svc_mod
        with patch(
            "app.modules.budget_planning.service.list_entities_for_tenant",
            return_value=plans,
        ):
            svc_mod._check_budget_plan_approved_for_allocation(
                tenant_id=1,
                plan_id=plan_id,
            )

    def test_no_plans_blocked(self):
        with pytest.raises(DomainValidationError):
            self._run_guard([])

    def test_different_plan_id_blocked(self):
        plans = [_make_plan(999, "approved")]
        with pytest.raises(DomainValidationError):
            self._run_guard(plans, plan_id=PLAN_ID)

    def test_error_contains_plan_id(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard([])
        assert str(PLAN_ID) in str(exc_info.value)

    def test_error_mentions_not_found(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard([])
        msg = str(exc_info.value).lower()
        assert "not found" in msg or "non-existent" in msg


# ===========================================================================
# GROUP 4 — Guard blocks: plan exists but wrong status
# ===========================================================================

class TestGuardBlocksWrongStatus:
    def _run_guard(self, status: str):
        import app.modules.budget_planning.service as svc_mod
        plans = [_make_plan(PLAN_ID, status)]
        with patch(
            "app.modules.budget_planning.service.list_entities_for_tenant",
            return_value=plans,
        ):
            svc_mod._check_budget_plan_approved_for_allocation(
                tenant_id=1,
                plan_id=PLAN_ID,
            )

    def test_draft_plan_blocked(self):
        with pytest.raises(DomainValidationError):
            self._run_guard("draft")

    def test_submitted_plan_blocked(self):
        with pytest.raises(DomainValidationError):
            self._run_guard("submitted")

    def test_rejected_plan_blocked(self):
        with pytest.raises(DomainValidationError):
            self._run_guard("rejected")

    def test_error_contains_plan_status(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard("draft")
        assert "draft" in str(exc_info.value)

    def test_error_mentions_approved_requirement(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard("submitted")
        assert "approved" in str(exc_info.value).lower()

    def test_error_mentions_unauthorized_or_commitment(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard("rejected")
        msg = str(exc_info.value).lower()
        assert "reject" in msg or "unauthorized" in msg or "commit" in msg


# ===========================================================================
# GROUP 5 — Guard allows: approved plan
# ===========================================================================

class TestGuardAllows:
    def _run_guard(self, plans: list[dict]):
        import app.modules.budget_planning.service as svc_mod
        with patch(
            "app.modules.budget_planning.service.list_entities_for_tenant",
            return_value=plans,
        ):
            svc_mod._check_budget_plan_approved_for_allocation(
                tenant_id=1,
                plan_id=PLAN_ID,
            )

    def test_approved_plan_allowed(self):
        plans = [_make_plan(PLAN_ID, "approved")]
        self._run_guard(plans)  # must not raise

    def test_approved_plan_among_others_allowed(self):
        """Guard finds the correct plan by plan_id, even among other plans."""
        plans = [
            _make_plan(1, "draft"),
            _make_plan(PLAN_ID, "approved"),
            _make_plan(100, "rejected"),
        ]
        self._run_guard(plans)

    def test_only_target_plan_status_matters(self):
        """Other plans' statuses do NOT affect the guard result."""
        plans = [
            _make_plan(1, "rejected"),
            _make_plan(2, "draft"),
            _make_plan(PLAN_ID, "approved"),
        ]
        self._run_guard(plans)

    def test_approved_plan_different_tenant_does_not_help(self):
        """Guard queries tenant-specific data; another tenant's approved plan is irrelevant."""
        import app.modules.budget_planning.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if tenant_id == 2:
                return [_make_plan(PLAN_ID, "approved")]
            return []

        with patch(
            "app.modules.budget_planning.service.list_entities_for_tenant",
            side_effect=fake_list,
        ):
            with pytest.raises(DomainValidationError):
                svc_mod._check_budget_plan_approved_for_allocation(
                    tenant_id=1,
                    plan_id=PLAN_ID,
                )


# ===========================================================================
# GROUP 6 — Fail-closed: lookup exception → DomainValidationError
# ===========================================================================

class TestFailClosed:
    def test_lookup_exception_raises_domain_error(self):
        import app.modules.budget_planning.service as svc_mod
        with patch(
            "app.modules.budget_planning.service.list_entities_for_tenant",
            side_effect=RuntimeError("DB connection refused"),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                svc_mod._check_budget_plan_approved_for_allocation(
                    tenant_id=1,
                    plan_id=PLAN_ID,
                )
        msg = str(exc_info.value).lower()
        assert "lookup failed" in msg or "cannot commit" in msg or "verif" in msg

    def test_timeout_exception_fail_closed(self):
        import app.modules.budget_planning.service as svc_mod
        with patch(
            "app.modules.budget_planning.service.list_entities_for_tenant",
            side_effect=TimeoutError("plan lookup timed out"),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod._check_budget_plan_approved_for_allocation(
                    tenant_id=1,
                    plan_id=PLAN_ID,
                )

    def test_lookup_failure_blocks_persist(self):
        """On lookup failure, create_entity_for_tenant must NOT be called."""
        import app.modules.budget_planning.service as svc_mod
        persisted: list = []

        def fake_list(entity_type, tenant_id):
            if entity_type == "budget_plans":
                raise RuntimeError("network error")
            return []

        def fake_create(entity_type, data, tenant_id):
            persisted.append(data)
            return {"id": 1, **data}

        with (
            patch("app.modules.budget_planning.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.budget_planning.service.create_entity_for_tenant", side_effect=fake_create),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_budget_allocation(_make_allocation_payload(), 1)

        assert persisted == [], "create_entity_for_tenant must NOT be called when guard raises"


# ===========================================================================
# GROUP 7 — Integration: create_budget_allocation end-to-end
# ===========================================================================

class TestCreateBudgetAllocationIntegration:
    def test_creation_allowed_with_approved_plan(self):
        import app.modules.budget_planning.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "budget_plans":
                return [_make_plan(PLAN_ID, "approved")]
            return []  # no existing allocations

        with (
            patch("app.modules.budget_planning.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.budget_planning.service.create_entity_for_tenant", side_effect=_fake_create_entity),
        ):
            result = svc_mod.create_budget_allocation(_make_allocation_payload(), 1)

        assert result["id"] == 99
        assert result["plan_id"] == PLAN_ID

    def test_creation_blocked_draft_plan(self):
        import app.modules.budget_planning.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "budget_plans":
                return [_make_plan(PLAN_ID, "draft")]
            return []

        with patch("app.modules.budget_planning.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_budget_allocation(_make_allocation_payload(), 1)

    def test_creation_blocked_submitted_plan(self):
        import app.modules.budget_planning.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "budget_plans":
                return [_make_plan(PLAN_ID, "submitted")]
            return []

        with patch("app.modules.budget_planning.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_budget_allocation(_make_allocation_payload(), 1)

    def test_creation_blocked_rejected_plan(self):
        import app.modules.budget_planning.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "budget_plans":
                return [_make_plan(PLAN_ID, "rejected")]
            return []

        with patch("app.modules.budget_planning.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_budget_allocation(_make_allocation_payload(), 1)

    def test_creation_blocked_missing_plan(self):
        import app.modules.budget_planning.service as svc_mod

        with patch(
            "app.modules.budget_planning.service.list_entities_for_tenant",
            return_value=[],
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_budget_allocation(_make_allocation_payload(), 1)

    def test_error_is_domain_validation_not_value_error(self):
        import app.modules.budget_planning.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "budget_plans":
                return [_make_plan(PLAN_ID, "draft")]
            return []

        with patch("app.modules.budget_planning.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_budget_allocation(_make_allocation_payload(), 1)

    def test_amount_cap_still_enforced_after_guard_passes(self):
        """After guard passes, existing over-budget check must still fire."""
        import app.modules.budget_planning.service as svc_mod

        # existing allocations already use up the full plan total
        existing_allocations = [
            {
                "id": i,
                "plan_id": PLAN_ID,
                "allocated_amount": 100_000.0,
                "spent_amount": 0.0,
                "category": "equipment",
                "currency": "USD",
            }
            for i in range(1, 6)  # 5 × 100k = 500k = entire plan budget
        ]

        def fake_list(entity_type, tenant_id):
            if entity_type == "budget_plans":
                return [_make_plan(PLAN_ID, "approved")]
            return existing_allocations

        with patch("app.modules.budget_planning.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(ValueError, match="Allocation exceeds"):
                svc_mod.create_budget_allocation(_make_allocation_payload(allocated_amount=1.0), 1)

    def test_all_categories_blocked_without_approved_plan(self):
        """Guard applies regardless of allocation category."""
        import app.modules.budget_planning.service as svc_mod

        for category in ("travel", "software", "equipment", "general", "staffing"):
            payload = _make_allocation_payload(category=category)
            with patch(
                "app.modules.budget_planning.service.list_entities_for_tenant",
                return_value=[_make_plan(PLAN_ID, "draft")],
            ):
                with pytest.raises(DomainValidationError):
                    svc_mod.create_budget_allocation(payload, 1)

    def test_tenant_isolation(self):
        """Guard only looks at budget_plans for the correct tenant_id."""
        import app.modules.budget_planning.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "budget_plans" and tenant_id == 2:
                return [_make_plan(PLAN_ID, "approved")]
            return []

        # tenant 1 has no approved plan — must be blocked
        with patch("app.modules.budget_planning.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_budget_allocation(_make_allocation_payload(), 1)

    def test_record_persisted_with_correct_plan_id(self):
        """After guard passes, allocation is persisted with correct plan_id."""
        import app.modules.budget_planning.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "budget_plans":
                return [_make_plan(PLAN_ID, "approved")]
            return []

        with (
            patch("app.modules.budget_planning.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.budget_planning.service.create_entity_for_tenant", side_effect=_fake_create_entity),
        ):
            result = svc_mod.create_budget_allocation(_make_allocation_payload(plan_id=PLAN_ID), 1)

        assert result["plan_id"] == PLAN_ID
        assert result["id"] == 99

    def test_invalid_plan_id_raises_value_error(self):
        """plan_id=0 raises ValueError before guard even fires."""
        import app.modules.budget_planning.service as svc_mod

        with pytest.raises(ValueError, match="plan_id"):
            svc_mod.create_budget_allocation({"plan_id": 0, "allocated_amount": 100.0}, 1)
