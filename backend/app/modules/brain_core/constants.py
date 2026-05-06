from __future__ import annotations

STUDENT_RISK_EVENT_TYPES = {
    "academic.attendance_risk.detected",
    "academic.grade_risk.detected",
}

THESIS_DELAY_EVENT_TYPES = {
    "thesis.status_changed",
}

FACULTY_OVERLOAD_EVENT_TYPES = {
    "faculty.workload_overload.detected",
    "faculty.quality_drop.detected",
}

PAYMENT_OVERDUE_EVENT_TYPES = {
    "finance.payment_overdue.detected",
}

BUDGET_OVERRUN_EVENT_TYPES = {
    "finance.expense.budget_exceeded",
    "campus.budget.overrun_risk_detected",
    "campus.expense_controls.budget_exceeded_risk_detected",
}

STUDENT_SUPPORT_EVENT_TYPES = {
    "financial_aid.warning.detected",
    "housing.status.risk_detected",
    "scholarship.award.at_risk_detected",
}

PROCUREMENT_EVENT_TYPES = {
    "finance.budget_variance.threshold_reached",
    "procurement.vendor_sla.degraded",
    "procurement.contract_risk.high",
}

# A-015.2 Procurement Approval Automation events
PROCUREMENT_APPROVAL_EVENT_TYPES = {
    "procurement.request_submitted",
    "procurement.approval_required",
}

# A-015.4 Finance Operations Health Brain events
FINANCE_OPERATIONS_HEALTH_EVENT_TYPES = {
    "finance.operations.health_check",
    "finance.operations.risk_detected",
}

SUPPLY_LOW_EVENT_TYPES = {
    "operations.consumable_stock.low",
}

# A-015.5 Inventory Low Stock / Supply Risk Brain events
INVENTORY_LOW_STOCK_EVENT_TYPES = {
    "inventory.low_stock.detected",
    "inventory.reorder_needed",
    "supply.risk.detected",
    "procurement.inventory_gap.detected",
}

ACCREDITATION_EVENT_TYPES = {
    "accreditation.status_changed",
}

PLATFORM_RELIABILITY_EVENT_TYPES = {
    "platform.workflow.failed",
    "platform.integration.degraded",
}

PLATFORM_ACTIVITY_EVENT_TYPES = {
    "platform.module.activity.logged",
}

RESEARCH_EVENT_TYPES = {
    "research.grant_deadline.approaching",
    "research.publication_stagnant",
    "research.grant_pipeline.at_risk",
    "research.lab_utilization.low",
}

OPERATIONS_EVENT_TYPES = {
    "campus.security_incident.detected",
    "campus.transport.disruption_detected",
    "campus.dining.capacity_exceeded",
    "operations.facility_issue.reported",
    "operations.cleaning_service.missed",
    "operations.maintenance.predicted_due",
    "operations.utilities.spike_detected",
}

STUDENT_LIFE_EVENT_TYPES = {
    "student_life.wellbeing.at_risk",
    "student_life.disciplinary.incident_reported",
}

ENROLLMENT_DROPOUT_EVENT_TYPES = {
    "enrollments.dropout_risk.detected",
}

ADMISSIONS_EVENT_TYPES = {
    "admissions.decision.made",
}

SCHEDULING_EVENT_TYPES = {
    "scheduling.section.scheduled",
}

# A-013.3: Scheduling conflict and enrollment capacity risk signals
SECTION_CONFLICT_EVENT_TYPES = {
    "scheduling.section.conflict_detected",
}

ENROLLMENT_CAPACITY_RISK_EVENT_TYPES = {
    "enrollment.capacity_risk.detected",
}

ACADEMIC_INTEGRITY_EVENT_TYPES = {
    "academic_integrity.case.escalated",
}

# A-016.2 Thesis Governance + Supervisor Assignment events
THESIS_GOVERNANCE_EVENT_TYPES = frozenset({
    "thesis.submission.created",
    "thesis.submission.pending_review",
    "thesis.supervisor.assignment_needed",
    "thesis.supervisor.overloaded",
    "thesis.review.delayed",
    "thesis.governance.risk_detected",
})

# A-016.2 Actions
ACTION_ASSIGN_SUPERVISOR = "assign_supervisor"
ACTION_REQUEST_SUPERVISOR_REVIEW = "request_supervisor_review"
ACTION_NOTIFY_DEPARTMENT = "notify_department"
ACTION_ESCALATE_TO_ACADEMIC_OFFICE = "escalate_to_academic_office"

