"""Platform event type constants for the event ingestion layer."""
from __future__ import annotations

# Fired when analytics event projection data is read (GET /api/analytics/kpis)
ANALYTICS_EVENT_READ: str = "analytics.event.read"

# Fired when KPI data is read (GET /api/analytics/kpis/trends|insights|recommendations)
ANALYTICS_KPI_READ: str = "analytics.kpi.read"

# Fired when billing usage is incremented (billing.increment_usage)
BILLING_USAGE_RECORDED: str = "billing.usage.recorded"

# Fired when tenant KPI refresh is executed (POST /api/analytics/kpis/refresh)
KPI_REFRESH_EXECUTED: str = "analytics.kpi.refresh.executed"

VALID_EVENT_TYPES: frozenset[str] = frozenset(
    {
        ANALYTICS_EVENT_READ,
        ANALYTICS_KPI_READ,
        BILLING_USAGE_RECORDED,
        KPI_REFRESH_EXECUTED,
        # A-013.5 Wave 1 KPI extension — student success / early warning
        "academic.attendance_risk.detected",
        "academic.grade_risk.detected",
        # A-013.5 Wave 1 KPI extension — intervention pipeline
        "interventions.case.created",
        "interventions.case_outcome.recorded",
        "interventions.auto_triggered",
        # A-013.5 Wave 1 KPI extension — scheduling / enrollment capacity
        "scheduling.section.created",
        "scheduling.section.conflict_detected",
        "enrollment.created",
        "enrollment.capacity_risk.detected",
        # A-014.6 Wave 2 KPI extension — graduation / degree progress
        "degree_progress.graduation_risk.detected",
        # A-014.6 Wave 2 KPI extension — scholarship / financial aid risk
        "scholarship.award.at_risk_detected",
        "financial_aid.warning.detected",
        # A-014.6 Wave 2 KPI extension — thesis completion risk
        "thesis.status_changed",
    }
)
