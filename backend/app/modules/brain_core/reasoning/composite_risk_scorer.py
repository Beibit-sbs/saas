"""Composite Early-Warning Risk Scorer (A-013.4).

Deterministic, no LLM.  Combines attendance, grade, financial, and enrollment
signals into a single 0-100 composite risk score with a factors breakdown.

Rules:
- tenant_id and student_id are required (fail-closed).
- Each optional signal that is absent contributes a neutral (50/100) score and
  is reported with evidence="missing".
- The final score is a weighted sum of factor contributions, clamped to [0, 100].
- risk_level thresholds: low <35, medium 35-54, high 55-74, critical >=75.
"""
from __future__ import annotations

import uuid
from typing import Any, Literal

RiskLevel = Literal["low", "medium", "high", "critical"]

# Weights must sum to 1.0
_FACTOR_WEIGHTS: dict[str, float] = {
    "attendance": 0.35,
    "grades": 0.30,
    "financial": 0.20,
    "enrollment": 0.15,
}

_NEUTRAL = 50.0  # Contribution when a signal is absent


# ---------------------------------------------------------------------------
# Per-factor sub-scorers (each returns (risk_contribution: float, evidence: str))
# ---------------------------------------------------------------------------


def _attendance_score(attendance_rate: float | None) -> tuple[float, str]:
    """Lower attendance → higher risk.  attendance_rate ∈ [0.0, 1.0]."""
    if attendance_rate is None:
        return _NEUTRAL, "missing"
    rate = max(0.0, min(1.0, float(attendance_rate)))
    score = (1.0 - rate) * 100.0
    return round(score, 2), f"attendance_rate={rate:.3f}"


def _grade_score(grade_pct: float | None) -> tuple[float, str]:
    """Lower grade → higher risk.  grade_pct ∈ [0, 100]."""
    if grade_pct is None:
        return _NEUTRAL, "missing"
    pct = max(0.0, min(100.0, float(grade_pct)))
    score = 100.0 - pct
    return round(score, 2), f"grade_pct={pct:.1f}"


def _financial_score(
    financial_flag: bool | None,
    overdue_amount: float | None,
) -> tuple[float, str]:
    """Financial hold flag or overdue amount → risk contribution."""
    if financial_flag is None and overdue_amount is None:
        return _NEUTRAL, "missing"

    risk = 0.0
    parts: list[str] = []

    if financial_flag:
        risk = max(risk, 75.0)
        parts.append("financial_flag=true")
    elif financial_flag is False:
        parts.append("financial_flag=false")

    if overdue_amount is not None:
        amt = float(overdue_amount)
        if amt > 0:
            # $0 → 0, $500 → 100, clamped
            dollar_risk = min(100.0, amt / 500.0 * 100.0)
            risk = max(risk, dollar_risk)
            parts.append(f"overdue_amount={amt:.2f}")
        else:
            parts.append("overdue_amount=0.00")

    return round(risk, 2), ",".join(parts) or "no_hold"


_ENROLLMENT_RISK: dict[str, float] = {
    "active": 0.0,
    "enrolled": 0.0,
    "admitted": 10.0,
    "inactive": 50.0,
    "on_leave": 40.0,
    "probation": 70.0,
    "suspended": 90.0,
    "withdrawn": 95.0,
    "dropped": 100.0,
}


def _enrollment_score(enrollment_status: str | None) -> tuple[float, str]:
    """Student enrollment status → risk contribution."""
    if enrollment_status is None:
        return _NEUTRAL, "missing"
    key = str(enrollment_status).lower().strip()
    risk = _ENROLLMENT_RISK.get(key, _NEUTRAL)
    return round(risk, 2), f"enrollment_status={key}"


# ---------------------------------------------------------------------------
# Risk level mapping
# ---------------------------------------------------------------------------


def _risk_level_from_score(score: float) -> RiskLevel:
    if score >= 75.0:
        return "critical"
    if score >= 55.0:
        return "high"
    if score >= 35.0:
        return "medium"
    return "low"


_RECOMMENDED_ACTIONS: dict[str, str] = {
    "low": "monitor",
    "medium": "schedule_advising",
    "high": "urgent_advising",
    "critical": "immediate_intervention",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_composite_risk_score(
    *,
    tenant_id: int,
    student_id: str,
    attendance_rate: float | None = None,
    grade_pct: float | None = None,
    financial_flag: bool | None = None,
    overdue_amount: float | None = None,
    enrollment_status: str | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Compute a composite early-warning risk score for a student.

    Args:
        tenant_id: Required.  Raises ValueError if falsy.
        student_id: Required.  Raises ValueError if falsy.
        attendance_rate: Fraction of classes attended [0.0-1.0], optional.
        grade_pct: Grade percentage [0-100], optional.
        financial_flag: True if student has an outstanding financial hold.
        overdue_amount: Overdue payment amount in USD, optional.
        enrollment_status: Enrollment status string, optional.
        correlation_id: Optional correlation ID (UUID generated if absent).

    Returns:
        {
            tenant_id, student_id, risk_score (float 0-100),
            risk_level (low/medium/high/critical),
            factors: [{name, score, weight, evidence}, ...],
            recommended_action, correlation_id
        }

    Raises:
        ValueError: tenant_id or student_id absent.
    """
    if not tenant_id:
        raise ValueError("tenant_id is required")
    if not student_id:
        raise ValueError("student_id is required")

    att_sc, att_ev = _attendance_score(attendance_rate)
    grade_sc, grade_ev = _grade_score(grade_pct)
    fin_sc, fin_ev = _financial_score(financial_flag, overdue_amount)
    enroll_sc, enroll_ev = _enrollment_score(enrollment_status)

    raw: dict[str, tuple[float, str]] = {
        "attendance": (att_sc, att_ev),
        "grades": (grade_sc, grade_ev),
        "financial": (fin_sc, fin_ev),
        "enrollment": (enroll_sc, enroll_ev),
    }

    composite = sum(
        raw[name][0] * _FACTOR_WEIGHTS[name] for name in _FACTOR_WEIGHTS
    )
    composite = round(max(0.0, min(100.0, composite)), 2)

    risk_level: RiskLevel = _risk_level_from_score(composite)
    recommended_action = _RECOMMENDED_ACTIONS[risk_level]

    factors = [
        {
            "name": name,
            "score": raw[name][0],
            "weight": _FACTOR_WEIGHTS[name],
            "evidence": raw[name][1],
        }
        for name in _FACTOR_WEIGHTS
    ]

    return {
        "tenant_id": tenant_id,
        "student_id": student_id,
        "risk_score": composite,
        "risk_level": risk_level,
        "factors": factors,
        "recommended_action": recommended_action,
        "correlation_id": correlation_id or str(uuid.uuid4()),
    }