# A-016.1 Academic Integrity Violation Detection Brain events
ACADEMIC_INTEGRITY_VIOLATION_EVENT_TYPES = {
    "academic_integrity.violation.detected",
    "academic_integrity.risk_detected",
    "plagiarism.similarity.high_detected",
    "exam.proctoring.violation_detected",
    "coursework.submission.suspicious_detected",
    "ai_plagiarism.risk_detected",
}

# A-016.1 Actions
ACTION_NOTIFY_ACADEMIC_OFFICE = "notify_academic_office"
ACTION_CREATE_INTEGRITY_REVIEW = "create_integrity_review"
ACTION_REQUEST_MANUAL_REVIEW = "request_manual_review"
ACTION_ESCALATE_TO_COMMITTEE = "escalate_to_committee"

# A-016.3 Exam Proctoring Violation Workflow events
EXAM_PROCTORING_EVENT_TYPES = frozenset({
    "exam.violation_detected",
    "faculty.proctoring.violation_detected",
    "exam.proctoring.suspicious_activity_detected",
    "exam.proctoring.multiple_faces_detected",
    "exam.proctoring.face_mismatch_detected",
    "exam.proctoring.forbidden_app_detected",
    "exam.proctoring.camera_absent_detected",
})

# A-016.3 Actions
ACTION_REQUEST_MANUAL_PROCTOR_REVIEW = "request_manual_proctor_review"
ACTION_NOTIFY_EXAM_OFFICE = "notify_exam_office"
ACTION_ESCALATE_TO_ACADEMIC_INTEGRITY_COMMITTEE = "escalate_to_academic_integrity_committee"
ACTION_COLLECT_ADDITIONAL_EVIDENCE = "collect_additional_evidence"

# A-016.4 Research Ethics / Compliance Review events
RESEARCH_ETHICS_COMPLIANCE_EVENT_TYPES = frozenset({
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
})

# A-016.4 Actions
ACTION_REQUEST_ETHICS_REVIEW = "request_ethics_review"
ACTION_NOTIFY_ETHICS_COMMITTEE = "notify_ethics_committee"
ACTION_REQUEST_MISSING_DOCUMENTS = "request_missing_documents"
ACTION_REQUEST_CONSENT_REVIEW = "request_consent_review"
ACTION_REQUEST_DATA_PRIVACY_REVIEW = "request_data_privacy_review"
ACTION_REQUEST_CONFLICT_OF_INTEREST_REVIEW = "request_conflict_of_interest_review"
ACTION_ESCALATE_TO_COMPLIANCE_OFFICER = "escalate_to_compliance_officer"

# A-016.5 Academic Integrity Case Resolution Automation events
ACADEMIC_INTEGRITY_CASE_RESOLUTION_EVENT_TYPES = frozenset({
    "academic_integrity.case.opened",
    "academic_integrity.case.evidence_requested",
    "academic_integrity.case.review_required",
    "academic_integrity.case.resolved",
    "academic_integrity.case.dismissed",
    "integrity.resolution.workflow_needed",
})

# A-016.5 Actions
ACTION_OPEN_REVIEW_CASE = "open_review_case"
ACTION_REQUEST_EVIDENCE = "request_evidence"
ACTION_ASSIGN_REVIEWER = "assign_reviewer"
ACTION_NOTIFY_COMMITTEE = "notify_committee"
ACTION_ESCALATE_OVERDUE_CASE = "escalate_overdue_case"
ACTION_MARK_READY_FOR_HUMAN_DECISION = "mark_ready_for_human_decision"
ACTION_CLOSE_AS_DISMISSED_REQUIRES_APPROVAL = "close_as_dismissed_requires_approval"
ACTION_CLOSE_AS_VIOLATION_REQUIRES_APPROVAL = "close_as_violation_requires_approval"

ACADEMIC_RECORDS_EVENT_TYPES = {
    "academic_records.inconsistency.detected",
}

PROGRAMS_EVENT_TYPES = {
    "programs.status.risk_detected",
}

COURSES_EVENT_TYPES = {
    "courses.status.risk_detected",
}

TRANSCRIPTS_EVENT_TYPES = {
    "transcripts.inconsistency.detected",
}

DEGREE_PROGRESS_EVENT_TYPES = {
    "degree_progress.graduation_risk.detected",
}

STUDENT_SERVICES_EVENT_TYPES = {
    "student_services.ticket.escalated",
}

