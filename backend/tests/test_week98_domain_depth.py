"""W98 — accreditation: Accreditation Compliant Transition Requires Minimum Active Faculty.

Real-world invariant:
  An accreditation body evaluates institutional compliance partly on the basis of
  having a sufficient number of actively-employed, contracted faculty. Marking an
  accreditation record "compliant" without that minimum in place misrepresents the
  institution's staffing to the accreditor — accreditation fraud.

Guard: _check_minimum_active_faculty_for_accreditation_compliant
  - Returns early (no-op) for any target_status that is not "compliant"
  - Fail-closed: faculty_contracts lookup exception → DomainValidationError
  - Minimum: 3 faculty with status == "active" must exist in faculty_contracts
  - Blocks if fewer than MIN active contracts found
  - Passes when at least MIN active contracts found
"""
from __future__ import annotations

import pytest
from unittest.mock import patch

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.accreditation.service import (
    _ACCREDITATION_COMPLIANT_TARGET_STATUS,
    _ACTIVE_FACULTY_CONTRACT_STATUSES,
    _MIN_ACTIVE_FACULTY_FOR_COMPLIANT,
    _check_minimum_active_faculty_for_accreditation_compliant,
)

TENANT = 1
REC_ID = 77


# ---------------------------------------------------------------------------
# 1. Constants
# ---------------------------------------------------------------------------

def test_w98_compliant_target_and_minimum_constants():
    assert _ACCREDITATION_COMPLIANT_TARGET_STATUS == "compliant"
    assert "active" in _ACTIVE_FACULTY_CONTRACT_STATUSES
    assert "draft" not in _ACTIVE_FACULTY_CONTRACT_STATUSES
    assert "pending" not in _ACTIVE_FACULTY_CONTRACT_STATUSES
    assert _MIN_ACTIVE_FACULTY_FOR_COMPLIANT >= 1


# ---------------------------------------------------------------------------
# 2. Guard importable and callable
# ---------------------------------------------------------------------------

def test_w98_guard_function_exists_and_callable():
    assert callable(_check_minimum_active_faculty_for_accreditation_compliant)


# ---------------------------------------------------------------------------
# 3. Non-compliant status → no-op
# ---------------------------------------------------------------------------

def test_w98_non_compliant_status_is_noop():
    """Guard must not query DB for non-compliant transitions."""
    for status in ("under_review", "remediation_required", "evidence_collected", "draft", ""):
        _check_minimum_active_faculty_for_accreditation_compliant(
            tenant_id=TENANT, record_id=REC_ID, target_status=status
        )


# ---------------------------------------------------------------------------
# 4. Blocked when zero faculty contracts
# ---------------------------------------------------------------------------

