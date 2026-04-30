"""W142 — budget_planning: DomainValidationError hardening depth tests.

Guard: W113 — budget allocation is blocked when referenced budget plan is not
in 'approved' status (or plan does not exist / lookup fails).
"""
from __future__ import annotations

import inspect
import sys
from unittest.mock import patch

import pytest
from fastapi import HTTPException

import app.modules.budget_planning.service as _svc
import app.modules.budget_planning.router  # noqa: F401

_ROUTER_MOD = sys.modules.get("app.modules.budget_planning.router")


def _plan(plan_id: int = 1, status: str = "approved", tenant_id: str = "1") -> dict:
    return {
        "id": plan_id,
        "department_id": "FIN",
        "fiscal_year": 2026,
        "total_amount": 1000.0,
        "currency": "USD",
        "status": status,
        "tenant_id": tenant_id,
    }


def _tenant(tenant_id: str = "1") -> dict:
    return {"id": tenant_id}


class TestW142Constants:
    def test_approved_plan_status_for_allocation_exists(self):
        assert hasattr(_svc, "_APPROVED_PLAN_STATUS_FOR_ALLOCATION")

    def test_approved_plan_status_contains_approved(self):
        assert "approved" in _svc._APPROVED_PLAN_STATUS_FOR_ALLOCATION

    def test_approved_plan_status_excludes_draft(self):
        assert "draft" not in _svc._APPROVED_PLAN_STATUS_FOR_ALLOCATION

    def test_approved_plan_status_excludes_submitted(self):
        assert "submitted" not in _svc._APPROVED_PLAN_STATUS_FOR_ALLOCATION

    def test_approved_plan_status_excludes_rejected(self):
        assert "rejected" not in _svc._APPROVED_PLAN_STATUS_FOR_ALLOCATION

    def test_approved_plan_status_is_frozenset(self):
        assert isinstance(_svc._APPROVED_PLAN_STATUS_FOR_ALLOCATION, frozenset)

    def test_budget_statuses_exists(self):
        assert hasattr(_svc, "_BUDGET_PLAN_STATUSES")

    def test_allowed_transitions_exists(self):
        assert hasattr(_svc, "_ALLOWED_BUDGET_PLAN_TRANSITIONS")

    def test_approval_uniqueness_statuses_exists(self):
        assert hasattr(_svc, "_APPROVAL_UNIQUENESS_STATUSES")

    def test_overrun_risk_statuses_exists(self):
        assert hasattr(_svc, "_OVERRUN_RISK_STATUSES")

    def test_active_plan_statuses_exists(self):
        assert hasattr(_svc, "_ACTIVE_PLAN_STATUSES")

    def test_budget_status_max_active_exists(self):
        assert hasattr(_svc, "_BUDGET_PLAN_STATUS_MAX_ACTIVE")


class TestW142GuardBlockPaths:
    def _run(self, plans: list[dict], plan_id: int = 1) -> None:
        with patch.object(_svc, "list_entities_for_tenant", return_value=plans):
            _svc._check_budget_plan_approved_for_allocation(tenant_id=1, plan_id=plan_id)

    def test_missing_plan_raises(self):
        with pytest.raises(_svc.DomainValidationError):
            self._run(plans=[], plan_id=1)

    def test_draft_plan_raises(self):
        with pytest.raises(_svc.DomainValidationError):
            self._run(plans=[_plan(status="draft")], plan_id=1)

    def test_submitted_plan_raises(self):
        with pytest.raises(_svc.DomainValidationError):
            self._run(plans=[_plan(status="submitted")], plan_id=1)

    def test_rejected_plan_raises(self):
        with pytest.raises(_svc.DomainValidationError):
            self._run(plans=[_plan(status="rejected")], plan_id=1)

    def test_wrong_plan_id_raises(self):
        with pytest.raises(_svc.DomainValidationError):
            self._run(plans=[_plan(plan_id=99, status="approved")], plan_id=1)

    def test_error_mentions_plan_id(self):
        with pytest.raises(_svc.DomainValidationError) as exc_info:
            self._run(plans=[], plan_id=42)
        assert "plan_id=42" in str(exc_info.value)


