"""W154 — ip_management: deep domain hardening pack.

Guard: W31R — IP asset creation blocked unless all inventors have active faculty contracts.
- fail-closed on faculty_contracts lookup failure
- validate-before-persist
- active asset cap enforcement
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.ip_management.service as svc


_TENANT = 22
_INV1 = "FAC-001"
_INV2 = "FAC-002"


def _contract(faculty_id: str, status: str) -> dict:
    return {"faculty_id": faculty_id, "status": status, "id": "c1"}


def _payload(**kwargs) -> dict:
    defaults = {
        "title": "Novel AI Scheduler",
        "ip_type": "patent",
        "status": "filed",
        "commercialization_status": "none",
        "inventor_ids": _INV1,
    }
    defaults.update(kwargs)
    return defaults


class TestConstants:
    def test_active_asset_statuses_is_frozenset(self):
        assert isinstance(svc._ACTIVE_ASSET_STATUSES, frozenset)

    def test_filed_in_active_statuses(self):
        assert "filed" in svc._ACTIVE_ASSET_STATUSES

    def test_granted_in_active_statuses(self):
        assert "granted" in svc._ACTIVE_ASSET_STATUSES

    def test_active_in_active_statuses(self):
        assert "active" in svc._ACTIVE_ASSET_STATUSES

    def test_draft_not_in_active_statuses(self):
        assert "draft" not in svc._ACTIVE_ASSET_STATUSES

    def test_commercial_statuses_is_frozenset(self):
        assert isinstance(svc._COMMERCIAL_STATUSES, frozenset)

    def test_commercialized_in_commercial_statuses(self):
        assert "commercialized" in svc._COMMERCIAL_STATUSES

    def test_licensed_in_commercial_statuses(self):
        assert "licensed" in svc._COMMERCIAL_STATUSES

    def test_inventor_active_contract_statuses_is_frozenset(self):
        assert isinstance(svc._INVENTOR_ACTIVE_CONTRACT_STATUSES, frozenset)

    def test_active_in_inventor_contract_statuses(self):
        assert "active" in svc._INVENTOR_ACTIVE_CONTRACT_STATUSES

    def test_ip_type_caps_exist(self):
        assert isinstance(svc._IP_TYPE_MAX_ACTIVE_ASSETS, dict)
        assert "patent" in svc._IP_TYPE_MAX_ACTIVE_ASSETS

    def test_patent_cap_positive(self):
        assert svc._IP_TYPE_MAX_ACTIVE_ASSETS["patent"] > 0


class TestParseInventorIds:
    def test_parse_comma_separated_string(self):
        result = svc._parse_inventor_ids("A, B, C")
        assert result == ["A", "B", "C"]

    def test_parse_list(self):
        result = svc._parse_inventor_ids(["A", "B"])
        assert result == ["A", "B"]

    def test_parse_none_returns_empty(self):
        result = svc._parse_inventor_ids(None)
        assert result == []

    def test_parse_deduplicates(self):
        result = svc._parse_inventor_ids("A, A, B")
        assert result.count("A") == 1

    def test_parse_empty_string_returns_empty(self):
        result = svc._parse_inventor_ids("")
        assert result == []

    def test_parse_single_value(self):
        result = svc._parse_inventor_ids("FAC-001")
        assert result == ["FAC-001"]


class TestW31GuardSignature:
    def test_guard_callable(self):
        assert callable(svc._check_inventors_have_active_contracts_for_ip_asset)

    def test_guard_requires_keyword_args(self):
        with pytest.raises(TypeError):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                _TENANT, "patent", "filed", "none", _INV1
            )

    def test_guard_returns_none_when_draft(self):
        # draft status → no validation required
        result = svc._check_inventors_have_active_contracts_for_ip_asset(
            tenant_id=_TENANT,
            ip_type="patent",
            status="draft",
            commercialization_status="none",
            inventor_ids_raw=None,
        )
        assert result is None

    def test_guard_passes_for_active_inventor(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: [_contract(_INV1, "active")],
        )
        svc._check_inventors_have_active_contracts_for_ip_asset(
            tenant_id=_TENANT,
            ip_type="patent",
            status="filed",
            commercialization_status="none",
            inventor_ids_raw=_INV1,
        )


class TestW31GuardFailures:
    def test_blocks_when_inventor_ids_missing_for_filed(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        with pytest.raises(DomainValidationError, match="inventor_ids is required"):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=_TENANT,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw=None,
            )

    def test_blocks_when_inventor_has_no_contract(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        with pytest.raises(DomainValidationError, match="inventor"):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=_TENANT,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw=_INV1,
            )

    def test_blocks_when_inventor_contract_terminated(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: [_contract(_INV1, "terminated")],
        )
        with pytest.raises(DomainValidationError, match="inventor"):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=_TENANT,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw=_INV1,
            )

    def test_blocks_when_one_of_two_inventors_inactive(self, monkeypatch):
        contracts = [_contract(_INV1, "active"), _contract(_INV2, "terminated")]
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: contracts,
        )
        with pytest.raises(DomainValidationError, match="inventor"):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=_TENANT,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw=f"{_INV1},{_INV2}",
            )

    def test_blocks_for_commercialized_status(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        with pytest.raises(DomainValidationError, match="inventor_ids is required"):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=_TENANT,
                ip_type="patent",
                status="draft",
                commercialization_status="commercialized",
                inventor_ids_raw=None,
            )

    def test_error_contains_missing_inventor_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: [_contract(_INV1, "active")],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=_TENANT,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw=f"{_INV1},{_INV2}",
            )
        assert _INV2 in str(exc_info.value)


class TestW31FailClosed:
    def test_fail_closed_on_runtime_error(self, monkeypatch):
        def boom(entity, tenant_id):
            raise RuntimeError("DB down")

        monkeypatch.setattr("app.modules.ip_management.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError, match="faculty_contracts lookup failed"):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=_TENANT,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw=_INV1,
            )

    def test_fail_closed_on_connection_error(self, monkeypatch):
        def boom(entity, tenant_id):
            raise ConnectionError("timeout")

        monkeypatch.setattr("app.modules.ip_management.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=_TENANT,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw=_INV1,
            )

    def test_fail_closed_on_value_error(self, monkeypatch):
        def boom(entity, tenant_id):
            raise ValueError("bad data")

        monkeypatch.setattr("app.modules.ip_management.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=_TENANT,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw=_INV1,
            )

    def test_fail_closed_no_open_fallback(self, monkeypatch):
        call_count = []

        def boom(entity, tenant_id):
            call_count.append(1)
            raise OSError("network")

        monkeypatch.setattr("app.modules.ip_management.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError):
            svc._check_inventors_have_active_contracts_for_ip_asset(
                tenant_id=_TENANT,
                ip_type="patent",
                status="filed",
                commercialization_status="none",
                inventor_ids_raw=_INV1,
            )
        assert call_count == [1]


class TestW31CreatePath:
    def test_guard_called_before_persist(self, monkeypatch):
        guard_calls = []

        def mock_guard(*, tenant_id, ip_type, status, commercialization_status, inventor_ids_raw):
            guard_calls.append(inventor_ids_raw)

        created = []
        monkeypatch.setattr(
            "app.modules.ip_management.service._check_inventors_have_active_contracts_for_ip_asset",
            mock_guard,
        )
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        monkeypatch.setattr(
            "app.modules.ip_management.service.create_entity_for_tenant",
            lambda e, p, t: created.append(p) or {"id": 1, **p},
        )
        svc.create_ip_asset(_payload(), _TENANT)
        assert guard_calls == [_INV1]
        assert created

    def test_create_not_called_when_guard_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        created = []
        monkeypatch.setattr(
            "app.modules.ip_management.service.create_entity_for_tenant",
            lambda e, p, t: created.append(p) or {"id": 1},
        )
        with pytest.raises(DomainValidationError, match="inventor"):
            svc.create_ip_asset(_payload(), _TENANT)
        assert created == []

    def test_draft_asset_skips_guard(self, monkeypatch):
        created = []
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        monkeypatch.setattr(
            "app.modules.ip_management.service.create_entity_for_tenant",
            lambda e, p, t: created.append(p) or {"id": 5, **p},
        )
        result = svc.create_ip_asset(_payload(status="draft", inventor_ids=None), _TENANT)
        assert result["id"] == 5
        assert created

    def test_succeeds_with_both_inventors_active(self, monkeypatch):
        contracts = [_contract(_INV1, "active"), _contract(_INV2, "active")]
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: contracts,
        )
        monkeypatch.setattr(
            "app.modules.ip_management.service.create_entity_for_tenant",
            lambda e, p, t: {"id": 99, **p},
        )
        result = svc.create_ip_asset(_payload(inventor_ids=f"{_INV1},{_INV2}"), _TENANT)
        assert result["id"] == 99


class TestBusinessInvariants:
    def test_tenant_isolation_contracts_lookup(self, monkeypatch):
        calls = []

        def mock_list(entity, tenant_id):
            calls.append((entity, tenant_id))
            return [_contract(_INV1, "active")]

        monkeypatch.setattr("app.modules.ip_management.service.list_entities_for_tenant", mock_list)
        svc._check_inventors_have_active_contracts_for_ip_asset(
            tenant_id=10,
            ip_type="patent",
            status="filed",
            commercialization_status="none",
            inventor_ids_raw=_INV1,
        )
        assert any(t == 10 for _, t in calls)

    def test_lookup_uses_faculty_contracts_entity(self, monkeypatch):
        entities = []

        def mock_list(entity, tenant_id):
            entities.append(entity)
            return [_contract(_INV1, "active")]

        monkeypatch.setattr("app.modules.ip_management.service.list_entities_for_tenant", mock_list)
        svc._check_inventors_have_active_contracts_for_ip_asset(
            tenant_id=_TENANT,
            ip_type="patent",
            status="filed",
            commercialization_status="none",
            inventor_ids_raw=_INV1,
        )
        assert entities[0] == "faculty_contracts"

    def test_active_status_case_insensitive(self, monkeypatch):
        row = {"faculty_id": _INV1, "status": "Active", "id": "c1"}
        monkeypatch.setattr(
            "app.modules.ip_management.service.list_entities_for_tenant",
            lambda e, t: [row],
        )
        svc._check_inventors_have_active_contracts_for_ip_asset(
            tenant_id=_TENANT,
            ip_type="patent",
            status="filed",
            commercialization_status="none",
            inventor_ids_raw=_INV1,
        )

    def test_cap_blocks_excess_active_assets(self, monkeypatch):
        cap = svc._IP_TYPE_MAX_ACTIVE_ASSETS["patent"]
        existing = [
            {"ip_type": "patent", "status": "filed", "id": i}
            for i in range(cap)
        ]
        contracts = [_contract(_INV1, "active")]

        def mock_list(entity, tenant_id):
            if entity == "faculty_contracts":
                return contracts
            if entity == "ip_assets":
                return existing
            return []

        monkeypatch.setattr("app.modules.ip_management.service.list_entities_for_tenant", mock_list)
        with pytest.raises(ValueError, match="cap"):
            svc.create_ip_asset(_payload(status="filed"), _TENANT)


class TestRouterStructure:
    def _router_source(self) -> str:
        return (Path(__file__).resolve().parents[1] / "app/modules/ip_management/router.py").read_text(encoding="utf-8")

    def test_router_imports_service_as_alias(self):
        source = self._router_source()
        assert "import app.modules.ip_management.service as _svc" in source

    def test_router_has_no_direct_service_imports(self):
        source = self._router_source()
        assert "from app.modules.ip_management.service import" not in source

    def test_create_endpoint_catches_domain_validation_error(self):
        source = self._router_source()
        assert "except (ValueError, DomainValidationError) as exc" in source
        assert "status_code=422" in source

    def test_router_has_expected_routes(self):
        router_mod = importlib.import_module("app.modules.ip_management.router")
        paths = {r.path for r in router_mod.router.routes}
        assert "/api/admin/ip-management/assets" in paths
        assert "/api/admin/ip-management/brain-context" in paths
