from __future__ import annotations

from app.modules.brain_core.constants import (
    BUDGET_OVERRUN_EVENT_TYPES,
    ACADEMIC_INTEGRITY_EVENT_TYPES,
    ACADEMIC_RECORDS_EVENT_TYPES,
    ACCREDITATION_EVENT_TYPES,
    COURSES_EVENT_TYPES,
    DEGREE_PROGRESS_EVENT_TYPES,
    ENROLLMENT_DROPOUT_EVENT_TYPES,
    FACULTY_OVERLOAD_EVENT_TYPES,
    FINANCE_OPERATIONS_HEALTH_EVENT_TYPES,
    INVENTORY_LOW_STOCK_EVENT_TYPES,
    OPERATIONS_EVENT_TYPES,
    PAYMENT_OVERDUE_EVENT_TYPES,
    PLATFORM_ACTIVITY_EVENT_TYPES,
    PLATFORM_RELIABILITY_EVENT_TYPES,
    PROCUREMENT_APPROVAL_EVENT_TYPES,
    PROCUREMENT_EVENT_TYPES,
    PROGRAMS_EVENT_TYPES,
    RESEARCH_EVENT_TYPES,
    STUDENT_LIFE_EVENT_TYPES,
    STUDENT_SERVICES_EVENT_TYPES,
    STUDENT_SUPPORT_EVENT_TYPES,
    STUDENT_RISK_EVENT_TYPES,
    SUPPLY_LOW_EVENT_TYPES,
    THESIS_DELAY_EVENT_TYPES,
    TRANSCRIPTS_EVENT_TYPES,
    SECTION_CONFLICT_EVENT_TYPES,
    ENROLLMENT_CAPACITY_RISK_EVENT_TYPES,
    ACADEMIC_INTEGRITY_VIOLATION_EVENT_TYPES,
    THESIS_GOVERNANCE_EVENT_TYPES,
    EXAM_PROCTORING_EVENT_TYPES,
)


