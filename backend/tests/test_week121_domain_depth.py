"""W121 — career_services: Student Active Enrollment Guard (behavioral depth).

Real-world problem:
    create_career_opportunity() had a cross-entity guard
    (_check_student_is_actively_enrolled_for_career_opportunity) but it was untested
    at the behavioral level, and the router only caught ValueError — not DomainValidationError.
    Withdrawn or expelled students could access institutional career placement services.

Root fix (W95, strengthened W121):
    Guard is fail-closed: any enrollment lookup exception → DomainValidationError.
    Router POST now catches (ValueError, DomainValidationError) → HTTP 422.

Guard answers the 5 hardening questions:
1. Dangerous action      : creating a career_opportunity (uses institutional placement capacity)
2. Real-world constraint : only actively enrolled students use institutional career services
3. External entity       : enrollments
4. Validate BEFORE       : create_entity_for_tenant("career_opportunities", ...)
5. Bad outcome prevented : expelled/withdrawn students consuming career placement resources,
                           polluting match-engine pipeline metrics
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.career_services.schemas import CareerOpportunityCreateSchema
from app.modules.career_services.service import (
    _CAREER_ACCESS_ENROLLMENT_STATUSES,
    _OPPORTUNITY_TYPE_MAX_OPEN,
    _OPPORTUNITY_PIPELINE_MAX_REVIEW,
    _check_student_is_actively_enrolled_for_career_opportunity,
    create_career_opportunity,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

ACTIVE_ENROLLMENT = {"student_id": 42, "status": "active", "tenant_id": 1}
ENROLLED_ENROLLMENT = {"student_id": 43, "status": "enrolled", "tenant_id": 1}
REGISTERED_ENROLLMENT = {"student_id": 44, "status": "registered", "tenant_id": 1}
WITHDRAWN_ENROLLMENT = {"student_id": 50, "status": "withdrawn", "tenant_id": 1}
EXPELLED_ENROLLMENT = {"student_id": 51, "status": "expelled", "tenant_id": 1}
COMPLETED_ENROLLMENT = {"student_id": 52, "status": "completed", "tenant_id": 1}


def _make_payload(
    student_id: int = 42,
    opportunity_type: str = "internship",
) -> CareerOpportunityCreateSchema:
    return CareerOpportunityCreateSchema(
        student_id=student_id,
        title="Software Intern",
        company="Acme Corp",
        opportunity_type=opportunity_type,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# TestW121Constants — sentinel values
# ---------------------------------------------------------------------------


class TestW121Constants:
    def test_career_enrollment_statuses_type(self):
        assert isinstance(_CAREER_ACCESS_ENROLLMENT_STATUSES, frozenset)

    def test_active_included(self):
        assert "active" in _CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_enrolled_included(self):
        assert "enrolled" in _CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_registered_included(self):
        assert "registered" in _CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_withdrawn_excluded(self):
        assert "withdrawn" not in _CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_expelled_excluded(self):
        assert "expelled" not in _CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_completed_excluded(self):
        assert "completed" not in _CAREER_ACCESS_ENROLLMENT_STATUSES

    def test_opportunity_type_max_open_is_dict(self):
        assert isinstance(_OPPORTUNITY_TYPE_MAX_OPEN, dict)

    def test_internship_cap_in_max_open(self):
        assert "internship" in _OPPORTUNITY_TYPE_MAX_OPEN

    def test_job_cap_in_max_open(self):
        assert "job" in _OPPORTUNITY_TYPE_MAX_OPEN

    def test_opportunity_pipeline_max_review_is_dict(self):
        assert isinstance(_OPPORTUNITY_PIPELINE_MAX_REVIEW, dict)

    def test_work_study_cap_is_one(self):
        # work_study is most restrictive — only 1 concurrent open
        assert _OPPORTUNITY_TYPE_MAX_OPEN.get("work_study", 0) == 1


# ---------------------------------------------------------------------------
# TestW121GuardSignature — guard raises DomainValidationError
# ---------------------------------------------------------------------------


class TestW121GuardSignature:
    def test_guard_raises_domain_validation_error_for_unknown_student(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=999, opportunity_type="internship"
            )

    def test_guard_does_not_raise_for_active_student(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ACTIVE_ENROLLMENT],
        )
        _check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1, student_id=42, opportunity_type="internship"
        )

    def test_guard_does_not_raise_for_enrolled_student(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ENROLLED_ENROLLMENT],
        )
        _check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1, student_id=43, opportunity_type="job"
        )

    def test_guard_does_not_raise_for_registered_student(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [REGISTERED_ENROLLMENT],
        )
        _check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1, student_id=44, opportunity_type="mentorship"
        )


# ---------------------------------------------------------------------------
# TestW121GuardFailures — all blocked scenarios
# ---------------------------------------------------------------------------


class TestW121GuardFailures:
    def test_no_enrollment_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no enrollment records found"):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=999, opportunity_type="internship"
            )

    def test_withdrawn_student_blocked(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [WITHDRAWN_ENROLLMENT],
        )
        with pytest.raises(DomainValidationError, match="not actively enrolled"):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=50, opportunity_type="internship"
            )

    def test_expelled_student_blocked(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [EXPELLED_ENROLLMENT],
        )
        with pytest.raises(DomainValidationError):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=51, opportunity_type="job"
            )

    def test_completed_enrollment_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [COMPLETED_ENROLLMENT],
        )
        with pytest.raises(DomainValidationError):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=52, opportunity_type="mentorship"
            )

    def test_wrong_student_id_blocks(self, monkeypatch):
        """Enrollment exists for student 42, not student 99."""
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ACTIVE_ENROLLMENT],  # student_id=42
        )
        with pytest.raises(DomainValidationError, match="no enrollment records found"):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=99, opportunity_type="internship"
            )


# ---------------------------------------------------------------------------
# TestW121FailClosed — lookup failure → DomainValidationError (never silently pass)
# ---------------------------------------------------------------------------


class TestW121FailClosed:
    def test_lookup_exception_raises_domain_validation_error(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise RuntimeError("DB unavailable")

        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError, match="enrollment lookup failed"):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=42, opportunity_type="internship"
            )

    def test_connection_error_blocks(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise ConnectionError("network error")

        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=42, opportunity_type="internship"
            )

    def test_ioerror_blocks(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise IOError("timeout")

        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=42, opportunity_type="internship"
            )

    def test_fail_closed_error_mentions_student_id(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise Exception("DB error")

        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError, match="student_id=42"):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=42, opportunity_type="internship"
            )


# ---------------------------------------------------------------------------
# TestW121CreatePath — end-to-end create_career_opportunity integration
# ---------------------------------------------------------------------------


class TestW121CreatePath:
    def _setup_monkeypatches(self, monkeypatch, enrollments, existing_opportunities=None):
        existing_opportunities = existing_opportunities or []
        created: dict[str, object] = {}

        def mock_list(entity_name, tenant_id):
            if entity_name == "enrollments":
                return enrollments
            if entity_name == "career_opportunities":
                return existing_opportunities
            return []

        def mock_create(entity_name, payload, tenant_id):
            record = dict(payload)
            record["id"] = 77
            record["tenant_id"] = str(tenant_id)
            created["entity_name"] = entity_name
            created["payload"] = record
            return record

        def mock_log(*args, **kwargs):
            pass

        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.career_services.service.create_entity_for_tenant", mock_create
        )
        monkeypatch.setattr(
            "app.modules.career_services.service.log_admin_action", mock_log
        )
        return created

    def test_create_succeeds_for_active_student(self, monkeypatch):
        created = self._setup_monkeypatches(
            monkeypatch, enrollments=[ACTIVE_ENROLLMENT]
        )
        result = create_career_opportunity(1, _make_payload(student_id=42), actor="admin")
        assert result.id == 77
        assert created["entity_name"] == "career_opportunities"

    def test_create_blocked_for_withdrawn_student(self, monkeypatch):
        self._setup_monkeypatches(monkeypatch, enrollments=[WITHDRAWN_ENROLLMENT])
        with pytest.raises(DomainValidationError):
            create_career_opportunity(1, _make_payload(student_id=50), actor="admin")

    def test_create_blocked_for_unknown_student(self, monkeypatch):
        self._setup_monkeypatches(monkeypatch, enrollments=[])
        with pytest.raises(DomainValidationError):
            create_career_opportunity(1, _make_payload(student_id=999), actor="admin")

    def test_guard_fires_before_cap_check(self, monkeypatch):
        """Enrollment guard must fire before open-count cap — enrollment lookup is first."""
        lookup_order: list[str] = []

        def mock_list(entity_name, tenant_id):
            lookup_order.append(entity_name)
            if entity_name == "enrollments":
                return []  # trigger guard failure
            return []

        def mock_create(entity_name, payload, tenant_id):
            return {"id": 1}

        def mock_log(*args, **kwargs):
            pass

        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.career_services.service.create_entity_for_tenant", mock_create
        )
        monkeypatch.setattr(
            "app.modules.career_services.service.log_admin_action", mock_log
        )
        with pytest.raises(DomainValidationError):
            create_career_opportunity(1, _make_payload(student_id=999), actor="admin")

        assert lookup_order[0] == "enrollments"

    def test_not_persisted_when_guard_fails(self, monkeypatch):
        created_calls: list[str] = []

        def mock_list(entity_name, tenant_id):
            if entity_name == "enrollments":
                return [WITHDRAWN_ENROLLMENT]
            return []

        def mock_create(entity_name, payload, tenant_id):
            created_calls.append(entity_name)
            return {"id": 1}

        def mock_log(*args, **kwargs):
            pass

        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.career_services.service.create_entity_for_tenant", mock_create
        )
        monkeypatch.setattr(
            "app.modules.career_services.service.log_admin_action", mock_log
        )
        with pytest.raises(DomainValidationError):
            create_career_opportunity(1, _make_payload(student_id=50), actor="admin")

        assert "career_opportunities" not in created_calls


# ---------------------------------------------------------------------------
# TestW121BusinessInvariants — multi-tenant, combined, matching engine
# ---------------------------------------------------------------------------


class TestW121BusinessInvariants:
    def test_two_tenants_isolated(self, monkeypatch):
        """Enrollment from tenant 1 must not satisfy tenant 2 guard."""

        def mock_list(entity_name, tenant_id):
            if entity_name == "enrollments" and tenant_id == 1:
                return [ACTIVE_ENROLLMENT]
            if entity_name == "enrollments" and tenant_id == 2:
                return []
            return []

        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant", mock_list
        )
        # Tenant 1 — passes
        _check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1, student_id=42, opportunity_type="internship"
        )
        # Tenant 2 — blocked
        with pytest.raises(DomainValidationError):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=2, student_id=42, opportunity_type="internship"
            )

    def test_one_active_among_multiple_rows_passes(self, monkeypatch):
        """If student has both historical completed and current active row, guard passes."""
        enrollments = [
            {"student_id": 42, "status": "completed", "tenant_id": 1},
            {"student_id": 42, "status": "active", "tenant_id": 1},
        ]
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda e, t: enrollments,
        )
        _check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1, student_id=42, opportunity_type="internship"
        )

    def test_all_inactive_blocks(self, monkeypatch):
        enrollments = [
            {"student_id": 42, "status": "completed", "tenant_id": 1},
            {"student_id": 42, "status": "withdrawn", "tenant_id": 1},
        ]
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda e, t: enrollments,
        )
        with pytest.raises(DomainValidationError, match="not actively enrolled"):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=42, opportunity_type="internship"
            )

    def test_error_message_includes_student_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        with pytest.raises(DomainValidationError, match="student_id=777"):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=777, opportunity_type="job"
            )

    def test_error_message_includes_opportunity_type(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        with pytest.raises(DomainValidationError, match="mentorship"):
            _check_student_is_actively_enrolled_for_career_opportunity(
                tenant_id=1, student_id=42, opportunity_type="mentorship"
            )

    def test_enrollment_status_key_variant(self, monkeypatch):
        """Guard handles 'enrollment_status' key variant in addition to 'status'."""
        enrollment_alt_key = {
            "student_id": 42,
            "enrollment_status": "active",
            "tenant_id": 1,
        }
        monkeypatch.setattr(
            "app.modules.career_services.service.list_entities_for_tenant",
            lambda e, t: [enrollment_alt_key],
        )
        _check_student_is_actively_enrolled_for_career_opportunity(
            tenant_id=1, student_id=42, opportunity_type="work_study"
        )
