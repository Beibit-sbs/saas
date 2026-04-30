"""
W124 — teaching_quality domain depth tests.

Guard: _check_faculty_has_active_contract_for_quality_metric
- Blocks when no faculty_contracts records found (fail-closed)
- Blocks when no active contract (terminated/resigned)
- Blocks on lookup exception (fail-closed)
- Passes when active contract exists
- create_quality_metric: guard fires FIRST before create_teaching_quality_record
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.teaching_quality.service import (
    _FACULTY_CONTRACT_ACTIVE_STATUSES,
    _check_faculty_has_active_contract_for_quality_metric,
    create_quality_metric,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TENANT = 42
_FACULTY = "fac-001"


def _contract(status: str, faculty_id: str = _FACULTY) -> dict:
    return {"faculty_id": faculty_id, "status": status, "id": "c1"}


def _alt_contract(status: str, faculty_id: str = _FACULTY) -> dict:
    """Simulate contract using contract_status key variant."""
    return {"employee_id": faculty_id, "contract_status": status, "id": "c2"}


# ---------------------------------------------------------------------------
# TestW124Constants
# ---------------------------------------------------------------------------


class TestW124Constants:
    def test_active_statuses_is_frozenset(self):
        assert isinstance(_FACULTY_CONTRACT_ACTIVE_STATUSES, frozenset)

    def test_active_in_statuses(self):
        assert "active" in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_terminated_not_in_statuses(self):
        assert "terminated" not in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_resigned_not_in_statuses(self):
        assert "resigned" not in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_expired_not_in_statuses(self):
        assert "expired" not in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_pending_not_in_statuses(self):
        assert "pending" not in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_inactive_not_in_statuses(self):
        assert "inactive" not in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_statuses_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _FACULTY_CONTRACT_ACTIVE_STATUSES.add("temp")  # type: ignore[attr-defined]

    def test_statuses_nonempty(self):
        assert len(_FACULTY_CONTRACT_ACTIVE_STATUSES) >= 1

    def test_active_statuses_lowercase(self):
        for s in _FACULTY_CONTRACT_ACTIVE_STATUSES:
            assert s == s.lower()


# ---------------------------------------------------------------------------
# TestW124GuardSignature
# ---------------------------------------------------------------------------


class TestW124GuardSignature:
    def test_guard_callable(self):
        assert callable(_check_faculty_has_active_contract_for_quality_metric)

    def test_guard_requires_keyword_tenant_id(self):
        with pytest.raises(TypeError):
            _check_faculty_has_active_contract_for_quality_metric(_TENANT, _FACULTY)  # type: ignore[call-arg]

    def test_guard_requires_keyword_faculty_id(self):
        with pytest.raises(TypeError):
            _check_faculty_has_active_contract_for_quality_metric(tenant_id=_TENANT)

    def test_guard_returns_none_on_success(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        result = _check_faculty_has_active_contract_for_quality_metric(
            tenant_id=_TENANT, faculty_id=_FACULTY
        )
        assert result is None

    def test_guard_strips_whitespace_faculty_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        # Should not raise
        _check_faculty_has_active_contract_for_quality_metric(
            tenant_id=_TENANT, faculty_id="  fac-001  "
        )


# ---------------------------------------------------------------------------
# TestW124GuardFailures
# ---------------------------------------------------------------------------


class TestW124GuardFailures:
    def test_blocks_when_no_contracts_at_all(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )

    def test_blocks_when_contracts_exist_but_wrong_faculty(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active", faculty_id="other-fac")],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )

    def test_blocks_when_contract_terminated(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("terminated")],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )

    def test_blocks_when_contract_resigned(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("resigned")],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )

    def test_blocks_when_contract_expired(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("expired")],
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )

    def test_blocks_when_contract_inactive(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("inactive")],
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )


# ---------------------------------------------------------------------------
# TestW124FailClosed
# ---------------------------------------------------------------------------


class TestW124FailClosed:
    def test_fail_closed_on_lookup_exception(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise RuntimeError("DB connection lost")

        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError, match="faculty_contracts lookup failed"):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )

    def test_fail_closed_error_includes_faculty_id(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ConnectionError("timeout")

        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError, match=_FACULTY):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )

    def test_fail_closed_on_value_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ValueError("malformed data")

        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )

    def test_fail_closed_not_open_by_default(self, monkeypatch):
        """Verify there's no fallback/allow path on exception."""
        call_count = []

        def boom(entity_type, tenant_id):
            call_count.append(1)
            raise OSError("unreachable")

        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )
        assert call_count == [1]


