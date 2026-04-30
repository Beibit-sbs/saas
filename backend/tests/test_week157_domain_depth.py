"""W157 — syllabus_governance: Router _svc Hardening (Faculty Active Contract Guard).

Guard: W123 — syllabus creation blocked unless faculty has active employment contract (fail-closed).
Guard order: W123 (faculty contract) fires FIRST, then cap check, then persist.
"""
from __future__ import annotations

import importlib
from pathlib import Path
from unittest.mock import patch

import pytest

import app.modules.syllabus_governance.service as svc
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.syllabus_governance.schemas import SyllabusCreateSchema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TENANT_ID = 10
FACULTY_ID = "fac-001"
DEPT_ID = "cs"


def _active_contract(faculty_id: str = FACULTY_ID) -> dict:
    return {"faculty_id": faculty_id, "status": "active"}


def _make_payload(faculty_id: str = FACULTY_ID, department_id: str = DEPT_ID) -> SyllabusCreateSchema:
    return SyllabusCreateSchema(
        faculty_id=faculty_id,
        course_code="CS-101",
        course_title="Intro to CS",
        department_id=department_id,
        term_id="2026-fall",
        status="draft",
    )


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_faculty_contract_active_statuses_is_frozenset(self):
        assert isinstance(svc._FACULTY_CONTRACT_ACTIVE_STATUSES, frozenset)

    def test_active_in_faculty_contract_statuses(self):
        assert "active" in svc._FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_active_syllabus_statuses_is_frozenset(self):
        assert isinstance(svc._ACTIVE_SYLLABUS_STATUSES, frozenset)

    def test_dept_max_active_syllabi_has_default(self):
        assert "default" in svc._DEPT_MAX_ACTIVE_SYLLABI

    def test_dept_max_active_syllabi_has_cs(self):
        assert "cs" in svc._DEPT_MAX_ACTIVE_SYLLABI

    def test_check_function_exists(self):
        assert callable(svc._check_faculty_has_active_contract_for_syllabus)

    def test_create_syllabus_exists(self):
        assert callable(svc.create_syllabus)

    def test_list_syllabi_exists(self):
        assert callable(svc.list_syllabi)

    def test_update_syllabus_exists(self):
        assert callable(svc.update_syllabus)


# ---------------------------------------------------------------------------
# 2. Guard — allow paths
# ---------------------------------------------------------------------------

class TestGuardAllowPaths:
    def test_active_contract_passes(self):
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract()]
            svc._check_faculty_has_active_contract_for_syllabus(
                tenant_id=TENANT_ID, faculty_id=FACULTY_ID
            )

    def test_multiple_contracts_one_active_passes(self):
        contracts = [
            {"faculty_id": FACULTY_ID, "status": "terminated"},
            {"faculty_id": FACULTY_ID, "status": "active"},
        ]
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            svc._check_faculty_has_active_contract_for_syllabus(
                tenant_id=TENANT_ID, faculty_id=FACULTY_ID
            )

    def test_faculty_id_whitespace_trimmed(self):
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract("fac-001")]
            svc._check_faculty_has_active_contract_for_syllabus(
                tenant_id=TENANT_ID, faculty_id="  fac-001  "
            )

    def test_status_case_insensitive(self):
        contracts = [{"faculty_id": FACULTY_ID, "status": "ACTIVE"}]
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            svc._check_faculty_has_active_contract_for_syllabus(
                tenant_id=TENANT_ID, faculty_id=FACULTY_ID
            )


# ---------------------------------------------------------------------------
# 3. Guard — block paths
# ---------------------------------------------------------------------------

