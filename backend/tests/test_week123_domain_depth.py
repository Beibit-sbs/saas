"""W123 — syllabus_governance: Faculty Active Contract Guard (behavioral depth).

Real-world problem:
    create_syllabus() had only a department-level SLA cap guard — NO cross-entity check
    that the assigned faculty member actually has an active employment contract.
    A terminated or resigned instructor could be assigned as syllabus author, creating
    ghost syllabi with no valid faculty accountability — accreditation compliance risk.

Root fix (W123):
    Guard _check_faculty_has_active_contract_for_syllabus() is FIRST action in
    create_syllabus() before the dept cap check or any persist call.
    Fail-closed: if faculty_contracts lookup fails → DomainValidationError.
    Router POST now catches (ValueError, DomainValidationError) → HTTP 422.

Guard answers the 5 hardening questions:
1. Dangerous action      : create_syllabus assigns faculty as course author for a term
2. Real-world constraint : only faculty with active employment contracts can be assigned
3. External entity       : faculty_contracts
4. Validate BEFORE       : create_entity_for_tenant("syllabi", ...)
5. Bad outcome prevented : terminated/resigned faculty assigned to syllabi —
                           ghost syllabus, accreditation compliance violation
"""
from __future__ import annotations

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.syllabus_governance.schemas import SyllabusCreateSchema
from app.modules.syllabus_governance.service import (
    _DEPT_MAX_ACTIVE_SYLLABI,
    _FACULTY_CONTRACT_ACTIVE_STATUSES,
    _PROGRAM_ACTIVE_STATUSES,
    _check_faculty_has_active_contract_for_syllabus,
    create_syllabus,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

ACTIVE_CONTRACT = {"faculty_id": "FAC-001", "status": "active", "tenant_id": 1}
EXPIRED_CONTRACT = {"faculty_id": "FAC-001", "status": "expired", "tenant_id": 1}
TERMINATED_CONTRACT = {"faculty_id": "FAC-001", "status": "terminated", "tenant_id": 1}
ON_LEAVE_CONTRACT = {"faculty_id": "FAC-001", "status": "on_leave", "tenant_id": 1}
OTHER_FACULTY_CONTRACT = {"faculty_id": "FAC-999", "status": "active", "tenant_id": 1}


def _make_payload(
    faculty_id: str = "FAC-001",
    department_id: str = "cs",
    status: str = "draft",
) -> SyllabusCreateSchema:
    return SyllabusCreateSchema(
        course_code="CS-101",
        course_title="Introduction to Computing",
        department_id=department_id,
        faculty_id=faculty_id,
        term_id="2026-S1",
        status=status,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------------------
# TestW123Constants
# ---------------------------------------------------------------------------


class TestW123Constants:
    def test_faculty_contract_active_statuses_is_frozenset(self):
        assert isinstance(_FACULTY_CONTRACT_ACTIVE_STATUSES, frozenset)

    def test_active_in_statuses(self):
        assert "active" in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_expired_not_in_statuses(self):
        assert "expired" not in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_terminated_not_in_statuses(self):
        assert "terminated" not in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_on_leave_not_in_statuses(self):
        assert "on_leave" not in _FACULTY_CONTRACT_ACTIVE_STATUSES

    def test_program_active_statuses_is_frozenset(self):
        assert isinstance(_PROGRAM_ACTIVE_STATUSES, frozenset)

    def test_dept_max_active_syllabi_is_dict(self):
        assert isinstance(_DEPT_MAX_ACTIVE_SYLLABI, dict)

    def test_cs_cap_set(self):
        assert "cs" in _DEPT_MAX_ACTIVE_SYLLABI

    def test_medicine_has_lowest_cap(self):
        assert _DEPT_MAX_ACTIVE_SYLLABI.get("medicine", 99) <= 20

    def test_default_cap_exists(self):
        assert "default" in _DEPT_MAX_ACTIVE_SYLLABI


# ---------------------------------------------------------------------------
# TestW123GuardSignature
# ---------------------------------------------------------------------------


class TestW123GuardSignature:
    def test_guard_passes_for_active_contract(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ACTIVE_CONTRACT],
        )
        _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_guard_raises_for_no_contracts(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_guard_raises_for_expired_contract(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [EXPIRED_CONTRACT],
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_guard_raises_for_terminated_contract(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [TERMINATED_CONTRACT],
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_guard_raises_for_on_leave(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [ON_LEAVE_CONTRACT],
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")


# ---------------------------------------------------------------------------
# TestW123GuardFailures — all blocked scenarios
# ---------------------------------------------------------------------------


class TestW123GuardFailures:
    def test_no_contracts_raises(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_terminated_contract_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [TERMINATED_CONTRACT],
        )
        with pytest.raises(DomainValidationError, match="no active contract"):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_expired_contract_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [EXPIRED_CONTRACT],
        )
        with pytest.raises(DomainValidationError, match="no active contract"):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_wrong_faculty_id_blocks(self, monkeypatch):
        """Contract exists for FAC-999, not FAC-001."""
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [OTHER_FACULTY_CONTRACT],
        )
        with pytest.raises(DomainValidationError, match="no faculty contract records found"):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_empty_faculty_id_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="faculty_id is missing"):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="")

    def test_none_faculty_id_blocks(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda entity_name, tenant_id: [],
        )
        with pytest.raises(DomainValidationError, match="faculty_id is missing"):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id=None)  # type: ignore


# ---------------------------------------------------------------------------
# TestW123FailClosed
# ---------------------------------------------------------------------------


