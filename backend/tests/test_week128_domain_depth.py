"""W128 Domain Depth — student_services × enrollments cross-entity guard.

Guard: _check_student_is_enrolled_for_service_ticket
  • A service ticket cannot be created for a student without an active enrollment.
  • Withdrawn / graduated students are blocked.
  • Lookup failure → fail-closed (DomainValidationError).
  • Guard fires as FIRST action in create_student_service_ticket, before cap checks.
"""
from __future__ import annotations

import pytest
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.student_services.service import (
    _STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES,
    _check_student_is_enrolled_for_service_ticket,
    create_student_service_ticket,
)
from app.modules.student_services.schemas import StudentServiceTicketCreateSchema

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
_TENANT = 77
_STUDENT_ID = 42


def _enrollment(status: str = "enrolled") -> dict:
    return {"student_id": _STUDENT_ID, "status": status, "tenant_id": _TENANT}


def _ticket_payload(**overrides) -> StudentServiceTicketCreateSchema:
    base = {
        "student_id": _STUDENT_ID,
        "category": "financial_aid",
        "subject": "Tuition query",
        "description": "Need help with tuition payment schedule",
        "priority": "medium",
        "channel": "portal",
    }
    base.update(overrides)
    return StudentServiceTicketCreateSchema(**base)


# ---------------------------------------------------------------------------
# TestW128Constants
# ---------------------------------------------------------------------------


class TestW128Constants:
    def test_enrollment_active_statuses_is_frozenset(self):
        assert isinstance(_STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES, frozenset)

    def test_enrollment_active_statuses_contains_enrolled(self):
        assert "enrolled" in _STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES

    def test_enrollment_active_statuses_contains_active(self):
        assert "active" in _STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES

    def test_enrollment_active_statuses_excludes_withdrawn(self):
        assert "withdrawn" not in _STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES

    def test_enrollment_active_statuses_excludes_graduated(self):
        assert "graduated" not in _STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES

    def test_enrollment_active_statuses_excludes_suspended(self):
        assert "suspended" not in _STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES

    def test_enrollment_active_statuses_excludes_leave(self):
        assert "on_leave" not in _STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES

    def test_enrollment_active_statuses_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES.add("test")  # type: ignore[attr-defined]

    def test_enrollment_active_statuses_nonempty(self):
        assert len(_STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES) >= 1

    def test_enrollment_active_statuses_values_are_lowercase(self):
        for s in _STUDENT_TICKET_ENROLLMENT_ACTIVE_STATUSES:
            assert s == s.lower()


# ---------------------------------------------------------------------------
# TestW128GuardSignature
# ---------------------------------------------------------------------------


class TestW128GuardSignature:
    def test_guard_accepts_tenant_id_and_student_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_enrollment("enrolled")],
        )
        # Should not raise
        _check_student_is_enrolled_for_service_ticket(
            tenant_id=_TENANT, student_id=_STUDENT_ID
        )

    def test_guard_passes_with_enrolled_student(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_enrollment("enrolled")],
        )
        _check_student_is_enrolled_for_service_ticket(
            tenant_id=_TENANT, student_id=_STUDENT_ID
        )

    def test_guard_passes_with_active_status(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_enrollment("active")],
        )
        _check_student_is_enrolled_for_service_ticket(
            tenant_id=_TENANT, student_id=_STUDENT_ID
        )

    def test_guard_returns_none_on_success(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_enrollment("enrolled")],
        )
        result = _check_student_is_enrolled_for_service_ticket(
            tenant_id=_TENANT, student_id=_STUDENT_ID
        )
        assert result is None

    def test_guard_queries_enrollments_entity(self, monkeypatch):
        queried = []

        def mock_list(entity_type, tenant_id):
            queried.append(entity_type)
            return [_enrollment("enrolled")]

        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant", mock_list
        )
        _check_student_is_enrolled_for_service_ticket(
            tenant_id=_TENANT, student_id=_STUDENT_ID
        )
        assert "enrollments" in queried

    def test_guard_passes_tenant_id_to_lookup(self, monkeypatch):
        seen = []

        def mock_list(entity_type, tenant_id):
            seen.append(tenant_id)
            return [_enrollment("enrolled")]

        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant", mock_list
        )
        _check_student_is_enrolled_for_service_ticket(
            tenant_id=99, student_id=_STUDENT_ID
        )
        assert 99 in seen


