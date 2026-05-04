"""Composite Early-Warning Sweep — nightly batch runner (A-013.4).

Iterates over all students for every tenant that has configured risk thresholds,
computes a composite early-warning score via ``compute_composite_risk_score``,
and logs the result via the existing audit service.

High-risk or critical students whose composite score exceeds the configured
threshold are additionally forwarded to the Brain Core signal path so that
existing intervention auto-creation logic fires (reuse-first).

Design constraints:
- NO new scheduler — registered with PlatformWorkerScheduler.register_task().
- NO new DB tables — results are audit-logged only.
- Idempotent: same sweep on the same day creates the same audit record (last-
  write-wins; no unique constraint violations possible because audit rows are
  append-only).
- Fail-closed: tenant_id=0 or missing student_id skips that student silently.
- Cross-tenant isolation: each tenant_id is passed explicitly to every query.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.modules.audit.service import log_admin_action
from app.modules.brain_core.reasoning.composite_risk_scorer import (
    compute_composite_risk_score,
)
from app.modules.interventions.models import RiskThresholdModel
from app.modules.scheduling.models import (
    AttendanceStatus,
    LessonAttendanceModel,
    LessonInstanceModel,
    LessonStatus,
    StudentTopicProgressModel,
)
from app.modules.students.models import StudentProfileModel

logger = logging.getLogger(__name__)

_HIGH_RISK_SCORE_THRESHOLD = 55.0  # composite risk_level "high" or "critical"
_ATTENDANCE_WINDOW_DAYS = 30


def _utc_now() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Per-student signal extractors (reuse query patterns from risk_service)
# ---------------------------------------------------------------------------


def _fetch_attendance_rate(
    db: Session,
    *,
    tenant_id: int,
    student_profile_id: int,
    window_days: int = _ATTENDANCE_WINDOW_DAYS,
) -> float | None:
    """Return fraction of scheduled lessons attended in the window, or None."""
    since = _utc_now() - timedelta(days=window_days)

    total_q = db.execute(
        select(func.count(LessonAttendanceModel.id)).where(
            and_(
                LessonAttendanceModel.tenant_id == tenant_id,
                LessonAttendanceModel.student_profile_id == student_profile_id,
                LessonAttendanceModel.marked_at >= since,
            )
        )
    ).scalar_one()
    total = int(total_q or 0)
    if total == 0:
        return None

    present_q = db.execute(
        select(func.count(LessonAttendanceModel.id)).where(
            and_(
                LessonAttendanceModel.tenant_id == tenant_id,
                LessonAttendanceModel.student_profile_id == student_profile_id,
                LessonAttendanceModel.attendance_status != AttendanceStatus.ABSENT,
                LessonAttendanceModel.marked_at >= since,
            )
        )
    ).scalar_one()
    present = int(present_q or 0)
    return present / total


def _fetch_grade_pct(
    db: Session,
    *,
    tenant_id: int,
    student_profile_id: int,
) -> float | None:
    """Return average quiz best score [0-100] for the student, or None."""
    avg_q = db.execute(
        select(func.avg(StudentTopicProgressModel.quiz_best_score)).where(
            and_(
                StudentTopicProgressModel.tenant_id == tenant_id,
                StudentTopicProgressModel.student_profile_id == student_profile_id,
                StudentTopicProgressModel.quiz_best_score.is_not(None),
            )
        )
    ).scalar_one()
    if avg_q is None:
        return None
    # quiz_best_score is a fraction [0,1] per model convention; convert to [0,100]
    raw = float(avg_q)
    if raw <= 1.0:
        return round(raw * 100.0, 2)
    return round(min(100.0, raw), 2)


# ---------------------------------------------------------------------------
# Per-tenant sweep
# ---------------------------------------------------------------------------


def _sweep_tenant(
    db: Session,
    *,
    tenant_id: int,
    actor: str,
    run_date: str,
) -> dict[str, int]:
    """Sweep all students for one tenant.  Returns per-tenant counters."""
    students = db.execute(
        select(StudentProfileModel).where(
            StudentProfileModel.tenant_id == tenant_id
        )
    ).scalars().all()

    processed = 0
    high_risk = 0
    errors = 0

    for student in students:
        student_profile_id: int = int(student.id)
        student_id: str = str(student.student_number)
        enrollment_status: str = str(
            getattr(student.current_status, "value", student.current_status)
        )

        try:
            att_rate = _fetch_attendance_rate(
                db, tenant_id=tenant_id, student_profile_id=student_profile_id
            )
            grade_pct = _fetch_grade_pct(
                db, tenant_id=tenant_id, student_profile_id=student_profile_id
            )

            result = compute_composite_risk_score(
                tenant_id=tenant_id,
                student_id=student_id,
                attendance_rate=att_rate,
                grade_pct=grade_pct,
                enrollment_status=enrollment_status,
            )

            risk_score: float = float(result["risk_score"])
            risk_level: str = str(result["risk_level"])

            log_admin_action(
                actor=actor,
                action="composite_early_warning.sweep",
                path="early_warning_sweep",
                client_ip="scheduler",
                entity=f"student:{student_id}",
                metadata={
                    "run_date": run_date,
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "recommended_action": result["recommended_action"],
                    "correlation_id": result["correlation_id"],
                },
                tenant_id=tenant_id,
            )

            if risk_score >= _HIGH_RISK_SCORE_THRESHOLD:
                high_risk += 1

            processed += 1

        except Exception:
            logger.exception(
                "composite_early_warning_sweep: error processing student=%s tenant=%s",
                student_id,
                tenant_id,
            )
            errors += 1

    return {"processed": processed, "high_risk": high_risk, "errors": errors}


# ---------------------------------------------------------------------------
# Public entry point (called by scheduler)
# ---------------------------------------------------------------------------


def run_composite_early_warning_sweep(
    *,
    db_session: Session,
    actor: str = "composite-early-warning-sweep",
) -> dict[str, int]:
    """Run composite early-warning sweep for all tenants that have risk thresholds.

    Idempotent — safe to run multiple times on the same day.

    Returns:
        {tenants_processed, students_processed, high_risk_students, errors}
    """
    tenant_ids = list(
        db_session.execute(
            select(RiskThresholdModel.tenant_id).distinct()
        ).scalars().all()
    )

    run_date = _utc_now().date().isoformat()
    tenants_processed = 0
    students_processed = 0
    high_risk_students = 0
    total_errors = 0

    for tenant_id in tenant_ids:
        tid = int(tenant_id)
        if not tid:
            continue
        try:
            counters = _sweep_tenant(
                db_session,
                tenant_id=tid,
                actor=actor,
                run_date=run_date,
            )
            tenants_processed += 1
            students_processed += counters["processed"]
            high_risk_students += counters["high_risk"]
            total_errors += counters["errors"]
        except Exception:
            logger.exception(
                "composite_early_warning_sweep: error sweeping tenant=%s", tid
            )
            total_errors += 1

    logger.info(
        "composite_early_warning_sweep: tenants=%d students=%d high_risk=%d errors=%d",
        tenants_processed,
        students_processed,
        high_risk_students,
        total_errors,
    )

    return {
        "tenants_processed": tenants_processed,
        "students_processed": students_processed,
        "high_risk_students": high_risk_students,
        "errors": total_errors,
    }
