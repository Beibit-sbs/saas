"""Read-only Internship runtime service (A-052.12-E1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.modules.academic_operations import repository
from app.modules.academic_operations.dependencies import validate_tenant_id
from app.modules.academic_operations_runtime.internship_runtime_schemas import (
    ActiveInternshipRecord,
    HighRiskInternship,
    InternshipActiveInternships,
    InternshipCompletionSummary,
    InternshipEmployerEngagement,
    InternshipHighRiskInternships,
    InternshipPlacementDistribution,
    InternshipReadiness,
    InternshipRiskSummary,
    InternshipRuntimeOverview,
    InternshipRuntimeResponse,
    InternshipRuntimeStatistics,
    InternshipSignals,
)
from app.modules.internship.service import list_applications, list_postings

_ACTIVE_APP_STATES = {"APPLIED", "SHORTLISTED", "INTERVIEW", "OFFERED"}
_COMPLETED_APP_STATES = {"ACCEPTED", "REJECTED"}


def _now() -> datetime:
    return datetime.now(UTC)


def _safe_iso_to_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _pct(part: int, whole: int) -> float:
    if whole <= 0:
        return 0.0
    return round((part / whole) * 100.0, 2)


def get_internship_runtime(db: Session, tenant_id: int) -> InternshipRuntimeResponse:
    tenant = validate_tenant_id(tenant_id)

    postings = list_postings(tenant)
    applications = list_applications(tenant)
    bridge_summary = repository.get_canonical_bridge_summary(db, tenant)

    applications_by_posting: dict[str, list[dict]] = {}
    for application in applications:
        posting_key = str(application.get("posting_id") or "")
        applications_by_posting.setdefault(posting_key, []).append(application)

    completed_applications = [app for app in applications if str(app.get("status") or "") in _COMPLETED_APP_STATES]
    active_applications = [app for app in applications if str(app.get("status") or "") in _ACTIVE_APP_STATES]
    accepted_applications = [app for app in applications if str(app.get("status") or "") == "ACCEPTED"]

    employer_ids = [str(posting.get("company_id") or "UNASSIGNED") for posting in postings]
    unique_employers = {employer for employer in employer_ids if employer}
    repeat_employers = sum(1 for employer in unique_employers if employer_ids.count(employer) > 1)

    by_employer: dict[str, int] = {}
    by_industry: dict[str, int] = {}
    by_department: dict[str, int] = {}
    active_items: list[ActiveInternshipRecord] = []
    high_risk_items: list[HighRiskInternship] = []

    overdue_cutoff = _now() - timedelta(days=90)
    overdue_total = 0

    for posting in postings:
        posting_id = str(posting.get("id") or "unknown")
        employer = str(posting.get("company_id") or "UNASSIGNED")
        industry = str(posting.get("industry") or "unspecified")
        department = str(posting.get("department_id") or "unspecified")
        posting_apps = applications_by_posting.get(posting_id, [])
        posting_active = [app for app in posting_apps if str(app.get("status") or "") in _ACTIVE_APP_STATES]
        posting_accepted = [app for app in posting_apps if str(app.get("status") or "") == "ACCEPTED"]
        posting_rejected = [app for app in posting_apps if str(app.get("status") or "") == "REJECTED"]

        by_employer[employer] = by_employer.get(employer, 0) + len(posting_apps)
        by_industry[industry] = by_industry.get(industry, 0) + len(posting_apps)
        by_department[department] = by_department.get(department, 0) + len(posting_apps)

        if posting_active or posting_accepted:
            active_items.append(
                ActiveInternshipRecord(
                    internship_identifier=posting_id,
                    employer=employer,
                    student_count=len(posting_active) + len(posting_accepted),
                    status="ACTIVE" if posting_active else "PLACED",
                )
            )

        created_at = _safe_iso_to_datetime(posting.get("created_at"))
        is_overdue = bool(created_at and created_at < overdue_cutoff and (posting_active or not posting_accepted))
        if is_overdue:
            overdue_total += 1

        risk_reason = ""
        if len(posting_apps) == 0:
            risk_reason = "no_participation_detected"
        elif posting_active and is_overdue:
            risk_reason = "active_internship_overdue"
        elif len(posting_rejected) > len(posting_accepted):
            risk_reason = "high_rejection_ratio"

        if risk_reason:
            high_risk_items.append(
                HighRiskInternship(
                    internship_identifier=posting_id,
                    employer=employer,
                    student_count=len(posting_apps),
                    risk_reason=risk_reason,
                )
            )

    total_internships = len(postings)
    active_internships_total = len(active_items)
    completed_internships_total = len(completed_applications)
    employer_count = len(unique_employers)
    total_applications = len(applications)

    high_risk_count = len(high_risk_items)
    medium_risk_count = max(0, min(len(postings), max(0, total_internships - high_risk_count - max(1, employer_count // 2))))
    low_risk_count = max(0, total_internships - high_risk_count - medium_risk_count)

    ao_signal_types: list[str] = []
    ao_indicators: list[str] = []
    if high_risk_count > 0:
        ao_signal_types.append("AO-SIG-INT-001")
        ao_indicators.append("high_risk_internships_present")
    if overdue_total > 0:
        ao_signal_types.append("AO-SIG-INT-002")
        ao_indicators.append("overdue_internships_detected")
    if employer_count == 0:
        ao_signal_types.append("AO-SIG-INT-003")
        ao_indicators.append("no_employer_engagement")
    if _pct(len(accepted_applications), max(1, total_applications)) < 35.0 and total_applications > 0:
        ao_signal_types.append("AO-SIG-INT-004")
        ao_indicators.append("low_placement_conversion")

    bridge_bonus = sum(int(v) for k, v in bridge_summary.items() if "internship" in str(k).lower())
    readiness_score = max(
        0,
        min(
            100,
            65
            + employer_count * 3
            + min(15, bridge_bonus)
            + len(accepted_applications)
            - high_risk_count * 10
            - overdue_total * 8,
        ),
    )
    readiness_classification = "READY" if readiness_score >= 70 else "PARTIAL" if readiness_score >= 45 else "NOT_READY"
    readiness_drivers = [
        "read_only_runtime",
        "aggregator_only_runtime",
        "tenant_scoped_visibility",
        "summary_read_rbac_required",
        "no_mutation_operations",
    ]
    if employer_count > 0:
        readiness_drivers.append("employer_participation_detected")
    if len(accepted_applications) > 0:
        readiness_drivers.append("placement_pipeline_active")

    return InternshipRuntimeResponse(
        tenant_id=tenant,
        overview=InternshipRuntimeOverview(generated_at=_now()),
        internship_statistics=InternshipRuntimeStatistics(
            participation_rate=_pct(total_applications, max(1, total_internships)),
            completion_rate=_pct(completed_internships_total, max(1, total_applications)),
            active_rate=_pct(active_internships_total, max(1, total_internships)),
            placement_rate=_pct(len(accepted_applications), max(1, total_applications)),
            total_internships=total_internships,
            active_internships=active_internships_total,
            completed_internships=completed_internships_total,
            employer_count=employer_count,
        ),
        placement_distribution=InternshipPlacementDistribution(
            by_employer=by_employer,
            by_industry=by_industry,
            by_department=by_department,
        ),
        completion_summary=InternshipCompletionSummary(
            completed=completed_internships_total,
            active=active_internships_total,
            overdue=overdue_total,
        ),
        active_internships=InternshipActiveInternships(
            records=active_internships_total,
            source_modules=["internship", "academic_operations"],
            items=active_items,
        ),
        employer_engagement=InternshipEmployerEngagement(
            employer_participation_rate=_pct(employer_count, max(1, total_internships)),
            repeat_employers=repeat_employers,
            placement_volume=len(accepted_applications),
            employer_count=employer_count,
        ),
        internship_risk_summary=InternshipRiskSummary(
            high_risk_count=high_risk_count,
            medium_risk_count=medium_risk_count,
            low_risk_count=low_risk_count,
        ),
        high_risk_internships=InternshipHighRiskInternships(
            records=high_risk_count,
            source_modules=["internship", "brain_core", "academic_operations"],
            items=high_risk_items,
        ),
        internship_signals=InternshipSignals(
            generated_signals=len(ao_signal_types),
            signal_types=ao_signal_types,
            indicators=ao_indicators,
        ),
        internship_readiness=InternshipReadiness(
            readiness_score=readiness_score,
            readiness_classification=readiness_classification,
            readiness_drivers=readiness_drivers,
            ready_for_runtime=readiness_score >= 70,
        ),
    )