# ---------------------------------------------------------------------------
# TestW124CreatePath
# ---------------------------------------------------------------------------


class TestW124CreatePath:
    def _setup_active(self, monkeypatch, captured: list):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.create_teaching_quality_record",
            lambda payload, tenant_id: {"id": "new-1", **payload, "captured": captured.append(payload) or True},
        )

    def test_guard_called_before_create(self, monkeypatch):
        order = []
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: order.append("guard") or [_contract("active")],
        )
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.create_teaching_quality_record",
            lambda payload, tenant_id: order.append("create") or {"id": "x"},
        )
        create_quality_metric({"faculty_id": _FACULTY, "quality_score": 80}, _TENANT)
        assert order[0] == "guard"
        assert order[1] == "create"

    def test_create_not_called_when_guard_blocks(self, monkeypatch):
        created = []
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("terminated")],
        )
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.create_teaching_quality_record",
            lambda payload, tenant_id: created.append(payload) or {"id": "x"},
        )
        with pytest.raises(DomainValidationError):
            create_quality_metric({"faculty_id": _FACULTY, "quality_score": 80}, _TENANT)
        assert created == []

    def test_create_blocked_no_faculty_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        with pytest.raises(DomainValidationError, match="faculty_id is required"):
            create_quality_metric({"quality_score": 80}, _TENANT)

    def test_create_succeeds_with_active_contract(self, monkeypatch):
        captured: list = []
        self._setup_active(monkeypatch, captured)
        result = create_quality_metric({"faculty_id": _FACULTY, "quality_score": 85.0}, _TENANT)
        assert result["id"] == "new-1"
        assert len(captured) == 1

    def test_create_passes_payload_to_record(self, monkeypatch):
        captured: list = []
        self._setup_active(monkeypatch, captured)
        create_quality_metric(
            {"faculty_id": _FACULTY, "quality_score": 90.0, "term_id": 5}, _TENANT
        )
        assert captured[0]["term_id"] == 5

    def test_create_blocked_when_no_contracts(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            create_quality_metric({"faculty_id": _FACULTY, "quality_score": 75}, _TENANT)


# ---------------------------------------------------------------------------
# TestW124BusinessInvariants
# ---------------------------------------------------------------------------


class TestW124BusinessInvariants:
    def test_allows_active_contract_status_key(self, monkeypatch):
        """status key variant."""
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [{"faculty_id": _FACULTY, "status": "active"}],
        )
        result = _check_faculty_has_active_contract_for_quality_metric(
            tenant_id=_TENANT, faculty_id=_FACULTY
        )
        assert result is None

    def test_allows_contract_status_alt_key(self, monkeypatch):
        """contract_status key variant."""
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_alt_contract("active")],
        )
        result = _check_faculty_has_active_contract_for_quality_metric(
            tenant_id=_TENANT, faculty_id=_FACULTY
        )
        assert result is None

    def test_two_tenant_isolation_guard(self, monkeypatch):
        """Tenant A active contract does NOT satisfy Tenant B guard."""
        calls = []

        def mock_list(entity_type, tenant_id):
            calls.append(tenant_id)
            # Only tenant 1 has an active contract
            if tenant_id == 1:
                return [_contract("active")]
            return []

        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant", mock_list
        )
        # Tenant 1 succeeds
        _check_faculty_has_active_contract_for_quality_metric(tenant_id=1, faculty_id=_FACULTY)
        # Tenant 2 blocked
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=2, faculty_id=_FACULTY
            )
        assert 1 in calls
        assert 2 in calls

    def test_multiple_contracts_one_active_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                _contract("terminated"),
                _contract("active"),
                _contract("expired"),
            ],
        )
        # Should not raise — at least one active
        _check_faculty_has_active_contract_for_quality_metric(
            tenant_id=_TENANT, faculty_id=_FACULTY
        )

    def test_all_terminated_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                _contract("terminated"),
                _contract("resigned"),
            ],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )

    def test_error_message_contains_faculty_id_on_no_contract(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.teaching_quality.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_faculty_has_active_contract_for_quality_metric(
                tenant_id=_TENANT, faculty_id=_FACULTY
            )
        assert _FACULTY in str(exc_info.value)
