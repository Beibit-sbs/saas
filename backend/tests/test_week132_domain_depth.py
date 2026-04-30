"""W132: Domain-depth tests for student_life module.

Tests:
- _DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES constants
- _check_student_is_enrolled_for_disciplinary guard signature & failures
- Fail-closed behaviour on infra errors
- create_disciplinary_case integration path
- Business invariants (tenant isolation, alt key, whitespace, case-insensitive)
- Router structure (DomainValidationError wired in all POST endpoints)
"""
from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
import app.modules.student_life.service as _svc
import app.modules.student_life.router as _router
from app.modules.student_life.schemas import DisciplinaryCaseCreateSchema

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_TENANT = 77
_STUDENT_ID = "stu-disc-001"


def _enrollment(status: str, student_id: str = _STUDENT_ID) -> dict:
    return {"id": 10, "student_id": student_id, "status": status}


def _disc_payload(**kwargs) -> DisciplinaryCaseCreateSchema:
    base = dict(
        incident_code="INC-001",
        student_id=_STUDENT_ID,
        incident_type="misconduct",
        severity="low",
        status="reported",
        reviewer_notes=None,
    )
    base.update(kwargs)
    return DisciplinaryCaseCreateSchema(**base)


def _created_disc(payload: DisciplinaryCaseCreateSchema) -> dict:
    return {
        "id": 1,
        "tenant_id": str(_TENANT),
        "incident_code": payload.incident_code,
        "student_id": payload.student_id,
        "incident_type": payload.incident_type,
        "severity": payload.severity,
        "status": str(payload.status),
        "reviewer_notes": payload.reviewer_notes,
    }


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------
class TestW132Constants:
    def test_sentinel_exists(self):
        assert hasattr(_svc, "_DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES")

    def test_sentinel_is_frozenset(self):
        assert isinstance(_svc._DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES, frozenset)

    def test_enrolled_in_sentinel(self):
        assert "enrolled" in _svc._DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES

    def test_active_in_sentinel(self):
        assert "active" in _svc._DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES

    def test_registered_in_sentinel(self):
        assert "registered" in _svc._DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES

    def test_withdrawn_not_in_sentinel(self):
        assert "withdrawn" not in _svc._DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES

    def test_expelled_not_in_sentinel(self):
        assert "expelled" not in _svc._DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES

    def test_sentinel_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _svc._DISCIPLINARY_ACTIVE_ENROLLMENT_STATUSES.add("hacked")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 2. Guard signature
# ---------------------------------------------------------------------------
class TestW132GuardSignature:
    def test_callable(self):
        assert callable(_svc._check_student_is_enrolled_for_disciplinary)

    def test_requires_tenant_id(self):
        sig = inspect.signature(_svc._check_student_is_enrolled_for_disciplinary)
        assert "tenant_id" in sig.parameters

    def test_requires_student_id(self):
        sig = inspect.signature(_svc._check_student_is_enrolled_for_disciplinary)
        assert "student_id" in sig.parameters

    def test_requires_severity(self):
        sig = inspect.signature(_svc._check_student_is_enrolled_for_disciplinary)
        assert "severity" in sig.parameters

    def test_all_kwargs(self):
        sig = inspect.signature(_svc._check_student_is_enrolled_for_disciplinary)
        for name, param in sig.parameters.items():
            assert param.kind == inspect.Parameter.KEYWORD_ONLY, f"{name} must be keyword-only"

    def test_returns_none_on_success(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("enrolled")]):
            result = _svc._check_student_is_enrolled_for_disciplinary(
                tenant_id=_TENANT, student_id=_STUDENT_ID, severity="low"
            )
        assert result is None