class TestW123FailClosed:
    def test_runtime_error_raises_domain_validation_error(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise RuntimeError("DB down")

        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError, match="faculty_contracts lookup failed"):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_connection_error_blocks(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise ConnectionError("network down")

        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_ioerror_blocks(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise IOError("timeout")

        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_fail_closed_error_mentions_faculty_id(self, monkeypatch):
        def boom(entity_name, tenant_id):
            raise Exception("unexpected")

        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            boom,
        )
        with pytest.raises(DomainValidationError, match="FAC-XYZ"):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-XYZ")


# ---------------------------------------------------------------------------
# TestW123CreatePath — end-to-end create_syllabus integration
# ---------------------------------------------------------------------------


class TestW123CreatePath:
    def _setup(self, monkeypatch, contracts=None, existing_syllabi=None):
        contracts = contracts or []
        existing_syllabi = existing_syllabi or []
        created: dict[str, object] = {}

        def mock_list(entity_name, tenant_id):
            if entity_name == "faculty_contracts":
                return contracts
            if entity_name == "syllabi":
                return existing_syllabi
            return []

        def mock_create(entity_name, payload, tenant_id):
            record = dict(payload)
            record["id"] = 88
            record["tenant_id"] = str(tenant_id)
            created["entity_name"] = entity_name
            created["payload"] = record
            return record

        def mock_log(*args, **kwargs):
            pass

        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.create_entity_for_tenant", mock_create
        )
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.log_admin_action", mock_log
        )
        return created

    def test_create_succeeds_for_active_faculty(self, monkeypatch):
        self._setup(monkeypatch, contracts=[ACTIVE_CONTRACT])
        result = create_syllabus(1, _make_payload(faculty_id="FAC-001"), actor="admin")
        assert result.id == 88

    def test_create_blocked_for_terminated_faculty(self, monkeypatch):
        self._setup(monkeypatch, contracts=[TERMINATED_CONTRACT])
        with pytest.raises(DomainValidationError):
            create_syllabus(1, _make_payload(faculty_id="FAC-001"), actor="admin")

    def test_create_blocked_for_unknown_faculty(self, monkeypatch):
        self._setup(monkeypatch, contracts=[])
        with pytest.raises(DomainValidationError):
            create_syllabus(1, _make_payload(faculty_id="FAC-UNKNOWN"), actor="admin")

    def test_guard_fires_before_cap_check(self, monkeypatch):
        """Faculty contract guard must fire before dept cap check."""
        lookup_order: list[str] = []

        def mock_list(entity_name, tenant_id):
            lookup_order.append(entity_name)
            if entity_name == "faculty_contracts":
                return []  # trigger guard failure
            return []

        def mock_create(entity_name, payload, tenant_id):
            return {"id": 1}

        def mock_log(*args, **kwargs):
            pass

        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.create_entity_for_tenant", mock_create
        )
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.log_admin_action", mock_log
        )
        with pytest.raises(DomainValidationError):
            create_syllabus(1, _make_payload(faculty_id="FAC-UNKNOWN"), actor="admin")

        assert lookup_order[0] == "faculty_contracts"

    def test_not_persisted_when_guard_fails(self, monkeypatch):
        created_calls: list[str] = []

        def mock_list(entity_name, tenant_id):
            if entity_name == "faculty_contracts":
                return [TERMINATED_CONTRACT]
            return []

        def mock_create(entity_name, payload, tenant_id):
            created_calls.append(entity_name)
            return {"id": 1}

        def mock_log(*args, **kwargs):
            pass

        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant", mock_list
        )
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.create_entity_for_tenant", mock_create
        )
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.log_admin_action", mock_log
        )
        with pytest.raises(DomainValidationError):
            create_syllabus(1, _make_payload(faculty_id="FAC-001"), actor="admin")

        assert "syllabi" not in created_calls


# ---------------------------------------------------------------------------
# TestW123BusinessInvariants
# ---------------------------------------------------------------------------


class TestW123BusinessInvariants:
    def test_two_tenants_isolated(self, monkeypatch):
        """Active contract for tenant 1 must not satisfy tenant 2 guard."""

        def mock_list(entity_name, tenant_id):
            if entity_name == "faculty_contracts" and tenant_id == 1:
                return [ACTIVE_CONTRACT]
            return []

        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant", mock_list
        )
        # Tenant 1 — passes
        _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")
        # Tenant 2 — blocked
        with pytest.raises(DomainValidationError):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=2, faculty_id="FAC-001")

    def test_one_active_among_multiple_contracts_passes(self, monkeypatch):
        """Expired + active contract → guard passes (active found)."""
        contracts = [EXPIRED_CONTRACT, ACTIVE_CONTRACT]
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda e, t: contracts,
        )
        _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_all_inactive_blocks(self, monkeypatch):
        contracts = [EXPIRED_CONTRACT, TERMINATED_CONTRACT, ON_LEAVE_CONTRACT]
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda e, t: contracts,
        )
        with pytest.raises(DomainValidationError, match="no active contract"):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_error_message_includes_faculty_id(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda e, t: [],
        )
        with pytest.raises(DomainValidationError, match="FAC-GHOSTNAME"):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-GHOSTNAME")

    def test_error_message_mentions_terminated_resigned(self, monkeypatch):
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda e, t: [TERMINATED_CONTRACT],
        )
        with pytest.raises(DomainValidationError, match="terminated or resigned"):
            _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="FAC-001")

    def test_whitespace_stripped_faculty_id(self, monkeypatch):
        """faculty_id with leading/trailing whitespace is matched after strip."""
        contract = {"faculty_id": "FAC-001", "status": "active"}
        monkeypatch.setattr(
            "app.modules.syllabus_governance.service.list_entities_for_tenant",
            lambda e, t: [contract],
        )
        _check_faculty_has_active_contract_for_syllabus(tenant_id=1, faculty_id="  FAC-001  ")