def test_w98_blocked_when_no_faculty_contracts():
    with patch(
        "app.modules.accreditation.service.list_entities_for_tenant",
        return_value=[],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_minimum_active_faculty_for_accreditation_compliant(
                tenant_id=TENANT, record_id=REC_ID, target_status="compliant"
            )
    msg = str(exc_info.value)
    assert str(REC_ID) in msg


# ---------------------------------------------------------------------------
# 5. Blocked when fewer than minimum active contracts (1 active)
# ---------------------------------------------------------------------------

def test_w98_blocked_when_one_active_contract():
    contracts = [{"id": 1, "status": "active"}]
    with patch(
        "app.modules.accreditation.service.list_entities_for_tenant",
        return_value=contracts,
    ):
        with pytest.raises(DomainValidationError):
            _check_minimum_active_faculty_for_accreditation_compliant(
                tenant_id=TENANT, record_id=REC_ID, target_status="compliant"
            )


# ---------------------------------------------------------------------------
# 6. Blocked when fewer than minimum active contracts (2 active)
# ---------------------------------------------------------------------------

def test_w98_blocked_when_two_active_contracts():
    contracts = [
        {"id": 1, "status": "active"},
        {"id": 2, "status": "active"},
    ]
    with patch(
        "app.modules.accreditation.service.list_entities_for_tenant",
        return_value=contracts,
    ):
        with pytest.raises(DomainValidationError):
            _check_minimum_active_faculty_for_accreditation_compliant(
                tenant_id=TENANT, record_id=REC_ID, target_status="compliant"
            )


# ---------------------------------------------------------------------------
# 7. Blocked when contracts exist but none are active
# ---------------------------------------------------------------------------

def test_w98_blocked_when_no_active_status_among_contracts():
    contracts = [
        {"id": 1, "status": "inactive"},
        {"id": 2, "status": "terminated"},
        {"id": 3, "status": "draft"},
        {"id": 4, "status": "pending"},
    ]
    with patch(
        "app.modules.accreditation.service.list_entities_for_tenant",
        return_value=contracts,
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_minimum_active_faculty_for_accreditation_compliant(
                tenant_id=TENANT, record_id=REC_ID, target_status="compliant"
            )
    assert str(REC_ID) in str(exc_info.value)


# ---------------------------------------------------------------------------
# 8. Blocked: mix of active/inactive but below minimum threshold
# ---------------------------------------------------------------------------

def test_w98_blocked_when_mixed_statuses_below_minimum():
    contracts = [
        {"id": 1, "status": "active"},
        {"id": 2, "status": "inactive"},
        {"id": 3, "status": "terminated"},
    ]
    with patch(
        "app.modules.accreditation.service.list_entities_for_tenant",
        return_value=contracts,
    ):
        with pytest.raises(DomainValidationError):
            _check_minimum_active_faculty_for_accreditation_compliant(
                tenant_id=TENANT, record_id=REC_ID, target_status="compliant"
            )


# ---------------------------------------------------------------------------
# 9. Fail-closed on faculty_contracts lookup error
# ---------------------------------------------------------------------------

def test_w98_fail_closed_on_contracts_lookup_error():
    with patch(
        "app.modules.accreditation.service.list_entities_for_tenant",
        side_effect=RuntimeError("DB connection lost"),
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_minimum_active_faculty_for_accreditation_compliant(
                tenant_id=TENANT, record_id=REC_ID, target_status="compliant"
            )
    assert str(REC_ID) in str(exc_info.value)


# ---------------------------------------------------------------------------
# 10. Passes when exactly minimum active contracts present
# ---------------------------------------------------------------------------

def test_w98_allowed_when_exactly_minimum_active_contracts():
    contracts = [
        {"id": i, "status": "active"}
        for i in range(1, _MIN_ACTIVE_FACULTY_FOR_COMPLIANT + 1)
    ]
    with patch(
        "app.modules.accreditation.service.list_entities_for_tenant",
        return_value=contracts,
    ):
        # Must not raise
        _check_minimum_active_faculty_for_accreditation_compliant(
            tenant_id=TENANT, record_id=REC_ID, target_status="compliant"
        )


# ---------------------------------------------------------------------------
# 11. Passes when more than minimum active contracts present
# ---------------------------------------------------------------------------

def test_w98_allowed_when_more_than_minimum_active_contracts():
    contracts = [
        {"id": i, "status": "active"}
        for i in range(1, _MIN_ACTIVE_FACULTY_FOR_COMPLIANT + 5)
    ]
    with patch(
        "app.modules.accreditation.service.list_entities_for_tenant",
        return_value=contracts,
    ):
        _check_minimum_active_faculty_for_accreditation_compliant(
            tenant_id=TENANT, record_id=REC_ID, target_status="compliant"
        )


# ---------------------------------------------------------------------------
# 12. Passes with mix of active and non-active, total active >= minimum
# ---------------------------------------------------------------------------

def test_w98_allowed_when_mixed_statuses_above_minimum():
    contracts = [
        {"id": 1, "status": "active"},
        {"id": 2, "status": "inactive"},
        {"id": 3, "status": "active"},
        {"id": 4, "status": "terminated"},
        {"id": 5, "status": "active"},
        {"id": 6, "status": "pending"},
    ]
    with patch(
        "app.modules.accreditation.service.list_entities_for_tenant",
        return_value=contracts,
    ):
        _check_minimum_active_faculty_for_accreditation_compliant(
            tenant_id=TENANT, record_id=REC_ID, target_status="compliant"
        )


# ---------------------------------------------------------------------------
# 13. Error message contains record_id and minimum count
# ---------------------------------------------------------------------------

def test_w98_error_message_contains_record_id_and_minimum():
    with patch(
        "app.modules.accreditation.service.list_entities_for_tenant",
        return_value=[],
    ):
        with pytest.raises(DomainValidationError) as exc_info:
            _check_minimum_active_faculty_for_accreditation_compliant(
                tenant_id=TENANT, record_id=REC_ID, target_status="compliant"
            )
    msg = str(exc_info.value)
    assert str(REC_ID) in msg
    assert str(_MIN_ACTIVE_FACULTY_FOR_COMPLIANT) in msg
