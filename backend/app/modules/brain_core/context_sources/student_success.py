from __future__ import annotations

from typing import Any

from app.modules.student_life.service import get_student_life_health_snapshot
from app.modules.student_life.schemas import StudentLifeHealthSnapshotSchema


def _empty_student_life_health_snapshot(tenant_id: int) -> dict[str, Any]:
    return StudentLifeHealthSnapshotSchema(
        tenant_id=tenant_id,
        counseling_cases_total=0,
        open_counseling_cases=0,
        wellbeing_checkins_total=0,
        at_risk_wellbeing_checkins=0,
        accessibility_supports_total=0,
        active_accessibility_supports=0,
        disciplinary_cases_total=0,
        unresolved_disciplinary_cases=0,
    ).model_dump()


def fetch_student_success_context(*, tenant_id: int, subject: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """Return student success context slice for Brain Core decisions."""
    try:
        student_life_health_snapshot = get_student_life_health_snapshot(tenant_id).model_dump()
    except Exception:
        student_life_health_snapshot = _empty_student_life_health_snapshot(tenant_id)

    student_id = subject.get("student_id") or payload.get("student_id")

    # Enrich with student-level risk context if student_id is available (I1.3)
    open_interventions: int = int(payload.get("open_interventions") or 0)
    last_advising_at: str | None = payload.get("last_advising_at")
    risk_flags: list[str] = []
    if student_id:
        try:
            from app.modules.students.service import get_student_risk_context
            risk_ctx = get_student_risk_context(tenant_id, student_id)
            open_interventions = risk_ctx.get("open_interventions", open_interventions)
            last_advising_at = risk_ctx.get("last_advising_outcome") or last_advising_at
            risk_flags = risk_ctx.get("risk_flags", [])
        except Exception:
            pass

    return {
        "student_id": student_id,
        "open_interventions": open_interventions,
        "last_advising_at": last_advising_at,
        "risk_flags": risk_flags,
        "student_life_health_snapshot": student_life_health_snapshot,
        "tenant_id": tenant_id,
    }
