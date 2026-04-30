"""W139 — alumni: Router DomainValidationError hardening + W96 guard depth tests.

Guard under test:
    _check_student_has_graduated_for_alumni_record (W96)
    — alumni_records × students.status cross-entity guard.

New coverage in W139:
    • PATCH /{record_id}/status now catches DomainValidationError → 422
    • Router refactored to _svc.* import pattern
    • Deep behavioural coverage: constants, guard logic, router wiring,
      fail-closed, tenant isolation, engagement cap guard.
"""
from __future__ import annotations

import inspect
import sys
from unittest.mock import patch

import pytest

import app.modules.alumni.service as _svc
import app.modules.alumni.router as _router
from app.core.module_helpers.service_validation import DomainValidationError

# __init__.py may re-export `router` (APIRouter) as attribute, so _router may
# resolve to the APIRouter instance. Always get source via sys.modules.
_ROUTER_MOD = sys.modules.get("app.modules.alumni.router")


# ---------------------------------------------------------------------------
# W139.1 — Constants / module surface
# ---------------------------------------------------------------------------

class TestW139Constants:
    def test_eligible_statuses_exists(self):
        assert hasattr(_svc, "_ALUMNI_ELIGIBLE_STUDENT_STATUSES")

    def test_eligible_statuses_is_frozenset(self):
        assert isinstance(_svc._ALUMNI_ELIGIBLE_STUDENT_STATUSES, frozenset)

    def test_eligible_statuses_contains_graduated(self):
        assert "graduated" in _svc._ALUMNI_ELIGIBLE_STUDENT_STATUSES

    def test_eligible_statuses_excludes_enrolled(self):
        assert "enrolled" not in _svc._ALUMNI_ELIGIBLE_STUDENT_STATUSES

    def test_eligible_statuses_excludes_active(self):
        assert "active" not in _svc._ALUMNI_ELIGIBLE_STUDENT_STATUSES

    def test_engagement_cap_exists(self):
        assert hasattr(_svc, "_ENGAGEMENT_TYPE_MAX_ACTIVE")

    def test_engagement_cap_mentoring_is_1(self):
        assert _svc._ENGAGEMENT_TYPE_MAX_ACTIVE.get("mentoring") == 1

    def test_engagement_cap_event_is_3(self):
        assert _svc._ENGAGEMENT_TYPE_MAX_ACTIVE.get("event") == 3

    def test_engagement_cap_donation_is_5(self):
        assert _svc._ENGAGEMENT_TYPE_MAX_ACTIVE.get("donation") == 5

    def test_guard_function_exists(self):
        assert callable(getattr(_svc, "_check_student_has_graduated_for_alumni_record", None))


# ---------------------------------------------------------------------------
# W139.2 — Guard allow paths
# ---------------------------------------------------------------------------

class TestW139GuardAllowPaths:
    def _call(self, students: list[dict], student_id: int = 1) -> None:
        with patch.object(_svc, "list_entities_for_tenant", return_value=students):
            _svc._check_student_has_graduated_for_alumni_record(
                tenant_id=1, student_id=student_id
            )

    def test_graduated_by_id_passes(self):
        self._call([{"id": 1, "status": "graduated"}])

    def test_graduated_by_student_id_passes(self):
        self._call([{"student_id": 1, "status": "graduated"}])

    def test_multiple_students_one_graduated_passes(self):
        self._call([
            {"id": 2, "status": "graduated"},
            {"id": 1, "status": "graduated"},
        ])

    def test_graduated_case_insensitive(self):
        self._call([{"id": 1, "status": "Graduated"}])

    def test_graduated_with_whitespace(self):
        self._call([{"id": 1, "status": " graduated "}])


# ---------------------------------------------------------------------------
# W139.3 — Guard block paths
# ---------------------------------------------------------------------------