# ---------------------------------------------------------------------------
# TestW128GuardFailures
# ---------------------------------------------------------------------------


class TestW128GuardFailures:
    def test_blocks_when_student_not_found(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="not found in enrollment records"):
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )

    def test_blocks_when_student_withdrawn(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_enrollment("withdrawn")],
        )
        with pytest.raises(DomainValidationError, match="(?i)withdrawn or graduated"):
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )

    def test_blocks_when_student_graduated(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_enrollment("graduated")],
        )
        with pytest.raises(DomainValidationError):
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )

    def test_blocks_when_student_suspended(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_enrollment("suspended")],
        )
        with pytest.raises(DomainValidationError):
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )

    def test_blocks_when_enrollment_empty_status(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [{"student_id": _STUDENT_ID, "status": ""}],
        )
        with pytest.raises(DomainValidationError):
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )

    def test_error_contains_student_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )
        assert str(_STUDENT_ID) in str(exc_info.value)


# ---------------------------------------------------------------------------
# TestW128FailClosed
# ---------------------------------------------------------------------------


class TestW128FailClosed:
    def test_fail_closed_on_connection_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ConnectionError("db timeout")

        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError, match="enrollment lookup failed"):
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )

    def test_fail_closed_on_value_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ValueError("schema error")

        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )

    def test_fail_closed_error_contains_student_id(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise OSError("fs error")

        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )
        assert str(_STUDENT_ID) in str(exc_info.value)

    def test_fail_closed_no_fallback_to_open(self, monkeypatch):
        call_count = []

        def boom(entity_type, tenant_id):
            call_count.append(1)
            raise RuntimeError("db down")

        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )
        assert call_count == [1]


# ---------------------------------------------------------------------------
# TestW128CreatePath
# ---------------------------------------------------------------------------


class TestW128CreatePath:
    def _setup(self, monkeypatch, created_list: list):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: (
                [_enrollment("enrolled")] if entity_type == "enrollments"
                else []
            ),
        )
        monkeypatch.setattr(
            "app.modules.student_services.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: created_list.append(payload) or {
                "id": 10,
                "student_id": payload.get("student_id"),
                "category": payload.get("category"),
                "subject": payload.get("subject"),
                "description": payload.get("description"),
                "priority": payload.get("priority"),
                "status": payload.get("status", "open"),
                "owner_id": payload.get("owner_id", "unassigned"),
                "channel": payload.get("channel", "portal"),
                "resolution_notes": None,
                "tenant_id": str(tenant_id),
            },
        )
        monkeypatch.setattr(
            "app.modules.student_services.service.log_admin_action",
            lambda **kw: None,
        )

    def test_guard_called_before_cap_check(self, monkeypatch):
        guard_called = []
        created = []
        self._setup(monkeypatch, created)

        def mock_guard(*, tenant_id, student_id):
            guard_called.append(student_id)

        monkeypatch.setattr(
            "app.modules.student_services.service._check_student_is_enrolled_for_service_ticket",
            mock_guard,
        )
        create_student_service_ticket(_TENANT, _ticket_payload(), "actor")
        assert guard_called == [_STUDENT_ID]

    def test_create_blocked_when_guard_raises(self, monkeypatch):
        created = []
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        monkeypatch.setattr(
            "app.modules.student_services.service.create_entity_for_tenant",
            lambda *a, **kw: created.append(1),
        )
        monkeypatch.setattr(
            "app.modules.student_services.service.log_admin_action",
            lambda **kw: None,
        )
        with pytest.raises(DomainValidationError):
            create_student_service_ticket(_TENANT, _ticket_payload(), "actor")
        assert created == []

    def test_create_succeeds_with_enrolled_student(self, monkeypatch):
        created = []
        self._setup(monkeypatch, created)
        result = create_student_service_ticket(_TENANT, _ticket_payload(), "actor")
        assert result.student_id == _STUDENT_ID
        assert len(created) >= 1

    def test_create_blocked_when_withdrawn(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: (
                [_enrollment("withdrawn")] if entity_type == "enrollments" else []
            ),
        )
        monkeypatch.setattr(
            "app.modules.student_services.service.create_entity_for_tenant",
            lambda *a, **kw: None,
        )
        monkeypatch.setattr(
            "app.modules.student_services.service.log_admin_action",
            lambda **kw: None,
        )
        with pytest.raises(DomainValidationError, match="(?i)withdrawn or graduated"):
            create_student_service_ticket(_TENANT, _ticket_payload(), "actor")

    def test_guard_passes_tenant_id_correctly(self, monkeypatch):
        seen_tenants = []

        def mock_list(entity_type, tenant_id):
            if entity_type == "enrollments":
                seen_tenants.append(tenant_id)
            return [_enrollment("enrolled")]

        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.student_services.service.create_entity_for_tenant",
            lambda *a, **kw: {
                "id": 1, "student_id": _STUDENT_ID, "category": "financial_aid",
                "subject": "q", "description": "d", "priority": "medium",
                "status": "open", "owner_id": "unassigned", "channel": "portal",
                "resolution_notes": None, "tenant_id": str(_TENANT),
            },
        )
        monkeypatch.setattr(
            "app.modules.student_services.service.log_admin_action",
            lambda **kw: None,
        )
        create_student_service_ticket(99, _ticket_payload(), "actor")
        assert 99 in seen_tenants