class SignalRegistry:
    signals = {
        "academic.attendance_risk.detected": {
            "signal_class": "academic_risk",
            "scenario": "student_risk",
            "context_sources": ["academic", "student_success", "faculty"],
        },
        "academic.grade_risk.detected": {
            "signal_class": "academic_risk",
            "scenario": "student_risk",
            "context_sources": ["academic", "student_success", "faculty"],
        },
        "thesis.status_changed": {
            "signal_class": "academic_risk",
            "scenario": "thesis_delay",
            "context_sources": ["academic", "student_success", "faculty"],
        },
        "faculty.workload_overload.detected": {
            "signal_class": "faculty_risk",
            "scenario": "faculty_overload",
            "context_sources": ["faculty", "academic"],
        },
        "faculty.quality_drop.detected": {
            "signal_class": "faculty_risk",
            "scenario": "faculty_quality_intervention",
            "context_sources": ["faculty", "academic"],
        },
        "finance.payment_overdue.detected": {
            "signal_class": "financial_risk",
            "scenario": "payment_recovery",
            "context_sources": ["finance", "student_success"],
        },
        "finance.expense.budget_exceeded": {
            "signal_class": "financial_risk",
            "scenario": "budget_overrun_prevention",
            "context_sources": ["finance", "operations", "procurement"],
        },
        "campus.budget.overrun_risk_detected": {
            "signal_class": "financial_risk",
            "scenario": "budget_overrun_prevention",
            "context_sources": ["finance", "operations", "procurement"],
        },
        "campus.expense_controls.budget_exceeded_risk_detected": {
            "signal_class": "financial_risk",
            "scenario": "budget_overrun_prevention",
            "context_sources": ["finance", "operations", "procurement"],
        },
        "financial_aid.warning.detected": {
            "signal_class": "student_success_risk",
            "scenario": "student_support_bridge",
            "context_sources": ["finance", "student_success", "academic"],
        },
        "scholarship.award.at_risk_detected": {
            "signal_class": "student_success_risk",
            "scenario": "student_support_bridge",
            "context_sources": ["finance", "student_success", "academic"],
        },
        "housing.status.risk_detected": {
            "signal_class": "student_success_risk",
            "scenario": "student_support_bridge",
            "context_sources": ["student_success", "operations", "academic"],
        },
        "finance.budget_variance.threshold_reached": {
            "signal_class": "procurement_risk",
            "scenario": "procurement_supply_chain",
            "context_sources": ["finance", "operations"],
        },
        "procurement.vendor_sla.degraded": {
            "signal_class": "procurement_risk",
            "scenario": "procurement_supply_chain",
            "context_sources": ["finance", "operations"],
        },
        "procurement.contract_risk.high": {
            "signal_class": "procurement_risk",
            "scenario": "procurement_supply_chain",
            "context_sources": ["finance", "operations"],
        },
        # A-015.2 — Procurement Approval Automation
        "procurement.request_submitted": {
            "signal_class": "procurement_risk",
            "scenario": "procurement_approval_automation",
            "context_sources": ["finance", "operations"],
        },
        "procurement.approval_required": {
            "signal_class": "procurement_risk",
            "scenario": "procurement_approval_automation",
            "context_sources": ["finance", "operations"],
        },
        "operations.consumable_stock.low": {
            "signal_class": "operational_risk",
            "scenario": "supply_management",
            "context_sources": ["operations", "finance"],
        },
        "accreditation.status_changed": {
            "signal_class": "compliance_risk",
            "scenario": "accreditation_remediation",
            "context_sources": ["academic", "platform"],
        },
        "platform.workflow.failed": {
            "signal_class": "platform_reliability_risk",
            "scenario": "platform_reliability",
            "context_sources": ["platform", "operations"],
        },
        "platform.integration.degraded": {
            "signal_class": "platform_reliability_risk",
            "scenario": "platform_reliability",
            "context_sources": ["platform", "operations"],
        },
        "platform.module.activity.logged": {
            "signal_class": "platform_activity",
            "scenario": "platform_activity_observability",
            "context_sources": ["platform"],
        },
        "research.grant_deadline.approaching": {
            "signal_class": "research_risk",
            "scenario": "research_innovation",
            "context_sources": ["research", "platform"],
        },
        "research.publication_stagnant": {
            "signal_class": "research_risk",
            "scenario": "research_innovation",
            "context_sources": ["research", "platform"],
        },
        "research.grant_pipeline.at_risk": {
            "signal_class": "research_risk",
            "scenario": "research_innovation",
            "context_sources": ["research", "platform"],
        },
        "research.lab_utilization.low": {
            "signal_class": "research_risk",
            "scenario": "research_innovation",
            "context_sources": ["research", "platform"],
        },
        "operations.facility_issue.reported": {
            "signal_class": "operational_risk",
            "scenario": "campus_operations",
            "context_sources": ["operations", "platform"],
        },
        "campus.security_incident.detected": {
            "signal_class": "operational_risk",
            "scenario": "campus_operations",
            "context_sources": ["operations", "platform"],
        },
        "campus.transport.disruption_detected": {
            "signal_class": "operational_risk",
            "scenario": "campus_operations",
            "context_sources": ["operations", "platform"],
        },
        "campus.dining.capacity_exceeded": {
            "signal_class": "operational_risk",
            "scenario": "campus_operations",
            "context_sources": ["operations", "platform"],
        },
        "operations.cleaning_service.missed": {
            "signal_class": "operational_risk",
            "scenario": "campus_operations",
            "context_sources": ["operations", "platform"],
        },
        "operations.maintenance.predicted_due": {
            "signal_class": "operational_risk",
            "scenario": "campus_operations",
            "context_sources": ["operations", "platform"],
        },
        "operations.utilities.spike_detected": {
            "signal_class": "operational_risk",
            "scenario": "campus_operations",
            "context_sources": ["operations", "platform"],
        },
        "student_life.wellbeing.at_risk": {
            "signal_class": "student_success_risk",
            "scenario": "advanced_student_life",
            "context_sources": ["student_success", "academic"],
        },
        "student_life.disciplinary.incident_reported": {
            "signal_class": "student_success_risk",
            "scenario": "advanced_student_life",
            "context_sources": ["student_success", "academic"],
        },
        "enrollments.dropout_risk.detected": {
            "signal_class": "academic_risk",
            "scenario": "enrollment_dropout_risk",
            "context_sources": ["academic", "student_success"],
        },
        "academic_integrity.case.escalated": {
            "signal_class": "academic_risk",
            "scenario": "academic_integrity_escalation",
            "context_sources": ["academic", "student_success"],
        },
        # A-016.1 Academic Integrity Violation Detection Brain signals
        "academic_integrity.violation.detected": {
            "signal_class": "academic_risk",
            "scenario": "academic_integrity_violation",
            "context_sources": ["academic", "student_success"],
        },
        "academic_integrity.risk_detected": {
            "signal_class": "academic_risk",
            "scenario": "academic_integrity_violation",
            "context_sources": ["academic", "student_success"],
        },
        "plagiarism.similarity.high_detected": {
            "signal_class": "academic_risk",
            "scenario": "academic_integrity_violation",
            "context_sources": ["academic", "student_success"],
        },
        "exam.proctoring.violation_detected": {
            "signal_class": "academic_risk",
            "scenario": "academic_integrity_violation",
            "context_sources": ["academic", "student_success"],
        },
        "coursework.submission.suspicious_detected": {
            "signal_class": "academic_risk",
            "scenario": "academic_integrity_violation",
            "context_sources": ["academic", "student_success"],
        },
        "ai_plagiarism.risk_detected": {
            "signal_class": "academic_risk",
            "scenario": "academic_integrity_violation",
            "context_sources": ["academic", "student_success"],
        },
        # A-016.2 Thesis Governance + Supervisor Assignment signals
        "thesis.submission.created": {
            "signal_class": "academic_risk",
            "scenario": "thesis_governance",
            "context_sources": ["academic", "faculty", "student_success"],
        },
        "thesis.submission.pending_review": {
            "signal_class": "academic_risk",
            "scenario": "thesis_governance",
            "context_sources": ["academic", "faculty", "student_success"],
        },
        "thesis.supervisor.assignment_needed": {
            "signal_class": "academic_risk",
            "scenario": "thesis_governance",
            "context_sources": ["academic", "faculty", "student_success"],
        },
        "thesis.supervisor.overloaded": {
            "signal_class": "academic_risk",
            "scenario": "thesis_governance",
            "context_sources": ["academic", "faculty", "student_success"],
        },
        "thesis.review.delayed": {
            "signal_class": "academic_risk",
            "scenario": "thesis_governance",
            "context_sources": ["academic", "faculty", "student_success"],
        },
        "thesis.governance.risk_detected": {
            "signal_class": "academic_risk",
            "scenario": "thesis_governance",
            "context_sources": ["academic", "faculty", "student_success"],
        },
        # A-016.3 Exam Proctoring Violation Workflow signals
        "faculty.proctoring.violation_detected": {
            "signal_class": "academic_risk",
            "scenario": "exam_proctoring_violation",
            "context_sources": ["academic", "exam", "student_success"],
        },
        "exam.proctoring.suspicious_activity_detected": {
            "signal_class": "academic_risk",
            "scenario": "exam_proctoring_violation",
            "context_sources": ["academic", "exam", "student_success"],
        },
        "exam.proctoring.multiple_faces_detected": {
            "signal_class": "academic_risk",
            "scenario": "exam_proctoring_violation",
            "context_sources": ["academic", "exam", "student_success"],
        },
        "exam.proctoring.face_mismatch_detected": {
            "signal_class": "academic_risk",
            "scenario": "exam_proctoring_violation",
            "context_sources": ["academic", "exam", "student_success"],
        },
        "exam.proctoring.forbidden_app_detected": {
            "signal_class": "academic_risk",
            "scenario": "exam_proctoring_violation",
            "context_sources": ["academic", "exam", "student_success"],
        },
        "exam.proctoring.camera_absent_detected": {
            "signal_class": "academic_risk",
            "scenario": "exam_proctoring_violation",
            "context_sources": ["academic", "exam", "student_success"],
        },
        "academic_records.inconsistency.detected": {
            "signal_class": "compliance_risk",
            "scenario": "academic_records_audit",
            "context_sources": ["academic", "platform"],
        },
        "programs.status.risk_detected": {
            "signal_class": "academic_risk",
            "scenario": "programs_status_risk",
            "context_sources": ["academic", "platform"],
        },
        "courses.status.risk_detected": {
            "signal_class": "academic_risk",
            "scenario": "courses_status_risk",
            "context_sources": ["academic", "platform"],
        },
        "degree_progress.graduation_risk.detected": {
            "signal_class": "academic_risk",
            "scenario": "graduation_degree_progress_risk",
            "context_sources": ["academic", "student_success"],
        },
        "transcripts.inconsistency.detected": {
            "signal_class": "compliance_risk",
            "scenario": "transcripts_audit",
            "context_sources": ["academic", "platform"],
        },
        "student_services.ticket.escalated": {
            "signal_class": "student_success_risk",
            "scenario": "student_services_escalation",
            "context_sources": ["student_success", "academic"],
        },
        "admissions.decision.made": {
            "signal_class": "academic_risk",
            "scenario": "student_risk",
            "context_sources": ["academic", "student_success"],
        },
        "scheduling.section.scheduled": {
            "signal_class": "faculty_risk",
            "scenario": "faculty_overload",
            "context_sources": ["faculty", "academic"],
        },
        # A-013.3: Scheduling conflict + enrollment capacity risk
        "scheduling.section.conflict_detected": {
            "signal_class": "operational_risk",
            "scenario": "section_conflict",
            "context_sources": ["scheduling", "academic", "faculty"],
        },
        "enrollment.capacity_risk.detected": {
            "signal_class": "academic_risk",
            "scenario": "enrollment_capacity_risk",
            "context_sources": ["scheduling", "academic"],
        },
        # A-015.4 — Finance Operations Health Brain
        "finance.operations.health_check": {
            "signal_class": "financial_risk",
            "scenario": "finance_operations_health",
            "context_sources": ["finance", "operations", "procurement"],
        },
        "finance.operations.risk_detected": {
            "signal_class": "financial_risk",
            "scenario": "finance_operations_health",
            "context_sources": ["finance", "operations", "procurement"],
        },
        # A-015.5 — Inventory Low Stock / Supply Risk Brain
        "inventory.low_stock.detected": {
            "signal_class": "supply_risk",
            "scenario": "inventory_low_stock",
            "context_sources": ["operations", "procurement", "finance"],
        },
        "inventory.reorder_needed": {
            "signal_class": "supply_risk",
            "scenario": "inventory_low_stock",
            "context_sources": ["operations", "procurement", "finance"],
        },
        "supply.risk.detected": {
            "signal_class": "supply_risk",
            "scenario": "inventory_low_stock",
            "context_sources": ["operations", "procurement", "finance"],
        },
        "procurement.inventory_gap.detected": {
            "signal_class": "supply_risk",
            "scenario": "inventory_low_stock",
            "context_sources": ["operations", "procurement", "finance"],
        },
    }

    @classmethod
    def is_supported(cls, event_type: str) -> bool:
        return event_type in cls.signals


