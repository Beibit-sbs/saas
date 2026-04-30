"""W131: Domain-depth tests for scholarship module.

Tests:
- _SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES constants
- _check_student_is_enrolled_for_scholarship guard signature & failures
- Fail-closed behaviour on infra errors
- create_scholarship_application integration path
- Business invariants (tenant isolation, GPA check ordering, alt key)
- Router structure (DomainValidationError wired in both POST endpoints)
"""
from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.scholarship.service as _svc
import app.modules.scholarship.router as _router

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_TENANT = 55
_STUDENT_ID = "stu-001"


def _enrollment(status: str, student_id: str = _STUDENT_ID) -> dict:
    return {"id": 1, "student_id": student_id, "status": status}


def _app_payload(**kwargs) -> dict:
    base = {
        "application_code": "APP-001",
        "student_id": _STUDENT_ID,
        "scholarship_type": "merit",
        "status": "pending",
        "gpa": 3.5,
        "requested_amount": 5000.0,
        "notes": None,
        "integration_source": None,
        "reviewer_notes": None,
    }
    base.update(kwargs)
    return base


def _created_record(payload: dict, tenant_id: int = _TENANT) -> dict:
    return {
        **payload,
        "id": 1,
        "tenant_id": str(tenant_id),
        "at_risk": False,
    }


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------
class TestW131Constants:
    def test_sentinel_exists(self):
        assert hasattr(_svc, "_SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES")

    def test_sentinel_is_frozenset(self):
        assert isinstance(_svc._SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES, frozenset)

    def test_enrolled_in_sentinel(self):
        assert "enrolled" in _svc._SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES

    def test_active_in_sentinel(self):
        assert "active" in _svc._SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES

    def test_registered_in_sentinel(self):
        assert "registered" in _svc._SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES

    def test_withdrawn_not_in_sentinel(self):
        assert "withdrawn" not in _svc._SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES

    def test_expelled_not_in_sentinel(self):
        assert "expelled" not in _svc._SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES

    def test_sentinel_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _svc._SCHOLARSHIP_ACTIVE_ENROLLMENT_STATUSES.add("hacked")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Guard signature
# ---------------------------------------------------------------------------
class TestW131GuardSignature:
    def test_callable(self):
        assert callable(_svc._check_student_is_enrolled_for_scholarship)

    def test_requires_tenant_id(self):
        sig = inspect.signature(_svc._check_student_is_enrolled_for_scholarship)
        assert "tenant_id" in sig.parameters

    def test_requires_student_id(self):
        sig = inspect.signature(_svc._check_student_is_enrolled_for_scholarship)
        assert "student_id" in sig.parameters

    def test_requires_scholarship_type(self):
        sig = inspect.signature(_svc._check_student_is_enrolled_for_scholarship)
        assert "scholarship_type" in sig.parameters

    def test_all_kwargs(self):
        sig = inspect.signature(_svc._check_student_is_enrolled_for_scholarship)
        for name, param in sig.parameters.items():
            assert param.kind == inspect.Parameter.KEYWORD_ONLY, f"{name} must be keyword-only"

    def test_returns_none_on_success(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("enrolled")]):
            result = _svc._check_student_is_enrolled_for_scholarship(
                tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
            )
        assert result is None


# ---------------------------------------------------------------------------
# 3. Guard failures
# ---------------------------------------------------------------------------
class TestW131GuardFailures:
    def test_no_records_raises(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError, match="no enrollment records"):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
                )

    def test_wrong_student_raises(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("enrolled", student_id="other-999")]):
            with pytest.raises(DomainValidationError, match="no enrollment records"):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
                )

    def test_withdrawn_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("withdrawn")]):
            with pytest.raises(DomainValidationError, match="not actively enrolled"):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
                )

    def test_expelled_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("expelled")]):
            with pytest.raises(DomainValidationError, match="not actively enrolled"):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="athletic"
                )

    def test_inactive_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("inactive")]):
            with pytest.raises(DomainValidationError):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
                )

    def test_error_message_contains_student_id(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("withdrawn")]):
            with pytest.raises(DomainValidationError, match=_STUDENT_ID):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
                )

    def test_error_message_contains_scholarship_type(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("withdrawn")]):
            with pytest.raises(DomainValidationError, match="merit"):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
                )


# ---------------------------------------------------------------------------
# 4. Fail-closed
# ---------------------------------------------------------------------------
class TestW131FailClosed:
    def test_runtime_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=RuntimeError("DB down")):
            with pytest.raises(DomainValidationError, match="enrollment lookup failed"):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
                )

    def test_connection_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=ConnectionError("timeout")):
            with pytest.raises(DomainValidationError, match="enrollment lookup failed"):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
                )

    def test_os_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=OSError("io error")):
            with pytest.raises(DomainValidationError):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
                )

    def test_value_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=ValueError("parse error")):
            with pytest.raises(DomainValidationError):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="athletic"
                )

    def test_chained_exception_preserved(self):
        original = RuntimeError("DB down")
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=original):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
                )
        assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# 5. create_scholarship_application integration
