"""W87 — delinquency_collections: Legal Escalation Requires Minimum Debt Threshold.

Transition Guard: `update_delinquency_escalation(→ legal)` must validate BOTH:
  1. amount_due >= 500.0  (debt is material — attorney costs must not exceed recovered sum)
  2. days_overdue >= 90   (debt is genuinely overdue — not a recent administrative delay)

Real-world impact:
- Escalating a trivial or recent debt to legal stage costs the university in attorney fees
  that exceed the recovered amount.
- It permanently destroys the student's credit record — an irreversible harm.
- It violates Title IV SAP and collections compliance best-practices.

Eight behavioral tests:
1. Guard function exists and is callable
2. Threshold constants exist with correct minimum values
3. Guard raises when amount_due is below minimum (days OK)
4. Guard raises when days_overdue is below minimum (amount OK)
5. Guard raises when BOTH amount and days are below minimum
6. Error message contains record_id, student_id, thresholds, and rationale
7. Guard passes when BOTH amount and days meet thresholds
8. Guard is surgical — non-legal escalation stages bypass the check
"""
from __future__ import annotations


import pytest

from app.modules.delinquency_collections.service import (
    _check_legal_escalation_threshold,
    _LEGAL_ESCALATION_MIN_AMOUNT_DUE,
    _LEGAL_ESCALATION_MIN_DAYS_OVERDUE,
    _LEGAL_ESCALATION_STAGES,
)
from app.core.module_helpers.service_validation import DomainValidationError


# ---------------------------------------------------------------------------
# Structural checks
# ---------------------------------------------------------------------------

def test_w87_guard_function_exists_and_callable():
    """_check_legal_escalation_threshold must be importable and callable."""
    assert callable(_check_legal_escalation_threshold), (
        "_check_legal_escalation_threshold not found or not callable"
    )


def test_w87_threshold_constants_have_correct_minimum_values():
    """Threshold constants must enforce meaningful legal-action criteria."""
    assert isinstance(_LEGAL_ESCALATION_MIN_AMOUNT_DUE, float), (
        "_LEGAL_ESCALATION_MIN_AMOUNT_DUE must be float"
    )
    assert _LEGAL_ESCALATION_MIN_AMOUNT_DUE >= 100.0, (
        "_LEGAL_ESCALATION_MIN_AMOUNT_DUE must be at least 100 to be meaningful"
    )
    assert isinstance(_LEGAL_ESCALATION_MIN_DAYS_OVERDUE, int), (
        "_LEGAL_ESCALATION_MIN_DAYS_OVERDUE must be int"
    )
    assert _LEGAL_ESCALATION_MIN_DAYS_OVERDUE >= 30, (
        "_LEGAL_ESCALATION_MIN_DAYS_OVERDUE must be at least 30 days"
    )
    assert "legal" in _LEGAL_ESCALATION_STAGES, (
        "'legal' must be in _LEGAL_ESCALATION_STAGES"
    )


# ---------------------------------------------------------------------------
# Negative cases — guard must block
# ---------------------------------------------------------------------------

def test_w87_blocked_when_amount_due_below_minimum():
    """Guard raises DomainValidationError when amount_due < minimum, even with sufficient days."""
    with pytest.raises(DomainValidationError) as exc_info:
        _check_legal_escalation_threshold(
            record_id=1,
            student_id="S001",
            amount_due=50.0,  # well below 500.0 minimum
            days_overdue=120,  # meets the days requirement
            target_stage="legal",
        )

    msg = str(exc_info.value)
    assert "record_id=1" in msg, f"record_id missing from error: {msg}"
    assert "S001" in msg, f"student_id missing from error: {msg}"
    assert "amount_due" in msg.lower(), f"'amount_due' missing from error: {msg}"
    assert "50" in msg or "minimum" in msg.lower(), f"amount context missing: {msg}"


def test_w87_blocked_when_days_overdue_below_minimum():
    """Guard raises DomainValidationError when days_overdue < minimum, even with sufficient amount."""
    with pytest.raises(DomainValidationError) as exc_info:
        _check_legal_escalation_threshold(
            record_id=2,
            student_id="S002",
            amount_due=1500.0,  # meets the amount requirement
            days_overdue=15,    # well below 90-day minimum
            target_stage="legal",
        )

    msg = str(exc_info.value)
    assert "record_id=2" in msg
    assert "days_overdue" in msg.lower() or "days" in msg.lower(), (
        f"'days_overdue' context missing: {msg}"
    )
    assert "15" in msg or "minimum" in msg.lower()


def test_w87_blocked_when_both_amount_and_days_below_minimum():
    """Guard raises when BOTH amount and days are below threshold."""
    with pytest.raises(DomainValidationError) as exc_info:
        _check_legal_escalation_threshold(
            record_id=3,
            student_id="S003",
            amount_due=10.0,   # trivial debt
            days_overdue=5,    # barely overdue
            target_stage="legal",
        )

    msg = str(exc_info.value)
    # error must mention both failure reasons
    assert "amount_due" in msg.lower() or "amount" in msg.lower()
    assert "days_overdue" in msg.lower() or "days" in msg.lower()


def test_w87_error_message_contains_rationale():
    """Error must explain WHY legal escalation is blocked (attorney costs > debt, credit impact)."""
    with pytest.raises(DomainValidationError) as exc_info:
        _check_legal_escalation_threshold(
            record_id=99,
            student_id="S999",
            amount_due=25.0,
            days_overdue=10,
            target_stage="legal",
        )

    msg = str(exc_info.value)
    # Must communicate the real-world harm being prevented
    assert (
        "attorney" in msg.lower()
        or "credit" in msg.lower()
        or "legal action" in msg.lower()
        or "attorney costs" in msg.lower()
    ), f"Error must explain legal escalation rationale: {msg}"
    assert "record_id=99" in msg


# ---------------------------------------------------------------------------
# Positive cases — guard must pass
# ---------------------------------------------------------------------------

def test_w87_allowed_when_both_amount_and_days_meet_threshold():
    """Guard does not raise when amount_due AND days_overdue both meet minimums."""
    # Must not raise
    _check_legal_escalation_threshold(
        record_id=10,
        student_id="S010",
        amount_due=_LEGAL_ESCALATION_MIN_AMOUNT_DUE,        # exactly at minimum
        days_overdue=_LEGAL_ESCALATION_MIN_DAYS_OVERDUE,   # exactly at minimum
        target_stage="legal",
    )


def test_w87_allowed_when_amount_and_days_far_exceed_minimum():
    """Guard does not raise for a clearly legitimate legal escalation."""
    _check_legal_escalation_threshold(
        record_id=11,
        student_id="S011",
        amount_due=5000.0,    # 10x minimum
        days_overdue=365,     # 4x minimum
        target_stage="legal",
    )


# ---------------------------------------------------------------------------
# Surgical — guard only fires for legal stage
# ---------------------------------------------------------------------------

def test_w87_surgical_non_legal_stages_bypass_guard():
    """Guard is a no-op for non-legal escalation stages regardless of amount/days.

    Only 'legal' stage requires threshold validation. stage_1, stage_2, stage_3
    are standard operational stages that should not be blocked by legal thresholds.
    """
    non_legal_stages = ["stage_1", "stage_2", "stage_3"]
    for stage in non_legal_stages:
        # trivial debt, trivial overdue — must NOT raise for non-legal stages
        _check_legal_escalation_threshold(
            record_id=20,
            student_id="S020",
            amount_due=1.0,
            days_overdue=1,
            target_stage=stage,
        )