class DecisionRegistry:
    decisions = {
        "student_risk": {
            "decision_type": "risk",
            "allowed_event_types": sorted(STUDENT_RISK_EVENT_TYPES),
            "action_map": {
                "create_intervention_case": "workflow_task",
                "create_attendance_recovery_plan": "workflow_task",
                "notify_advisor": "notification",
                "notify_faculty": "notification",
            },
        },
        "thesis_delay": {
            "decision_type": "preventive",
            "allowed_event_types": sorted(THESIS_DELAY_EVENT_TYPES),
            "action_map": {
                "create_intervention_case": "workflow_task",
                "create_supervision_task": "workflow_task",
                "notify_advisor": "notification",
                "notify_faculty": "notification",
            },
        },
        "faculty_overload": {
            "decision_type": "optimization",
            "allowed_event_types": sorted(FACULTY_OVERLOAD_EVENT_TYPES),
            "action_map": {
                "create_workload_review_task": "workflow_task",
                "notify_faculty": "notification",
            },
        },
        "payment_recovery": {
            "decision_type": "risk",
            "allowed_event_types": sorted(PAYMENT_OVERDUE_EVENT_TYPES),
            "action_map": {
                "create_collections_case": "workflow_task",
                "notify_finance": "notification",
            },
        },
        "budget_overrun_prevention": {
            "decision_type": "risk",
            "allowed_event_types": sorted(BUDGET_OVERRUN_EVENT_TYPES),
            "action_map": {
                "create_intervention_case": "workflow_task",
                "notify_finance": "notification",
            },
        },
        "student_support_bridge": {
            "decision_type": "risk",
            "allowed_event_types": sorted(STUDENT_SUPPORT_EVENT_TYPES),
            "action_map": {
                "create_student_support_case": "workflow_task",
                "notify_student_success_team": "notification",
                "notify_advisor": "notification",
            },
        },
        "procurement_supply_chain": {
            "decision_type": "procurement",
            "allowed_event_types": sorted(PROCUREMENT_EVENT_TYPES),
            "action_map": {
                "initiate_procurement_request": "workflow_task",
                "notify_procurement_team": "notification",
            },
        },
        # A-015.2 — Procurement Approval Automation
        "procurement_approval_automation": {
            "decision_type": "procurement",
            "allowed_event_types": sorted(PROCUREMENT_APPROVAL_EVENT_TYPES),
            "action_map": {
                "create_procurement_approval_case": "workflow_task",
                "notify_procurement_team": "notification",
            },
        },
        "supply_management": {
            "decision_type": "operational",
            "allowed_event_types": sorted(SUPPLY_LOW_EVENT_TYPES),
            "action_map": {
                "create_replenishment_task": "workflow_task",
                "initiate_procurement_request": "workflow_task",
                "notify_operations": "notification",
            },
        },
        "accreditation_remediation": {
            "decision_type": "compliance",
            "allowed_event_types": sorted(ACCREDITATION_EVENT_TYPES),
            "action_map": {
                "create_accreditation_remediation_workflow": "workflow_task",
                "notify_compliance": "notification",
            },
        },
        "platform_reliability": {
            "decision_type": "operational",
            "allowed_event_types": sorted(PLATFORM_RELIABILITY_EVENT_TYPES),
            "action_map": {
                "create_platform_reliability_incident": "workflow_task",
                "notify_platform": "notification",
            },
        },
        "platform_activity_observability": {
            "decision_type": "operational",
            "allowed_event_types": sorted(PLATFORM_ACTIVITY_EVENT_TYPES),
            "action_map": {},
        },
        "research_innovation": {
            "decision_type": "preventive",
            "allowed_event_types": sorted(RESEARCH_EVENT_TYPES),
            "action_map": {
                "create_research_remediation_workflow": "workflow_task",
                "notify_research_office": "notification",
            },
        },
        "campus_operations": {
            "decision_type": "operational",
            "allowed_event_types": sorted(OPERATIONS_EVENT_TYPES),
            "action_map": {
                "create_facility_incident_workflow": "workflow_task",
                "create_cleaning_recovery_task": "workflow_task",
                "notify_facilities_team": "notification",
            },
        },
        "advanced_student_life": {
            "decision_type": "risk",
            "allowed_event_types": sorted(STUDENT_LIFE_EVENT_TYPES),
            "action_map": {
                "create_student_support_case": "workflow_task",
                "create_disciplinary_review_case": "workflow_task",
                "notify_student_success_team": "notification",
            },
        },
        "enrollment_dropout_risk": {
            "decision_type": "risk",
            "allowed_event_types": sorted(ENROLLMENT_DROPOUT_EVENT_TYPES),
            "action_map": {
                "create_dropout_intervention": "workflow_task",
                "notify_enrollment_advisor": "notification",
            },
        },
        "academic_integrity_escalation": {
            "decision_type": "compliance",
            "allowed_event_types": sorted(ACADEMIC_INTEGRITY_EVENT_TYPES),
            "action_map": {
                "create_integrity_review_case": "workflow_task",
                "notify_registrar": "notification",
            },
        },
        # A-016.1 Academic Integrity Violation Detection Brain
        "academic_integrity_violation": {
            "decision_type": "academic_integrity_review",
            "allowed_event_types": sorted(ACADEMIC_INTEGRITY_VIOLATION_EVENT_TYPES),
            "action_map": {
                "integrity_review": "workflow_task",
                "notify_academic_office": "notification",
                "request_manual_review": "workflow_task",
                "escalate_to_committee": "workflow_task",
            },
        },
        # A-016.2 Thesis Governance + Supervisor Assignment
        "thesis_governance": {
            "decision_type": "thesis_supervisor_assignment",
            "allowed_event_types": sorted(THESIS_GOVERNANCE_EVENT_TYPES),
            "action_map": {
                "assign_supervisor": "workflow_task",
                "request_supervisor_review": "workflow_task",
                "notify_department": "notification",
                "notify_academic_office": "notification",
                "escalate_to_academic_office": "workflow_task",
            },
        },
        # A-016.3 Exam Proctoring Violation Workflow
        "exam_proctoring_violation": {
            "decision_type": "exam_integrity_review",
            "allowed_event_types": sorted(EXAM_PROCTORING_EVENT_TYPES),
            "action_map": {
                "create_integrity_review": "workflow_task",
                "request_manual_proctor_review": "workflow_task",
                "notify_exam_office": "notification",
                "escalate_to_academic_integrity_committee": "workflow_task",
                "collect_additional_evidence": "workflow_task",
            },
        },
        "academic_records_audit": {
            "decision_type": "compliance",
            "allowed_event_types": sorted(ACADEMIC_RECORDS_EVENT_TYPES),
            "action_map": {
                "create_records_review_task": "workflow_task",
                "notify_registrar": "notification",
            },
        },
        "programs_status_risk": {
            "decision_type": "risk",
            "allowed_event_types": sorted(PROGRAMS_EVENT_TYPES),
            "action_map": {
                "create_program_review_task": "workflow_task",
                "notify_academic_dean": "notification",
            },
        },
        "courses_status_risk": {
            "decision_type": "risk",
            "allowed_event_types": sorted(COURSES_EVENT_TYPES),
            "action_map": {
                "create_course_review_task": "workflow_task",
                "notify_academic_dean": "notification",
            },
        },
        "graduation_degree_progress_risk": {
            "decision_type": "risk",
            "allowed_event_types": sorted(DEGREE_PROGRESS_EVENT_TYPES),
            "action_map": {
                "create_intervention_case": "workflow_task",
                "notify_advisor": "notification",
            },
        },
        "transcripts_audit": {
            "decision_type": "compliance",
            "allowed_event_types": sorted(TRANSCRIPTS_EVENT_TYPES),
            "action_map": {
                "create_transcript_review_task": "workflow_task",
                "notify_registrar": "notification",
            },
        },
        "student_services_escalation": {
            "decision_type": "risk",
            "allowed_event_types": sorted(STUDENT_SERVICES_EVENT_TYPES),
            "action_map": {
                "create_student_support_case": "workflow_task",
                "notify_student_success_team": "notification",
            },
        },
        # A-013.3: Scheduling conflict + enrollment capacity risk decisions
        "section_conflict": {
            "decision_type": "operational",
            "allowed_event_types": sorted(SECTION_CONFLICT_EVENT_TYPES),
            "action_map": {
                "create_section_conflict_task": "workflow_task",
                "notify_scheduling_office": "notification",
            },
        },
        "enrollment_capacity_risk": {
            "decision_type": "risk",
            "allowed_event_types": sorted(ENROLLMENT_CAPACITY_RISK_EVENT_TYPES),
            "action_map": {
                "create_enrollment_capacity_task": "workflow_task",
                "notify_enrollment_office": "notification",
            },
        },
        # A-015.4 — Finance Operations Health Brain
        "finance_operations_health": {
            "decision_type": "finance_health",
            "allowed_event_types": sorted(FINANCE_OPERATIONS_HEALTH_EVENT_TYPES),
            "action_map": {
                "create_finance_health_review_task": "workflow_task",
                "notify_finance": "notification",
                "notify_procurement_team": "notification",
            },
        },
        # A-015.5 — Inventory Low Stock / Supply Risk Brain
        "inventory_low_stock": {
            "decision_type": "supply_risk",
            "allowed_event_types": sorted(INVENTORY_LOW_STOCK_EVENT_TYPES),
            "action_map": {
                "create_procurement_request": "workflow_task",
                "reorder_review": "workflow_task",
                "vendor_followup": "notification",
                "budget_review": "notification",
            },
        },
    }
