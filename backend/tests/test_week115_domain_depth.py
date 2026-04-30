"""W115 — Delinquency Collections × Enrollment History Guard.

Business invariant: A delinquency record may ONLY be created when the referenced
student_id has at least one enrollment record in the institution's enrollment system.

Tuition and fee debts arise ONLY from registered students who received academic
services. Creating a delinquency record against a non-enrolled person:
  - Constitutes a fraudulent debt record (FCRA / FDCPA violation risk)
  - May trigger illegal automated collection actions against non-debtors
  - Distorts collection portfolio metrics with phantom accounts
  - Creates regulatory and legal liability for the institution

Guard: _check_student_has_enrollment_history() — BEFORE create_entity_for_tenant()
Fail-closed: enrollment lookup exception → DomainValidationError.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError

STUDENT_ID = "STU-001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_enrollment(
    student_id: str = STUDENT_ID,
    course_id: str = "CS101",
    semester: str = "2025-fall",
    status: str = "active",
    eid: int = 1,
) -> dict:
    return {
        "id": eid,
        "student_id": student_id,
        "course_id": course_id,
        "semester": semester,
        "status": status,
    }


def _make_delinquency_request(
    student_id: str = STUDENT_ID,
    invoice_code: str = "INV-001",
    amount_due: float = 1500.0,
    days_overdue: int = 45,
    escalation_stage: str = "stage_1",
    status: str = "open",
):
    from app.modules.delinquency_collections.schemas import DelinquencyRecordCreateSchema
    return DelinquencyRecordCreateSchema(
        student_id=student_id,
        invoice_code=invoice_code,
        amount_due=amount_due,
        days_overdue=days_overdue,
        escalation_stage=escalation_stage,
        status=status,
    )


def _fake_create_entity(entity_type, data, tenant_id):
    return {"id": 77, **data}


def _fake_update_entity(entity_type, entity_id, data, tenant_id):
    return {"id": entity_id, **data}


# ===========================================================================
# GROUP 1 — Guard constant correctness
# ===========================================================================

class TestDelinquencyEnrollmentConstant:
    def test_constant_exists(self):
        import app.modules.delinquency_collections.service as svc
        assert hasattr(svc, "_DELINQUENCY_REQUIRES_ENROLLMENT_HISTORY")

    def test_constant_is_truthy(self):
        import app.modules.delinquency_collections.service as svc
        assert svc._DELINQUENCY_REQUIRES_ENROLLMENT_HISTORY is True

    def test_active_statuses_constant_still_intact(self):
        import app.modules.delinquency_collections.service as svc
        assert "open" in svc._ACTIVE_STATUSES_DC

    def test_escalation_stage_max_active_still_intact(self):
        import app.modules.delinquency_collections.service as svc
        assert svc._ESCALATION_STAGE_MAX_ACTIVE["stage_1"] == 5

    def test_legal_escalation_stages_still_intact(self):
        import app.modules.delinquency_collections.service as svc
        assert "legal" in svc._LEGAL_ESCALATION_STAGES


# ===========================================================================
# GROUP 2 — Guard function exists and is wired BEFORE persist
# ===========================================================================

class TestGuardFunctionExists:
    def test_guard_function_exists(self):
        import app.modules.delinquency_collections.service as svc
        assert hasattr(svc, "_check_student_has_enrollment_history")

    def test_guard_function_is_callable(self):
        import app.modules.delinquency_collections.service as svc
        assert callable(svc._check_student_has_enrollment_history)

    def test_guard_fires_before_persist(self):
        """Guard must be the first action — before any create_entity_for_tenant call."""
        import app.modules.delinquency_collections.service as svc_mod
        call_order: list[str] = []

        def fake_guard(*, tenant_id, student_id):
            call_order.append("guard")

        def fake_list(entity_type, tenant_id):
            return [_make_enrollment()]

        def fake_create(entity_type, data, tenant_id):
            call_order.append("persist")
            return {"id": 1, "status": "open", **data}

        with (
            patch.object(svc_mod, "_check_student_has_enrollment_history", fake_guard),
            patch("app.modules.delinquency_collections.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.delinquency_collections.service.create_entity_for_tenant", side_effect=fake_create),
            patch("app.modules.delinquency_collections.service.log_admin_action"),
            patch("app.modules.delinquency_collections.service.EventPublisher"),
        ):
            svc_mod.create_delinquency_record(1, _make_delinquency_request(), "actor")

        assert call_order[0] == "guard", f"Guard must fire first; got: {call_order}"
        assert "persist" in call_order

    def test_guard_fires_before_w23_cap(self):
        """Guard fires before W23 cap check — enrollment missing blocks everything."""
        import app.modules.delinquency_collections.service as svc_mod
        call_order: list[str] = []

        def fake_guard(*, tenant_id, student_id):
            call_order.append("guard")
            raise DomainValidationError("no enrollment")

        def fake_list(entity_type, tenant_id):
            call_order.append(f"list:{entity_type}")
            return []

        with (
            patch.object(svc_mod, "_check_student_has_enrollment_history", fake_guard),
            patch("app.modules.delinquency_collections.service.list_entities_for_tenant", side_effect=fake_list),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_delinquency_record(1, _make_delinquency_request(), "actor")

        assert call_order[0] == "guard"
        # No list calls should happen after guard raises
        assert not any("delinquency_records" in e for e in call_order)


# ===========================================================================
# GROUP 3 — Guard blocks: no enrollment history
# ===========================================================================

class TestGuardBlocksNoEnrollment:
    def _run_guard(self, enrollments: list[dict], student_id: str = STUDENT_ID):
        import app.modules.delinquency_collections.service as svc_mod
        with patch(
            "app.modules.delinquency_collections.service.list_entities_for_tenant",
            return_value=enrollments,
        ):
            svc_mod._check_student_has_enrollment_history(tenant_id=1, student_id=student_id)

    def test_empty_enrollment_list_blocked(self):
        with pytest.raises(DomainValidationError):
            self._run_guard([])

    def test_different_student_blocked(self):
        enrollments = [_make_enrollment(student_id="STU-999")]
        with pytest.raises(DomainValidationError):
            self._run_guard(enrollments, student_id=STUDENT_ID)

    def test_error_contains_student_id(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard([])
        assert STUDENT_ID in str(exc_info.value)

    def test_error_mentions_enrollment(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard([])
        msg = str(exc_info.value).lower()
        assert "enrollment" in msg or "enrolled" in msg

    def test_error_mentions_fraud_or_fcra(self):
        with pytest.raises(DomainValidationError) as exc_info:
            self._run_guard([])
        msg = str(exc_info.value).lower()
        assert "fraud" in msg or "fcra" in msg or "fdcpa" in msg or "registered" in msg or "non-enrolled" in msg

    def test_error_is_domain_validation_not_value_error(self):
        with pytest.raises(DomainValidationError):
            self._run_guard([])


# ===========================================================================
# GROUP 4 — Guard allows: student with enrollment history (any status)
# ===========================================================================

class TestGuardAllows:
    def _run_guard(self, enrollments: list[dict]):
        import app.modules.delinquency_collections.service as svc_mod
        with patch(
            "app.modules.delinquency_collections.service.list_entities_for_tenant",
            return_value=enrollments,
        ):
            svc_mod._check_student_has_enrollment_history(tenant_id=1, student_id=STUDENT_ID)

    def test_active_enrollment_allowed(self):
        enrollments = [_make_enrollment(status="active")]
        self._run_guard(enrollments)  # must not raise

    def test_completed_enrollment_allowed(self):
        """Graduated/completed students may still owe tuition fees."""
        enrollments = [_make_enrollment(status="completed")]
        self._run_guard(enrollments)

    def test_withdrawn_enrollment_allowed(self):
        """Withdrawn students may still owe fees for received services."""
        enrollments = [_make_enrollment(status="withdrawn")]
        self._run_guard(enrollments)

    def test_suspended_enrollment_allowed(self):
        enrollments = [_make_enrollment(status="suspended")]
        self._run_guard(enrollments)

    def test_multiple_semesters_allowed(self):
        enrollments = [
            _make_enrollment(semester="2024-spring", status="completed", eid=1),
            _make_enrollment(semester="2024-fall", status="completed", eid=2),
            _make_enrollment(semester="2025-spring", status="active", eid=3),
        ]
        self._run_guard(enrollments)

    def test_correct_student_among_others(self):
        """Guard finds the correct student even when other students exist."""
        enrollments = [
            _make_enrollment(student_id="STU-OTHER", status="active", eid=1),
            _make_enrollment(student_id=STUDENT_ID, status="active", eid=2),
        ]
        self._run_guard(enrollments)


# ===========================================================================
# GROUP 5 — Case-insensitive student_id matching
# ===========================================================================

class TestCaseInsensitiveMatching:
    def _run_guard(self, enrollments: list[dict], student_id: str):
        import app.modules.delinquency_collections.service as svc_mod
        with patch(
            "app.modules.delinquency_collections.service.list_entities_for_tenant",
            return_value=enrollments,
        ):
            svc_mod._check_student_has_enrollment_history(tenant_id=1, student_id=student_id)

    def test_uppercase_student_id_matched(self):
        enrollments = [_make_enrollment(student_id="stu-001", status="active")]
        self._run_guard(enrollments, "STU-001")  # must not raise

    def test_lowercase_student_id_matched(self):
        enrollments = [_make_enrollment(student_id="STU-001", status="active")]
        self._run_guard(enrollments, "stu-001")  # must not raise


# ===========================================================================
# GROUP 6 — Fail-closed: lookup exception → DomainValidationError
# ===========================================================================

class TestFailClosed:
    def test_lookup_exception_raises_domain_error(self):
        import app.modules.delinquency_collections.service as svc_mod
        with patch(
            "app.modules.delinquency_collections.service.list_entities_for_tenant",
            side_effect=RuntimeError("DB connection failed"),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                svc_mod._check_student_has_enrollment_history(tenant_id=1, student_id=STUDENT_ID)
        msg = str(exc_info.value).lower()
        assert "lookup failed" in msg or "cannot initiate" in msg or "enrollment" in msg

    def test_timeout_exception_fail_closed(self):
        import app.modules.delinquency_collections.service as svc_mod
        with patch(
            "app.modules.delinquency_collections.service.list_entities_for_tenant",
            side_effect=TimeoutError("network timeout"),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod._check_student_has_enrollment_history(tenant_id=1, student_id=STUDENT_ID)

    def test_lookup_failure_blocks_persist(self):
        """On lookup failure, create_entity_for_tenant must NOT be called."""
        import app.modules.delinquency_collections.service as svc_mod
        persisted: list = []

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                raise RuntimeError("connection error")
            return []

        def fake_create(entity_type, data, tenant_id):
            persisted.append(data)
            return {"id": 1, **data}

        with (
            patch("app.modules.delinquency_collections.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.delinquency_collections.service.create_entity_for_tenant", side_effect=fake_create),
            patch("app.modules.delinquency_collections.service.log_admin_action"),
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_delinquency_record(1, _make_delinquency_request(), "actor")

        assert persisted == [], "persist must NOT be called when guard raises"


# ===========================================================================
# GROUP 7 — Integration: create_delinquency_record end-to-end
# ===========================================================================

class TestCreateDelinquencyRecordIntegration:
    def test_creation_allowed_with_active_enrollment(self):
        import app.modules.delinquency_collections.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_make_enrollment(status="active")]
            return []  # no existing delinquency records for cap check

        with (
            patch("app.modules.delinquency_collections.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.delinquency_collections.service.create_entity_for_tenant", side_effect=_fake_create_entity),
            patch("app.modules.delinquency_collections.service.log_admin_action"),
            patch("app.modules.delinquency_collections.service.EventPublisher"),
        ):
            result = svc_mod.create_delinquency_record(1, _make_delinquency_request(), "actor")

        assert result.student_id == STUDENT_ID

    def test_creation_allowed_with_completed_enrollment(self):
        import app.modules.delinquency_collections.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_make_enrollment(status="completed")]
            return []

        with (
            patch("app.modules.delinquency_collections.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.delinquency_collections.service.create_entity_for_tenant", side_effect=_fake_create_entity),
            patch("app.modules.delinquency_collections.service.log_admin_action"),
            patch("app.modules.delinquency_collections.service.EventPublisher"),
        ):
            result = svc_mod.create_delinquency_record(1, _make_delinquency_request(), "actor")

        assert result.student_id == STUDENT_ID

    def test_creation_blocked_no_enrollment(self):
        import app.modules.delinquency_collections.service as svc_mod

        with patch(
            "app.modules.delinquency_collections.service.list_entities_for_tenant",
            return_value=[],
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_delinquency_record(1, _make_delinquency_request(), "actor")

    def test_creation_blocked_wrong_student_id(self):
        import app.modules.delinquency_collections.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_make_enrollment(student_id="STU-OTHER")]
            return []

        with patch("app.modules.delinquency_collections.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_delinquency_record(1, _make_delinquency_request(), "actor")

    def test_error_is_domain_validation_not_value_error(self):
        import app.modules.delinquency_collections.service as svc_mod

        with patch(
            "app.modules.delinquency_collections.service.list_entities_for_tenant",
            return_value=[],
        ):
            with pytest.raises(DomainValidationError):
                svc_mod.create_delinquency_record(1, _make_delinquency_request(), "actor")

    def test_w23_cap_still_enforced_after_guard_passes(self):
        """After guard passes, W23 per-stage cap must still fire."""
        import app.modules.delinquency_collections.service as svc_mod

        # stage_1 cap is 5 — create 5 existing active records
        existing_records = [
            {
                "id": i,
                "student_id": STUDENT_ID,
                "escalation_stage": "stage_1",
                "status": "open",
                "invoice_code": f"INV-{i}",
                "amount_due": 100.0,
                "days_overdue": 30,
            }
            for i in range(1, 6)  # 5 = cap
        ]

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_make_enrollment(status="active")]
            if entity_type == "delinquency_records":
                return existing_records
            return []

        with patch("app.modules.delinquency_collections.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(ValueError, match="max=5"):
                svc_mod.create_delinquency_record(1, _make_delinquency_request(escalation_stage="stage_1"), "actor")

    def test_tenant_isolation(self):
        """Guard only looks at enrollments for the correct tenant_id."""
        import app.modules.delinquency_collections.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments" and tenant_id == 2:
                return [_make_enrollment(status="active")]
            return []

        with patch("app.modules.delinquency_collections.service.list_entities_for_tenant", side_effect=fake_list):
            with pytest.raises(DomainValidationError):
                svc_mod.create_delinquency_record(1, _make_delinquency_request(), "actor")

    def test_record_persisted_with_correct_student_id(self):
        """After guard passes, record is persisted with correct student_id."""
        import app.modules.delinquency_collections.service as svc_mod

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_make_enrollment(status="active")]
            return []

        with (
            patch("app.modules.delinquency_collections.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.delinquency_collections.service.create_entity_for_tenant", side_effect=_fake_create_entity),
            patch("app.modules.delinquency_collections.service.log_admin_action"),
            patch("app.modules.delinquency_collections.service.EventPublisher"),
        ):
            result = svc_mod.create_delinquency_record(1, _make_delinquency_request(), "actor")

        assert result.id == 77
        assert result.student_id == STUDENT_ID

    def test_w87_legal_threshold_applies_to_escalation_update(self):
        """W87 legal threshold guard lives in update_delinquency_escalation(), not create.
        Creating a legal-stage record directly still works (pre-existing behavior);
        escalating an existing record to legal is where the threshold fires.
        This test verifies the guard function exists in the service.
        """
        import app.modules.delinquency_collections.service as svc_mod
        assert hasattr(svc_mod, "_check_legal_escalation_threshold")

    def test_critical_overdue_event_emitted_for_enrolled_student(self):
        """Events are emitted only AFTER successful guard + persist."""
        import app.modules.delinquency_collections.service as svc_mod

        published: list = []

        class FakePublisher:
            def publish_event(self, **kwargs):
                published.append(kwargs)

        def fake_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                return [_make_enrollment(status="active")]
            return []

        with (
            patch("app.modules.delinquency_collections.service.list_entities_for_tenant", side_effect=fake_list),
            patch("app.modules.delinquency_collections.service.create_entity_for_tenant", side_effect=_fake_create_entity),
            patch("app.modules.delinquency_collections.service.log_admin_action"),
            patch("app.modules.delinquency_collections.service.EventPublisher", return_value=FakePublisher()),
        ):
            svc_mod.create_delinquency_record(
                1,
                _make_delinquency_request(days_overdue=95),  # >= 90 triggers critical event
                "actor",
            )

        assert any("critical_overdue" in str(p) for p in published)
