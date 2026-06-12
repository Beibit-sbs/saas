"""Read-only Teaching Load runtime service (A-052.11-E1)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.modules.academic_operations import repository
from app.modules.academic_operations.dependencies import validate_tenant_id
from app.modules.faculty.service import get_workload_metrics, list_workload_alerts
from app.modules.teaching_load_contracts.service import get_teaching_load_contracts_l4_visibility_summary

from app.modules.academic_operations_runtime.teaching_load_runtime_schemas import (
    FacultyWorkloadDistribution,
    TeachingLoadReadiness,
    TeachingLoadRiskSummary,
    TeachingLoadRuntimeOverview,
    TeachingLoadRuntimeResponse,
    TeachingLoadRuntimeSection,
    TeachingLoadRuntimeStatistics,
    TeachingLoadSignals,
    WorkloadUtilization,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _bridge_count(bridge_summary: dict[str, int], *tokens: str) -> int:
    lowered = tuple(token.lower() for token in tokens)
    total = 0
    for key, value in bridge_summary.items():
        key_lower = str(key).lower()
        if any(token in key_lower for token in lowered):
            total += int(value)
    return total


def _coerce_term_id(term_total: int) -> int:
    return term_total if term_total > 0 else 1


def get_teaching_load_runtime(db: Session, tenant_id: int) -> TeachingLoadRuntimeResponse:
    tenant = validate_tenant_id(tenant_id)

    dashboard_summary = repository.compute_dashboard_summary(db, tenant)
    bridge_summary = repository.get_canonical_bridge_summary(db, tenant)
    term_id = _coerce_term_id(sum(int(v) for v in dashboard_summary["summer_semester_terms"].values()))

    workload_metrics = get_workload_metrics(tenant, term_id)
    workload_alerts = list_workload_alerts(tenant, term_id)
    readiness_summary = get_teaching_load_contracts_l4_visibility_summary(
        tenant,
        {
            "faculty_identity_present": True,
            "teaching_load_plan_present": workload_metrics["total_faculty"] > 0,
            "course_assignment_evidence_present": workload_metrics["total_faculty"] > 0,
            "workload_policy_available": True,
            "faculty_review_required": True,
        },
    )

    tracked_faculty_total = int(workload_metrics["total_faculty"])
    department_groups_total = len(workload_metrics["departments"])
    overload_total = int(workload_metrics["alert_count_by_type"]["overload"]) + int(
        workload_metrics["alert_count_by_type"]["max_credit_exceeded"]
    )
    underutilized_total = int(workload_metrics["alert_count_by_type"]["underload"])
    fairness_alert_total = sum(1 for alert in workload_alerts if "fairness_check" in (alert.get("alerts") or []))
    high_risk_assignments_total = sum(
        1
        for alert in workload_alerts
        if any(flag in (alert.get("alerts") or []) for flag in ("overload_threshold", "max_credit_exceeded"))
    )
    assignment_health_total = tracked_faculty_total - high_risk_assignments_total

    workload_signal_types: list[str] = []
    if overload_total > 0:
        workload_signal_types.append("teaching_load_overload")
    if underutilized_total > 0:
        workload_signal_types.append("teaching_load_underutilization")
    if fairness_alert_total > 0:
        workload_signal_types.append("teaching_load_distribution_variance")
    if assignment_health_total == 0 and tracked_faculty_total > 0:
        workload_signal_types.append("faculty_assignment_coverage_gap")

    overload_indicators: list[str] = []
    if workload_metrics["max_utilization_pct"] > 1.0:
        overload_indicators.append("utilization_above_capacity")
    if overload_total > 0:
        overload_indicators.append("overload_alerts_present")

    coverage_indicators: list[str] = []
    if fairness_alert_total > 0:
        coverage_indicators.append("department_distribution_imbalance")
    if assignment_health_total < tracked_faculty_total:
        coverage_indicators.append("high_risk_assignment_gap")
    if tracked_faculty_total == 0:
        coverage_indicators.append("faculty_workload_visibility_unavailable")

    risk_score = max(0, min(100, overload_total * 20 + fairness_alert_total * 10 + underutilized_total * 8))
    coverage_risk_score = max(0, min(100, len(coverage_indicators) * 25 + max(0, tracked_faculty_total - assignment_health_total) * 4))
    readiness_score = max(
        0,
        min(
            100,
            int(readiness_summary["evidence_summary"]["completeness_percent"])
            + tracked_faculty_total
            - risk_score
            - coverage_risk_score
            + len(workload_signal_types) * 3,
        ),
    )

    return TeachingLoadRuntimeResponse(
        tenant_id=tenant,
        overview=TeachingLoadRuntimeOverview(generated_at=_now()),
        teaching_load_statistics=TeachingLoadRuntimeStatistics(
            tracked_faculty_total=tracked_faculty_total,
            department_groups_total=department_groups_total,
            high_utilization_total=overload_total,
            low_utilization_total=underutilized_total,
            high_risk_assignments_total=high_risk_assignments_total,
            teaching_load_signals_total=len(workload_signal_types),
            canonical_bridge_total=_bridge_count(bridge_summary, "teaching_load", "workload", "faculty"),
        ),
        faculty_workload_distribution=FacultyWorkloadDistribution(
            evenly_distributed_total=max(0, tracked_faculty_total - overload_total - underutilized_total),
            overloaded_total=overload_total,
            underutilized_total=underutilized_total,
            fairness_alert_total=fairness_alert_total,
        ),
        workload_utilization=WorkloadUtilization(
            average_utilization_pct=float(workload_metrics["average_utilization_pct"]),
            median_utilization_pct=float(workload_metrics["median_utilization_pct"]),
            min_utilization_pct=float(workload_metrics["min_utilization_pct"]),
            max_utilization_pct=float(workload_metrics["max_utilization_pct"]),
            utilization_std_dev=float(workload_metrics["utilization_std_dev"]),
        ),
        overload_risk_summary=TeachingLoadRiskSummary(
            risk_score=risk_score,
            open_risks=overload_total,
            indicators=overload_indicators,
        ),
        underutilization_summary=TeachingLoadRuntimeSection(
            records=underutilized_total,
            source_modules=["faculty", "teaching_load_contracts"],
        ),
        faculty_assignment_health=TeachingLoadRuntimeSection(
            records=assignment_health_total,
            source_modules=["faculty", "scheduling"],
        ),
        coverage_risk_summary=TeachingLoadRiskSummary(
            risk_score=coverage_risk_score,
            open_risks=len(coverage_indicators),
            indicators=coverage_indicators,
        ),
        high_risk_assignments=TeachingLoadRuntimeSection(
            records=high_risk_assignments_total,
            source_modules=["faculty", "scheduling", "teaching_load_contracts"],
        ),
        teaching_load_signals=TeachingLoadSignals(
            generated_signals=len(workload_signal_types),
            signal_types=workload_signal_types,
        ),
        teaching_load_readiness=TeachingLoadReadiness(
            ready_for_runtime=readiness_score >= 60 and tracked_faculty_total > 0,
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