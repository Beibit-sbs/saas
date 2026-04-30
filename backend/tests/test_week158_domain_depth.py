"""W158 — teaching_quality: Router _svc Hardening (Faculty Active Contract Guard).

Guard: W124 — quality metric creation blocked unless faculty has active employment contract.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.teaching_quality.service import (
    _FACULTY_CONTRACT_ACTIVE_STATUSES,
    _check_faculty_has_active_contract_for_quality_metric,
    create_quality_metric,
)


_TENANT = 42
_FACULTY = "fac-001"


def _contract(status: str, faculty_id: str = _FACULTY) -> dict:
    return {"faculty_id": faculty_id, "status": status, "id": "c1"}


def _alt_contract(status: str, faculty_id: str = _FACULTY) -> dict:
    return {"employee_id": faculty_id, "contract_status": status, "id": "c2"}


class TestConstants:
    def test_active_statuses_is_frozenset(self):
        assert isinstance(_FACULTY_CONTRACT_ACTIVE_STATUSES, frozenset)

    def test_active_in_statuses(self):
        assert "active" in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_terminated_not_in_statuses(self):
        assert "terminated" not in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_resigned_not_in_statuses(self):
        assert "resigned" not in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_guard_callable(self):
        assert callable(_check_faculty_has_active_contract_for_quality_metric)

    def test_create_callable(self):
        assert callable(create_quality_metric)


class TestGuardAllowPaths:
    def test_active_contract_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [_contract("active")],
        )
        _check_faculty_has_active_contract_for_quality_metric(
            tenant_id=_TENANT,
            faculty_id=_FACULTY,
        )

    def test_multiple_contracts_one_active_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [
                _contract("terminated"),
                _contract("active"),
                _contract("expired"),
            ],
        )
        _check_faculty_has_active_contract_for_quality_metric(
            tenant_id=_TENANT,
            faculty_id=_FACULTY,
        )

    def test_allows_contract_status_alt_key(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [_alt_contract("active")],
        )
        _check_faculty_has_active_contract_for_quality_metric(
            tenant_id=_TENANT,
            faculty_id=_FACULTY,
        )

    def test_faculty_id_whitespace_trimmed(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [_contract("active")],
        )
        _check_faculty_has_active_contract_for_quality_metric(
            tenant_id=_TENANT,
            faculty_id="  fac-001  ",
        )

    def test_status_case_insensitive(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [_contract("ACTIVE")],
        )
        _check_faculty_has_active_contract_for_quality_metric(
            tenant_id=_TENANT,
            faculty_id=_FACULTY,
        )


class TestGuardBlockPaths:
    def test_no_contracts_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT,
                faculty_id=_FACULTY,
            )

    def test_wrong_faculty_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [_contract("active", faculty_id="other")],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT,
                faculty_id=_FACULTY,
            )

    def test_terminated_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [_contract("terminated")],
        )
        with pytest.raises(DomainValidationError, match="no active contract"):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT,
                faculty_id=_FACULTY,
            )

    def test_resigned_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [_contract("resigned")],
        )
        with pytest.raises(DomainValidationError, match="no active contract"):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT,
                faculty_id=_FACULTY,
            )

    def test_error_message_contains_faculty_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT,
                faculty_id=_FACULTY,
            )
        assert _FACULTY in str(exc_info.value)


class TestFailClosed:
    def test_lookup_runtime_error_blocks(self, monkeypatch):
        def boom(entity, tenant_id):
            raise RuntimeError("db down")

        monkeypatch.setattr("app.modules.teaching_quality.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError, match="lookup failed"):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT,
                faculty_id=_FACULTY,
            )

    def test_lookup_connection_error_blocks(self, monkeypatch):
        def boom(entity, tenant_id):
            raise ConnectionError("timeout")

        monkeypatch.setattr("app.modules.teaching_quality.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT,
                faculty_id=_FACULTY,
            )

    def test_lookup_os_error_blocks(self, monkeypatch):
        def boom(entity, tenant_id):
            raise OSError("io")

        monkeypatch.setattr("app.modules.teaching_quality.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT,
                faculty_id=_FACULTY,
            )

    def test_cause_preserved(self, monkeypatch):
        original = RuntimeError("root")

        def boom(entity, tenant_id):
            raise original

        monkeypatch.setattr("app.modules.teaching_quality.service.list_entities_for_tenant", boom)
        with pytest.raises(DomainValidationError) as exc_info:
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT,
                faculty_id=_FACULTY,
            )
        assert exc_info.value.__cause__ is original


class TestCreatePath:
    def test_create_requires_faculty_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [_contract("active")],
        )
        with pytest.raises(DomainValidationError, match="faculty_id is required"):
            create_quality_metric({"quality_score": 88}, _TENANT)

    def test_guard_before_persist_order(self, monkeypatch):
        order: list[str] = []

        def list_side(entity, tenant_id):
            order.append("guard")
            return [_contract("active")]

        def create_side(payload, tenant_id):
            order.append("persist")
            return {"id": "ok", **payload}

        monkeypatch.setattr("app.modules.teaching_quality.service.list_entities_for_tenant", list_side)
        monkeypatch.setattr("app.modules.teaching_quality.service.create_teaching_quality_record", create_side)
        create_quality_metric({"faculty_id": _FACULTY, "quality_score": 80}, _TENANT)
        assert order == ["guard", "persist"]

    def test_persist_not_called_when_guard_blocks(self, monkeypatch):
        created: list[dict] = []
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [_contract("terminated")],
        )
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.create_teaching_quality_record",
            lambda payload, tenant_id: created.append(payload) or {"id": "bad"},
        )
        with pytest.raises(DomainValidationError):
            create_quality_metric({"faculty_id": _FACULTY, "quality_score": 80}, _TENANT)
        assert created == []

    def test_create_success_with_active_contract(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [_contract("active")],
        )
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.create_teaching_quality_record",
            lambda payload, tenant_id: {"id": "new-1", **payload},
        )
        result = create_quality_metric({"faculty_id": _FACULTY, "quality_score": 91}, _TENANT)
        assert result["id"] == "new-1"
        assert result["faculty_id"] == _FACULTY

    def test_payload_forwarded_to_persist(self, monkeypatch):
        captured: list[dict] = []
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity, tenant_id: [_contract("active")],
        )
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.create_teaching_quality_record",
            lambda payload, tenant_id: captured.append(payload) or {"id": "new-1", **payload},
        )
        create_quality_metric({"faculty_id": _FACULTY, "term_id": 5, "quality_score": 77}, _TENANT)
        assert captured[0]["term_id"] == 5


class TestTenantIsolation:
    def test_guard_uses_requested_tenant(self, monkeypatch):
        calls: list[tuple[str, int]] = []

        def list_side(entity, tenant_id):
            calls.append((entity, tenant_id))
            return [_contract("active")]

        monkeypatch.setattr("app.modules.teaching_quality.service.list_entities_for_tenant", list_side)
        _check_faculty_has_active_contract_for_quality_metric(
            tenant_id=7,
            faculty_id=_FACULTY,
        )
        assert calls == [("faculty_contracts", 7)]

    def test_other_tenant_not_used(self, monkeypatch):
        def list_side(entity, tenant_id):
            if tenant_id == 1:
                return [_contract("active")]
            return []

        monkeypatch.setattr("app.modules.teaching_quality.service.list_entities_for_tenant", list_side)
        _check_faculty_has_active_contract_for_quality_metric(tenant_id=1, faculty_id=_FACULTY)
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_quality_metric(tenant_id=2, faculty_id=_FACULTY)


class TestRouterStructure:
    def _source(self) -> str:
        return (Path(__file__).resolve().parents[1] / "app/modules/teaching_quality/router.py").read_text()

    def test_router_imports_module_svc(self):
        source = self._source()
        assert "import app.modules.teaching_quality.service as _svc" in source

    def test_router_has_no_direct_teaching_quality_imports(self):
        source = self._source()
        assert "from app.modules.teaching_quality.service import" not in source

    def test_router_uses_svc_list_calls(self):
        source = self._source()
        assert "_svc.list_teaching_quality" in source

    def test_router_uses_svc_create_metric_call(self):
        source = self._source()
        assert "_svc.create_quality_metric" in source

    def test_router_keeps_domain_validation_error_mapping(self):
        source = self._source()
        assert "except (ValueError, DomainValidationError)" in source
        assert "status_code=422" in source

    def test_router_contains_metric_route(self):
        mod = importlib.import_module("app.modules.teaching_quality.router")
        paths = [r.path for r in mod.router.routes]
        assert any("/faculty/{faculty_id}/metric" in p for p in paths)

    def test_router_contains_kpi_route(self):
        mod = importlib.import_module("app.modules.teaching_quality.router")
        paths = [r.path for r in mod.router.routes]
        assert any("/faculty/{faculty_id}/kpi" in p for p in paths)

    def test_router_contains_report_route(self):
        mod = importlib.import_module("app.modules.teaching_quality.router")
        paths = [r.path for r in mod.router.routes]
        assert any("/report" in p for p in paths)