class TestGuardBlockPaths:
    def test_empty_faculty_id_raises(self):
        with pytest.raises(DomainValidationError, match="faculty_id is missing"):
            svc._check_faculty_has_active_contract_for_syllabus(
                tenant_id=TENANT_ID, faculty_id=""
            )

    def test_no_contracts_raises(self):
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            with pytest.raises(DomainValidationError, match="no faculty contract records found"):
                svc._check_faculty_has_active_contract_for_syllabus(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_terminated_contract_raises(self):
        contracts = [{"faculty_id": FACULTY_ID, "status": "terminated"}]
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            with pytest.raises(DomainValidationError, match="no active contract"):
                svc._check_faculty_has_active_contract_for_syllabus(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_resigned_contract_raises(self):
        contracts = [{"faculty_id": FACULTY_ID, "status": "resigned"}]
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            with pytest.raises(DomainValidationError):
                svc._check_faculty_has_active_contract_for_syllabus(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_wrong_faculty_id_raises(self):
        contracts = [{"faculty_id": "other-fac", "status": "active"}]
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = contracts
            with pytest.raises(DomainValidationError, match="no faculty contract records found"):
                svc._check_faculty_has_active_contract_for_syllabus(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_error_message_contains_faculty_id(self):
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_faculty_has_active_contract_for_syllabus(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )
            assert FACULTY_ID in str(exc_info.value)


# ---------------------------------------------------------------------------
# 4. Fail-closed
# ---------------------------------------------------------------------------

class TestFailClosed:
    def test_runtime_error_raises_domain_validation(self):
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = RuntimeError("db down")
            with pytest.raises(DomainValidationError, match="lookup failed"):
                svc._check_faculty_has_active_contract_for_syllabus(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_connection_error_raises_domain_validation(self):
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = ConnectionError("timeout")
            with pytest.raises(DomainValidationError):
                svc._check_faculty_has_active_contract_for_syllabus(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )

    def test_cause_preserved(self):
        original = RuntimeError("original")
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = original
            with pytest.raises(DomainValidationError) as exc_info:
                svc._check_faculty_has_active_contract_for_syllabus(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )
            assert exc_info.value.__cause__ is original

    def test_os_error_raises_domain_validation(self):
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.side_effect = OSError("io error")
            with pytest.raises(DomainValidationError):
                svc._check_faculty_has_active_contract_for_syllabus(
                    tenant_id=TENANT_ID, faculty_id=FACULTY_ID
                )


# ---------------------------------------------------------------------------
# 5. Tenant isolation
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    def test_guard_passes_correct_tenant_id(self):
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = [_active_contract()]
            svc._check_faculty_has_active_contract_for_syllabus(
                tenant_id=99, faculty_id=FACULTY_ID
            )
            mock_list.assert_called_once_with("faculty_contracts", 99)

    def test_other_tenant_contracts_dont_satisfy(self):
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []
            with pytest.raises(DomainValidationError):
                svc._check_faculty_has_active_contract_for_syllabus(
                    tenant_id=1, faculty_id=FACULTY_ID
                )
            mock_list.assert_called_once_with("faculty_contracts", 1)


# ---------------------------------------------------------------------------
# 6. Guard fires first in create_syllabus
# ---------------------------------------------------------------------------

class TestGuardFiresFirst:
    def _list_side_effect_factory(self, entity_returns: dict):
        """Return different data per entity name."""
        def side_effect(entity, tenant_id):
            return entity_returns.get(entity, [])
        return side_effect

    def test_guard_blocks_before_create(self):
        payload = _make_payload()
        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant") as mock_list:
            mock_list.return_value = []  # no contracts → guard blocks
            with patch("app.modules.syllabus_governance.service.create_entity_for_tenant") as mock_create:
                with pytest.raises(DomainValidationError):
                    svc.create_syllabus(TENANT_ID, payload, "actor-1")
                mock_create.assert_not_called()

    def test_guard_blocks_before_cap_check(self):
        # If guard fires, cap check (list_syllabi) should not matter
        payload = _make_payload()
        calls = []

        def list_side(entity, tenant_id):
            calls.append(entity)
            if entity == "faculty_contracts":
                return []  # no contracts → DomainValidationError
            return []

        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant", side_effect=list_side):
            with pytest.raises(DomainValidationError):
                svc.create_syllabus(TENANT_ID, payload, "actor-1")
        # First call must be faculty_contracts
        assert calls[0] == "faculty_contracts"

    def test_create_proceeds_when_guard_passes(self):
        payload = _make_payload()
        new_row = {
            "id": 1, "tenant_id": TENANT_ID, "faculty_id": FACULTY_ID,
            "course_code": "CS-101", "course_title": "Intro to CS",
            "department_id": DEPT_ID, "term_id": "2026-fall", "status": "draft",
        }

        def list_side(entity, tenant_id):
            if entity == "faculty_contracts":
                return [_active_contract()]
            if entity == "syllabi":
                return []  # no existing → cap not exceeded
            if entity == "syllabus_review_backlogs":
                return []
            return []

        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant", side_effect=list_side):
            with patch("app.modules.syllabus_governance.service.create_entity_for_tenant", return_value=new_row):
                with patch("app.modules.syllabus_governance.service.log_admin_action"):
                    result = svc.create_syllabus(TENANT_ID, payload, "actor-1")
        assert result.faculty_id == FACULTY_ID


# ---------------------------------------------------------------------------
# 7. Cap enforcement (department max active syllabi)
# ---------------------------------------------------------------------------

class TestCapEnforcement:
    def test_cap_exceeded_raises_value_error(self):
        payload = _make_payload(department_id="cs")
        cap = svc._DEPT_MAX_ACTIVE_SYLLABI["cs"]  # 30
        existing_syllabi = [
            {"department_id": "cs", "status": "draft"}
            for _ in range(cap)
        ]

        def list_side(entity, tenant_id):
            if entity == "faculty_contracts":
                return [_active_contract()]
            if entity == "syllabi":
                return existing_syllabi
            return []

        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant", side_effect=list_side):
            with pytest.raises(ValueError, match="cap"):
                svc.create_syllabus(TENANT_ID, payload, "actor-1")

    def test_cap_not_exceeded_allows(self):
        payload = _make_payload(department_id="cs")
        new_row = {
            "id": 5, "tenant_id": TENANT_ID, "faculty_id": FACULTY_ID,
            "course_code": "CS-101", "course_title": "Intro to CS",
            "department_id": "cs", "term_id": "2026-fall", "status": "draft",
        }

        def list_side(entity, tenant_id):
            if entity == "faculty_contracts":
                return [_active_contract()]
            if entity == "syllabi":
                return [{"department_id": "cs", "status": "draft"}]  # 1 < 30
            if entity == "syllabus_review_backlogs":
                return []
            return []

        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant", side_effect=list_side):
            with patch("app.modules.syllabus_governance.service.create_entity_for_tenant", return_value=new_row):
                with patch("app.modules.syllabus_governance.service.log_admin_action"):
                    result = svc.create_syllabus(TENANT_ID, payload, "actor-1")
        assert result is not None

    def test_inactive_syllabi_not_counted_toward_cap(self):
        payload = _make_payload(department_id="cs")
        cap = svc._DEPT_MAX_ACTIVE_SYLLABI["cs"]
        # Fill with approved syllabi (not in _ACTIVE_SYLLABUS_STATUSES)
        inactive_syllabi = [{"department_id": "cs", "status": "approved"} for _ in range(cap + 5)]
        new_row = {
            "id": 99, "tenant_id": TENANT_ID, "faculty_id": FACULTY_ID,
            "course_code": "CS-101", "course_title": "Intro",
            "department_id": "cs", "term_id": "2026-fall", "status": "draft",
        }

        def list_side(entity, tenant_id):
            if entity == "faculty_contracts":
                return [_active_contract()]
            if entity == "syllabi":
                return inactive_syllabi
            if entity == "syllabus_review_backlogs":
                return []
            return []

        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant", side_effect=list_side):
            with patch("app.modules.syllabus_governance.service.create_entity_for_tenant", return_value=new_row):
                with patch("app.modules.syllabus_governance.service.log_admin_action"):
                    result = svc.create_syllabus(TENANT_ID, payload, "actor-1")
        assert result is not None

    def test_default_cap_used_for_unknown_dept(self):
        payload = _make_payload(department_id="unknown_dept")
        cap = svc._DEPT_MAX_ACTIVE_SYLLABI["default"]
        existing = [{"department_id": "unknown_dept", "status": "draft"} for _ in range(cap)]

        def list_side(entity, tenant_id):
            if entity == "faculty_contracts":
                return [_active_contract()]
            if entity == "syllabi":
                return existing
            return []

        with patch("app.modules.syllabus_governance.service.list_entities_for_tenant", side_effect=list_side):
            with pytest.raises(ValueError, match="cap"):
                svc.create_syllabus(TENANT_ID, payload, "actor-1")


# ---------------------------------------------------------------------------
# 8. Router structure
# ---------------------------------------------------------------------------

class TestRouterStructure:
    def _read_router_source(self) -> str:
        return (Path(__file__).resolve().parents[1] / "app/modules/syllabus_governance/router.py").read_text()

    def test_router_imports_svc_module(self):
        source = self._read_router_source()
        assert "import app.modules.syllabus_governance.service as _svc" in source

    def test_router_no_direct_function_imports(self):
        source = self._read_router_source()
        assert "from app.modules.syllabus_governance.service import" not in source

    def test_router_has_domain_validation_error_import(self):
        source = self._read_router_source()
        assert "DomainValidationError" in source

    def test_router_uses_svc_create_syllabus(self):
        source = self._read_router_source()
        assert "_svc.create_syllabus" in source

    def test_router_uses_svc_list_syllabi(self):
        source = self._read_router_source()
        assert "_svc.list_syllabi" in source

    def test_router_uses_svc_update_syllabus(self):
        source = self._read_router_source()
        assert "_svc.update_syllabus" in source

    def test_router_has_post_route(self):
        router_mod = importlib.import_module("app.modules.syllabus_governance.router")
        paths = [r.path for r in router_mod.router.routes]
        assert any(p == "" or p == "/" for p in paths) or any("syllabus" in p or p == "" for p in paths)

    def test_router_post_catches_domain_validation_error(self):
        source = self._read_router_source()
        assert "except (ValueError, DomainValidationError)" in source

    def test_router_maps_to_422(self):
        source = self._read_router_source()
        assert "status_code=422" in source

    def test_router_has_approval_workflow_route(self):
        router_mod = importlib.import_module("app.modules.syllabus_governance.router")
        paths = [r.path for r in router_mod.router.routes]
        assert any("approval-workflow" in p for p in paths)

    def test_router_has_get_and_put_routes(self):
        router_mod = importlib.import_module("app.modules.syllabus_governance.router")
        paths = [r.path for r in router_mod.router.routes]
        assert any("{syllabus_id}" in p for p in paths)
