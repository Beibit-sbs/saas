"""W145: expense_controls Router DomainValidationError Hardening.

W116 Guard: Cost center must be active for expense record creation.
Category cap guard: Per-category active expense count limits.
Budget limit guard: Total expenses cannot exceed cost center budget.

Tests validate:
- Constants existence and content
- Guard allow paths (valid data)
- Guard block paths (guard violations)
- Fail-closed paths (exception preservation)
- Tenant isolation
- Router structure (_svc pattern)
- HTTP status mappings (422 for domain errors)
"""
import pytest

import app.modules.expense_controls.service as _svc
from app.core.module_helpers.service_validation import DomainValidationError


class TestW145Constants:
    """Verify guard constants are defined and contain expected values."""

    def test_cost_center_required_active_exists(self):
        assert hasattr(_svc, "_COST_CENTER_REQUIRED_ACTIVE")
        assert _svc._COST_CENTER_REQUIRED_ACTIVE is True

    def test_expense_category_max_active_exists(self):
        assert hasattr(_svc, "_EXPENSE_CATEGORY_MAX_ACTIVE")
        assert isinstance(_svc._EXPENSE_CATEGORY_MAX_ACTIVE, dict)
        assert _svc._EXPENSE_CATEGORY_MAX_ACTIVE.get("travel") == 3
        assert _svc._EXPENSE_CATEGORY_MAX_ACTIVE.get("software") == 5
        assert _svc._EXPENSE_CATEGORY_MAX_ACTIVE.get("equipment") == 2
        assert _svc._EXPENSE_CATEGORY_MAX_ACTIVE.get("general") == 10

    def test_active_statuses_ec_exists(self):
        assert hasattr(_svc, "_ACTIVE_STATUSES_EC")
        assert isinstance(_svc._ACTIVE_STATUSES_EC, frozenset)
        assert "pending" in _svc._ACTIVE_STATUSES_EC
        assert "in_review" in _svc._ACTIVE_STATUSES_EC

    def test_budget_risk_statuses_exists(self):
        assert hasattr(_svc, "_BUDGET_RISK_STATUSES")
        assert isinstance(_svc._BUDGET_RISK_STATUSES, frozenset)
        assert "pending" in _svc._BUDGET_RISK_STATUSES
        assert "approved" in _svc._BUDGET_RISK_STATUSES


class TestW116CostCenterGuard:
    """W116: Cost center must be active for expense record creation."""

    def test_guard_function_exists(self):
        assert hasattr(_svc, "_check_cost_center_is_active")
        assert callable(_svc._check_cost_center_is_active)

    def test_guard_passes_active_cost_center(self, monkeypatch):
        """Guard passes when cost center exists and is active."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [{"id": 1, "name": "CC-001", "active": True}] if entity == "cost_centers" else []
        )

        # Should not raise
        _svc._check_cost_center_is_active(tenant_id=1, cost_center_id=1)

    def test_guard_blocks_inactive_cost_center(self, monkeypatch):
        """Guard blocks expense when cost center is not active."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [{"id": 1, "name": "CC-001", "active": False}] if entity == "cost_centers" else []
        )

        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_cost_center_is_active(tenant_id=1, cost_center_id=1)

        assert "not active" in str(exc_info.value).lower()
        assert "CC-001" in str(exc_info.value)

    def test_guard_blocks_missing_cost_center(self, monkeypatch):
        """Guard blocks when cost center doesn't exist."""
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: [] if entity == "cost_centers" else []
        )

        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_cost_center_is_active(tenant_id=1, cost_center_id=999)

        assert "not found" in str(exc_info.value).lower()

    def test_guard_handles_active_variations(self, monkeypatch):
        """Guard correctly interprets various active field values."""
        def mock_list_with_active(entity, tid, active_val):
            if entity == "cost_centers":
                return [{"id": 1, "name": "CC", "active": active_val}]
            return []

        # Test: active=True passes
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: mock_list_with_active(entity, tid, True)
        )
        _svc._check_cost_center_is_active(tenant_id=1, cost_center_id=1)

        # Test: active=1 passes
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: mock_list_with_active(entity, tid, 1)
        )
        _svc._check_cost_center_is_active(tenant_id=1, cost_center_id=1)

        # Test: active="active" passes
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: mock_list_with_active(entity, tid, "active")
        )
        _svc._check_cost_center_is_active(tenant_id=1, cost_center_id=1)

        # Test: active="frozen" fails
        monkeypatch.setattr(
            _svc,
            "list_entities_for_tenant",
            lambda entity, tid: mock_list_with_active(entity, tid, "frozen")
        )
        with pytest.raises(DomainValidationError):
            _svc._check_cost_center_is_active(tenant_id=1, cost_center_id=1)

    def test_guard_fail_closed_on_lookup_exception(self, monkeypatch):
        """Guard raises DomainValidationError with __cause__ on lookup failure."""
        def mock_list_fail(entity, tid):
            raise RuntimeError("Database connection lost")

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list_fail)

        with pytest.raises(DomainValidationError) as exc_info:
            _svc._check_cost_center_is_active(tenant_id=1, cost_center_id=1)

        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, RuntimeError)


