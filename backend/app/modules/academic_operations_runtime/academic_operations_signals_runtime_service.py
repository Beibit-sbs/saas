"""Read-only Academic Operations Signals runtime service (A-052.13-E1)."""

from __future__ import annotations

from datetime import UTC, datetime
from statistics import mean

from sqlalchemy.orm import Session

from app.modules.academic_operations.dependencies import validate_tenant_id
from app.modules.academic_operations_runtime.academic_operations_signals_runtime_schemas import (
    AcademicOperationsHealthScore,
    AcademicOperationsRecommendedAction,
    AcademicOperationsSignalDistribution,
    AcademicOperationsSignalItem,
    AcademicOperationsSignalSection,
    AcademicOperationsSignalsRuntimeOverview,
    AcademicOperationsSignalsRuntimeResponse,
    AcademicOperationsSignalSummary,
)
from app.modules.academic_operations_runtime.academic_registry_runtime_service import get_academic_registry_runtime
from app.modules.academic_operations_runtime.assessment_runtime_service import get_assessment_runtime
from app.modules.academic_operations_runtime.attendance_runtime_service import get_attendance_runtime
from app.modules.academic_operations_runtime.curriculum_runtime_service import get_curriculum_runtime
from app.modules.academic_operations_runtime.internship_runtime_service import get_internship_runtime
from app.modules.academic_operations_runtime.teaching_load_runtime_service import get_teaching_load_runtime
from app.modules.academic_operations_runtime.timetable_runtime_service import get_timetable_runtime


def _now() -> datetime:
    return datetime.now(UTC)


