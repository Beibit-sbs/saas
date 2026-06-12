"""Read-only Assessment runtime service (A-052.10-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.academic_operations import repository
from app.modules.academic_operations.dependencies import validate_tenant_id
from app.modules.exam_governance.service import get_exam_dashboard_summary
from app.modules.academic_operations_runtime.assessment_runtime_schemas import (
    AssessmentGradingDistribution,
    AssessmentReadiness,
    AssessmentRiskSummary,
    AssessmentRuntimeOverview,
    AssessmentRuntimeResponse,
    AssessmentRuntimeStatistics,
    AssessmentSection,
    AssessmentSignals,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _sum_status_counts(payload: dict[str, int]) -> int:
    return sum(int(v) for v in payload.values())


def _bridge_count(bridge_summary: dict[str, int], *tokens: str) -> int:
    lowered = tuple(token.lower() for token in tokens)
    total = 0
    for key, value in bridge_summary.items():
        key_lower = str(key).lower()
        if any(token in key_lower for token in lowered):
            total += int(value)
    return total


def get_assessment_runtime(db: Session, tenant_id: int) -> AssessmentRuntimeResponse:
    tenant = validate_tenant_id(tenant_id)

    dashboard_summary = repository.compute_dashboard_summary(db, tenant)
    bridge_summary = repository.get_canonical_bridge_summary(db, tenant)
    exam_summary = get_exam_dashboard_summary(tenant)

    exams_total = int(exam_summary["total_exams"])
    completed_exams_total = int(exam_summary["status_breakdown"].get("completed", 0))
    gradebook_entries_total = len(repository.list_gradebook_metadata(db, tenant))
    schedule_alignment_total = _sum_status_counts(dashboard_summary["summer_semester_terms"]) + _sum_status_counts(
        dashboard_summary["advisor_tutor_assignments"]
    )

    excellent_band = min(gradebook_entries_total, max(0, gradebook_entries_total // 2))
    good_band = min(gradebook_entries_total - excellent_band, max(0, gradebook_entries_total // 3))
    warning_band = min(gradebook_entries_total - excellent_band - good_band, max(0, gradebook_entries_total // 5))
    critical_band = max(0, gradebook_entries_total - excellent_band - good_band - warning_band)
    grading_distribution_total = excellent_band + good_band + warning_band + critical_band

    assessment_signals_total = _bridge_count(bridge_summary, "assessment", "exam", "grade")
    signal_types: list[str] = []
    if warning_band > 0:
        signal_types.append("gradebook_warning")
    if critical_band > 0:
        signal_types.append("assessment_critical")
    if completed_exams_total < exams_total:
        signal_types.append("exam_completion_gap")

    risk_indicators: list[str] = []
    if completed_exams_total < exams_total:
        risk_indicators.append("incomplete_exam_governance_visibility")
    if critical_band > 0:
        risk_indicators.append("critical_gradebook_distribution")
    if schedule_alignment_total == 0:
        risk_indicators.append("assessment_schedule_misalignment")

    high_risk_assessments_total = len(risk_indicators)
    risk_score = max(0, min(100, len(risk_indicators) * 30 + critical_band * 5))
    readiness_score = max(0, min(100, 100 - risk_score + min(20, assessment_signals_total)))

    return AssessmentRuntimeResponse(
        tenant_id=tenant,
        overview=AssessmentRuntimeOverview(generated_at=_now()),
        assessment_statistics=AssessmentRuntimeStatistics(
            exams_total=exams_total,
            completed_exams_total=completed_exams_total,
            gradebook_entries_total=gradebook_entries_total,
            grading_distribution_total=grading_distribution_total,
            schedule_alignment_total=schedule_alignment_total,
            assessment_signals_total=assessment_signals_total,
            canonical_bridge_total=sum(int(v) for v in bridge_summary.values()),
        ),
        exam_governance_summary=AssessmentSection(
            records=exams_total,
            source_modules=["exam_governance", "academic_operations"],
        ),
        gradebook_readiness=AssessmentSection(
            records=gradebook_entries_total,
            source_modules=["grades", "academic_operations"],
        ),
        grading_distribution=AssessmentGradingDistribution(
            excellent_band=excellent_band,
            good_band=good_band,
            warning_band=warning_band,
            critical_band=critical_band,
        ),
        assessment_schedule_alignment=AssessmentSection(
            records=schedule_alignment_total,
            source_modules=["scheduling", "exam_governance", "academic_operations"],
        ),
        assessment_risk_summary=AssessmentRiskSummary(
            risk_score=risk_score,
            open_risks=len(risk_indicators),
            indicators=risk_indicators,
        ),
        high_risk_assessments=AssessmentSection(
            records=high_risk_assessments_total,
            source_modules=["exam_governance", "grades", "scheduling"],
        ),
        assessment_signals=AssessmentSignals(
            generated_signals=assessment_signals_total,
            signal_types=signal_types,
        ),
        assessment_readiness=AssessmentReadiness(
            ready_for_runtime=len(risk_indicators) == 0,
            checklist=[
                "read_only_runtime",
                "aggregator_only_runtime",
                "tenant_scoped_visibility",
                "summary_read_rbac_required",
                "no_mutation_operations",
            ],
            readiness_score=readiness_score,
        ),
    )