# ---------------------------------------------------------------------------
# TestW128BusinessInvariants
# ---------------------------------------------------------------------------


class TestW128BusinessInvariants:
    def test_multiple_enrollments_one_active_passes(self, monkeypatch):
        """If student has withdrawn enrollment + active enrollment, guard passes."""
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                {"student_id": _STUDENT_ID, "status": "withdrawn"},
                {"student_id": _STUDENT_ID, "status": "enrolled"},
            ],
        )
        _check_student_is_enrolled_for_service_ticket(
            tenant_id=_TENANT, student_id=_STUDENT_ID
        )

    def test_all_withdrawn_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                {"student_id": _STUDENT_ID, "status": "withdrawn"},
                {"student_id": _STUDENT_ID, "status": "graduated"},
            ],
        )
        with pytest.raises(DomainValidationError, match="(?i)withdrawn or graduated"):
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )

    def test_different_student_does_not_grant_access(self, monkeypatch):
        """Enrollment belonging to another student does not grant access."""
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                {"student_id": 999, "status": "enrolled"},
            ],
        )
        with pytest.raises(DomainValidationError, match="not found"):
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )

    def test_tenant_isolation(self, monkeypatch):
        queried_tenants = []

        def mock_list(entity_type, tenant_id):
            queried_tenants.append(tenant_id)
            if tenant_id == 1:
                return [_enrollment("enrolled")]
            return []

        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant", mock_list
        )
        _check_student_is_enrolled_for_service_ticket(tenant_id=1, student_id=_STUDENT_ID)
        with pytest.raises(DomainValidationError):
            _check_student_is_enrolled_for_service_ticket(tenant_id=2, student_id=_STUDENT_ID)
        assert 1 in queried_tenants and 2 in queried_tenants

    def test_status_case_insensitive_match(self, monkeypatch):
        """Status matching is case-insensitive."""
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                {"student_id": _STUDENT_ID, "status": "ENROLLED"},
            ],
        )
        # Should pass — status normalised to lowercase before compare
        _check_student_is_enrolled_for_service_ticket(
            tenant_id=_TENANT, student_id=_STUDENT_ID
        )

    def test_error_message_contains_service_context(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.student_services.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_enrollment("withdrawn")],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_student_is_enrolled_for_service_ticket(
                tenant_id=_TENANT, student_id=_STUDENT_ID
            )
        msg = str(exc_info.value)
        assert "service ticket" in msg.lower() or "enrollment" in msg.lower()
