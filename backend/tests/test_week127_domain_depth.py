"""
W127 — advising domain depth tests.

Guard: _check_advisor_is_active_faculty_for_advising
- Blocks when advisor not found in faculty registry
- Blocks when advisor has non-active faculty status (terminated/resigned)
- Blocks on faculty lookup exception (fail-closed)
- Passes when advisor has active faculty status
- create_advising_session: guard fires FIRST before cap and enrollment checks
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.advising.service import (
    _ADVISOR_FACULTY_ACTIVE_STATUSES,
    _check_advisor_is_active_faculty_for_advising,
    create_advising_session,
)
from app.modules.advising.schemas import AdvisingSessionCreateSchema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TENANT = 88
_ADVISOR_ID = "faculty-adv-001"
_STUDENT_ID = 42


def _faculty(status: str, faculty_id: str = _ADVISOR_ID) -> dict:
    return {"id": 1, "faculty_id": faculty_id, "status": status}


def _session_payload(**kwargs) -> AdvisingSessionCreateSchema:
    defaults = {
        "student_id": _STUDENT_ID,
        "advisor_id": _ADVISOR_ID,
        "session_type": "academic",
        "scheduled_at": "2026-05-01T10:00:00",
        "notes": "Mid-semester check-in",
    }
    defaults.update(kwargs)
    return AdvisingSessionCreateSchema(**defaults)


# ---------------------------------------------------------------------------
# TestW127Constants
# ---------------------------------------------------------------------------


class TestW127Constants:
    def test_advisor_faculty_active_statuses_is_frozenset(self):
        assert isinstance(_ADVISOR_FACULTY_ACTIVE_STATUSES, frozenset)

    def test_active_in_statuses(self):
        assert "active" in _ADVISOR_FACULTY_ACTIVE_STATUSES

    def test_terminated_not_in_statuses(self):
        assert "terminated" not in _ADVISOR_FACULTY_ACTIVE_STATUSES

    def test_resigned_not_in_statuses(self):
        assert "resigned" not in _ADVISOR_FACULTY_ACTIVE_STATUSES

    def test_on_leave_not_in_statuses(self):
        assert "on_leave" not in _ADVISOR_FACULTY_ACTIVE_STATUSES

    def test_inactive_not_in_statuses(self):
        assert "inactive" not in _ADVISOR_FACULTY_ACTIVE_STATUSES

    def test_statuses_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _ADVISOR_FACULTY_ACTIVE_STATUSES.add("temp")  # type: ignore[attr-defined]

    def test_statuses_nonempty(self):
        assert len(_ADVISOR_FACULTY_ACTIVE_STATUSES) >= 1

    def test_statuses_lowercase(self):
        for s in _ADVISOR_FACULTY_ACTIVE_STATUSES:
            assert s == s.lower()

    def test_pending_not_in_statuses(self):
        assert "pending" not in _ADVISOR_FACULTY_ACTIVE_STATUSES


# ---------------------------------------------------------------------------
# TestW127GuardSignature
# ---------------------------------------------------------------------------


class TestW127GuardSignature:
    def test_guard_callable(self):
        assert callable(_check_advisor_is_active_faculty_for_advising)

    def test_guard_requires_keyword_args(self):
        with pytest.raises(TypeError):
            _check_advisor_is_active_faculty_for_advising(_TENANT, _ADVISOR_ID)  # type: ignore[call-arg]

    def test_guard_requires_advisor_id(self):
        with pytest.raises(TypeError):
            _check_advisor_is_active_faculty_for_advising(tenant_id=_TENANT)

    def test_guard_returns_none_on_success(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_faculty("active")],
        )
        result = _check_advisor_is_active_faculty_for_advising(
            tenant_id=_TENANT, advisor_id=_ADVISOR_ID
        )
        assert result is None

    def test_guard_strips_whitespace_advisor_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_faculty("active")],
        )
        _check_advisor_is_active_faculty_for_advising(
            tenant_id=_TENANT, advisor_id="  faculty-adv-001  "
        )


# ---------------------------------------------------------------------------
# TestW127GuardFailures
# ---------------------------------------------------------------------------


class TestW127GuardFailures:
    def test_blocks_when_advisor_not_in_faculty(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="not found in faculty registry"):
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )

    def test_blocks_when_advisor_faculty_is_different_person(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_faculty("active", faculty_id="other-faculty")],
        )
        with pytest.raises(DomainValidationError, match="not found in faculty registry"):
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )

    def test_blocks_when_advisor_terminated(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_faculty("terminated")],
        )
        with pytest.raises(DomainValidationError, match="(?i)terminated or resigned"):
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_faculty("resigned")],
        )
        with pytest.raises(DomainValidationError, match="(?i)terminated or resigned"):
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )

    def test_blocks_when_advisor_on_leave(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_faculty("on_leave")],
        )
        with pytest.raises(DomainValidationError):
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )

    def test_error_contains_advisor_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )
        assert _ADVISOR_ID in str(exc_info.value)


# ---------------------------------------------------------------------------
# TestW127FailClosed
# ---------------------------------------------------------------------------


class TestW127FailClosed:
    def test_fail_closed_on_runtime_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise RuntimeError("DB unavailable")

        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError, match="faculty lookup failed"):
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )

    def test_fail_closed_error_contains_advisor_id(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ConnectionError("network timeout")

        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )
        assert _ADVISOR_ID in str(exc_info.value)

    def test_fail_closed_on_value_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ValueError("schema mismatch")

        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )

    def test_fail_closed_no_open_fallback(self, monkeypatch):
        call_count = []

        def boom(entity_type, tenant_id):
            call_count.append(1)
            raise OSError("fs error")

        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )
        assert call_count == [1]


# ---------------------------------------------------------------------------
# TestW127CreatePath
# ---------------------------------------------------------------------------


class TestW127CreatePath:
    def _setup(self, monkeypatch, created_list: list):
        """Set up working mocks for create_advising_session tests."""
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: (
                [_faculty("active")] if entity_type == "faculty"
                else [{"student_id": _STUDENT_ID, "status": "enrolled"}] if entity_type == "enrollments"
                else []
            ),
        )
        monkeypatch.setattr(
            "app.modules.advising.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: created_list.append(payload) or {
                "id": 99,
                "student_id": payload.get("student_id"),
                "advisor_id": payload.get("advisor_id"),
                "session_type": payload.get("session_type"),
                "status": payload.get("status", "scheduled"),
                "scheduled_at": payload.get("scheduled_at"),
                "notes": payload.get("notes"),
                "outcome": payload.get("outcome", "pending"),
            },
        )
        monkeypatch.setattr(
            "app.modules.advising.service.log_admin_action",
            lambda **kw: None,
        )

    def test_guard_called_before_cap_and_enrollment(self, monkeypatch):
        guard_called = []
        created = []
        self._setup(monkeypatch, created)

        def mock_guard(*, tenant_id, advisor_id):
            guard_called.append(advisor_id)

        monkeypatch.setattr(
            "app.modules.advising.service._check_advisor_is_active_faculty_for_advising",
            mock_guard,
        )
        create_advising_session(_TENANT, _session_payload(), "actor")
        assert guard_called == [_ADVISOR_ID]
        assert len(created) >= 1

    def test_create_not_called_when_guard_blocks(self, monkeypatch):
        created = []
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        monkeypatch.setattr(
            "app.modules.advising.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: created.append(payload) or {"id": 1},
        )
        with pytest.raises(DomainValidationError):
            create_advising_session(_TENANT, _session_payload(), "actor")
        assert created == []

    def test_guard_blocks_terminated_advisor(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: (
                [_faculty("terminated")] if entity_type == "faculty" else []
            ),
        )
        with pytest.raises(DomainValidationError, match="(?i)terminated or resigned"):
            create_advising_session(_TENANT, _session_payload(), "actor")

    def test_succeeds_with_active_advisor(self, monkeypatch):
        created = []
        self._setup(monkeypatch, created)
        result = create_advising_session(_TENANT, _session_payload(), "actor")
        assert result.advisor_id == _ADVISOR_ID
        assert len(created) >= 1

    def test_guard_fires_before_enrollment_guard(self, monkeypatch):
        """W127 guard fires before W100 enrollment guard — terminated advisor blocked immediately."""
        enrollment_calls = []
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: (
                [_faculty("terminated")] if entity_type == "faculty"
                else enrollment_calls.append(entity_type) or []
            ),
        )
        with pytest.raises(DomainValidationError, match="(?i)terminated or resigned"):
            create_advising_session(_TENANT, _session_payload(), "actor")
        # enrollment lookup should not have been called if advisor guard fires first
        assert "enrollments" not in enrollment_calls


# ---------------------------------------------------------------------------
# TestW127BusinessInvariants
# ---------------------------------------------------------------------------


class TestW127BusinessInvariants:
    def test_allows_alt_key_employee_id(self, monkeypatch):
        """Accepts advisor matched via employee_id field."""
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                {"id": 1, "employee_id": _ADVISOR_ID, "status": "active"}
            ],
        )
        result = _check_advisor_is_active_faculty_for_advising(
            tenant_id=_TENANT, advisor_id=_ADVISOR_ID
        )
        assert result is None

    def test_two_tenant_isolation(self, monkeypatch):
        queried_tenants = []

        def mock_list(entity_type, tenant_id):
            queried_tenants.append(tenant_id)
            return [_faculty("active")] if tenant_id == 1 else []

        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant", mock_list
        )
        _check_advisor_is_active_faculty_for_advising(tenant_id=1, advisor_id=_ADVISOR_ID)
        with pytest.raises(DomainValidationError):
            _check_advisor_is_active_faculty_for_advising(tenant_id=2, advisor_id=_ADVISOR_ID)
        assert 1 in queried_tenants and 2 in queried_tenants

    def test_multiple_faculty_one_active_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                _faculty("terminated"),
                _faculty("active"),
            ],
        )
        _check_advisor_is_active_faculty_for_advising(
            tenant_id=_TENANT, advisor_id=_ADVISOR_ID
        )

    def test_all_terminated_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                _faculty("terminated"),
                _faculty("resigned"),
            ],
        )
        with pytest.raises(DomainValidationError, match="(?i)terminated or resigned"):
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )

    def test_error_message_advising_context(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_faculty("terminated")],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_advisor_is_active_faculty_for_advising(
                tenant_id=_TENANT, advisor_id=_ADVISOR_ID
            )
        msg = str(exc_info.value)
        assert "advising" in msg.lower() or "terminated" in msg

    def test_lookup_queries_faculty_entity(self, monkeypatch):
        queried = []

        def mock_list(entity_type, tenant_id):
            queried.append(entity_type)
            return [_faculty("active")]

        monkeypatch.setattr(
            "app.modules.advising.service.list_entities_for_tenant", mock_list
        )
        _check_advisor_is_active_faculty_for_advising(
            tenant_id=_TENANT, advisor_id=_ADVISOR_ID
        )
        assert "faculty" in queried