class TestW142GuardAllowPaths:
    def _run(self, plans: list[dict], plan_id: int = 1) -> None:
        with patch.object(_svc, "list_entities_for_tenant", return_value=plans):
            _svc._check_budget_plan_approved_for_allocation(tenant_id=1, plan_id=plan_id)

    def test_approved_plan_allows(self):
        self._run(plans=[_plan(status="approved")], plan_id=1)

    def test_approved_plan_case_insensitive_status_allows(self):
        self._run(plans=[_plan(status="APPROVED")], plan_id=1)

    def test_multiple_plans_one_approved_allows(self):
        plans = [_plan(plan_id=1, status="draft"), _plan(plan_id=2, status="approved")]
        self._run(plans=plans, plan_id=2)


class TestW142FailClosed:
    def test_lookup_exception_raises_domain_validation_error(self):
        def boom(*_args, **_kwargs):
            raise RuntimeError("db down")

        with patch.object(_svc, "list_entities_for_tenant", side_effect=boom):
            with pytest.raises(_svc.DomainValidationError):
                _svc._check_budget_plan_approved_for_allocation(tenant_id=1, plan_id=1)

    def test_lookup_exception_cause_preserved(self):
        original = RuntimeError("timeout")

        def boom(*_args, **_kwargs):
            raise original

        with patch.object(_svc, "list_entities_for_tenant", side_effect=boom):
            with pytest.raises(_svc.DomainValidationError) as exc_info:
                _svc._check_budget_plan_approved_for_allocation(tenant_id=1, plan_id=1)
        assert exc_info.value.__cause__ is original

    def test_lookup_exception_mentions_plan_id(self):
        def boom(*_args, **_kwargs):
            raise RuntimeError("connection refused")

        with patch.object(_svc, "list_entities_for_tenant", side_effect=boom):
            with pytest.raises(_svc.DomainValidationError) as exc_info:
                _svc._check_budget_plan_approved_for_allocation(tenant_id=1, plan_id=123)
        assert "plan_id=123" in str(exc_info.value)


class TestW142CreateAllocationWiring:
    def _payload(self, plan_id: int = 1) -> dict[str, object]:
        return {
            "plan_id": plan_id,
            "category": "infra",
            "allocated_amount": 200.0,
            "spent_amount": 0.0,
            "currency": "USD",
            "notes": None,
        }

    def test_plan_id_must_be_positive(self):
        with pytest.raises(ValueError):
            _svc.create_budget_allocation(self._payload(plan_id=0), tenant_id=1)

    def test_nonapproved_plan_blocks_create(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[_plan(status="draft")]):
            with pytest.raises(_svc.DomainValidationError):
                _svc.create_budget_allocation(self._payload(plan_id=1), tenant_id=1)

    def test_missing_plan_blocks_create(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(_svc.DomainValidationError):
                _svc.create_budget_allocation(self._payload(plan_id=1), tenant_id=1)

    def test_approved_plan_allows_create(self):
        created = {
            "id": 7,
            "plan_id": 1,
            "category": "infra",
            "allocated_amount": 200.0,
            "spent_amount": 0.0,
            "currency": "USD",
            "notes": None,
            "tenant_id": "1",
        }

        def _list(entity_type, tenant_id):
            if entity_type == "budget_plans":
                return [_plan(status="approved")]
            if entity_type == "budget_allocations":
                return []
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list), \
             patch.object(_svc, "create_entity_for_tenant", return_value=created), \
             patch.object(_svc.EventPublisher, "publish_event"):
            result = _svc.create_budget_allocation(self._payload(plan_id=1), tenant_id=1)
        assert int(result["id"]) == 7

    def test_over_allocation_raises(self):
        def _list(entity_type, tenant_id):
            if entity_type == "budget_plans":
                return [{**_plan(status="approved"), "total_amount": 100.0}]
            if entity_type == "budget_allocations":
                return [{"plan_id": 1, "allocated_amount": 90.0}]
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(ValueError):
                _svc.create_budget_allocation(self._payload(plan_id=1), tenant_id=1)


