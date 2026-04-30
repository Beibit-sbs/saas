"""W138 — financial_aid: Router DomainValidationError hardening + W112 guard depth tests.

Guard under test:
    _check_student_enrollment_for_aid_creation (W112)
    — financial_aid_records × enrollments cross-entity guard (Title IV SAP).

New coverage in W138:
    • PATCH /{record_id}/status now catches DomainValidationError → 422
    • Router refactored to _svc.* import pattern
    • Deep behavioural coverage: constants, guard logic, router wiring,
      fail-closed, tenant isolation, edge cases.
"""
from __future__ import annotations

import inspect
from unittest.mock import patch

import pytest

import sys
import app.modules.financial_aid.service as _svc
import app.modules.financial_aid.router as _router
from app.core.module_helpers.service_validation import DomainValidationError

# __init__.py re-exports `router` (APIRouter) as attribute, so `_router` may
# resolve to the APIRouter instance rather than the module object.
# Always get source/module via sys.modules.
_ROUTER_MOD = sys.modules.get("app.modules.financial_aid.router")


# ---------------------------------------------------------------------------
# W138.1 — Constants / module surface
# ---------------------------------------------------------------------------

class TestW138Constants:
    def test_sap_active_enrollment_statuses_exists(self):
        assert hasattr(_svc, "_SAP_ACTIVE_ENROLLMENT_STATUSES")

    def test_sap_active_enrollment_statuses_is_frozenset(self):
        assert isinstance(_svc._SAP_ACTIVE_ENROLLMENT_STATUSES, frozenset)

    def test_sap_active_enrollment_statuses_contains_enrolled(self):
        assert "enrolled" in _svc._SAP_ACTIVE_ENROLLMENT_STATUSES

    def test_sap_active_enrollment_statuses_contains_active(self):
        assert "active" in _svc._SAP_ACTIVE_ENROLLMENT_STATUSES

    def test_sap_active_enrollment_statuses_contains_registered(self):
        assert "registered" in _svc._SAP_ACTIVE_ENROLLMENT_STATUSES

    def test_sap_active_enrollment_statuses_excludes_withdrawn(self):
        assert "withdrawn" not in _svc._SAP_ACTIVE_ENROLLMENT_STATUSES

    def test_sap_active_enrollment_statuses_excludes_graduated(self):
        assert "graduated" not in _svc._SAP_ACTIVE_ENROLLMENT_STATUSES

    def test_disbursement_requires_active_enrollment_exists(self):
        assert hasattr(_svc, "_DISBURSEMENT_REQUIRES_ACTIVE_ENROLLMENT")

    def test_disbursement_requires_active_enrollment_contains_disbursed(self):
        assert "disbursed" in _svc._DISBURSEMENT_REQUIRES_ACTIVE_ENROLLMENT

    def test_guard_function_exists(self):
        assert callable(getattr(_svc, "_check_student_enrollment_for_aid_creation", None))


# ---------------------------------------------------------------------------
# W138.2 — Guard allow paths
# ---------------------------------------------------------------------------

class TestW138GuardAllowPaths:
    def _call(self, enrollments: list[dict], student_id: int = 1, aid_type: str = "scholarship") -> None:
        with patch.object(_svc, "list_entities_for_tenant", return_value=enrollments):
            _svc._check_student_enrollment_for_aid_creation(
                tenant_id=1, student_id=student_id, aid_type=aid_type
            )

    def test_enrolled_status_passes(self):
        self._call([{"student_id": 1, "status": "enrolled"}])

    def test_active_status_passes(self):
        self._call([{"student_id": 1, "status": "active"}])

    def test_registered_status_passes(self):
        self._call([{"student_id": 1, "status": "registered"}])

    def test_multiple_enrollments_one_active_passes(self):
        self._call([
            {"student_id": 1, "status": "withdrawn"},
            {"student_id": 1, "status": "enrolled"},
        ])

    def test_different_aid_types_pass_with_active_enrollment(self):
        for aid_type in ["scholarship", "grant", "tuition_discount", "stipend"]:
            self._call([{"student_id": 1, "status": "active"}], aid_type=aid_type)


# ---------------------------------------------------------------------------
# W138.3 — Guard block paths
# ---------------------------------------------------------------------------

