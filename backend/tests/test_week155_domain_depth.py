"""W155 — faculty_performance_kpis: deep domain hardening pack.

Guard: W130 (W103) — KPI creation blocked unless faculty has active employment contract.
- fail-closed on faculty_contracts lookup failure
- validate-before-persist (cap checked first, then guard, then persist)
- active KPI period cap enforcement
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.faculty_performance_kpis.service as svc


_TENANT = 30
_FAC_ID = "FAC-999"
_PERIOD = "Q1"


def _contract(faculty_id: str, status: str) -> dict:
    return {"faculty_id": faculty_id, "status": status, "id": "c1"}


def _kpi_schema(**kwargs):
    from app.modules.faculty_performance_kpis.schemas import FacultyKpiCreateSchema
    defaults = {
        "faculty_id": _FAC_ID,
        "name": "Teaching Excellence",
        "department_id": "DEPT-1",
        "kpi_period": _PERIOD,
        "teaching_score": 80.0,
        "research_score": 75.0,
        "service_score": 70.0,
        "overall_score": 75.0,
        "status": "satisfactory",
    }
    defaults.update(kwargs)
    return FacultyKpiCreateSchema(**defaults)


class TestConstants:
    def test_active_kpi_statuses_is_frozenset(self):
        assert isinstance(svc._ACTIVE_KPI_STATUSES, frozenset)

    def test_satisfactory_in_active_statuses(self):
        assert "satisfactory" in svc._ACTIVE_KPI_STATUSES

    def test_needs_improvement_in_active_statuses(self):
        assert "needs_improvement" in svc._ACTIVE_KPI_STATUSES

    def test_on_probation_in_active_statuses(self):
        assert "on_probation" in svc._ACTIVE_KPI_STATUSES

    def test_kpi_active_contract_statuses_is_frozenset(self):
        assert isinstance(svc._KPI_ACTIVE_CONTRACT_STATUSES, frozenset)

    def test_active_in_contract_statuses(self):
        assert "active" in svc._KPI_ACTIVE_CONTRACT_STATUSES

    def test_terminated_not_in_contract_statuses(self):
        assert "terminated" not in svc._KPI_ACTIVE_CONTRACT_STATUSES

    def test_kpi_period_max_active_has_q1(self):
        assert "Q1" in svc._KPI_PERIOD_MAX_ACTIVE

    def test_kpi_period_max_active_positive(self):
        assert all(v > 0 for v in svc._KPI_PERIOD_MAX_ACTIVE.values())

    def test_low_score_threshold_is_float(self):
        assert isinstance(svc._LOW_SCORE_THRESHOLD, float)

    def test_performance_risk_statuses_is_frozenset(self):
        assert isinstance(svc._PERFORMANCE_RISK_STATUSES, frozenset)


class TestW130GuardSignature:
    def test_guard_callable(self):
        assert callable(svc._check_faculty_has_active_contract_for_kpi)

    def test_guard_requires_keyword_args(self):
        with pytest.raises(TypeError):
            svc._check_faculty_has_active_contract_for_kpi(_TENANT, _FAC_ID, _PERIOD)

    def test_guard_returns_none_for_active_contract(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: [_contract(_FAC_ID, "active")],
        )
        result = svc._check_faculty_has_active_contract_for_kpi(
            tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
        )
        assert result is None

    def test_guard_passes_with_multiple_contracts_one_active(self, monkeypatch):
        contracts = [_contract(_FAC_ID, "terminated"), _contract(_FAC_ID, "active")]
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: contracts,
        )
        svc._check_faculty_has_active_contract_for_kpi(
            tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
        )


class TestW130GuardFailures:
    def test_blocks_when_no_contracts_for_faculty(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        with pytest.raises(DomainValidationError, match="no contract records found"):
            svc._check_faculty_has_active_contract_for_kpi(
                tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
            )

    def test_blocks_when_contract_terminated(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: [_contract(_FAC_ID, "terminated")],
        )
        with pytest.raises(DomainValidationError, match="no active contract"):
            svc._check_faculty_has_active_contract_for_kpi(
                tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
            )

    def test_blocks_when_contract_resigned(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: [_contract(_FAC_ID, "resigned")],
        )
        with pytest.raises(DomainValidationError, match="no active contract"):
            svc._check_faculty_has_active_contract_for_kpi(
                tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
            )

    def test_error_contains_faculty_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_faculty_has_active_contract_for_kpi(
                tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
            )
        assert _FAC_ID in str(exc_info.value)

    def test_error_contains_kpi_period(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_faculty_has_active_contract_for_kpi(
                tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
            )
        assert _PERIOD in str(exc_info.value)

    def test_error_shows_found_statuses(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: [_contract(_FAC_ID, "terminated")],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_faculty_has_active_contract_for_kpi(
                tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
            )
        assert "terminated" in str(exc_info.value)

    def test_ignores_other_faculty_contracts(self, monkeypatch):
        # only OTHER faculty has active contract — should still block
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: [_contract("FAC-OTHER", "active")],
        )
        with pytest.raises(DomainValidationError, match="no contract records found"):
            svc._check_faculty_has_active_contract_for_kpi(
                tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
            )


class TestW130FailClosed:
    def test_fail_closed_on_runtime_error(self, monkeypatch):
        def boom(entity, tenant_id):
            raise RuntimeError("DB down")

        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError, match="lookup failed"):
            svc._check_faculty_has_active_contract_for_kpi(
                tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
            )

    def test_fail_closed_on_connection_error(self, monkeypatch):
        def boom(entity, tenant_id):
            raise ConnectionError("timeout")

        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            svc._check_faculty_has_active_contract_for_kpi(
                tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
            )

    def test_fail_closed_on_os_error(self, monkeypatch):
        def boom(entity, tenant_id):
            raise OSError("network unreachable")

        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            svc._check_faculty_has_active_contract_for_kpi(
                tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
            )

    def test_fail_closed_cause_preserved(self, monkeypatch):
        original_exc = RuntimeError("DB down")

        def boom(entity, tenant_id):
            raise original_exc

        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_faculty_has_active_contract_for_kpi(
                tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
            )
        assert exc_info.value.__cause__ is original_exc


class TestBusinessInvariants:
    def test_lookup_uses_faculty_contracts_entity(self, monkeypatch):
        entities = []

        def mock_list(entity, tenant_id):
            entities.append(entity)
            return [_contract(_FAC_ID, "active")]

        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", mock_list
        )
        svc._check_faculty_has_active_contract_for_kpi(
            tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
        )
        assert entities[0] == "faculty_contracts"

    def test_tenant_isolation(self, monkeypatch):
        calls = []

        def mock_list(entity, tenant_id):
            calls.append((entity, tenant_id))
            return [_contract(_FAC_ID, "active")]

        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", mock_list
        )
        svc._check_faculty_has_active_contract_for_kpi(
            tenant_id=55, faculty_id=_FAC_ID, kpi_period=_PERIOD
        )
        assert any(t == 55 for _, t in calls)

    def test_active_status_case_insensitive(self, monkeypatch):
        # "Active" (capitalized) should match
        row = {"faculty_id": _FAC_ID, "status": "Active"}
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: [row],
        )
        svc._check_faculty_has_active_contract_for_kpi(
            tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
        )

    def test_faculty_id_whitespace_trimmed(self, monkeypatch):
        row = {"faculty_id": f"  {_FAC_ID}  ", "status": "active"}
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: [row],
        )
        svc._check_faculty_has_active_contract_for_kpi(
            tenant_id=_TENANT, faculty_id=_FAC_ID, kpi_period=_PERIOD
        )


class TestPeriodCapEnforcement:
    def test_cap_blocks_when_q1_at_limit(self, monkeypatch):
        cap = svc._KPI_PERIOD_MAX_ACTIVE["Q1"]
        existing = [
            {"kpi_period": "Q1", "status": "satisfactory", "id": i} for i in range(cap)
        ]
        contracts = [_contract(_FAC_ID, "active")]

        def mock_list(entity, tenant_id):
            if entity == "faculty_contracts":
                return contracts
            return existing

        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.create_entity_for_tenant",
            lambda e, p, t: {"id": 999, **p},
        )
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.log_admin_action",
            lambda **kw: None,
        )
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.EventPublisher",
            lambda: type("EP", (), {"publish_event": lambda self, **kw: None})(),
        )
        with pytest.raises(ValueError, match="cap"):
            svc.create_faculty_kpi(_TENANT, _kpi_schema(), "actor")

    def test_cap_allows_below_limit(self, monkeypatch):
        cap = svc._KPI_PERIOD_MAX_ACTIVE["Q1"]
        existing = [
            {"kpi_period": "Q1", "status": "satisfactory", "id": i}
            for i in range(cap - 1)
        ]
        contracts = [_contract(_FAC_ID, "active")]

        def mock_list(entity, tenant_id):
            if entity == "faculty_contracts":
                return contracts
            return existing

        created = []
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.create_entity_for_tenant",
            lambda e, p, t: created.append(p) or {"id": 1, **p},
        )
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.log_admin_action",
            lambda **kw: None,
        )
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.EventPublisher",
            lambda: type("EP", (), {"publish_event": lambda self, **kw: None})(),
        )
        svc.create_faculty_kpi(_TENANT, _kpi_schema(), "actor")
        assert created


class TestValidateBeforePersist:
    def test_create_not_called_when_guard_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        created = []
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.create_entity_for_tenant",
            lambda e, p, t: created.append(p) or {"id": 1},
        )
        with pytest.raises(DomainValidationError):
            svc.create_faculty_kpi(_TENANT, _kpi_schema(), "actor")
        assert created == []

    def test_guard_not_called_when_cap_blocks(self, monkeypatch):
        """Cap check fires BEFORE guard — guard should not be called when cap exceeded."""
        cap = svc._KPI_PERIOD_MAX_ACTIVE["Q1"]
        existing = [
            {"kpi_period": "Q1", "status": "satisfactory", "id": i} for i in range(cap)
        ]
        guard_calls = []
        original_guard = svc._check_faculty_has_active_contract_for_kpi

        def tracking_guard(**kwargs):
            guard_calls.append(kwargs)
            return original_guard(**kwargs)

        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant",
            lambda e, t: existing,
        )
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service._check_faculty_has_active_contract_for_kpi",
            tracking_guard,
        )
        with pytest.raises(ValueError, match="cap"):
            svc.create_faculty_kpi(_TENANT, _kpi_schema(), "actor")
        # guard not called because cap check raised first
        assert guard_calls == []

    def test_guard_called_before_create_entity(self, monkeypatch):
        call_order = []
        contracts = [_contract(_FAC_ID, "active")]

        def mock_list(entity, tenant_id):
            return contracts if entity == "faculty_contracts" else []

        def mock_guard(*, tenant_id, faculty_id, kpi_period):
            call_order.append("guard")

        created = []

        def mock_create(entity, payload, tenant_id):
            call_order.append("create")
            created.append(payload)
            return {"id": 42, **payload}

        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service._check_faculty_has_active_contract_for_kpi",
            mock_guard,
        )
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.create_entity_for_tenant", mock_create
        )
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.log_admin_action",
            lambda **kw: None,
        )
        monkeypatch.setattr(
            "app.modules.faculty_performance_kpis.service.EventPublisher",
            lambda: type("EP", (), {"publish_event": lambda self, **kw: None})(),
        )
        svc.create_faculty_kpi(_TENANT, _kpi_schema(), "actor")
        assert call_order == ["guard", "create"]


class TestRouterStructure:
    def _router_source(self) -> str:
        return (
            Path(__file__).resolve().parents[1]
            / "app/modules/faculty_performance_kpis/router.py"
        ).read_text(encoding="utf-8")

    def test_router_imports_service_as_svc(self):
        source = self._router_source()
        assert "import app.modules.faculty_performance_kpis.service as _svc" in source

    def test_router_has_no_direct_service_imports(self):
        source = self._router_source()
        assert "from app.modules.faculty_performance_kpis.service import" not in source

    def test_create_endpoint_catches_domain_validation_error(self):
        source = self._router_source()
        assert "except (ValueError, DomainValidationError) as exc" in source
        assert "status_code=422" in source

    def test_router_has_expected_routes(self):
        router_mod = importlib.import_module("app.modules.faculty_performance_kpis.router")
        paths = {r.path for r in router_mod.router.routes}
        assert "/api/admin/faculty-performance-kpis" in paths
        assert "/api/admin/faculty-performance-kpis/{kpi_id}" in paths
        assert "/api/admin/faculty-performance-kpis/{kpi_id}/status" in paths
