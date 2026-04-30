"""W112 — Financial Aid × Enrollment cross-entity guard (Title IV SAP).

Business invariant: A financial aid record may only be created when the
student has at least one active enrollment (status: enrolled, active,
registered). Creating aid records for non-enrolled students violates
Title IV SAP (Satisfactory Academic Progress) requirements and exposes
the institution to federal financial aid audit failures.

Guard: _check_student_enrollment_for_aid_creation() — BEFORE create_entity_for_tenant()
Fail-closed: if enrollment lookup raises any exception → DomainValidationError.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError

STUDENT_ID = 42
AID_TYPE = "scholarship"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_enrollment(student_id: int, status: str, eid: int = 1) -> dict:
    return {
        "id": eid,
        "student_id": student_id,
        "course_id": 101,
        "status": status,
        "term": "2026-FALL",
    }


def _make_aid_payload(
    student_id: int = STUDENT_ID,
    aid_type: str = AID_TYPE,
    amount: float = 5000.0,
):
    from app.modules.financial_aid.schemas import FinancialAidRecordCreateSchema
    return FinancialAidRecordCreateSchema(
        student_id=student_id,
        aid_type=aid_type,
        amount=amount,
        currency="USD",
        term="2026-FALL",
    )


def _fake_create_entity(entity_type, data, tenant_id):
    return {"id": 77, **data}


# ===========================================================================
# GROUP 1 — Guard constant correctness
# ===========================================================================

class TestSapEnrollmentConstant:
    def test_constant_exists(self):
        import app.modules.financial_aid.service as svc
        assert hasattr(svc, "_SAP_ACTIVE_ENROLLMENT_STATUSES")

    def test_constant_is_frozenset(self):
        import app.modules.financial_aid.service as svc
        assert isinstance(svc._SAP_ACTIVE_ENROLLMENT_STATUSES, frozenset)

    def test_enrolled_in_constant(self):
        import app.modules.financial_aid.service as svc
        assert "enrolled" in svc._SAP_ACTIVE_ENROLLMENT_STATUSES

    def test_active_in_constant(self):
        import app.modules.financial_aid.service as svc
        assert "active" in svc._SAP_ACTIVE_ENROLLMENT_STATUSES

    def test_registered_in_constant(self):
        import app.modules.financial_aid.service as svc
        assert "registered" in svc._SAP_ACTIVE_ENROLLMENT_STATUSES

    def test_withdrawn_not_in_constant(self):
        import app.modules.financial_aid.service as svc
        assert "withdrawn" not in svc._SAP_ACTIVE_ENROLLMENT_STATUSES

    def test_dropped_not_in_constant(self):
        import app.modules.financial_aid.service as svc
        assert "dropped" not in svc._SAP_ACTIVE_ENROLLMENT_STATUSES

    def test_completed_not_in_constant(self):
        import app.modules.financial_aid.service as svc
        assert "completed" not in svc._SAP_ACTIVE_ENROLLMENT_STATUSES


# ===========================================================================
# GROUP 2 — Guard function exists and is wired before persist
# ===========================================================================

class TestGuardFunctionExists:
    def test_guard_function_exists(self):
        import app.modules.financial_aid.service as svc
        assert hasattr(svc, "_check_student_enrollment_for_aid_creation")

    def test_guard_function_is_callable(self):
        import app.modules.financial_aid.service as svc
        assert callable(svc._check_student_enrollment_for_aid_creation)

    def test_guard_fires_before_persist(self):
        """Guard must call before create_entity_for_tenant."""
        import app.modules.financial_aid.service as svc_mod
        call_order: list[str] = []

        def fake_guard(*, tenant_id, student_id, aid_type):
            call_order.append("guard")

        def fake_create(entity_type, data, tenant_id):
            call_order.append("persist")
            return {"id": 1, "status": "pending", **data}

        def fake_list(entity_type, tenant_id):
            return []

        with (
            patch.object(svc_mod, "_check_student_enrollment_for_aid_creation", fake_guard),
            patch("app.modules.financial_aid.service.create_entity_for_tenant", side_effect=fake_create),
            patch("app.modules.financial_aid.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.financial_aid.service.log_admin_action"),
        ):
            svc_mod.create_financial_aid_record(1, _make_aid_payload(), "actor")

        assert call_order[0] == "guard", f"Guard must be first; got: {call_order}"
        assert "persist" in call_order


# ===========================================================================
# GROUP 3 — Guard blocks: no enrollments
# ===========================================================================

class TestGuardBlocksNoEnrollment:
    def _run_guard(self, enrollments: list[dict], student_id: int = STUDENT_ID):
        import app.modules.financial_aid.service as svc_mod
        with patch(
            "app.modules.financial_aid.service.list_entities_for_tenant",
            return_value=enrollments,
        ):
            svc_mod._check_student_enrollment_for_aid_creation(
                tenant_id=1,
                student_id=student_id,
                aid_type=AID_TYPE,
            )

    def test_no_enrollments_blocked(self):
        with pytest.raises(DomainValidationError):
            self._run_guard([])

    def test_other_student_enrollment_does_not_help(self):
        """Enrollments for another student must NOT unblock this student."""
        enrollments = [_make_enrollment(999, "enrolled")]
        with pytest.raises(DomainValidationError):
            self._run_guard(enrollments)

    def test_error_contains_student_id(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard([])
        assert str(STUDENT_ID) in str(exc_info.value)

    def test_error_mentions_sap_or_enrollment(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard([])
        msg = str(exc_info.value).lower()
        assert "enrollment" in msg or "sap" in msg


# ===========================================================================
# GROUP 4 — Guard blocks: enrollment exists but wrong status
# ===========================================================================

class TestGuardBlocksInactiveEnrollment:
    def _run_guard(self, enrollments: list[dict], student_id: int = STUDENT_ID):
        import app.modules.financial_aid.service as svc_mod
        with patch(
            "app.modules.financial_aid.service.list_entities_for_tenant",
            return_value=enrollments,
        ):
            svc_mod._check_student_enrollment_for_aid_creation(
                tenant_id=1,
                student_id=student_id,
                aid_type=AID_TYPE,
            )

    def test_withdrawn_enrollment_blocked(self):
        enrollments = [_make_enrollment(STUDENT_ID, "withdrawn")]
        with pytest.raises(DomainValidationError):
            self._run_guard(enrollments)

    def test_dropped_enrollment_blocked(self):
        enrollments = [_make_enrollment(STUDENT_ID, "dropped")]
        with pytest.raises(DomainValidationError):
            self._run_guard(enrollments)

    def test_completed_enrollment_blocked(self):
        enrollments = [_make_enrollment(STUDENT_ID, "completed")]
        with pytest.raises(DomainValidationError):
            self._run_guard(enrollments)

    def test_expelled_enrollment_blocked(self):
        enrollments = [_make_enrollment(STUDENT_ID, "expelled")]
        with pytest.raises(DomainValidationError):
            self._run_guard(enrollments)

    def test_error_contains_existing_statuses(self):
        enrollments = [_make_enrollment(STUDENT_ID, "withdrawn")]
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard(enrollments)
        assert "withdrawn" in str(exc_info.value)

    def test_multiple_inactive_statuses_blocked(self):
        enrollments = [
            _make_enrollment(STUDENT_ID, "withdrawn", 1),
            _make_enrollment(STUDENT_ID, "dropped", 2),
        ]
        with pytest.raises(DomainValidationError):
            self._run_guard(enrollments)


# ===========================================================================
# GROUP 5 — Guard allows: active enrollment present
# ===========================================================================

class TestGuardAllows:
    def _run_guard(self, enrollments: list[dict], student_id: int = STUDENT_ID):
        import app.modules.financial_aid.service as svc_mod
        with patch(
            "app.modules.financial_aid.service.list_entities_for_tenant",
            return_value=enrollments,
        ):
            svc_mod._check_student_enrollment_for_aid_creation(
                tenant_id=1,
                student_id=student_id,
                aid_type=AID_TYPE,
            )

    def test_enrolled_allowed(self):
        enrollments = [_make_enrollment(STUDENT_ID, "enrolled")]
        self._run_guard(enrollments)  # must not raise

    def test_active_allowed(self):
        enrollments = [_make_enrollment(STUDENT_ID, "active")]
        self._run_guard(enrollments)

    def test_registered_allowed(self):
        enrollments = [_make_enrollment(STUDENT_ID, "registered")]
        self._run_guard(enrollments)

    def test_one_active_among_inactive_allowed(self):
        """One active enrollment is sufficient even with withdrawn ones."""
        enrollments = [
            _make_enrollment(STUDENT_ID, "withdrawn", 1),
            _make_enrollment(STUDENT_ID, "enrolled", 2),
        ]
        self._run_guard(enrollments)

    def test_active_enrollment_for_other_student_does_not_help(self):
        """Active enrollment for another student must NOT unblock this student."""
        enrollments = [_make_enrollment(999, "enrolled")]
        with pytest.raises(DomainValidationError):
            self._run_guard(enrollments)


# ===========================================================================
# GROUP 6 — Case insensitive status matching
# ===========================================================================

class TestCaseInsensitiveMatching:
    def _run_guard(self, enrollments: list[dict], student_id: int = STUDENT_ID):
        import app.modules.financial_aid.service as svc_mod
        with patch(
            "app.modules.financial_aid.service.list_entities_for_tenant",
            return_value=enrollments,
        ):
            svc_mod._check_student_enrollment_for_aid_creation(
                tenant_id=1,
                student_id=student_id,
                aid_type=AID_TYPE,
            )

    def test_status_uppercase_enrolled_allowed(self):
        enrollment = _make_enrollment(STUDENT_ID, "ENROLLED")
        self._run_guard([enrollment])

    def test_status_mixed_case_active_allowed(self):
        enrollment = _make_enrollment(STUDENT_ID, "Active")
        self._run_guard([enrollment])

    def test_status_uppercase_registered_allowed(self):
        enrollment = _make_enrollment(STUDENT_ID, "REGISTERED")
        self._run_guard([enrollment])


# ===========================================================================
# GROUP 7 — Fail-closed: lookup exception → DomainValidationError
# ===========================================================================

class TestFailClosed:
    def test_lookup_exception_raises_domain_error(self):
        import app.modules.financial_aid.service as svc_mod
        with patch(
            "app.modules.financial_aid.service.list_entities_for_tenant",
            side_effect=RuntimeError("DB connection refused"),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                svc_mod._check_student_enrollment_for_aid_creation(
                    tenant_id=1,
                    student_id=STUDENT_ID,
                    aid_type=AID_TYPE,
                )
        msg = str(exc_info.value).lower()
        assert "cannot verify" in msg or "lookup failed" in msg

    def test_lookup_failure_blocks_persist(self):
        """On lookup failure, create_entity_for_tenant must NOT be called."""
        import app.modules.financial_aid.service as svc_mod
        persisted: list = []

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                raise RuntimeError("network error")
            return []

        def fake_create(entity_type, data, tenant_id):
            persisted.append(data)
            return {"id": 1, **data}

        with (
            patch("app.modules.financial_aid.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.financial_aid.service.create_entity_for_tenant", side_effect=fake_create),
            patch("app.modules.financial_aid.service.log_admin_action"),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_financial_aid_record(1, _make_aid_payload(), "actor")

        assert persisted == [], "persist must NOT be called when guard raises"

    def test_timeout_exception_fail_closed(self):
        import app.modules.financial_aid.service as svc_mod
        with patch(
            "app.modules.financial_aid.service.list_entities_for_tenant",
            side_effect=TimeoutError("enrollment lookup timed out"),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod._check_student_enrollment_for_aid_creation(
                    tenant_id=1,
                    student_id=STUDENT_ID,
                    aid_type=AID_TYPE,
                )


# ===========================================================================
# GROUP 8 — Integration: create_financial_aid_record end-to-end
# ===========================================================================

class TestCreateAidRecordIntegration:
    def test_creation_allowed_with_active_enrollment(self):
        import app.modules.financial_aid.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_make_enrollment(STUDENT_ID, "enrolled")]
            return []

        with (
            patch("app.modules.financial_aid.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.financial_aid.service.create_entity_for_tenant", side_effect=_fake_create_entity),
            patch("app.modules.financial_aid.service.log_admin_action"),
        ):
            result = svc_mod.create_financial_aid_record(1, _make_aid_payload(), "actor")

        assert result.student_id == STUDENT_ID

    def test_creation_blocked_no_enrollment(self):
        import app.modules.financial_aid.service as svc_mod

        with patch(
            "app.modules.financial_aid.service.list_entities_for_tenant",
            return_value=[],
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_financial_aid_record(1, _make_aid_payload(), "actor")

    def test_creation_blocked_withdrawn_enrollment(self):
        import app.modules.financial_aid.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_make_enrollment(STUDENT_ID, "withdrawn")]
            return []

        with patch("app.modules.financial_aid.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_financial_aid_record(1, _make_aid_payload(), "actor")

    def test_error_is_domain_validation_not_value_error(self):
        import app.modules.financial_aid.service as svc_mod

        with patch(
            "app.modules.financial_aid.service.list_entities_for_tenant",
            return_value=[],
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_financial_aid_record(1, _make_aid_payload(), "actor")

    def test_all_aid_types_blocked_without_enrollment(self):
        """Guard applies to all aid_types."""
        import app.modules.financial_aid.service as svc_mod

        for aid_type in ("scholarship", "grant", "tuition_discount", "stipend"):
            with patch(
                "app.modules.financial_aid.service.list_entities_for_tenant",
                return_value=[],
            ):
                with pytest.raises(DomainValidationError):
                    svc_mod.create_financial_aid_record(
                        1,
                        _make_aid_payload(aid_type=aid_type),
                        "actor",
                    )

    def test_tenant_isolation(self):
        """Guard only sees enrollments for the correct tenant_id."""
        import app.modules.financial_aid.service as svc_mod

        # tenant 2 has active enrollment; tenant 1 has none
        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments" and tenant_id == 2:
                return [_make_enrollment(STUDENT_ID, "enrolled")]
            return []

        with patch("app.modules.financial_aid.service.list_entities_for_tenant", side_effect=fake_list):
            # tenant 1 — blocked
            with pytest.raises(DomainValidationError):
                svc_mod.create_financial_aid_record(1, _make_aid_payload(), "actor")

    def test_aid_cap_still_enforced_after_guard_passes(self):
        """After guard passes, existing aid cap must still block over-limit."""
        import app.modules.financial_aid.service as svc_mod

        # 200 existing scholarship aid records = at cap
        existing_aids = [
            {
                "id": i,
                "student_id": 99,
                "aid_type": "scholarship",
                "status": "pending",
                "amount": 1000,
                "currency": "USD",
                "term": "2026-FALL",
                "reviewer_id": "aid-office",
                "notes": "n/a",
            }
            for i in range(1, 201)  # 200 = cap for scholarship
        ]

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_make_enrollment(STUDENT_ID, "enrolled")]
            return existing_aids

        with patch("app.modules.financial_aid.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(ValueError, match="cap"):
                svc_mod.create_financial_aid_record(
                    1, _make_aid_payload(aid_type="scholarship"), "actor"
                )

    def test_record_created_with_correct_student_id(self):
        """After guard passes, record is persisted with correct student_id."""
        import app.modules.financial_aid.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_make_enrollment(STUDENT_ID, "enrolled")]
            return []

        with (
            patch("app.modules.financial_aid.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.financial_aid.service.create_entity_for_tenant", side_effect=_fake_create_entity),
            patch("app.modules.financial_aid.service.log_admin_action"),
        ):
            result = svc_mod.create_financial_aid_record(1, _make_aid_payload(), "actor")

        assert result.id == 77
        assert result.student_id == STUDENT_ID