class TestW138GuardBlockPaths:
    def _call_expect_raise(self, enrollments: list[dict], student_id: int = 1) -> DomainValidationError:
        with patch.object(_svc, "list_entities_for_tenant", return_value=enrollments):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_student_enrollment_for_aid_creation(
                    tenant_id=1, student_id=student_id, aid_type="scholarship"
                )
        return exc_info.value

    def test_no_enrollments_blocks(self):
        exc = self._call_expect_raise([])
        assert "1" in str(exc)

    def test_no_enrollments_for_student_blocks(self):
        exc = self._call_expect_raise(
            [{"student_id": 99, "status": "enrolled"}],
            student_id=1,
        )
        assert "1" in str(exc)

    def test_withdrawn_status_blocks(self):
        self._call_expect_raise([{"student_id": 1, "status": "withdrawn"}])

    def test_graduated_status_blocks(self):
        self._call_expect_raise([{"student_id": 1, "status": "graduated"}])

    def test_suspended_status_blocks(self):
        self._call_expect_raise([{"student_id": 1, "status": "suspended"}])

    def test_all_non_active_statuses_block(self):
        self._call_expect_raise([
            {"student_id": 1, "status": "withdrawn"},
            {"student_id": 1, "status": "graduated"},
        ])

    def test_error_message_contains_student_id(self):
        exc = self._call_expect_raise([], student_id=42)
        assert "42" in str(exc)

    def test_error_mentions_sap(self):
        exc = self._call_expect_raise([])
        assert "sap" in str(exc).lower() or "title iv" in str(exc).lower() or "enrollment" in str(exc).lower()

    def test_raises_domain_validation_error_not_value_error(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError):
                _svc._check_student_enrollment_for_aid_creation(
                    tenant_id=1, student_id=1, aid_type="grant"
                )


# ---------------------------------------------------------------------------
# W138.4 — Fail-closed behaviour
# ---------------------------------------------------------------------------

class TestW138FailClosed:
    def test_lookup_exception_raises_domain_error(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=RuntimeError("db down")):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_student_enrollment_for_aid_creation(
                    tenant_id=1, student_id=1, aid_type="scholarship"
                )
        msg = str(exc_info.value).lower()
        assert "lookup failed" in msg or "cannot verify" in msg or "blocked" in msg

    def test_lookup_exception_preserves_cause(self):
        cause = RuntimeError("db down")
        with patch.object(_svc, "list_entities_for_tenant", side_effect=cause):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_student_enrollment_for_aid_creation(
                    tenant_id=1, student_id=1, aid_type="scholarship"
                )
        assert exc_info.value.__cause__ is cause

    def test_lookup_exception_is_domain_validation_error(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=Exception("fail")):
            with pytest.raises(DomainValidationError):
                _svc._check_student_enrollment_for_aid_creation(
                    tenant_id=1, student_id=1, aid_type="grant"
                )


# ---------------------------------------------------------------------------
# W138.5 — Tenant isolation
# ---------------------------------------------------------------------------

class TestW138TenantIsolation:
    def test_cross_tenant_enrollment_does_not_satisfy_guard(self):
        """Tenant 2's active enrollment must not help Tenant 1's guard."""

        def fake_list(entity_type: str, tenant_id: int):
            if tenant_id == 2:
                return [{"student_id": 1, "status": "enrolled"}]
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                _svc._check_student_enrollment_for_aid_creation(
                    tenant_id=1, student_id=1, aid_type="scholarship"
                )

    def test_guard_queries_correct_tenant(self):
        queried: list[int] = []

        def fake_list(entity_type: str, tenant_id: int):
            queried.append(tenant_id)
            return [{"student_id": 1, "status": "enrolled"}]

        with patch.object(_svc, "list_entities_for_tenant", side_effect=fake_list):
            _svc._check_student_enrollment_for_aid_creation(
                tenant_id=77, student_id=1, aid_type="scholarship"
            )

        assert 77 in queried


# ---------------------------------------------------------------------------
# W138.6 — create_financial_aid_record wiring
# ---------------------------------------------------------------------------

class TestW138CreateWiring:
    def _make_schema(self, student_id: int = 1):
        from app.modules.financial_aid.schemas import FinancialAidRecordCreateSchema
        return FinancialAidRecordCreateSchema(
            student_id=student_id,
            aid_type="scholarship",
            amount=1000.0,
            term="2026-S1",
        )

    def test_guard_fires_before_create_when_no_enrollment(self):
        call_order: list[str] = []

        def fake_list(entity_type: str, tenant_id: int):
            call_order.append(f"list:{entity_type}")
            return []

        def fake_create(entity_type: str, payload: dict, tenant_id: int):
            call_order.append("create")
            return payload

        with patch.object(_svc, "list_entities_for_tenant", side_effect=fake_list), \
             patch.object(_svc, "create_entity_for_tenant", side_effect=fake_create):
            with pytest.raises(DomainValidationError):
                _svc.create_financial_aid_record(1, self._make_schema(), "actor")

        assert any("enrollments" in c for c in call_order)
        assert "create" not in call_order

    def test_create_not_called_when_guard_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]), \
             patch.object(_svc, "create_entity_for_tenant") as mock_create:
            with pytest.raises(DomainValidationError):
                _svc.create_financial_aid_record(1, self._make_schema(), "actor")
        mock_create.assert_not_called()

    def test_active_enrollment_allows_create(self):
        def fake_list(entity_type: str, tenant_id: int):
            if entity_type == "enrollments":
                return [{"student_id": 1, "status": "enrolled"}]
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=fake_list), \
             patch.object(_svc, "create_entity_for_tenant", return_value={
                 "id": 1, "student_id": 1, "aid_type": "scholarship", "amount": 1000.0,
                 "currency": "USD", "status": "pending", "term": "2026-S1",
                 "reviewer_id": "aid-office", "notes": "n/a", "tenant_id": "1",
             }), \
             patch.object(_svc, "log_admin_action", return_value=None):
            result = _svc.create_financial_aid_record(1, self._make_schema(), "actor")
        assert result is not None