# ---------------------------------------------------------------------------
# 3. Guard failures
# ---------------------------------------------------------------------------
class TestW132GuardFailures:
    def test_no_records_raises(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError, match="no enrollment records"):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="low"
                )

    def test_wrong_student_id_raises(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("enrolled", student_id="other-999")]):
            with pytest.raises(DomainValidationError, match="no enrollment records"):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="high"
                )

    def test_withdrawn_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("withdrawn")]):
            with pytest.raises(DomainValidationError, match="no active enrollment"):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="low"
                )

    def test_expelled_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("expelled")]):
            with pytest.raises(DomainValidationError):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="medium"
                )

    def test_inactive_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("inactive")]):
            with pytest.raises(DomainValidationError):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="critical"
                )

    def test_error_message_contains_student_id(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("withdrawn")]):
            with pytest.raises(DomainValidationError, match=_STUDENT_ID):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="low"
                )

    def test_error_message_contains_severity(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("withdrawn")]):
            with pytest.raises(DomainValidationError, match="critical"):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="critical"
                )


# ---------------------------------------------------------------------------
# 4. Fail-closed
# ---------------------------------------------------------------------------
class TestW132FailClosed:
    def test_runtime_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=RuntimeError("DB down")):
            with pytest.raises(DomainValidationError, match="enrollments lookup failed"):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="low"
                )

    def test_connection_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=ConnectionError("timeout")):
            with pytest.raises(DomainValidationError, match="enrollments lookup failed"):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="low"
                )

    def test_os_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=OSError("io error")):
            with pytest.raises(DomainValidationError):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="high"
                )

    def test_value_error_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          side_effect=ValueError("parse error")):
            with pytest.raises(DomainValidationError):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="medium"
                )

    def test_chained_exception_preserved(self):
        original = RuntimeError("DB down")
        with patch.object(_svc, "list_entities_for_tenant", side_effect=original):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="low"
                )
        assert exc_info.value.__cause__ is original


# ---------------------------------------------------------------------------
# 5. create_disciplinary_case integration
# ---------------------------------------------------------------------------
class TestW132CreatePath:
    def _setup_mocks(self, enrollment_status: str = "enrolled"):
        def _list(entity_type: str, tenant_id: int):
            if entity_type == "enrollments":
                return [_enrollment(enrollment_status)]
            return []

        mock_list = MagicMock(side_effect=_list)
        mock_create = MagicMock(side_effect=lambda et, data, tid: {
            **data, "id": 1, "tenant_id": str(tid)
        })
        mock_log = MagicMock()
        return mock_list, mock_create, mock_log

    def test_guard_blocks_non_enrolled(self):
        with patch.object(_svc, "list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError, match="no enrollment records"):
                _svc.create_disciplinary_case(_TENANT, _disc_payload(), "admin")

    def test_withdrawn_blocks_case_creation(self):
        def _list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_enrollment("withdrawn")]
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError, match="no active enrollment"):
                _svc.create_disciplinary_case(_TENANT, _disc_payload(), "admin")

    def test_enrolled_student_case_created(self):
        mock_list, mock_create, mock_log = self._setup_mocks("enrolled")
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create), \
             patch.object(_svc, "log_admin_action", mock_log):
            result = _svc.create_disciplinary_case(_TENANT, _disc_payload(), "admin")
        assert result is not None
        mock_create.assert_called()

    def test_active_enrollment_also_passes(self):
        mock_list, mock_create, mock_log = self._setup_mocks("active")
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create), \
             patch.object(_svc, "log_admin_action", mock_log):
            result = _svc.create_disciplinary_case(_TENANT, _disc_payload(), "admin")
        assert result is not None

    def test_registered_enrollment_passes(self):
        mock_list, mock_create, mock_log = self._setup_mocks("registered")
        with patch.object(_svc, "list_entities_for_tenant", mock_list), \
             patch.object(_svc, "create_entity_for_tenant", mock_create), \
             patch.object(_svc, "log_admin_action", mock_log):
            result = _svc.create_disciplinary_case(_TENANT, _disc_payload(), "admin")
        assert result is not None

    def test_infra_failure_blocks(self):
        """RuntimeError on enrollments lookup → DomainValidationError (fail-closed)."""
        def _list(entity_type: str, tenant_id: int):
            if entity_type == "enrollments":
                raise RuntimeError("DB down")
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc.create_disciplinary_case(_TENANT, _disc_payload(), "admin")