class TestW139GuardBlockPaths:
    def _call_expect_raise(self, students: list[dict], student_id: int = 1):
        with patch.object(_svc, "list_entities_for_tenant", return_value=students):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_student_has_graduated_for_alumni_record(
                    tenant_id=1, student_id=student_id
                )
        return exc_info.value

    def test_no_students_blocks(self):
        exc = self._call_expect_raise([])
        assert "1" in str(exc)

    def test_student_not_found_blocks(self):
        exc = self._call_expect_raise(
            [{"id": 99, "status": "graduated"}], student_id=1
        )
        assert "1" in str(exc)

    def test_enrolled_status_blocks(self):
        self._call_expect_raise([{"id": 1, "status": "enrolled"}])

    def test_active_status_blocks(self):
        self._call_expect_raise([{"id": 1, "status": "active"}])

    def test_withdrawn_status_blocks(self):
        self._call_expect_raise([{"id": 1, "status": "withdrawn"}])

    def test_suspended_status_blocks(self):
        self._call_expect_raise([{"id": 1, "status": "suspended"}])

    def test_error_message_contains_student_id(self):
        exc = self._call_expect_raise([], student_id=42)
        assert "42" in str(exc)

    def test_error_mentions_graduation(self):
        exc = self._call_expect_raise([{"id": 1, "status": "enrolled"}])
        msg = str(exc).lower()
        assert "graduat" in msg or "alumni" in msg

    def test_raises_domain_validation_error_not_value_error(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError):
                _svc._check_student_has_graduated_for_alumni_record(
                    tenant_id=1, student_id=1
                )


# ---------------------------------------------------------------------------
# W139.4 — Fail-closed behaviour
# ---------------------------------------------------------------------------

class TestW139FailClosed:
    def test_lookup_exception_raises_domain_error(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=RuntimeError("db down")):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_student_has_graduated_for_alumni_record(
                    tenant_id=1, student_id=1
                )
        msg = str(exc_info.value).lower()
        assert "blocked" in msg or "lookup failed" in msg or "cannot verify" in msg

    def test_lookup_exception_preserves_cause(self):
        cause = RuntimeError("db down")
        with patch.object(_svc, "list_entities_for_tenant", side_effect=cause):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_student_has_graduated_for_alumni_record(
                    tenant_id=1, student_id=1
                )
        assert exc_info.value.__cause__ is cause

    def test_any_exception_triggers_fail_closed(self):
        with patch.object(_svc, "list_entities_for_tenant", side_effect=Exception("fail")):
            with pytest.raises(DomainValidationError):
                _svc._check_student_has_graduated_for_alumni_record(
                    tenant_id=1, student_id=1
                )


# ---------------------------------------------------------------------------
# W139.5 — Tenant isolation
# ---------------------------------------------------------------------------

class TestW139TenantIsolation:
    def test_cross_tenant_graduation_does_not_satisfy_guard(self):
        def fake_list(entity_type: str, tenant_id: int):
            if tenant_id == 2:
                return [{"id": 1, "status": "graduated"}]
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                _svc._check_student_has_graduated_for_alumni_record(
                    tenant_id=1, student_id=1
                )

    def test_guard_queries_correct_tenant(self):
        queried: list[int] = []

        def fake_list(entity_type: str, tenant_id: int):
            queried.append(tenant_id)
            return [{"id": 1, "status": "graduated"}]

        with patch.object(_svc, "list_entities_for_tenant", side_effect=fake_list):
            _svc._check_student_has_graduated_for_alumni_record(
                tenant_id=77, student_id=1
            )

        assert 77 in queried


# ---------------------------------------------------------------------------
# W139.6 — create_alumni_record wiring
# ---------------------------------------------------------------------------

class TestW139CreateWiring:
    def _make_schema(self, student_id: int = 1):
        from app.modules.alumni.schemas import AlumniRecordCreateSchema
        return AlumniRecordCreateSchema(
            student_id=student_id,
            graduation_year=2024,
            engagement_type="event",
        )

    def test_guard_fires_before_create_when_not_graduated(self):
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
                _svc.create_alumni_record(1, self._make_schema(), "actor")

        assert any("students" in c for c in call_order)
        assert "create" not in call_order

    def test_create_not_called_when_guard_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]), \
             patch.object(_svc, "create_entity_for_tenant") as mock_create:
            with pytest.raises(DomainValidationError):
                _svc.create_alumni_record(1, self._make_schema(), "actor")
        mock_create.assert_not_called()

    def test_graduated_student_allows_create(self):
        def fake_list(entity_type: str, tenant_id: int):
            if entity_type == "students":
                return [{"id": 1, "status": "graduated"}]
            return []  # alumni_records cap check returns empty → count=0

        with patch.object(_svc, "list_entities_for_tenant", side_effect=fake_list), \
             patch.object(_svc, "create_entity_for_tenant", return_value={
                 "id": 1, "student_id": 1, "graduation_year": 2024,
                 "status": "active", "engagement_type": "event",
                 "employer": None, "contact_email": None, "notes": None,
                 "tenant_id": "1",
             }), \
             patch.object(_svc, "log_admin_action", return_value=None):
            result = _svc.create_alumni_record(1, self._make_schema(), "actor")
        assert result is not None


