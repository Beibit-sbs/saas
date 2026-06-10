"""Quality / Accreditation backend foundation permission constants."""

from __future__ import annotations

OVERVIEW_READ = "quality_accreditation.overview.read"
DASHBOARD_READ = "quality_accreditation.dashboard.read"
HEALTH_READ = "quality_accreditation.health.read"
MATRIX_READ = "quality_accreditation.matrix.read"
LIMITATIONS_READ = "quality_accreditation.limitations.read"

STANDARDS_READ = "quality_accreditation.standards.read"
STANDARDS_CREATE = "quality_accreditation.standards.create"
STANDARDS_UPDATE = "quality_accreditation.standards.update"
CRITERIA_READ = "quality_accreditation.criteria.read"
CRITERIA_CREATE = "quality_accreditation.criteria.create"
CRITERIA_UPDATE = "quality_accreditation.criteria.update"

EVIDENCE_READ = "quality_accreditation.evidence.read"
EVIDENCE_ATTACH = "quality_accreditation.evidence.attach"
EVIDENCE_REVIEW = "quality_accreditation.evidence.review"
EVIDENCE_LIMITATIONS_MANAGE = "quality_accreditation.evidence.limitations.manage"

PROGRAM_READINESS_READ = "quality_accreditation.program_readiness.read"
PROGRAM_READINESS_UPDATE = "quality_accreditation.program_readiness.update"
INSTITUTIONAL_READINESS_READ = "quality_accreditation.institutional_readiness.read"
INSTITUTIONAL_READINESS_UPDATE = "quality_accreditation.institutional_readiness.update"

SELF_ASSESSMENT_READ = "quality_accreditation.self_assessment.read"
SELF_ASSESSMENT_CREATE = "quality_accreditation.self_assessment.create"
SELF_ASSESSMENT_UPDATE = "quality_accreditation.self_assessment.update"

IMPROVEMENT_PLANS_READ = "quality_accreditation.improvement_plans.read"
IMPROVEMENT_PLANS_CREATE = "quality_accreditation.improvement_plans.create"
IMPROVEMENT_PLANS_UPDATE = "quality_accreditation.improvement_plans.update"
INTERNAL_AUDITS_READ = "quality_accreditation.internal_audits.read"
INTERNAL_AUDITS_CREATE = "quality_accreditation.internal_audits.create"
INTERNAL_AUDITS_UPDATE = "quality_accreditation.internal_audits.update"
AUDIT_FINDINGS_READ = "quality_accreditation.audit_findings.read"
AUDIT_FINDINGS_UPDATE = "quality_accreditation.audit_findings.update"

PROGRAM_REVIEW_READ = "quality_accreditation.program_review.read"
PROGRAM_REVIEW_CREATE = "quality_accreditation.program_review.create"
PROGRAM_REVIEW_UPDATE = "quality_accreditation.program_review.update"
LEARNING_OUTCOMES_READ = "quality_accreditation.learning_outcomes.read"
FEEDBACK_READ = "quality_accreditation.feedback.read"
FEEDBACK_METADATA_CREATE = "quality_accreditation.feedback.metadata.create"

COMMITTEE_READ = "quality_accreditation.committee.read"
COMMITTEE_UPDATE = "quality_accreditation.committee.update"
EXTERNAL_REVIEW_READ = "quality_accreditation.external_review.read"
EXTERNAL_REVIEW_CREATE = "quality_accreditation.external_review.create"
EXTERNAL_REVIEW_UPDATE = "quality_accreditation.external_review.update"

GAP_ANALYSIS_READ = "quality_accreditation.gap_analysis.read"
GAP_ANALYSIS_UPDATE = "quality_accreditation.gap_analysis.update"
CALENDAR_READ = "quality_accreditation.calendar.read"
CALENDAR_UPDATE = "quality_accreditation.calendar.update"
RISK_REGISTER_READ = "quality_accreditation.risk_register.read"
RISK_REGISTER_UPDATE = "quality_accreditation.risk_register.update"

BRIDGES_READ = "quality_accreditation.bridges.read"
BRIDGES_CREATE = "quality_accreditation.bridges.create"
BRIDGES_UPDATE = "quality_accreditation.bridges.update"
BRAIN_SIGNALS_READ = "quality_accreditation.brain_signals.read"
AUDIT_READ = "quality_accreditation.audit.read"
STATUS_HISTORY_READ = "quality_accreditation.status_history.read"
SUMMARY_READ = "quality_accreditation.summary.read"

ADMIN_READ = "quality_accreditation.admin.read"
ADMIN_CONFIGURE = "quality_accreditation.admin.configure"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        OVERVIEW_READ,
        DASHBOARD_READ,
        HEALTH_READ,
        MATRIX_READ,
        LIMITATIONS_READ,
        STANDARDS_READ,
        STANDARDS_CREATE,
        STANDARDS_UPDATE,
        CRITERIA_READ,
        CRITERIA_CREATE,
        CRITERIA_UPDATE,
        EVIDENCE_READ,
        EVIDENCE_ATTACH,
        EVIDENCE_REVIEW,
        EVIDENCE_LIMITATIONS_MANAGE,
        PROGRAM_READINESS_READ,
        PROGRAM_READINESS_UPDATE,
        INSTITUTIONAL_READINESS_READ,
        INSTITUTIONAL_READINESS_UPDATE,
        SELF_ASSESSMENT_READ,
        SELF_ASSESSMENT_CREATE,
        SELF_ASSESSMENT_UPDATE,
        IMPROVEMENT_PLANS_READ,
        IMPROVEMENT_PLANS_CREATE,
        IMPROVEMENT_PLANS_UPDATE,
        INTERNAL_AUDITS_READ,
        INTERNAL_AUDITS_CREATE,
        INTERNAL_AUDITS_UPDATE,
        AUDIT_FINDINGS_READ,
        AUDIT_FINDINGS_UPDATE,
        PROGRAM_REVIEW_READ,
        PROGRAM_REVIEW_CREATE,
        PROGRAM_REVIEW_UPDATE,
        LEARNING_OUTCOMES_READ,
        FEEDBACK_READ,
        FEEDBACK_METADATA_CREATE,
        COMMITTEE_READ,
        COMMITTEE_UPDATE,
        EXTERNAL_REVIEW_READ,
        EXTERNAL_REVIEW_CREATE,
        EXTERNAL_REVIEW_UPDATE,
        GAP_ANALYSIS_READ,
        GAP_ANALYSIS_UPDATE,
        CALENDAR_READ,
        CALENDAR_UPDATE,
        RISK_REGISTER_READ,
        RISK_REGISTER_UPDATE,
        BRIDGES_READ,
        BRIDGES_CREATE,
        BRIDGES_UPDATE,
        BRAIN_SIGNALS_READ,
        AUDIT_READ,
        STATUS_HISTORY_READ,
        ADMIN_READ,
        ADMIN_CONFIGURE,
    }
)

QUALITY_ACCREDITATION_PERMISSIONS = sorted(ALL_PERMISSIONS)