def _clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _severity(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def _status(score: int) -> str:
    if score >= 70:
        return "ACTION_REQUIRED"
    if score >= 40:
        return "WATCH"
    return "STABLE"


def _mk_signal(
    signal_id: str,
    signal_name: str,
    score: int,
    summary: str,
    source_modules: list[str],
) -> AcademicOperationsSignalItem:
    return AcademicOperationsSignalItem(
        signal_id=signal_id,
        signal_name=signal_name,
        severity=_severity(score),
        score=score,
        status=_status(score),
        summary=summary,
        source_modules=source_modules,
    )


def _build_section(items: list[AcademicOperationsSignalItem], source_modules: list[str]) -> AcademicOperationsSignalSection:
    return AcademicOperationsSignalSection(
        records=len(items),
        source_modules=source_modules,
        items=items,
    )


def _recommended_actions(signals: list[AcademicOperationsSignalItem]) -> list[AcademicOperationsRecommendedAction]:
    top = sorted(signals, key=lambda item: item.score, reverse=True)[:5]
    actions: list[AcademicOperationsRecommendedAction] = []
    for index, item in enumerate(top, start=1):
        priority = "HIGH" if item.score >= 70 else "MEDIUM" if item.score >= 40 else "LOW"
        actions.append(
            AcademicOperationsRecommendedAction(
                action_id=f"AO-ACT-{index:03d}",
                title=f"Mitigate {item.signal_name}",
                priority=priority,
                rationale=item.summary,
                source_signal_ids=[item.signal_id],
            )
        )
    return actions


def get_academic_operations_signals_runtime(db: Session, tenant_id: int) -> AcademicOperationsSignalsRuntimeResponse:
    tenant = validate_tenant_id(tenant_id)

    registry = get_academic_registry_runtime(db, tenant)
    curriculum = get_curriculum_runtime(db, tenant)
    timetable = get_timetable_runtime(db, tenant)
    attendance = get_attendance_runtime(db, tenant)
    assessment = get_assessment_runtime(db, tenant)
    teaching_load = get_teaching_load_runtime(db, tenant)
    internship = get_internship_runtime(db, tenant)

    sig_001 = _clamp_score(
        (100 - curriculum.curriculum_health.consistency_score) * 0.55
        + curriculum.curriculum_risks.risk_score * 0.45
    )
    sig_002 = _clamp_score(
        timetable.schedule_conflicts.conflict_rate
        + timetable.schedule_conflicts.critical_conflicts * 12
        + (100 - timetable.timetable_health.consistency_score) * 0.25
    )
    sig_003 = _clamp_score(
        attendance.attendance_risk_summary.risk_score
        + max(0, attendance.attendance_trends.declining_count - attendance.attendance_trends.improving_count) * 4
    )
    sig_004 = _clamp_score(
        assessment.assessment_risk_summary.risk_score
        + assessment.grading_distribution.critical_band * 8
    )
    sig_005 = _clamp_score(
        max(teaching_load.overload_risk_summary.risk_score, teaching_load.coverage_risk_summary.risk_score)
        + teaching_load.faculty_workload_distribution.fairness_alert_total * 6
    )
    sig_006 = _clamp_score(
        (100 - internship.internship_readiness.readiness_score)
        + internship.internship_risk_summary.high_risk_count * 10
    )
    sig_007 = _clamp_score(
        max(0.0, 55.0 - internship.employer_engagement.employer_participation_rate) * 1.7
        + max(0, 3 - internship.employer_engagement.repeat_employers) * 10
    )
    sig_008 = _clamp_score(
        mean(
            [
                attendance.attendance_risk_summary.risk_score,
                assessment.assessment_risk_summary.risk_score,
                curriculum.curriculum_risks.risk_score,
            ]
        )
        + max(0, attendance.attendance_statistics.at_risk_students_total // 3)
    )
    sig_009 = _clamp_score(
        mean([sig_002, sig_004, sig_005])
        + max(0, 100 - registry.health.consistency_score) * 0.2
    )
    sig_010 = _clamp_score(100 - mean([sig_001, sig_002, sig_003, sig_004, sig_005, sig_006, sig_007, sig_008, sig_009]))

    all_signals = [
        _mk_signal(
            "AO-SIG-001",
            "Curriculum Coverage Risk",
            sig_001,
            "Curriculum health and risk indicators suggest potential coverage gaps.",
            ["academic_operations", "curriculum", "brain_core"],
        ),
        _mk_signal(
            "AO-SIG-002",
            "Schedule Conflict Risk",
            sig_002,
            "Timetable conflicts and consistency pressure indicate scheduling risk.",
            ["scheduling", "academic_operations", "brain_core"],
        ),
        _mk_signal(
            "AO-SIG-003",
            "Attendance Deterioration Risk",
            sig_003,
            "Attendance decline and trend pressure indicate deterioration risk.",
            ["attendance", "scheduling", "brain_core"],
        ),
        _mk_signal(
            "AO-SIG-004",
            "Assessment Performance Risk",
            sig_004,
            "Assessment risk and critical grading bands indicate performance pressure.",
            ["academic_operations", "scheduling", "brain_core"],
        ),
        _mk_signal(
            "AO-SIG-005",
            "Teaching Load Imbalance",
            sig_005,
            "Workload fairness and assignment coverage indicate teaching-load imbalance.",
            ["faculty", "academic_operations", "brain_core"],
        ),
        _mk_signal(
            "AO-SIG-006",
            "Internship Readiness Risk",
            sig_006,
            "Internship readiness and high-risk internship indicators show readiness pressure.",
            ["internship", "academic_operations", "brain_core"],
        ),
        _mk_signal(
            "AO-SIG-007",
            "Employer Engagement Decline",
            sig_007,
            "Employer participation and repeat engagement trend indicates decline risk.",
            ["internship", "academic_operations", "brain_core"],
        ),
        _mk_signal(
            "AO-SIG-008",
            "Academic Progress Deviation",
            sig_008,
            "Combined attendance, assessment, and curriculum signals indicate progress deviation.",
            ["academic_operations", "attendance", "brain_core"],
        ),
        _mk_signal(
            "AO-SIG-009",
            "Program Delivery Risk",
            sig_009,
            "Cross-runtime delivery signals suggest pressure on program delivery reliability.",
            ["academic_operations", "scheduling", "brain_core"],
        ),
        _mk_signal(
            "AO-SIG-010",
            "Academic Operations Health Score",
            sig_010,
            "Composite health score derived from all Academic Operations runtime signals.",
            ["academic_operations_runtime", "academic_operations", "brain_core"],
        ),
    ]

    high_priority = [item for item in all_signals if item.severity == "HIGH"]
    medium_priority = [item for item in all_signals if item.severity == "MEDIUM"]
    low_priority = [item for item in all_signals if item.severity == "LOW"]

    curriculum_signals = [item for item in all_signals if item.signal_id in {"AO-SIG-001", "AO-SIG-008"}]
    timetable_signals = [item for item in all_signals if item.signal_id in {"AO-SIG-002", "AO-SIG-009"}]
    attendance_signals = [item for item in all_signals if item.signal_id in {"AO-SIG-003", "AO-SIG-008"}]
    assessment_signals = [item for item in all_signals if item.signal_id in {"AO-SIG-004", "AO-SIG-008"}]
    teaching_load_signals = [item for item in all_signals if item.signal_id in {"AO-SIG-005", "AO-SIG-009"}]
    internship_signals = [item for item in all_signals if item.signal_id in {"AO-SIG-006", "AO-SIG-007"}]

    health_classification = "HEALTHY" if sig_010 >= 75 else "WATCH" if sig_010 >= 50 else "CRITICAL"

    return AcademicOperationsSignalsRuntimeResponse(
        tenant_id=tenant,
        overview=AcademicOperationsSignalsRuntimeOverview(generated_at=_now()),
        signal_summary=AcademicOperationsSignalSummary(
            total_signals=len(all_signals),
            high_priority_total=len(high_priority),
            medium_priority_total=len(medium_priority),
            low_priority_total=len(low_priority),
        ),
        signal_distribution=AcademicOperationsSignalDistribution(
            by_severity={
                "HIGH": len(high_priority),
                "MEDIUM": len(medium_priority),
                "LOW": len(low_priority),
            },
            by_domain={
                "curriculum": len(curriculum_signals),
                "timetable": len(timetable_signals),
                "attendance": len(attendance_signals),
                "assessment": len(assessment_signals),
                "teaching_load": len(teaching_load_signals),
                "internship": len(internship_signals),
            },
        ),
        high_priority_signals=_build_section(high_priority, ["academic_operations", "brain_core"]),
        medium_priority_signals=_build_section(medium_priority, ["academic_operations", "brain_core"]),
        low_priority_signals=_build_section(low_priority, ["academic_operations", "brain_core"]),
        curriculum_signals=_build_section(curriculum_signals, ["academic_operations", "curriculum", "brain_core"]),
        timetable_signals=_build_section(timetable_signals, ["scheduling", "academic_operations", "brain_core"]),
        attendance_signals=_build_section(attendance_signals, ["attendance", "academic_operations", "brain_core"]),
        assessment_signals=_build_section(assessment_signals, ["academic_operations", "scheduling", "brain_core"]),
        teaching_load_signals=_build_section(teaching_load_signals, ["faculty", "academic_operations", "brain_core"]),
        internship_signals=_build_section(internship_signals, ["internship", "academic_operations", "brain_core"]),
        health_score=AcademicOperationsHealthScore(
            composite_score=sig_010,
            classification=health_classification,
            contributing_factors=[
                f"curriculum_risk={sig_001}",
                f"schedule_risk={sig_002}",
                f"attendance_risk={sig_003}",
                f"assessment_risk={sig_004}",
                f"teaching_load_risk={sig_005}",
                f"internship_risk={sig_006}",
                f"engagement_risk={sig_007}",
                f"progress_deviation={sig_008}",
                f"program_delivery={sig_009}",
            ],
        ),
        recommended_actions=_recommended_actions(all_signals),
    )