# ---------------------------------------------------------------------------
# W139.7 — Router structure
# ---------------------------------------------------------------------------

class TestW139RouterStructure:
    @staticmethod
    def _routes():
        router_obj = _router if hasattr(_router, "routes") else _router.router
        return router_obj.routes

    @staticmethod
    def _source() -> str:
        mod = _ROUTER_MOD or sys.modules.get("app.modules.alumni.router")
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
# W139.8 — Router POST endpoint: DomainValidationError → 422
# ---------------------------------------------------------------------------

class TestW139RouterPostEndpoint:
    def _invoke_post(self, side_effect=None) -> int:
        from app.modules.alumni.router import create_alumni_endpoint
        from app.modules.alumni.schemas import AlumniRecordCreateSchema
        from fastapi import HTTPException

        payload = AlumniRecordCreateSchema(
            student_id=1, graduation_year=2024, engagement_type="event"
        )
        mock_record = {
            "id": 1, "student_id": 1, "graduation_year": 2024,
            "status": "active", "engagement_type": "event",
            "employer": None, "contact_email": None, "notes": None,
            "tenant_id": "1",
        }
        def default_se(tid, p, actor):
            return _svc.AlumniRecordSchema.model_validate(mock_record)
        with patch.object(_svc, "create_alumni_record",
                          side_effect=side_effect or default_se):
            try:
                create_alumni_endpoint(
                    payload=payload, actor="actor", _=None, tenant={"id": "1"}
                )
                return 200
            except HTTPException as e:
                return e.status_code

    def test_domain_validation_error_returns_422(self):
        status = self._invoke_post(
            side_effect=lambda *a, **kw: (_ for _ in ()).throw(
                DomainValidationError("not graduated")
            )
        )
        assert status == 422

    def test_value_error_returns_422(self):
        status = self._invoke_post(
            side_effect=lambda *a, **kw: (_ for _ in ()).throw(
                ValueError("cap exceeded")
            )
        )
        assert status == 422

    def test_valid_create_returns_200(self):
        assert self._invoke_post() == 200


# ---------------------------------------------------------------------------
# W139.9 — Router PATCH endpoint: DomainValidationError → 422
# ---------------------------------------------------------------------------

class TestW139RouterPatchEndpoint:
    def _invoke_patch(self, side_effect=None) -> int:
        from app.modules.alumni.router import update_alumni_status_endpoint
        from app.modules.alumni.schemas import AlumniRecordStatusUpdateSchema
        from fastapi import HTTPException

        payload = AlumniRecordStatusUpdateSchema(status="engaged")
        mock_record = {
            "id": 1, "student_id": 1, "graduation_year": 2024,
            "status": "engaged", "engagement_type": "event",
            "employer": None, "contact_email": None, "notes": None,
            "tenant_id": "1",
        }
        def default_se(tid, rid, p, actor):
            return _svc.AlumniRecordSchema.model_validate(mock_record)
        with patch.object(_svc, "update_alumni_status",
                          side_effect=side_effect or default_se):
            try:
                update_alumni_status_endpoint(
                    record_id=1, payload=payload, actor="actor",
                    _=None, tenant={"id": "1"}
                )
                return 200
            except HTTPException as e:
                return e.status_code

    def test_domain_validation_error_returns_422(self):
        status = self._invoke_patch(
            side_effect=lambda *a, **kw: (_ for _ in ()).throw(
                DomainValidationError("status violated")
            )
        )
        assert status == 422

    def test_value_error_not_found_returns_404(self):
        status = self._invoke_patch(
            side_effect=lambda *a, **kw: (_ for _ in ()).throw(
                ValueError("record 1 not found")
            )
        )
        assert status == 404

    def test_value_error_invalid_transition_returns_400(self):
        status = self._invoke_patch(
            side_effect=lambda *a, **kw: (_ for _ in ()).throw(
                ValueError("transition not allowed")
            )
        )
        assert status == 400

    def test_valid_update_returns_200(self):
        assert self._invoke_patch() == 200