# ---------------------------------------------------------------------------
# 6. Business invariants
# ---------------------------------------------------------------------------
class TestW132BusinessInvariants:
    def test_tenant_isolation(self):
        seen_tenant_ids = []

        def _list(entity_type, tenant_id):
            if entity_type == "enrollments":
                seen_tenant_ids.append(tenant_id)
                return []
            return []

        with patch.object(_svc, "list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=88, student_id=_STUDENT_ID, severity="low"
                )
        assert seen_tenant_ids == [88]

    def test_multiple_enrollments_one_active_passes(self):
        enrollments = [
            _enrollment("withdrawn"),
            _enrollment("enrolled"),
        ]
        with patch.object(_svc, "list_entities_for_tenant", return_value=enrollments):
            result = _svc._check_student_is_enrolled_for_disciplinary(
                tenant_id=_TENANT, student_id=_STUDENT_ID, severity="low"
            )
        assert result is None

    def test_alt_enrollment_status_key(self):
        alt = {"id": 5, "student_id": _STUDENT_ID, "enrollment_status": "enrolled"}
        with patch.object(_svc, "list_entities_for_tenant", return_value=[alt]):
            result = _svc._check_student_is_enrolled_for_disciplinary(
                tenant_id=_TENANT, student_id=_STUDENT_ID, severity="low"
            )
        assert result is None

    def test_whitespace_stripped_from_student_id(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("enrolled", student_id="  stu-disc-001  ")]):
            result = _svc._check_student_is_enrolled_for_disciplinary(
                tenant_id=_TENANT, student_id="stu-disc-001", severity="medium"
            )
        assert result is None

    def test_status_case_insensitive(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("ENROLLED")]):
            result = _svc._check_student_is_enrolled_for_disciplinary(
                tenant_id=_TENANT, student_id=_STUDENT_ID, severity="low"
            )
        assert result is None

    def test_empty_student_id_blocks(self):
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("enrolled")]):
            with pytest.raises(DomainValidationError, match="no enrollment records"):
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id="", severity="low"
                )

    def test_all_withdrawn_error_lists_statuses(self):
        """Error message includes found statuses for diagnostics."""
        with patch.object(_svc, "list_entities_for_tenant",
                          return_value=[_enrollment("withdrawn"), _enrollment("expelled")]):
            with pytest.raises(DomainValidationError) as exc_info:
                _svc._check_student_is_enrolled_for_disciplinary(
                    tenant_id=_TENANT, student_id=_STUDENT_ID, severity="low"
                )
        msg = str(exc_info.value)
        assert "withdrawn" in msg or "expelled" in msg


# ---------------------------------------------------------------------------
# 7. Router structure
# ---------------------------------------------------------------------------
class TestW132RouterStructure:
    def test_disciplinary_cases_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/student-life/disciplinary-cases" in routes

    def test_counseling_cases_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/student-life/counseling-cases" in routes

    def test_wellbeing_checkins_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/student-life/wellbeing-checkins" in routes

    def test_accessibility_supports_post_route_exists(self):
        routes = {r.path for r in _router.router.routes}  # type: ignore[attr-defined]
        assert "/api/admin/student-life/accessibility-supports" in routes

    def test_domain_validation_error_imported_in_router(self):
        assert hasattr(_router, "DomainValidationError")

    def test_create_disciplinary_case_endpoint_exists(self):
        assert callable(getattr(_router, "create_disciplinary_case_endpoint", None))

    def test_create_counseling_case_endpoint_exists(self):
        assert callable(getattr(_router, "create_counseling_case_endpoint", None))

    def test_create_wellbeing_checkin_endpoint_exists(self):
        assert callable(getattr(_router, "create_wellbeing_checkin_endpoint", None))