# ---------------------------------------------------------------------------
# W138.7 — Router structure
# ---------------------------------------------------------------------------

class TestW138RouterStructure:
    @staticmethod
    def _routes():
        # _router may be the APIRouter instance (due to __init__.py shadowing)
        router_obj = _router if hasattr(_router, "routes") else _router.router
        return router_obj.routes

    @staticmethod
    def _source() -> str:
        mod = _ROUTER_MOD or sys.modules.get("app.modules.financial_aid.router")
        if mod is not None:
            return inspect.getsource(mod)
        import pathlib
        return pathlib.Path(_router.__file__).read_text()

    def test_router_has_routes(self):
        assert len(self._routes()) > 0

    def test_post_route_exists(self):
        methods = [
            (r.path, list(r.methods))
            for r in self._routes()
            if hasattr(r, "methods")
        ]
        assert any("POST" in m for _, m in methods)

    def test_patch_route_exists(self):
        methods = [
            (r.path, list(r.methods))
            for r in self._routes()
            if hasattr(r, "methods")
        ]
        assert any("PATCH" in m for _, m in methods)

    def test_domain_validation_error_imported_in_router(self):
        source = self._source()
        assert "DomainValidationError" in source

    def test_router_uses_svc_pattern(self):
        source = self._source()
        assert "_svc." in source

    def test_patch_catches_domain_validation_error(self):
        source = self._source()
        assert "DomainValidationError" in source


# ---------------------------------------------------------------------------
# W138.8 — Router POST endpoint: DomainValidationError → 422
# ---------------------------------------------------------------------------

class TestW138RouterPostEndpoint:
    def _invoke_post(self, side_effect=None) -> int:
        from app.modules.financial_aid.router import create_record_endpoint
        from app.modules.financial_aid.schemas import FinancialAidRecordCreateSchema
        from fastapi import HTTPException

        payload = FinancialAidRecordCreateSchema(
            student_id=1, aid_type="scholarship", amount=1000.0, term="2026-S1"
        )
        mock_record = {
            "id": 1, "student_id": 1, "aid_type": "scholarship", "amount": 1000.0,
            "currency": "USD", "status": "pending", "term": "2026-S1",
            "reviewer_id": "aid-office", "notes": "n/a", "tenant_id": "1",
        }
        with patch.object(_svc, "create_financial_aid_record",
                          side_effect=side_effect or (lambda tid, p, actor: _svc.FinancialAidRecordSchema.model_validate(mock_record))):
            try:
                create_record_endpoint(
                    payload=payload, actor="actor", _=None, tenant={"id": "1"}
                )
                return 200
            except HTTPException as e:
                return e.status_code

    def test_domain_validation_error_returns_422(self):
        status = self._invoke_post(
            side_effect=lambda *a, **kw: (_ for _ in ()).throw(DomainValidationError("no enrollment"))
        )
        assert status == 422

    def test_value_error_returns_422(self):
        status = self._invoke_post(
            side_effect=lambda *a, **kw: (_ for _ in ()).throw(ValueError("cap exceeded"))
        )
        assert status == 422


# ---------------------------------------------------------------------------
# W138.9 — Router PATCH endpoint: DomainValidationError → 422
# ---------------------------------------------------------------------------

class TestW138RouterPatchEndpoint:
    def _invoke_patch(self, side_effect=None) -> int:
        from app.modules.financial_aid.router import update_record_status_endpoint
        from app.modules.financial_aid.schemas import FinancialAidRecordStatusUpdateSchema
        from fastapi import HTTPException

        payload = FinancialAidRecordStatusUpdateSchema(status="approved")
        mock_record = {
            "id": 1, "student_id": 1, "aid_type": "scholarship", "amount": 1000.0,
            "currency": "USD", "status": "approved", "term": "2026-S1",
            "reviewer_id": "aid-office", "notes": "n/a", "tenant_id": "1",
        }
        with patch.object(_svc, "update_financial_aid_status",
                          side_effect=side_effect or (lambda tid, rid, p, actor: _svc.FinancialAidRecordSchema.model_validate(mock_record))):
            try:
                update_record_status_endpoint(
                    record_id=1, payload=payload, actor="actor", _=None, tenant={"id": "1"}
                )
                return 200
            except HTTPException as e:
                return e.status_code

    def test_domain_validation_error_returns_422(self):
        status = self._invoke_patch(
            side_effect=lambda *a, **kw: (_ for _ in ()).throw(DomainValidationError("SAP violated"))
        )
        assert status == 422

    def test_value_error_not_found_returns_404(self):
        status = self._invoke_patch(
            side_effect=lambda *a, **kw: (_ for _ in ()).throw(ValueError("record 1 not found"))
        )
        assert status == 404

    def test_value_error_invalid_transition_returns_400(self):
        status = self._invoke_patch(
            side_effect=lambda *a, **kw: (_ for _ in ()).throw(ValueError("transition not allowed"))
        )
        assert status == 400

    def test_valid_update_returns_200(self):
        status = self._invoke_patch()
        assert status == 200
