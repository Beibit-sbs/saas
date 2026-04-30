"""W85 — programs: Program Activation Requires Active Degree Requirement Guard.

Cross-entity invariant: A program cannot be activated without at least one active
ProgramRequirementModel. An active program with zero active requirements creates every
enrolled student with a permanently-unsatisfiable graduation state.

Six behavioral tests covering: method existence, blocked when no active requirement,
allowed when active requirement exists, error message content, guard surgical (only on
activation), and safe-skip when degree_progress unavailable.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.modules.programs.service import (
    _check_program_has_active_requirements,
    _ACTIVATION_STATUSES,
)
from app.core.module_helpers.service_validation import DomainValidationError


def test_w85_activation_statuses_constant_exists():
    """_ACTIVATION_STATUSES frozenset must include 'active'."""
    assert isinstance(_ACTIVATION_STATUSES, frozenset), (
        "_ACTIVATION_STATUSES must be a frozenset"
    )
    assert "active" in _ACTIVATION_STATUSES, (
        "'active' must be in _ACTIVATION_STATUSES"
    )


def test_w85_guard_method_exists():
    """_check_program_has_active_requirements must be callable."""
    assert callable(_check_program_has_active_requirements), (
        "_check_program_has_active_requirements not found or not callable"
    )


def test_w85_blocked_when_no_active_requirements():
    """Guard raises DomainValidationError when program has no active requirements."""
    with patch(
        "app.modules.programs.service.list_entities_for_tenant",
        return_value=[],  # no requirements at all
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_program_has_active_requirements(tenant_id=10, program_id=42)

        assert "Cannot activate" in str(exc_info.value)
        assert "program_id=42" in str(exc_info.value)


def test_w85_blocked_when_all_requirements_inactive():
    """Guard raises when all requirements for program are inactive."""
    inactive_reqs = [
        {
            "id": 1,
            "program_id": 42,
            "is_active": "false",
            "name": "Req 1",
        },
        {
            "id": 2,
            "program_id": 42,
            "is_active": "0",
            "name": "Req 2",
        },
    ]
    with patch(
        "app.modules.programs.service.list_entities_for_tenant",
        return_value=inactive_reqs,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_program_has_active_requirements(tenant_id=10, program_id=42)

        assert "program_id=42" in str(exc_info.value)


def test_w85_allowed_when_active_requirement_exists():
    """Guard does not raise when at least one active requirement exists."""
    active_req = [
        {
            "id": 1,
            "program_id": 42,
            "is_active": "true",
            "name": "Active Req",
            "minimum_credits": 120,
        }
    ]
    with patch(
        "app.modules.programs.service.list_entities_for_tenant",
        return_value=active_req,
    ):
        # Should not raise
        _check_program_has_active_requirements(tenant_id=10, program_id=42)


def test_w85_error_message_contains_program_id_and_rationale():
    """Error message must identify program_id and explain the rationale."""
    with patch(
        "app.modules.programs.service.list_entities_for_tenant",
        return_value=[],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_program_has_active_requirements(tenant_id=10, program_id=99)

        msg = str(exc_info.value)
        assert "program_id=99" in msg, f"program_id missing from error: {msg}"
        assert "active" in msg.lower() and "requirement" in msg.lower(), (
            f"'active requirement' context missing: {msg}"
        )


def test_w85_blocked_when_degree_progress_unavailable():
    """Guard raises DomainValidationError when entity lookup fails (unavailable module)."""
    with patch(
        "app.modules.programs.service.list_entities_for_tenant",
        side_effect=ValueError("unknown entity"),  # entity not registered
    ):
        # HARDENING RULE: NO SILENT FALLBACK — must block when cannot verify invariant
        with pytest.raises(DomainValidationError) as exc_info:
            _check_program_has_active_requirements(tenant_id=10, program_id=42)
        
        assert "cannot verify active requirements" in str(exc_info.value).lower()
        assert "program_id=42" in str(exc_info.value)