class TestW142RouterStructure:
    def test_router_has_routes(self):
        assert _ROUTER_MOD is not None
        assert len(_ROUTER_MOD.router.routes) > 0

    def test_routes_exist(self):
        assert _ROUTER_MOD is not None
        paths = [r.path for r in _ROUTER_MOD.router.routes]
        assert "/api/admin/budget-planning/plans" in paths
        assert "/api/admin/budget-planning/allocations" in paths
        assert "/api/admin/budget-planning/plans/{plan_id}/status" in paths

    def test_router_imports_domain_validation_error(self):
        assert _ROUTER_MOD is not None
        src = inspect.getsource(_ROUTER_MOD)
        assert "DomainValidationError" in src

    def test_router_uses_svc_pattern(self):
        assert _ROUTER_MOD is not None
        src = inspect.getsource(_ROUTER_MOD)
        assert "_svc." in src

    def test_create_plan_catches_domain_validation_error(self):
        assert _ROUTER_MOD is not None
        src = inspect.getsource(_ROUTER_MOD)
        assert "except (ValueError, DomainValidationError)" in src


class TestW142RouterPostAllocationEndpoint:
    def _endpoint(self):
        assert _ROUTER_MOD is not None
        return _ROUTER_MOD.create_budget_allocation_endpoint

    def _payload(self):
        from app.modules.budget_planning.schemas import BudgetAllocationCreatePayload
        return BudgetAllocationCreatePayload(
            plan_id=1,
            category="infra",
            allocated_amount=200.0,
            spent_amount=0.0,
            currency="USD",
            notes=None,
        )

    def test_domain_validation_error_returns_422(self):
        ep = self._endpoint()
        with patch.object(_svc, "create_budget_allocation", side_effect=_svc.DomainValidationError("blocked")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._payload(), _="actor", __=None, tenant=_tenant())
        assert exc_info.value.status_code == 422

    def test_value_error_returns_422(self):
        ep = self._endpoint()
        with patch.object(_svc, "create_budget_allocation", side_effect=ValueError("bad payload")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._payload(), _="actor", __=None, tenant=_tenant())
        assert exc_info.value.status_code == 422

    def test_success_returns_item(self):
        ep = self._endpoint()
        record = {
            "id": 7,
            "plan_id": 1,
            "category": "infra",
            "allocated_amount": 200.0,
            "spent_amount": 0.0,
            "currency": "USD",
            "notes": None,
            "tenant_id": "1",
        }
        with patch.object(_svc, "create_budget_allocation", return_value=record):
            resp = ep(payload=self._payload(), _="actor", __=None, tenant=_tenant())
        assert int(resp.record.id) == 7


