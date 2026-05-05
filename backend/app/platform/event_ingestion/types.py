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
        # A-016.2 Thesis Governance + Supervisor Assignment events
        "thesis.submission.created",
        "thesis.submission.pending_review",
        "thesis.supervisor.assignment_needed",
        "thesis.supervisor.overloaded",
        "thesis.review.delayed",
        "thesis.governance.risk_detected",
        # A-015.6 Wave 3 KPI extension — budget overrun / finance
        "finance.expense.budget_exceeded",
        "campus.budget.overrun_risk_detected",
        "campus.expense_controls.budget_exceeded_risk_detected",
        # A-017.1 budget_planning maturity closure — budget plan lifecycle events
        "budget_plan.created",
        "budget_plan.review_requested",
        "budget_plan.approved",
        "budget_plan.locked",
        "budget_plan.rejected",
        "budget_plan.outcome_recorded",
        # A-017.1 budget_planning maturity closure — budget variance drift signal
        "finance.budget_variance.threshold_reached",
        # A-015.6 Wave 3 KPI extension — procurement
        "procurement.request_submitted",
        "procurement.approval_required",
        "procurement.po_issued",
        # A-015.6 Wave 3 KPI extension — PO delivery / asset
        "procurement.asset_created",
        # A-015.6 Wave 3 KPI extension — finance operations health
        "finance.operations.health_check",
        "finance.operations.risk_detected",
        # A-015.6 Wave 3 KPI extension — inventory / supply risk
        "inventory.low_stock.detected",
        "inventory.reorder_needed",
        "supply.risk.detected",
        "procurement.inventory_gap.detected",
        # A-016.1 Wave 4 KPI extension — academic integrity violation signals
        "academic_integrity.violation.detected",
        "academic_integrity.risk_detected",
        "plagiarism.similarity.high_detected",
        "exam.proctoring.violation_detected",
        "coursework.submission.suspicious_detected",
        "ai_plagiarism.risk_detected",
        # A-016.3 Exam Proctoring Violation Workflow dedicated signals
        "faculty.proctoring.violation_detected",
        "exam.proctoring.suspicious_activity_detected",
        "exam.proctoring.multiple_faces_detected",
        "exam.proctoring.face_mismatch_detected",
        "exam.proctoring.forbidden_app_detected",
        "exam.proctoring.camera_absent_detected",
        # A-016.4 Research Ethics / Compliance Review signals
        "research_ethics.application.submitted",
        "research_ethics.review.overdue",
        "research_ethics.high_risk.detected",
        "research_ethics.missing_consent.detected",
        "research_ethics.document_missing.detected",
        "research_ethics.conflict_of_interest.detected",
        "research_ethics.violation.reported",
        "research.compliance.risk_detected",
        "research.data_privacy.risk_detected",
        "compliance.review.required",
        # A-016.5 Academic Integrity Case Resolution Automation signals
        "academic_integrity.case.opened",
        "academic_integrity.case.evidence_requested",
        "academic_integrity.case.review_required",
        "academic_integrity.case.resolved",
        "academic_integrity.case.dismissed",
        "integrity.resolution.workflow_needed",
    }
)
