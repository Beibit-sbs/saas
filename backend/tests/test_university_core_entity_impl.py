"""
Unit tests for university_core/entity_impl.py — pure function layer.

Currently at 29% coverage. These tests cover the non-DB impl functions
via memory fallback mode (no DATABASE_URL needed), avoiding any docker/pg
dependency.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.university_core import entity_impl, shared as university_shared


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_state():
    """Reset in-memory state before each test and force memory mode."""
    university_shared._state.data = {name: {} for name in university_shared.ENTITY_CONFIGS}
    university_shared._state.counters = {name: 0 for name in university_shared.ENTITY_CONFIGS}
    with patch.object(entity_impl, "_use_database_impl", return_value=False):
        yield
    university_shared._state.data = {name: {} for name in university_shared.ENTITY_CONFIGS}
    university_shared._state.counters = {name: 0 for name in university_shared.ENTITY_CONFIGS}


# ---------------------------------------------------------------------------
# _normalize_string_impl
# ---------------------------------------------------------------------------


class TestNormalizeString:
    def test_strips_whitespace(self):
        assert entity_impl._normalize_string_impl("field", "  hello  ") == "hello"

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="is required"):
            entity_impl._normalize_string_impl("field", "")

    def test_rejects_whitespace_only(self):
        with pytest.raises(ValueError, match="is required"):
            entity_impl._normalize_string_impl("field", "   ")

    def test_rejects_too_long(self):
        with pytest.raises(ValueError, match="at most"):
            entity_impl._normalize_string_impl("field", "a" * 256)

    def test_custom_max_len(self):
        with pytest.raises(ValueError, match="at most 5"):
            entity_impl._normalize_string_impl("field", "abcdef", max_len=5)


# ---------------------------------------------------------------------------
# _normalize_optional_tenant_impl
# ---------------------------------------------------------------------------


class TestNormalizeOptionalTenant:
    def test_returns_none_for_empty(self):
        assert entity_impl._normalize_optional_tenant_impl("") is None
        assert entity_impl._normalize_optional_tenant_impl(None) is None

    def test_strips_and_returns(self):
        assert entity_impl._normalize_optional_tenant_impl(" 42 ") == "42"


# ---------------------------------------------------------------------------
# _normalize_payload_impl — students
# ---------------------------------------------------------------------------


class TestNormalizePayloadStudents:
    def test_valid_student_payload(self):
        result = entity_impl._normalize_payload_impl("students", {
            "student_id": "S001",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "status": "active",
            "tenant_id": "1",
        })
        assert result["student_id"] == "S001"
        assert result["email"] == "john@example.com"

    def test_missing_required_field(self):
        with pytest.raises(ValueError, match="student_id is required"):
            entity_impl._normalize_payload_impl("students", {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "status": "active",
                "tenant_id": "1",
            })

    def test_email_without_at(self):
        with pytest.raises(ValueError, match="email must contain @"):
            entity_impl._normalize_payload_impl("students", {
                "student_id": "S001",
                "first_name": "John",
                "last_name": "Doe",
                "email": "not-an-email",
                "status": "active",
                "tenant_id": "1",
            })

    def test_empty_required_field(self):
        with pytest.raises(ValueError, match="is required"):
            entity_impl._normalize_payload_impl("students", {
                "student_id": "",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "status": "active",
                "tenant_id": "1",
            })


# ---------------------------------------------------------------------------
# _normalize_payload_impl — courses (with credits + fk)
# ---------------------------------------------------------------------------


class TestNormalizePayloadCourses:
    def test_valid_course_payload(self):
        result = entity_impl._normalize_payload_impl("courses", {
            "course_code": "CS101",
            "title": "Intro to CS",
            "credits": "3",
            "program_id": "1",
            "status": "active",
            "tenant_id": "1",
        })
        assert result["credits"] == 3
        assert result["program_id"] == 1

    def test_negative_credits(self):
        with pytest.raises(ValueError, match="non-negative"):
            entity_impl._normalize_payload_impl("courses", {
                "course_code": "CS101",
                "title": "Intro to CS",
                "credits": "-1",
                "program_id": "1",
                "status": "active",
                "tenant_id": "1",
            })

    def test_non_integer_credits(self):
        with pytest.raises(ValueError, match="integer"):
            entity_impl._normalize_payload_impl("courses", {
                "course_code": "CS101",
                "title": "Intro to CS",
                "credits": "abc",
                "program_id": "1",
                "status": "active",
                "tenant_id": "1",
            })

    def test_non_positive_program_id(self):
        with pytest.raises(ValueError, match="must be positive"):
            entity_impl._normalize_payload_impl("courses", {
                "course_code": "CS101",
                "title": "Intro to CS",
                "credits": "3",
                "program_id": "0",
                "status": "active",
                "tenant_id": "1",
            })

    def test_non_integer_program_id(self):
        with pytest.raises(ValueError, match="must be an integer"):
            entity_impl._normalize_payload_impl("courses", {
                "course_code": "CS101",
                "title": "Intro to CS",
                "credits": "3",
                "program_id": "abc",
                "status": "active",
                "tenant_id": "1",
            })


# ---------------------------------------------------------------------------
# Memory CRUD — create / list / update / delete
# ---------------------------------------------------------------------------


class TestMemoryCreateEntity:
    def test_create_student(self):
        result = entity_impl.create_entity_impl("students", {
            "student_id": "S001",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "status": "active",
            "tenant_id": "1",
        })
        assert result["id"] == 1
        assert result["first_name"] == "Alice"
        assert "created_at" in result

    def test_create_program(self):
        result = entity_impl.create_entity_impl("programs", {
            "program_code": "CS",
            "title": "Computer Science",
            "degree_type": "Bachelor",
            "faculty": "Engineering",
            "status": "active",
            "tenant_id": "1",
        })
        assert result["id"] == 1
        assert result["program_code"] == "CS"

    def test_unknown_entity_raises(self):
        with pytest.raises(ValueError, match="unknown entity"):
            entity_impl.create_entity_impl("nonexistent_entity", {})

    def test_create_course_with_valid_fk(self):
        # Create a program first
        entity_impl.create_entity_impl("programs", {
            "program_code": "CS",
            "title": "Computer Science",
            "degree_type": "Bachelor",
            "faculty": "Engineering",
            "status": "active",
            "tenant_id": "1",
        })
        # Now create a course referencing it
        result = entity_impl.create_entity_impl("courses", {
            "course_code": "CS101",
            "title": "Intro",
            "credits": "3",
            "program_id": "1",
            "status": "active",
            "tenant_id": "1",
        })
        assert result["id"] == 1
        assert result["program_id"] == 1

    def test_create_course_with_missing_fk(self):
        with pytest.raises(ValueError, match="unknown program"):
            entity_impl.create_entity_impl("courses", {
                "course_code": "CS101",
                "title": "Intro",
                "credits": "3",
                "program_id": "999",
                "status": "active",
                "tenant_id": "1",
            })


class TestMemoryListEntities:
    def test_empty_list(self):
        result = entity_impl.list_entities_impl("students")
        assert result == []

    def test_list_after_create(self):
        entity_impl.create_entity_impl("programs", {"program_code": "CS", "title": "CS", "degree_type": "BS", "faculty": "Eng", "status": "active", "tenant_id": "1"})
        entity_impl.create_entity_impl("programs", {"program_code": "EE", "title": "EE", "degree_type": "BS", "faculty": "Eng", "status": "active", "tenant_id": "1"})
        result = entity_impl.list_entities_impl("programs")
        assert len(result) == 2
        assert result[0]["id"] < result[1]["id"]

    def test_unknown_entity(self):
        with pytest.raises(ValueError, match="unknown entity"):
            entity_impl.list_entities_impl("nonexistent")


class TestMemoryUpdateEntity:
    def test_update_existing(self):
        entity_impl.create_entity_impl("programs", {"program_code": "CS", "title": "Old Name", "degree_type": "BS", "faculty": "Eng", "status": "active", "tenant_id": "1"})
        result = entity_impl.update_entity_impl("programs", 1, {"program_code": "CS", "title": "New Name", "degree_type": "BS", "faculty": "Eng", "status": "active", "tenant_id": "1"})
        assert result["title"] == "New Name"

    def test_update_not_found(self):
        with pytest.raises(ValueError, match="not found"):
            entity_impl.update_entity_impl("programs", 999, {"program_code": "CS", "title": "N", "degree_type": "BS", "faculty": "Eng", "status": "active", "tenant_id": "1"})

    def test_update_student_preserves_created_at(self):
        created = entity_impl.create_entity_impl("students", {
            "student_id": "S001", "first_name": "A", "last_name": "B",
            "email": "a@b.com", "status": "active", "tenant_id": "1",
        })
        updated = entity_impl.update_entity_impl("students", 1, {
            "student_id": "S001", "first_name": "Updated", "last_name": "B",
            "email": "a@b.com", "status": "active", "tenant_id": "1",
        })
        assert updated["created_at"] == created["created_at"]
        assert updated["first_name"] == "Updated"


class TestMemoryDeleteEntity:
    def test_delete_existing(self):
        entity_impl.create_entity_impl("programs", {"program_code": "CS", "title": "CS", "degree_type": "BS", "faculty": "Eng", "status": "active", "tenant_id": "1"})
        result = entity_impl.delete_entity_impl("programs", 1)
        assert result["id"] == 1
        assert entity_impl.list_entities_impl("programs") == []

    def test_delete_not_found(self):
        with pytest.raises(ValueError, match="not found"):
            entity_impl.delete_entity_impl("programs", 999)


# ---------------------------------------------------------------------------
# _should_fallback_to_memory_impl
# ---------------------------------------------------------------------------


class TestShouldFallbackToMemory:
    def test_db_unavailable_runtime_error(self):
        assert entity_impl._should_fallback_to_memory_impl(
            RuntimeError("database unavailable")
        ) is True

    def test_other_runtime_error(self):
        assert entity_impl._should_fallback_to_memory_impl(
            RuntimeError("some other error")
        ) is False

    def test_connection_error(self):
        assert entity_impl._should_fallback_to_memory_impl(ConnectionError()) is True

    def test_timeout_error(self):
        assert entity_impl._should_fallback_to_memory_impl(TimeoutError()) is True

    def test_os_error(self):
        assert entity_impl._should_fallback_to_memory_impl(OSError()) is True

    def test_value_error(self):
        assert entity_impl._should_fallback_to_memory_impl(ValueError()) is True

    def test_key_error_not_fallback(self):
        assert entity_impl._should_fallback_to_memory_impl(KeyError()) is False


# ---------------------------------------------------------------------------
# _sql_identifier_impl
# ---------------------------------------------------------------------------


class TestSqlIdentifier:
    def test_valid_identifier(self):
        # Only works if psycopg is available
        if university_shared.psycopg is not None:
            result = entity_impl._sql_identifier_impl("app_students")
            assert result is not None

    def test_empty_raises_without_psycopg(self):
        # If psycopg missing, raises RuntimeError
        if university_shared.psycopg is None:
            with pytest.raises(RuntimeError, match="database unavailable"):
                entity_impl._sql_identifier_impl("test")

    def test_unsafe_identifier(self):
        if university_shared.psycopg is not None:
            with pytest.raises(ValueError, match="unsafe SQL identifier"):
                entity_impl._sql_identifier_impl("DROP TABLE; --")


# ---------------------------------------------------------------------------
# _row_to_dict_impl
# ---------------------------------------------------------------------------


class TestRowToDict:
    def test_without_created_at(self):
        row = (42, "CS101", "Intro", 3, 1, "active", "1")
        fields = ("course_code", "title", "credits", "program_id", "status", "tenant_id")
        result = entity_impl._row_to_dict_impl(row, fields, include_created_at=False)
        assert result["id"] == 42
        assert result["course_code"] == "CS101"
        assert "created_at" not in result

    def test_with_created_at(self):
        from datetime import datetime, timezone
        ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
        row = (1, ts, "S001", "John", "Doe", "j@e.com", "active", "1")
        fields = ("student_id", "first_name", "last_name", "email", "status", "tenant_id")
        result = entity_impl._row_to_dict_impl(row, fields, include_created_at=True)
        assert result["id"] == 1
        assert result["created_at"] == ts.isoformat()
        assert result["first_name"] == "John"


# ---------------------------------------------------------------------------
# FK validation in memory
# ---------------------------------------------------------------------------


class TestForeignKeyValidation:
    def test_course_requires_existing_program(self):
        with pytest.raises(ValueError, match="unknown program"):
            entity_impl._validate_foreign_keys_memory_impl("courses", {"program_id": 999})

    def test_course_with_valid_program(self):
        university_shared._state.data["programs"][1] = {"id": 1}
        entity_impl._validate_foreign_keys_memory_impl("courses", {"program_id": 1})