class TestCategoryCapGuard:
    """Category-level active expense caps."""

    def test_category_caps_enforced(self, monkeypatch):
        """Category active count respected in create_expense_record."""

        # Mock to have 3 existing pending travel expenses
        def mock_list(entity, tid):
            if entity == "cost_centers":
                return [{"id": 1, "active": True, "budget_limit": 10000.0}]
            elif entity == "expense_records":
                return [
                    {"id": 1, "cost_center_id": 1, "category": "travel", "status": "pending", "amount": 100.0},
                    {"id": 2, "cost_center_id": 1, "category": "travel", "status": "pending", "amount": 200.0},
                    {"id": 3, "cost_center_id": 1, "category": "travel", "status": "pending", "amount": 150.0},
                ]
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", lambda *a, **k: {"id": 99})

        # Attempting 4th travel when max is 3 should fail
        with pytest.raises(ValueError) as exc_info:
            _svc.create_expense_record(
                {
                    "cost_center_id": 1,
                    "category": "travel",
                    "amount": 100.0,
                    "status": "pending",
                },
                tenant_id=1
            )

        assert "cap exceeded" in str(exc_info.value).lower()
        assert "travel" in str(exc_info.value)

    def test_different_categories_independent(self, monkeypatch):
        """Category caps are independent per category."""
        # Mock with 3 pending travel but 0 software
        def mock_list(entity, tid):
            if entity == "cost_centers":
                return [{"id": 1, "active": True, "budget_limit": 10000.0}]
            elif entity == "expense_records":
                return [
                    {"id": 1, "cost_center_id": 1, "category": "travel", "status": "pending", "amount": 100.0},
                    {"id": 2, "cost_center_id": 1, "category": "travel", "status": "pending", "amount": 200.0},
                    {"id": 3, "cost_center_id": 1, "category": "travel", "status": "pending", "amount": 150.0},
                ]
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", lambda *a, **k: {"id": 99})

        # Creating software should succeed despite travel being full
        result = _svc.create_expense_record(
            {
                "cost_center_id": 1,
                "category": "software",
                "amount": 500.0,
                "status": "pending",
            },
            tenant_id=1
        )
        assert result is not None


class TestBudgetLimitGuard:
    """Cost center budget limit enforcement."""

    def test_budget_limit_not_exceeded(self, monkeypatch):
        """Expense allowed when total <= budget."""
        def mock_list(entity, tid):
            if entity == "cost_centers":
                return [{"id": 1, "active": True, "budget_limit": 1000.0}]
            elif entity == "expense_records":
                return [
                    {"id": 1, "cost_center_id": 1, "category": "travel", "status": "approved", "amount": 400.0},
                ]
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", lambda *a, **k: {"id": 99})

        # 400 + 500 = 900 < 1000 limit
        result = _svc.create_expense_record(
            {"cost_center_id": 1, "category": "general", "amount": 500.0},
            tenant_id=1
        )
        assert result is not None

    def test_budget_limit_exceeded(self, monkeypatch):
        """Expense blocked when total > budget."""
        def mock_list(entity, tid):
            if entity == "cost_centers":
                return [{"id": 1, "active": True, "budget_limit": 1000.0}]
            elif entity == "expense_records":
                return [
                    {"id": 1, "cost_center_id": 1, "category": "travel", "status": "approved", "amount": 700.0},
                ]
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)

        # 700 + 400 = 1100 > 1000 limit
        with pytest.raises(ValueError) as exc_info:
            _svc.create_expense_record(
                {"cost_center_id": 1, "category": "general", "amount": 400.0},
                tenant_id=1
            )

        assert "exceeds" in str(exc_info.value).lower() or "budget" in str(exc_info.value).lower()