class TestW142RouterPatchPlanStatusEndpoint:
    def _endpoint(self):
        assert _ROUTER_MOD is not None
        return _ROUTER_MOD.update_budget_plan_status_endpoint

    def _payload(self, status: str = "submitted"):
        from app.modules.budget_planning.schemas import BudgetPlanStatusUpdatePayload
        return BudgetPlanStatusUpdatePayload(status=status)

    def test_domain_validation_error_returns_422(self):
        ep = self._endpoint()
        with patch.object(_svc, "update_budget_plan_status", side_effect=_svc.DomainValidationError("duplicate approved")):
            with pytest.raises(HTTPException) as exc_info:
                ep(plan_id=1, payload=self._payload("approved"), _="actor", __=None, tenant=_tenant())
        assert exc_info.value.status_code == 422

    def test_value_error_returns_422(self):
        ep = self._endpoint()
        with patch.object(_svc, "update_budget_plan_status", side_effect=ValueError("invalid transition")):
            with pytest.raises(HTTPException) as exc_info:
                ep(plan_id=1, payload=self._payload("approved"), _="actor", __=None, tenant=_tenant())
        assert exc_info.value.status_code == 422

    def test_not_found_returns_404(self):
        ep = self._endpoint()
        with patch.object(_svc, "update_budget_plan_status", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                ep(plan_id=999, payload=self._payload("approved"), _="actor", __=None, tenant=_tenant())
        assert exc_info.value.status_code == 404

    def test_success_returns_item(self):
        ep = self._endpoint()
        record = {
            "id": 1,
            "department_id": "FIN",
            "fiscal_year": 2026,
            "total_amount": 1000.0,
            "currency": "USD",
            "status": "submitted",
            "tenant_id": "1",
        }
        with patch.object(_svc, "update_budget_plan_status", return_value=record):
            resp = ep(plan_id=1, payload=self._payload("submitted"), _="actor", __=None, tenant=_tenant())
        assert resp.record.status == "submitted"


class TestW142RouterPostPlanEndpoint:
    def _endpoint(self):
        assert _ROUTER_MOD is not None
        return _ROUTER_MOD.create_budget_plan_endpoint

    def _payload(self):
        from app.modules.budget_planning.schemas import BudgetPlanCreatePayload
        return BudgetPlanCreatePayload(
            department_id="FIN",
            fiscal_year=2026,
            total_amount=1000.0,
            currency="USD",
            status="draft",
            description=None,
            notes_internal=None,
        )

    def test_domain_validation_error_returns_422(self):
        ep = self._endpoint()
        with patch.object(_svc, "create_budget_plan", side_effect=_svc.DomainValidationError("invariant failed")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._payload(), _="actor", __=None, tenant=_tenant())
        assert exc_info.value.status_code == 422

    def test_value_error_returns_422(self):
        ep = self._endpoint()
        with patch.object(_svc, "create_budget_plan", side_effect=ValueError("must be draft")):
            with pytest.raises(HTTPException) as exc_info:
                ep(payload=self._payload(), _="actor", __=None, tenant=_tenant())
        assert exc_info.value.status_code == 422

    def test_success_returns_record(self):
        ep = self._endpoint()
        record = {
            "id": 1,
            "department_id": "FIN",
            "fiscal_year": 2026,
            "total_amount": 1000.0,
            "currency": "USD",
            "status": "draft",
            "description": None,
            "notes_internal": None,
            "tenant_id": "1",
        }
        with patch.object(_svc, "create_budget_plan", return_value=record):
            resp = ep(payload=self._payload(), _="actor", __=None, tenant=_tenant())
        assert resp.record.id == 1


class TestW142ListAndContextEndpoints:
    def test_list_plans_uses_tenant_id(self):
        ep = _ROUTER_MOD.list_budget_plans_endpoint
        with patch.object(_svc, "list_budget_plans", return_value=[]) as mocked:
            ep(_="actor", __=None, tenant=_tenant("17"), department_id=None, fiscal_year=None)
        mocked.assert_called_once_with(17, department_id=None, fiscal_year=None)

    def test_list_allocations_uses_tenant_id(self):
        ep = _ROUTER_MOD.list_budget_allocations_endpoint
        with patch.object(_svc, "list_budget_allocations", return_value=[]) as mocked:
            ep(_="actor", __=None, tenant=_tenant("17"), plan_id=None)
        mocked.assert_called_once_with(17, plan_id=None)

    def test_brain_context_uses_tenant_id(self):
        ep = _ROUTER_MOD.get_budget_brain_context_endpoint
        with patch.object(_svc, "get_budget_brain_context", return_value={"module": "budget_planning"}) as mocked:
            resp = ep(_="actor", __=None, tenant=_tenant("17"))
        mocked.assert_called_once_with(17)
        assert resp["module"] == "budget_planning"
