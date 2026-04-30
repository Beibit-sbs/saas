"""W153 — research_ethics: deep domain hardening pack.

Guard: W126
- create blocked unless PI has active faculty contract
- fail-closed on faculty_contracts lookup failure
- validate-before-persist in create_ethics_review
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.research_ethics.service as svc


_TENANT = 77
_PI = "pi-001"


def _contract(status: str, pi_id: str = _PI) -> dict:
    return {"faculty_id": pi_id, "status": status, "id": "c1"}


def _alt_contract(status: str, pi_id: str = _PI) -> dict:
    return {"employee_id": pi_id, "contract_status": status, "id": "c2"}


def _review_payload(**kwargs) -> dict:
    defaults = {
        "principal_investigator_id": _PI,
        "review_type": "irb",
        "status": "pending",
        "risk_level": "low",
        "review_code": "IRB-2026-001",
    }
    defaults.update(kwargs)
    return defaults


class TestConstants:
    def test_pi_contract_active_statuses_is_frozenset(self):
        assert isinstance(svc._PI_CONTRACT_ACTIVE_STATUSES, frozenset)

    def test_active_in_statuses(self):
        assert "active" in svc._PI_CONTRACT_ACTIVE_STATUSES

    def test_terminated_not_in_statuses(self):
        assert "terminated" not in svc._PI_CONTRACT_ACTIVE_STATUSES

    def test_resigned_not_in_statuses(self):
        assert "resigned" not in svc._PI_CONTRACT_ACTIVE_STATUSES

    def test_expired_not_in_statuses(self):
        assert "expired" not in svc._PI_CONTRACT_ACTIVE_STATUSES

    def test_statuses_nonempty(self):
        assert len(svc._PI_CONTRACT_ACTIVE_STATUSES) >= 1

    def test_review_type_caps_exist(self):
        assert isinstance(svc._REVIEW_TYPE_MAX_ACTIVE_REVIEWS, dict)

    def test_irb_cap_exists(self):
        assert "irb" in svc._REVIEW_TYPE_MAX_ACTIVE_REVIEWS


class TestW126GuardSignature:
    def test_guard_callable(self):
        assert callable(svc._check_pi_has_active_contract_for_ethics_review)

    def test_guard_requires_keyword_args(self):
        with pytest.raises(TypeError):
            svc._check_pi_has_active_contract_for_ethics_review(_TENANT, _PI)  # type: ignore[call-arg]

    def test_guard_requires_pi_id(self):
        with pytest.raises(TypeError):
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT)

    def test_guard_returns_none_on_success(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        result = svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)
        assert result is None

    def test_guard_strips_whitespace_pi_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id="  pi-001  ")


class TestW126GuardFailures:
    def test_blocks_when_no_contracts_at_all(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)

    def test_blocks_when_contracts_wrong_pi(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active", pi_id="other-pi")],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)

    def test_blocks_when_contract_terminated(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("terminated")],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)

    def test_blocks_when_contract_resigned(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("resigned")],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)

    def test_blocks_when_contract_expired(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("expired")],
        )
        with pytest.raises(DomainValidationError):
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)

    def test_error_contains_pi_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)
        assert _PI in str(exc_info.value)


class TestW126FailClosed:
    def test_fail_closed_on_runtime_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise RuntimeError("DB connection lost")

        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError, match="faculty_contracts lookup failed"):
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)

    def test_fail_closed_error_includes_pi_id(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ConnectionError("timeout")

        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)
        assert _PI in str(exc_info.value)

    def test_fail_closed_on_value_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ValueError("bad data")

        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError):
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)

    def test_fail_closed_no_open_fallback(self, monkeypatch):
        call_count = []

        def boom(entity_type, tenant_id):
            call_count.append(1)
            raise OSError("network down")

        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError):
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)
        assert call_count == [1]


class TestW126CreatePath:
    def test_guard_called_before_cap_and_create(self, monkeypatch):
        guard_called = []

        def mock_guard(*, tenant_id, pi_id):
            guard_called.append(pi_id)

        create_called = []

        monkeypatch.setattr(
            "app.modules.research_ethics.service._check_pi_has_active_contract_for_ethics_review",
            mock_guard,
        )
        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", lambda e, t: [])
        monkeypatch.setattr(
            "app.modules.research_ethics.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: create_called.append(True) or {"id": 1, **payload},
        )
        svc.create_ethics_review(_review_payload(), _TENANT)
        assert guard_called == [_PI]
        assert create_called

    def test_create_not_called_when_guard_blocks(self, monkeypatch):
        created = []
        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", lambda e, t: [])
        monkeypatch.setattr(
            "app.modules.research_ethics.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: created.append(payload) or {"id": 1},
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            svc.create_ethics_review(_review_payload(), _TENANT)
        assert created == []

    def test_blocks_missing_pi_id(self, monkeypatch):
        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", lambda e, t: [_contract("active")])
        with pytest.raises(DomainValidationError, match="principal_investigator_id is required"):
            svc.create_ethics_review(_review_payload(principal_investigator_id=""), _TENANT)

    def test_succeeds_with_active_contract(self, monkeypatch):
        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", lambda e, t: [_contract("active")])
        monkeypatch.setattr(
            "app.modules.research_ethics.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: {"id": 99, **payload},
        )
        result = svc.create_ethics_review(_review_payload(), _TENANT)
        assert result["id"] == 99

    def test_blocked_terminated_pi(self, monkeypatch):
        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", lambda e, t: [_contract("terminated")])
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            svc.create_ethics_review(_review_payload(), _TENANT)

    def test_alt_contract_key_succeeds(self, monkeypatch):
        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", lambda e, t: [_alt_contract("active")])
        monkeypatch.setattr(
            "app.modules.research_ethics.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: {"id": 55, **payload},
        )
        result = svc.create_ethics_review(_review_payload(), _TENANT)
        assert result["id"] == 55


class TestBusinessInvariants:
    def test_two_tenant_isolation(self, monkeypatch):
        calls = []

        def mock_list(entity_type, tenant_id):
            calls.append(tenant_id)
            if tenant_id == 1:
                return [_contract("active")]
            return []

        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", mock_list)
        svc._check_pi_has_active_contract_for_ethics_review(tenant_id=1, pi_id=_PI)
        with pytest.raises(DomainValidationError):
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=2, pi_id=_PI)
        assert 1 in calls and 2 in calls

    def test_lookup_entity_is_faculty_contracts(self, monkeypatch):
        entities = []

        def mock_list(entity_type, tenant_id):
            entities.append(entity_type)
            return []

        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", mock_list)
        with pytest.raises(DomainValidationError):
            svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)
        assert entities[0] == "faculty_contracts"

    def test_active_status_case_insensitive(self, monkeypatch):
        row = {"faculty_id": _PI, "status": "Active", "id": "c1"}
        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", lambda e, t: [row])
        svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id=_PI)

    def test_pi_whitespace_handling(self, monkeypatch):
        row = {"faculty_id": _PI, "status": "active", "id": "c1"}
        monkeypatch.setattr("app.modules.research_ethics.service.list_entities_for_tenant", lambda e, t: [row])
        svc._check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT, pi_id="  pi-001  ")


class TestRouterStructure:
    def _router_source(self) -> str:
        return (Path(__file__).resolve().parents[1] / "app/modules/research_ethics/router.py").read_text(encoding="utf-8")

    def test_router_imports_service_alias(self):
        source = self._router_source()
        assert "import app.modules.research_ethics.service as _svc" in source

    def test_router_has_no_direct_service_imports(self):
        source = self._router_source()
        assert "from app.modules.research_ethics.service import" not in source

    def test_create_endpoint_catches_domain_validation_error(self):
        source = self._router_source()
        assert "except (ValueError, DomainValidationError) as exc" in source
        assert "status_code=422" in source

    def test_router_has_expected_routes(self):
        router_mod = importlib.import_module("app.modules.research_ethics.router")
        paths = {r.path for r in router_mod.router.routes}
        assert "/api/admin/research-ethics/reviews" in paths
        assert "/api/admin/research-ethics/brain-context" in paths