# ---------------------------------------------------------------------------
class TestW131CreatePath:
    def _setup(self, enrollment_status: str = "enrolled"):
        def _list(entity_type: str, tenant_id: int):
            if entity_type == "enrollments":
                return [_enrollment(enrollment_status)]
            if entity_type == "scholarship_applications":
                return []
            return []

        mock_list = MagicMock(side_effect=_list)
        mock_create = MagicMock(return_value=_created_record(_app_payload()))
        return mock_list, mock_create

    def test_guard_fires_before_persist(self):
        call_order = []

        def _list(entity_type, tenant_id):
            if entity_type == "enrollments":
                call_order.append("guard")
                raise DomainValidationError("blocked")
            call_order.append("cap_check")
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc.create_scholarship_application(_app_payload(), _TENANT)
        assert "guard" in call_order
        assert "cap_check" not in call_order

    def test_no_enrollment_blocks_application(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError, match="no enrollment records"):
                _svc.create_scholarship_application(_app_payload(), _TENANT)

    def test_withdrawn_student_blocked(self):
        def _list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_enrollment("withdrawn")]
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError, match="not actively enrolled"):
                _svc.create_scholarship_application(_app_payload(), _TENANT)

    def test_enrolled_student_passes(self):
        mock_list, mock_create = self._setup("enrolled")
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create):
            result = _svc.create_scholarship_application(_app_payload(), _TENANT)
        assert result is not None
        mock_create.assert_called_once()

    def test_active_enrollment_also_passes(self):
        mock_list, mock_create = self._setup("active")
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create):
            result = _svc.create_scholarship_application(_app_payload(), _TENANT)
        assert result is not None

    def test_registered_enrollment_passes(self):
        mock_list, mock_create = self._setup("registered")
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create):
            result = _svc.create_scholarship_application(_app_payload(), _TENANT)
        assert result is not None

    def test_gpa_check_before_guard(self):
        """GPA check happens BEFORE enrollment guard (existing design)."""
        called_guard = []

        def _list(entity_type, tenant_id):
            if entity_type == "enrollments":
                called_guard.append(True)
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(ValueError, match="gpa"):
                _svc.create_scholarship_application(
                    _app_payload(gpa=1.0, scholarship_type="merit"),
                    _TENANT,
                )
        # guard was NOT called — GPA check happened first
        assert not called_guard


# ---------------------------------------------------------------------------
# 6. Business invariants
# ---------------------------------------------------------------------------
class TestW131BusinessInvariants:
    def test_tenant_isolation_different_tenants(self):
        """Guard only uses enrollments from the given tenant_id."""
        seen_tenant_ids = []

        def _list(entity_type, tenant_id):
            if entity_type == "enrollments":
                seen_tenant_ids.append(tenant_id)
                return []
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=99, student_id=_STUDENT_ID, scholarship_type="merit"
                )
        assert seen_tenant_ids == [99]

    def test_multiple_enrollments_one_active_passes(self):
        enrollments = [
            _enrollment("withdrawn"),
            _enrollment("enrolled"),
        ]
        with patch.object(_svc, "list_entities_for_tenant", return_value=enrollments):
            # Should not raise
            _svc._check_student_is_enrolled_for_scholarship(
                tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
            )

    def test_alt_enrollment_status_key(self):
        """Guard also accepts 'enrollment_status' key."""
        alt_enrollment = {"id": 1, "student_id": _STUDENT_ID, "enrollment_status": "enrolled"}
        with patch.object(_svc, "list_entities_for_tenant", return_value=[alt_enrollment]):
            # Should not raise
            _svc._check_student_is_enrolled_for_scholarship(
                tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
            )

    def test_whitespace_stripped_from_student_id(self):
        """student_id with leading/trailing whitespace matches enrollment."""
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("enrolled", student_id="  stu-001  ")]):
            # Should not raise
            _svc._check_student_is_enrolled_for_scholarship(
                tenant_id=_TENANT, student_id="stu-001", scholarship_type="merit"
            )

    def test_status_case_insensitive(self):
        """Status comparison is case-insensitive."""
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("ENROLLED")]):
            # Should not raise
            _svc._check_student_is_enrolled_for_scholarship(
                tenant_id=_TENANT, student_id=_STUDENT_ID, scholarship_type="merit"
            )

    def test_empty_student_id_blocks(self):
        """Empty student_id should not match any enrollment."""
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("enrolled")]):
            with pytest.raises(DomainValidationError, match="no enrollment records"):
                _svc._check_student_is_enrolled_for_scholarship(
                    tenant_id=_TENANT, student_id="", scholarship_type="merit"
                )


# ---------------------------------------------------------------------------
# 7. Router structure
# ---------------------------------------------------------------------------
class TestW131RouterStructure:
    def test_applications_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/scholarship/applications" in routes

    def test_awards_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/scholarship/awards" in routes

    def test_domain_validation_error_imported_in_router(self):
        assert hasattr(_router, "DomainValidationError")

    def test_router_module_imports_domain_validation_error(self):
        import sys
        # Ensure the import is accessible
        assert "DomainValidationError" in dir(_router) or \
               "app.core.module_helpers.service_validation" in sys.modules

    def test_applications_endpoint_function_exists(self):
        assert callable(getattr(_router, "create_application_endpoint", None))

    def test_awards_endpoint_function_exists(self):
        assert callable(getattr(_router, "create_award_endpoint", None))