SUPPORTED_SIGNAL_EVENT_TYPES = set(
    STUDENT_RISK_EVENT_TYPES
    | THESIS_DELAY_EVENT_TYPES
    | FACULTY_OVERLOAD_EVENT_TYPES
    | PAYMENT_OVERDUE_EVENT_TYPES
    | BUDGET_OVERRUN_EVENT_TYPES
    | STUDENT_SUPPORT_EVENT_TYPES
    | PROCUREMENT_EVENT_TYPES
    | SUPPLY_LOW_EVENT_TYPES
    | ACCREDITATION_EVENT_TYPES
    | PLATFORM_RELIABILITY_EVENT_TYPES
    | PLATFORM_ACTIVITY_EVENT_TYPES
    | RESEARCH_EVENT_TYPES
    | OPERATIONS_EVENT_TYPES
    | STUDENT_LIFE_EVENT_TYPES
    | ENROLLMENT_DROPOUT_EVENT_TYPES
    | ACADEMIC_INTEGRITY_EVENT_TYPES
    | ACADEMIC_INTEGRITY_VIOLATION_EVENT_TYPES
    | ACADEMIC_RECORDS_EVENT_TYPES
    | PROGRAMS_EVENT_TYPES
    | COURSES_EVENT_TYPES
    | TRANSCRIPTS_EVENT_TYPES
    | DEGREE_PROGRESS_EVENT_TYPES
    | STUDENT_SERVICES_EVENT_TYPES
    | ADMISSIONS_EVENT_TYPES
    | SCHEDULING_EVENT_TYPES
    | SECTION_CONFLICT_EVENT_TYPES
    | ENROLLMENT_CAPACITY_RISK_EVENT_TYPES
    | PROCUREMENT_APPROVAL_EVENT_TYPES
    | THESIS_GOVERNANCE_EVENT_TYPES
    | EXAM_PROCTORING_EVENT_TYPES
    | RESEARCH_ETHICS_COMPLIANCE_EVENT_TYPES
    | ACADEMIC_INTEGRITY_CASE_RESOLUTION_EVENT_TYPES
)

ACTION_CREATE_INTERVENTION_CASE = "create_intervention_case"
ACTION_NOTIFY_ADVISOR = "notify_advisor"
ACTION_NOTIFY_FACULTY = "notify_faculty"
ACTION_CREATE_SUPERVISION_TASK = "create_supervision_task"
ACTION_CREATE_WORKLOAD_REVIEW_TASK = "create_workload_review_task"
ACTION_CREATE_COLLECTIONS_CASE = "create_collections_case"
ACTION_NOTIFY_FINANCE = "notify_finance"
ACTION_NOTIFY_PROCUREMENT_TEAM = "notify_procurement_team"
ACTION_CREATE_REPLENISHMENT_TASK = "create_replenishment_task"
ACTION_INITIATE_PROCUREMENT_REQUEST = "initiate_procurement_request"
# A-015.2
ACTION_CREATE_PROCUREMENT_APPROVAL_CASE = "create_procurement_approval_case"
ACTION_NOTIFY_OPERATIONS = "notify_operations"
ACTION_CREATE_ACCREDITATION_REMEDIATION_WORKFLOW = "create_accreditation_remediation_workflow"
ACTION_NOTIFY_COMPLIANCE = "notify_compliance"
ACTION_CREATE_PLATFORM_RELIABILITY_INCIDENT = "create_platform_reliability_incident"
ACTION_NOTIFY_PLATFORM = "notify_platform"
ACTION_CREATE_RESEARCH_REMEDIATION_WORKFLOW = "create_research_remediation_workflow"
ACTION_NOTIFY_RESEARCH_OFFICE = "notify_research_office"
ACTION_CREATE_FACILITY_INCIDENT_WORKFLOW = "create_facility_incident_workflow"
ACTION_CREATE_CLEANING_RECOVERY_TASK = "create_cleaning_recovery_task"
ACTION_NOTIFY_FACILITIES_TEAM = "notify_facilities_team"
ACTION_CREATE_STUDENT_SUPPORT_CASE = "create_student_support_case"
ACTION_CREATE_DISCIPLINARY_REVIEW_CASE = "create_disciplinary_review_case"
ACTION_NOTIFY_STUDENT_SUCCESS_TEAM = "notify_student_success_team"

DEFAULT_DECISION_TTL_HOURS = 72
