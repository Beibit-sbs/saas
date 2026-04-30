"""W118 — academic_records: transcript record requires real enrollment relation.

Root fix:
- create_record() now validates enrollment existence (student_id + course_id + semester)
  BEFORE persist.
- Guard is fail-closed on enrollment lookup failures.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.academic_records.service import (
    _check_enrollment_exists_for_academic_record,
    create_record,
    _ENROLLMENT_ELIGIBLE_STATUSES,
)


TENANT_ID = 9


def _payload(**overrides):
    base = {
        "student_id": 101,
        "course_id": 501,
        "grade": "A",
        "semester": "2026-spring",
        "status": "pending",
        "notes": "ok",
    }
    base.update(overrides)
    return base


def _enrollment(student_id=101, course_id=501, semester="2026-spring", status="active"):
    return {
        "id": 1,
        "student_id": student_id,
        "course_id": course_id,
        "semester": semester,
        "status": status,
    }


class TestW118Constants:
    def test_eligible_statuses_defined(self):
        assert "active" in _ENROLLMENT_ELIGIBLE_STATUSES

    def test_guard_is_callable(self):
        assert callable(_check_enrollment_exists_for_academic_record)


class TestW118GuardFailClosed:
    def test_lookup_failure_blocks(self):
        with patch(
            "app.modules.academic_records.service.list_entities_for_tenant",
            side_effect=RuntimeError("db down"),
        ):
            with pytest.raises(DomainValidationError, match="lookup failed"):
                _check_enrollment_exists_for_academic_record(
                    tenant_id=TENANT_ID,
                    student_id=101,
                    course_id=501,
                    semester="2026-spring",
                )

    def test_lookup_failure_chains_cause(self):
        with patch(
            "app.modules.academic_records.service.list_entities_for_tenant",
            side_effect=RuntimeError("timeout"),
        ):
            with pytest.raises(DomainValidationError) as exc_info:
                _check_enrollment_exists_for_academic_record(
                    tenant_id=TENANT_ID,
                    student_id=101,
                    course_id=501,
                    semester="2026-spring",
                )
            assert exc_info.value.__cause__ is not None


class TestW118GuardNegativeCases:
    def test_no_enrollments_blocks(self):
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError, match="no eligible enrollment"):
                _check_enrollment_exists_for_academic_record(
                    tenant_id=TENANT_ID,
                    student_id=101,
                    course_id=501,
                    semester="2026-spring",
                )

    def test_wrong_student_blocks(self):
        rows = [_enrollment(student_id=999)]
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=rows):
            with pytest.raises(DomainValidationError):
                _check_enrollment_exists_for_academic_record(
                    tenant_id=TENANT_ID,
                    student_id=101,
                    course_id=501,
                    semester="2026-spring",
                )

    def test_wrong_course_blocks(self):
        rows = [_enrollment(course_id=777)]
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=rows):
            with pytest.raises(DomainValidationError):
                _check_enrollment_exists_for_academic_record(
                    tenant_id=TENANT_ID,
                    student_id=101,
                    course_id=501,
                    semester="2026-spring",
                )

    def test_wrong_semester_blocks_when_semester_present(self):
        rows = [_enrollment(semester="2026-fall")]
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=rows):
            with pytest.raises(DomainValidationError):
                _check_enrollment_exists_for_academic_record(
                    tenant_id=TENANT_ID,
                    student_id=101,
                    course_id=501,
                    semester="2026-spring",
                )

    @pytest.mark.parametrize("status", ["cancelled", "rejected", "no_show", "dropped"])
    def test_ineligible_status_blocks(self, status):
        rows = [_enrollment(status=status)]
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=rows):
            with pytest.raises(DomainValidationError):
                _check_enrollment_exists_for_academic_record(
                    tenant_id=TENANT_ID,
                    student_id=101,
                    course_id=501,
                    semester="2026-spring",
                )


class TestW118GuardPositiveCases:
    @pytest.mark.parametrize("status", ["active", "enrolled", "registered", "completed", "withdrawn"])
    def test_eligible_status_passes(self, status):
        rows = [_enrollment(status=status)]
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=rows):
            _check_enrollment_exists_for_academic_record(
                tenant_id=TENANT_ID,
                student_id=101,
                course_id=501,
                semester="2026-spring",
            )

    def test_semester_case_insensitive_passes(self):
        rows = [_enrollment(semester=" 2026-SPRING ")]
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=rows):
            _check_enrollment_exists_for_academic_record(
                tenant_id=TENANT_ID,
                student_id=101,
                course_id=501,
                semester="2026-spring",
            )

    def test_missing_semester_in_enrollment_allows_student_course_match(self):
        row = _enrollment()
        del row["semester"]
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=[row]):
            _check_enrollment_exists_for_academic_record(
                tenant_id=TENANT_ID,
                student_id=101,
                course_id=501,
                semester="2026-spring",
            )

    def test_term_field_used_as_semester_alias(self):
        row = {
            "id": 1,
            "student_id": 101,
            "course_id": 501,
            "term": "2026-spring",
            "status": "active",
        }
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=[row]):
            _check_enrollment_exists_for_academic_record(
                tenant_id=TENANT_ID,
                student_id=101,
                course_id=501,
                semester="2026-spring",
            )


class TestW118CreateRecordIntegration:
    def test_block_before_persist_when_guard_fails(self):
        payload = _payload()

        def _list(entity, tenant_id):
            if entity == "enrollments":
                return []
            if entity == "academic_records":
                return []
            return []

        with patch("app.modules.academic_records.service.list_entities_for_tenant", side_effect=_list), patch(
            "app.modules.academic_records.service.create_entity_for_tenant"
        ) as mock_create:
            with pytest.raises(DomainValidationError):
                create_record(payload, TENANT_ID)
            mock_create.assert_not_called()

    def test_block_before_persist_on_lookup_exception(self):
        payload = _payload()
        with patch(
            "app.modules.academic_records.service.list_entities_for_tenant",
            side_effect=RuntimeError("db"),
        ), patch("app.modules.academic_records.service.create_entity_for_tenant") as mock_create:
            with pytest.raises(DomainValidationError):
                create_record(payload, TENANT_ID)
            mock_create.assert_not_called()

    def test_pass_and_persist_with_eligible_enrollment(self):
        payload = _payload()

        def _list(entity, tenant_id):
            if entity == "enrollments":
                return [_enrollment()]
            if entity == "academic_records":
                return []
            return []

        with patch("app.modules.academic_records.service.list_entities_for_tenant", side_effect=_list), patch(
            "app.modules.academic_records.service.create_entity_for_tenant",
            return_value={"id": 77, **payload},
        ) as mock_create:
            result = create_record(payload, TENANT_ID)
            assert result["id"] == 77
            mock_create.assert_called_once()

    def test_guard_executes_before_cap_check(self):
        payload = _payload()
        call_order: list[str] = []

        def _list(entity, tenant_id):
            call_order.append(entity)
            if entity == "enrollments":
                return []
            if entity == "academic_records":
                pytest.fail("academic_records lookup should not occur after guard failure")
            return []

        with patch("app.modules.academic_records.service.list_entities_for_tenant", side_effect=_list):
            with pytest.raises(DomainValidationError):
                create_record(payload, TENANT_ID)

        assert call_order[0] == "enrollments"

    def test_invalid_student_id_still_value_error(self):
        payload = _payload(student_id=0)
        with pytest.raises(ValueError, match="student_id"):
            create_record(payload, TENANT_ID)

    def test_invalid_course_id_still_value_error(self):
        payload = _payload(course_id=0)
        with pytest.raises(ValueError, match="course_id"):
            create_record(payload, TENANT_ID)

    def test_missing_semester_value_error(self):
        payload = _payload(semester="")
        with pytest.raises(ValueError, match="semester"):
            create_record(payload, TENANT_ID)


class TestW118ErrorMessageIntegrity:
    def test_error_mentions_student_course_semester(self):
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=[]):
            with pytest.raises(DomainValidationError) as exc_info:
                _check_enrollment_exists_for_academic_record(
                    tenant_id=TENANT_ID,
                    student_id=101,
                    course_id=501,
                    semester="2026-spring",
                )
        msg = str(exc_info.value)
        assert "student_id=101" in msg
        assert "course_id=501" in msg
        assert "2026-spring" in msg


class TestW118TenantIsolation:
    def test_guard_uses_current_tenant(self):
        seen: list[int] = []

        def _list(entity, tenant_id):
            seen.append(tenant_id)
            return [_enrollment()]

        with patch("app.modules.academic_records.service.list_entities_for_tenant", side_effect=_list):
            _check_enrollment_exists_for_academic_record(
                tenant_id=444,
                student_id=101,
                course_id=501,
                semester="2026-spring",
            )
        assert seen == [444]


class TestW118MultipleRowsSelection:
    def test_one_valid_row_among_invalid_rows_passes(self):
        rows = [
            _enrollment(student_id=999),
            _enrollment(course_id=999),
            _enrollment(status="cancelled"),
            _enrollment(),
        ]
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=rows):
            _check_enrollment_exists_for_academic_record(
                tenant_id=TENANT_ID,
                student_id=101,
                course_id=501,
                semester="2026-spring",
            )

    def test_numeric_string_ids_in_enrollment_are_supported(self):
        row = {
            "id": "1",
            "student_id": "101",
            "course_id": "501",
            "semester": "2026-spring",
            "status": "active",
        }
        with patch("app.modules.academic_records.service.list_entities_for_tenant", return_value=[row]):
            _check_enrollment_exists_for_academic_record(
                tenant_id=TENANT_ID,
                student_id=101,
                course_id=501,
                semester="2026-spring",
            )
