"""
W126 — research_ethics domain depth tests.

Guard: _check_pi_has_active_contract_for_ethics_review
- Blocks when no faculty_contracts records found for PI (fail-closed)
- Blocks when PI contract is terminated/resigned
- Blocks on lookup exception (fail-closed)
- Passes when PI has active contract
- create_ethics_review: guard fires FIRST before cap check and persistence
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.research_ethics.service import (
    _PI_CONTRACT_ACTIVE_STATUSES,
    _check_pi_has_active_contract_for_ethics_review,
    create_ethics_review,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TENANT = 77
_PI = "pi-001"


def _contract(status: str, pi_id: str = _PI) -> dict:
    return {"faculty_id": pi_id, "status": status, "id": "c1"}


def _alt_contract(status: str, pi_id: str = _PI) -> dict:
    return {"employee_id": pi_id, "contract_status": status, "id": "c2"}


def _review_payload(**kwargs) -> dict:
    defaults = {
        "principal_investigator_id": _PI,
        "review_type": "irb",
        "status": "pending",
        "risk_level": "low",
        "review_code": "IRB-2026-001",
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# TestW126Constants
# ---------------------------------------------------------------------------


class TestW126Constants:
    def test_pi_contract_active_statuses_is_frozenset(self):
        assert isinstance(_PI_CONTRACT_ACTIVE_STATUSES, frozenset)

    def test_active_in_statuses(self):
        assert "active" in _PI_CONTRACT_ACTIVE_STATUSES

    def test_terminated_not_in_statuses(self):
        assert "terminated" not in _PI_CONTRACT_ACTIVE_STATUSES

    def test_resigned_not_in_statuses(self):
        assert "resigned" not in _PI_CONTRACT_ACTIVE_STATUSES

    def test_expired_not_in_statuses(self):
        assert "expired" not in _PI_CONTRACT_ACTIVE_STATUSES

    def test_inactive_not_in_statuses(self):
        assert "inactive" not in _PI_CONTRACT_ACTIVE_STATUSES

    def test_statuses_immutable(self):
        with pytest.raises((AttributeError, TypeError)):
            _PI_CONTRACT_ACTIVE_STATUSES.add("temp")  # type: ignore[attr-defined]

    def test_statuses_nonempty(self):
        assert len(_PI_CONTRACT_ACTIVE_STATUSES) >= 1

    def test_statuses_lowercase(self):
        for s in _PI_CONTRACT_ACTIVE_STATUSES:
            assert s == s.lower()

    def test_pending_not_in_statuses(self):
        assert "pending" not in _PI_CONTRACT_ACTIVE_STATUSES


# ---------------------------------------------------------------------------
# TestW126GuardSignature
# ---------------------------------------------------------------------------


class TestW126GuardSignature:
    def test_guard_callable(self):
        assert callable(_check_pi_has_active_contract_for_ethics_review)

    def test_guard_requires_keyword_args(self):
        with pytest.raises(TypeError):
            _check_pi_has_active_contract_for_ethics_review(_TENANT, _PI)  # type: ignore[call-arg]

    def test_guard_requires_pi_id(self):
        with pytest.raises(TypeError):
            _check_pi_has_active_contract_for_ethics_review(tenant_id=_TENANT)

    def test_guard_returns_none_on_success(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        result = _check_pi_has_active_contract_for_ethics_review(
            tenant_id=_TENANT, pi_id=_PI
        )
        assert result is None

    def test_guard_strips_whitespace_pi_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        _check_pi_has_active_contract_for_ethics_review(
            tenant_id=_TENANT, pi_id="  pi-001  "
        )


# ---------------------------------------------------------------------------
# TestW126GuardFailures
# ---------------------------------------------------------------------------


class TestW126GuardFailures:
    def test_blocks_when_no_contracts_at_all(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )

    def test_blocks_when_contracts_wrong_pi(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active", pi_id="other-pi")],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )

    def test_blocks_when_contract_terminated(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("terminated")],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )

    def test_blocks_when_contract_resigned(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("resigned")],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )

    def test_blocks_when_contract_expired(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("expired")],
        )
        with pytest.raises(DomainValidationError):
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )

    def test_error_contains_pi_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )
        assert _PI in str(exc_info.value)


# ---------------------------------------------------------------------------
# TestW126FailClosed
# ---------------------------------------------------------------------------


class TestW126FailClosed:
    def test_fail_closed_on_runtime_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise RuntimeError("DB connection lost")

        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError, match="faculty_contracts lookup failed"):
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )

    def test_fail_closed_error_includes_pi_id(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ConnectionError("timeout")

        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )
        assert _PI in str(exc_info.value)

    def test_fail_closed_on_value_error(self, monkeypatch):
        def boom(entity_type, tenant_id):
            raise ValueError("bad data")

        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )

    def test_fail_closed_no_open_fallback(self, monkeypatch):
        call_count = []

        def boom(entity_type, tenant_id):
            call_count.append(1)
            raise OSError("network down")

        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant", boom
        )
        with pytest.raises(DomainValidationError):
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )
        assert call_count == [1]


# ---------------------------------------------------------------------------
# TestW126CreatePath
# ---------------------------------------------------------------------------


class TestW126CreatePath:
    def test_guard_called_before_cap_and_create(self, monkeypatch):
        guard_called = []

        def mock_guard(*, tenant_id, pi_id):
            guard_called.append(pi_id)

        create_called = []

        monkeypatch.setattr(
            "app.modules.research_ethics.service._check_pi_has_active_contract_for_ethics_review",
            mock_guard,
        )
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        monkeypatch.setattr(
            "app.modules.research_ethics.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: create_called.append(True) or {
                "id": 1, **payload
            },
        )
        create_ethics_review(_review_payload(), _TENANT)
        assert guard_called == [_PI]
        assert create_called

    def test_create_not_called_when_guard_blocks(self, monkeypatch):
        created = []
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [],
        )
        monkeypatch.setattr(
            "app.modules.research_ethics.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: created.append(payload) or {"id": 1},
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            create_ethics_review(_review_payload(), _TENANT)
        assert created == []

    def test_blocks_missing_pi_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        with pytest.raises(DomainValidationError, match="principal_investigator_id is required"):
            create_ethics_review(_review_payload(principal_investigator_id=""), _TENANT)

    def test_succeeds_with_active_contract(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("active")],
        )
        monkeypatch.setattr(
            "app.modules.research_ethics.service.create_entity_for_tenant",
            lambda entity_type, payload, tenant_id: {"id": 99, **payload},
        )
        result = create_ethics_review(_review_payload(), _TENANT)
        assert result["id"] == 99

    def test_blocked_terminated_pi(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("terminated")],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            create_ethics_review(_review_payload(), _TENANT)


# ---------------------------------------------------------------------------
# TestW126BusinessInvariants
# ---------------------------------------------------------------------------


class TestW126BusinessInvariants:
    def test_allows_alt_key_contract_status(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_alt_contract("active")],
        )
        result = _check_pi_has_active_contract_for_ethics_review(
            tenant_id=_TENANT, pi_id=_PI
        )
        assert result is None

    def test_two_tenant_isolation(self, monkeypatch):
        calls = []

        def mock_list(entity_type, tenant_id):
            calls.append(tenant_id)
            return [_contract("active")] if tenant_id == 1 else []

        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant", mock_list
        )
        _check_pi_has_active_contract_for_ethics_review(tenant_id=1, pi_id=_PI)
        with pytest.raises(DomainValidationError):
            _check_pi_has_active_contract_for_ethics_review(tenant_id=2, pi_id=_PI)
        assert 1 in calls and 2 in calls

    def test_multiple_contracts_one_active_passes(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [
                _contract("terminated"),
                _contract("active"),
                _contract("expired"),
            ],
        )
        _check_pi_has_active_contract_for_ethics_review(
            tenant_id=_TENANT, pi_id=_PI
        )

    def test_all_terminated_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("terminated"), _contract("resigned")],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )

    def test_error_message_contains_ethics_review_context(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant",
            lambda entity_type, tenant_id: [_contract("terminated")],
        )
        with pytest.raises(DomainValidationError) as exc_info:
            _check_pi_has_active_contract_for_ethics_review(
                tenant_id=_TENANT, pi_id=_PI
            )
        msg = str(exc_info.value)
        assert "ethics review" in msg.lower() or "terminated" in msg

    def test_lookup_queries_faculty_contracts_entity(self, monkeypatch):
        queried = []

        def mock_list(entity_type, tenant_id):
            queried.append(entity_type)
            return [_contract("active")]

        monkeypatch.setattr(
            "app.modules.research_ethics.service.list_entities_for_tenant", mock_list
        )
        _check_pi_has_active_contract_for_ethics_review(
            tenant_id=_TENANT, pi_id=_PI
        )
        assert "faculty_contracts" in queried