class TestTenantIsolation:
    """Tenant isolation for expense records."""

    def test_cost_center_check_per_tenant(self, monkeypatch):
        """Cost center lookup scoped to specific tenant."""
        call_args = []

        def mock_list(entity, tid):
            call_args.append((entity, tid))
            return [] if entity == "cost_centers" else []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)

        with pytest.raises(DomainValidationError):
            _svc._check_cost_center_is_active(tenant_id=42, cost_center_id=1)

        # Verify tenant_id was passed
        assert any(args[1] == 42 for args in call_args if args[0] == "cost_centers")


class TestRouterStructure:
    """Verify router uses _svc pattern."""

    def test_router_imports_svc_module(self):
        import app.modules.expense_controls.router as router_module
        assert hasattr(router_module, "_svc")

    def test_router_has_endpoints(self):
        import app.modules.expense_controls.router as router_module
        assert hasattr(router_module, "list_expense_records_endpoint")
        assert hasattr(router_module, "create_expense_record_endpoint")
        assert hasattr(router_module, "list_cost_centers_endpoint")
        assert hasattr(router_module, "create_cost_center_endpoint")
        assert hasattr(router_module, "get_expense_brain_context_endpoint")


class TestErrorHandling:
    """Error handling on write endpoints."""

    def test_create_catches_domain_validation_error(self, monkeypatch):
        """create endpoint catches DomainValidationError → 422."""
        def mock_list(entity, tid):
            raise RuntimeError("DB error")

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)

        # Should raise DomainValidationError
        with pytest.raises(DomainValidationError):
            _svc.create_expense_record(
                {"cost_center_id": 1, "amount": 100.0},
                tenant_id=1
            )

    def test_positive_amount_validation(self, monkeypatch):
        """Amount must be positive."""
        def mock_list(entity, tid):
            if entity == "cost_centers":
                return [{"id": 1, "active": True}]
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)

        with pytest.raises(ValueError) as exc_info:
            _svc.create_expense_record(
                {"cost_center_id": 1, "amount": -100.0},
                tenant_id=1
            )
        assert "greater than 0" in str(exc_info.value)

    def test_valid_cost_center_id_required(self):
        """Cost center ID must be positive integer."""
        with pytest.raises(ValueError):
            _svc.create_expense_record(
                {"cost_center_id": 0, "amount": 100.0},
                tenant_id=1
            )


class TestBoundaryConditions:
    """Boundary and edge cases."""

    def test_zero_amount_rejected(self):
        """Zero or negative amounts rejected."""
        with pytest.raises(ValueError):
            _svc.create_expense_record(
                {"cost_center_id": 1, "amount": 0.0},
                tenant_id=1
            )

    def test_empty_category_allowed(self, monkeypatch):
        """Empty category string handled gracefully."""
        def mock_list(entity, tid):
            if entity == "cost_centers":
                return [{"id": 1, "active": True, "budget_limit": 10000.0}]
            return []

        monkeypatch.setattr(_svc, "list_entities_for_tenant", mock_list)
        monkeypatch.setattr(_svc, "create_entity_for_tenant", lambda *a, **k: {"id": 99})

        # Empty category should not crash
        result = _svc.create_expense_record(
            {"cost_center_id": 1, "category": "", "amount": 100.0},
            tenant_id=1
        )
        assert result is not None
