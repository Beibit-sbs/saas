from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from app.platform.event_ingestion import service as event_ingestion_service
from app.platform.event_ingestion.types import (
    ANALYTICS_EVENT_READ,
    ANALYTICS_KPI_READ,
    BILLING_USAGE_RECORDED,
    KPI_REFRESH_EXECUTED,
)
from app.platform.kpi.repository import KpiRepository

_SHARED_KPI_REPOSITORY = KpiRepository()
_kpi_repository = _SHARED_KPI_REPOSITORY


METRIC_TITLES: dict[str, str] = {
    "total_students": "Total Students",
    "total_enrollments": "Total Enrollments",
    "total_grades_submitted": "Total Grades Submitted",
    "total_active_subscriptions": "Active Subscriptions",
    "total_failed_jobs": "Failed Jobs",
    "total_failed_notifications": "Failed Notifications",
    "analytics_events_ingested_total": "Analytics Events Ingested Total",
    "analytics_events_reads_total": "Analytics Events Reads Total",
    "analytics_kpi_reads_total": "Analytics KPI Reads Total",
    "analytics_reads_total": "Analytics Total Reads",
    "analytics_kpi_reads_share_pct": "Analytics KPI Reads Share (%)",
    "analytics_events_reads_from_events_total": "Analytics Events Reads (Event-Derived) Total",
    "analytics_kpi_reads_from_events_total": "Analytics KPI Reads (Event-Derived) Total",
    "billing_usage_recorded_from_events_total": "Billing Usage Recorded (Event-Derived) Total",
    "high_risk_students_count": "High Risk Students Count",
    "intervention_resolution_rate": "Intervention Resolution Rate (%)",
    "intervention_auto_created_count": "Intervention Auto-Create Count",
    "composite_risk_average": "Composite Risk Average",
    "critical_risk_students_count": "Critical Risk Students Count",
    "sweep_coverage_rate": "Early-Warning Sweep Coverage Rate (%)",
    "delinquency_recovery_rate": "Delinquency Recovery Rate (%)",
    "overdue_amount_at_risk": "Overdue Amount At Risk (Cents)",
    "delinquency_cases_active": "Delinquency Cases Active",
    "course_fill_rate": "Course Fill Rate (%)",
    "capacity_risk_sections_count": "Enrollment Capacity Risk Count",
    "scheduling_conflicts_count": "Scheduling Conflict Count",
    "room_conflict_count": "Room Conflict Count",
    "room_allocation_recommendations_count": "Room Allocation Recommendations Count",
    "room_allocation_review_required_count": "Room Allocation Review Required Count",
    "room_allocation_no_viable_candidate_count": "Room Allocation No Viable Candidate Count",
    "room_allocation_candidate_evaluated_count": "Room Allocation Candidate Evaluated Count",
    "room_capacity_mismatch_count": "Room Capacity Mismatch Count",
    "room_equipment_mismatch_count": "Room Equipment Mismatch Count",
    "room_computer_shortage_count": "Room Computer Shortage Count",
    "room_type_mismatch_count": "Room Type Mismatch Count",
    # A-020.5 compatibility keys kept for backward compatibility
    "room_allocation_recommendations_generated_count": "Room Allocation Recommendations Generated Count",
    # A-014.6 Wave 2 metrics
    "grade_decline_risk_count": "Grade Decline Risk Count",
    "grade_intervention_cases_count": "Grade Intervention Cases",
    "thesis_completion_risk_count": "Thesis Completion Risk Count",
    "thesis_intervention_cases_count": "Thesis Intervention Cases",
    "attendance_recovery_actions_count": "Attendance Recovery Actions",
    "graduation_risk_students_count": "Graduation Risk Students Count",
    "degree_progress_intervention_cases_count": "Degree Progress Intervention Cases",
    "scholarship_risk_cases_count": "Scholarship Risk Cases",
    "financial_aid_risk_cases_count": "Financial Aid Risk Cases",
    # A-015.6 Wave 3 metrics — Budget
    "budget_overrun_risk_count": "Budget Overrun Risk Count",
    "budget_overrun_amount_at_risk": "Budget Overrun Amount At Risk",
    "budget_review_actions_count": "Budget Review Actions Count",
    # A-015.6 Wave 3 metrics — Procurement
    "procurement_requests_pending_approval": "Procurement Requests Pending Approval",
    "procurement_approval_automation_count": "Procurement Approval Automation Count",
    "procurement_po_issued_count": "Procurement PO Issued Count",
    # A-015.6 Wave 3 metrics — PO / Delivery / Asset
    "po_delivery_completion_rate": "PO Delivery Completion Rate (%)",
    "delivered_po_asset_conversion_rate": "Delivered PO Asset Conversion Rate (%)",
    "asset_conversion_gap_count": "Asset Conversion Gap Count",
    # A-015.6 Wave 3 metrics — Finance Operations Health
    "finance_operations_health_score": "Finance Operations Health Score",
    "budget_health_score": "Budget Health Score",
    "procurement_health_score": "Procurement Health Score",
    "po_delivery_health_score": "PO Delivery Health Score",
    "asset_conversion_health_score": "Asset Conversion Health Score",
    "active_finance_risk_signals_count": "Active Finance Risk Signals Count",
    "finance_operations_actionability_count": "Finance Operations Actionability Count",
    # A-015.6 Wave 3 metrics — Inventory / Supply
    "inventory_low_stock_items_count": "Inventory Low Stock Items Count",
    "critical_supply_risk_count": "Critical Supply Risk Count",
    "reorder_recommendations_count": "Reorder Recommendations Count",
    "supply_risk_actions_count": "Supply Risk Actions Count",
    # A-016.6 Wave 4 metrics — Academic Integrity
    "academic_integrity_risk_count": "Academic Integrity Risk Count",
    "academic_integrity_review_cases_count": "Academic Integrity Review Cases",
    "academic_integrity_high_risk_count": "Academic Integrity High Risk Count",
    "academic_integrity_cases_pending_review": "Academic Integrity Cases Pending Review",
    # A-016.6 Wave 4 metrics — Exam Proctoring
    "exam_proctoring_violations_count": "Exam Proctoring Violations Count",
    "exam_integrity_reviews_count": "Exam Integrity Reviews Count",
    "exam_integrity_high_risk_count": "Exam Integrity High Risk Count",
    "exam_integrity_requires_approval_count": "Exam Integrity Requires Approval Count",
    # A-016.6 Wave 4 metrics — Thesis Governance
    "thesis_governance_risk_count": "Thesis Governance Risk Count",
    "thesis_supervisor_assignment_needed_count": "Thesis Supervisor Assignment Needed",
    "thesis_review_delayed_count": "Thesis Review Delayed Count",
    "thesis_governance_requires_approval_count": "Thesis Governance Requires Approval",
    # A-016.6 Wave 4 metrics — Research Ethics / Compliance
    "research_ethics_review_cases_count": "Research Ethics Review Cases",
    "research_ethics_high_risk_count": "Research Ethics High Risk Count",
    "research_ethics_missing_documents_count": "Research Ethics Missing Documents",
    "research_ethics_requires_approval_count": "Research Ethics Requires Approval",
    # A-016.6 Wave 4 metrics — Case Resolution
    "integrity_cases_open_count": "Integrity Cases Open",
    "integrity_cases_escalated_count": "Integrity Cases Escalated",
    "integrity_cases_resolved_count": "Integrity Cases Resolved",
    "integrity_cases_evidence_requested_count": "Integrity Cases Evidence Requested",
    "integrity_case_resolution_sla_risk_count": "Integrity Case Resolution SLA Risk",
    # A-018.3 Wave 6 metrics — Access Control
    "access_denied_count": "Access Denied Count",
    "unauthorized_attempts_count": "Unauthorized Attempts Count",
    "active_access_cards_count": "Active Access Cards Count",
    "suspended_access_cards_count": "Suspended Access Cards Count",
    "security_access_anomaly_count": "Security Access Anomaly Count",
    # A-018.4 Wave 6 metrics — Events Management
    "events_published_count": "Events Published Count",
    "events_started_count": "Events Started Count",
    "events_completed_count": "Events Completed Count",
    "events_cancelled_count": "Events Cancelled Count",
    "events_registration_full_count": "Events Registration Full Count",
    # A-018.6 Wave 6 metrics — Visitor Management
    "visitor_requests_pending_count": "Visitor Requests Pending Count",
    "visitors_checked_in_count": "Visitors Checked In Count",
    "visitor_unauthorized_attempts_count": "Visitor Unauthorized Attempts Count",
    # A-019.2 Wave 7 maturity — Visitor Management completion
    "visitor_visits_completed_count": "Visitor Visits Completed Count",
    "visitor_visits_cancelled_count": "Visitor Visits Cancelled Count",
    # A-018.6 Wave 6 metrics — Security Operations
    "security_incidents_open_count": "Security Incidents Open Count",
    "security_incidents_escalated_count": "Security Incidents Escalated Count",
    # A-019.5 Wave 7 metrics — Security Operations completion
    "security_incidents_resolved_count": "Security Incidents Resolved Count",
    "security_incident_review_required_count": "Security Incidents Review Required Count",
    "security_high_risk_incidents_count": "Security High-Risk Incidents Count",
    # A-022.5 timetable workflow KPI/dashboard metrics
    "timetable_change_proposals_count": "Timetable Change Proposals Count",
    "timetable_change_pending_review_count": "Timetable Change Pending Review Count",
    "timetable_change_approved_count": "Timetable Change Approved Count",
    "timetable_change_rejected_count": "Timetable Change Declined Count",
    "timetable_change_revision_requested_count": "Timetable Change Revision Requested Count",
    "timetable_simulations_count": "Timetable Simulations Count",
    "timetable_simulations_review_required_count": "Timetable Simulations Review Required Count",
    "timetable_simulation_conflicts_created_count": "Timetable Simulation Conflicts Created Count",
    "timetable_simulation_conflicts_resolved_count": "Timetable Simulation Conflicts Resolved Count",
    "timetable_approval_queue_count": "Timetable Approval Queue Count",
    "timetable_approval_pending_count": "Timetable Approval Pending Count",
    "timetable_approval_approved_count": "Timetable Approval Approved Count",
    "timetable_approval_rejected_count": "Timetable Approval Declined Count",
    "timetable_approval_revision_requested_count": "Timetable Approval Revision Requested Count",
    "timetable_approval_high_risk_count": "Timetable Approval High-Risk Count",
}


EVENT_METRIC_MAP: dict[str, str] = {
    "student.created": "total_students",
    "enrollment.created": "total_enrollments",
    "grade.submitted": "total_grades_submitted",
}


EVENT_DERIVED_METRIC_LINEAGE: dict[str, list[str]] = {
    "analytics_events_reads_from_events_total": [ANALYTICS_EVENT_READ],
    "analytics_kpi_reads_from_events_total": [ANALYTICS_KPI_READ],
    "billing_usage_recorded_from_events_total": [BILLING_USAGE_RECORDED],
    "intervention_auto_created_count": ["interventions.auto_triggered"],
    "intervention_resolution_rate": ["interventions.case.created", "interventions.case_outcome.recorded"],
    "high_risk_students_count": [
        "academic.attendance_risk.detected",
        "academic.grade_risk.detected",
        "finance.payment_overdue.detected",
        "student.needs_intervention",
    ],
    "composite_risk_average": [
        "academic.attendance_risk.detected",
        "academic.grade_risk.detected",
        "finance.payment_overdue.detected",
        "enrollment.capacity_risk.detected",
    ],
    "critical_risk_students_count": [
        "collections.delinquency.critical_overdue",
        "student.needs_intervention",
    ],
    "sweep_coverage_rate": [
        "academic.attendance_risk.detected",
        "academic.grade_risk.detected",
        "finance.payment_overdue.detected",
        "student.needs_intervention",
    ],
    "course_fill_rate": ["scheduling.section.created", "enrollment.created"],
    "capacity_risk_sections_count": [
        "enrollment.capacity_risk.detected",
        "scheduling.capacity_mismatch.detected",
        "resource.overload",
    ],
    "scheduling_conflicts_count": [
        "scheduling.section.conflict_detected",
        "scheduling.room_conflict.detected",
        "scheduling.room_allocation.required",
        "booking.conflict_detected",
    ],
    "room_conflict_count": [
        "scheduling.room_conflict.detected",
        "scheduling.room_allocation.required",
    ],
    "room_allocation_recommendations_count": [
        "scheduling.room_allocation.recommendation_generated",
    ],
    "room_allocation_review_required_count": [
        "scheduling.room_allocation.review_required",
    ],
    "room_allocation_no_viable_candidate_count": [
        "scheduling.room_allocation.no_viable_candidate",
    ],
    "room_allocation_candidate_evaluated_count": [
        "scheduling.room_allocation.candidate_ranked",
    ],
    "room_capacity_mismatch_count": [
        "scheduling.capacity_mismatch.detected",
    ],
    "room_equipment_mismatch_count": [
        "scheduling.equipment_mismatch.detected",
    ],
    "room_computer_shortage_count": [
        "scheduling.computer_shortage.detected",
    ],
    "room_type_mismatch_count": [
        "scheduling.room_type_mismatch.detected",
    ],
    # A-020.5 compatibility keys kept for backward compatibility
    "room_allocation_recommendations_generated_count": [
        "scheduling.room_allocation.recommendation_generated",
    ],
    # A-014.6 Wave 2 event lineage
    "grade_decline_risk_count": ["academic.grade_risk.detected"],
    "grade_intervention_cases_count": ["interventions.case.created"],
    "thesis_completion_risk_count": ["thesis.status_changed"],
    "thesis_intervention_cases_count": ["interventions.case.created"],
    "attendance_recovery_actions_count": ["academic.attendance_risk.detected"],
    "graduation_risk_students_count": ["degree_progress.graduation_risk.detected"],
    "degree_progress_intervention_cases_count": ["interventions.case.created"],
    "scholarship_risk_cases_count": ["scholarship.award.at_risk_detected"],
    "financial_aid_risk_cases_count": ["financial_aid.warning.detected"],
    # A-015.6 Wave 3 event lineage — Budget
    # A-017.1 budget_planning maturity: finance.budget_variance.threshold_reached added
    "budget_overrun_risk_count": [
        "finance.expense.budget_exceeded",
        "campus.budget.overrun_risk_detected",
        "campus.expense_controls.budget_exceeded_risk_detected",
        "finance.budget_variance.threshold_reached",
    ],
    "budget_overrun_amount_at_risk": ["finance.expense.budget_exceeded"],
    "budget_review_actions_count": [
        "campus.budget.overrun_risk_detected",
        "campus.expense_controls.budget_exceeded_risk_detected",
        "finance.budget_variance.threshold_reached",
    ],
    # A-015.6 Wave 3 event lineage — Procurement
    "procurement_requests_pending_approval": [
        "procurement.request_submitted",
        "procurement.approval_required",
    ],
    "procurement_approval_automation_count": ["procurement.request_submitted"],
    "procurement_po_issued_count": ["procurement.po_issued"],
    # A-015.6 Wave 3 event lineage — PO / Delivery / Asset
    "po_delivery_completion_rate": ["procurement.po_issued", "procurement.asset_created"],
    "delivered_po_asset_conversion_rate": ["procurement.asset_created"],
    "asset_conversion_gap_count": ["procurement.po_issued", "procurement.asset_created"],
    # A-015.6 Wave 3 event lineage — Finance Operations Health
    "finance_operations_health_score": ["finance.operations.health_check"],
    "budget_health_score": ["finance.operations.health_check"],
    "procurement_health_score": ["finance.operations.risk_detected"],
    "po_delivery_health_score": ["finance.operations.risk_detected"],
    "asset_conversion_health_score": ["finance.operations.health_check"],
    "active_finance_risk_signals_count": ["finance.operations.risk_detected"],
    "finance_operations_actionability_count": [
        "finance.operations.risk_detected",
        "finance.operations.health_check",
    ],
    # A-015.6 Wave 3 event lineage — Inventory / Supply
    "inventory_low_stock_items_count": ["inventory.low_stock.detected"],
    "critical_supply_risk_count": ["inventory.low_stock.detected", "supply.risk.detected"],
    "reorder_recommendations_count": ["inventory.reorder_needed"],
    "supply_risk_actions_count": ["supply.risk.detected", "procurement.inventory_gap.detected"],
    # A-016.6 Wave 4 event lineage — Academic Integrity
    "academic_integrity_risk_count": [
        "academic_integrity.violation.detected",
        "academic_integrity.risk_detected",
    ],
    "academic_integrity_review_cases_count": [
        "academic_integrity.case.opened",
        "academic_integrity.case.review_required",
    ],
    "academic_integrity_high_risk_count": [
        "academic_integrity.violation.detected",
        "academic_integrity.case.review_required",
    ],
    "academic_integrity_cases_pending_review": ["academic_integrity.case.review_required"],
    # A-016.6 Wave 4 event lineage — Exam Proctoring
    "exam_proctoring_violations_count": [
        "exam.violation_detected",
        "exam.proctoring.violation_detected",
        "faculty.proctoring.violation_detected",
    ],
    "exam_integrity_reviews_count": [
        "exam.proctoring.suspicious_activity_detected",
        "exam.proctoring.multiple_faces_detected",
        "exam.proctoring.face_mismatch_detected",
        "exam.proctoring.forbidden_app_detected",
        "exam.proctoring.camera_absent_detected",
    ],
    "exam_integrity_high_risk_count": [
        "exam.proctoring.multiple_faces_detected",
        "exam.proctoring.face_mismatch_detected",
    ],
    "exam_integrity_requires_approval_count": [
        "exam.violation_detected",
        "exam.proctoring.violation_detected",
    ],
    # A-016.6 Wave 4 event lineage — Thesis Governance
    "thesis_governance_risk_count": ["thesis.governance.risk_detected"],
    "thesis_supervisor_assignment_needed_count": ["thesis.supervisor.assignment_needed"],
    "thesis_review_delayed_count": ["thesis.review.delayed"],
    "thesis_governance_requires_approval_count": [
        "thesis.supervisor.overloaded",
        "thesis.governance.risk_detected",
    ],
    # A-016.6 Wave 4 event lineage — Research Ethics / Compliance
    "research_ethics_review_cases_count": [
        "research_ethics.application.submitted",
        "research_ethics.review.overdue",
    ],
    "research_ethics_high_risk_count": [
        "research_ethics.high_risk.detected",
        "research_ethics.missing_consent.detected",
    ],
    "research_ethics_missing_documents_count": ["research_ethics.document_missing.detected"],
    "research_ethics_requires_approval_count": [
        "research_ethics.high_risk.detected",
        "research_ethics.missing_consent.detected",
    ],
    # A-016.6 Wave 4 event lineage — Case Resolution
    "integrity_cases_open_count": ["academic_integrity.case.opened"],
    "integrity_cases_escalated_count": ["academic_integrity.case.review_required"],
    "integrity_cases_resolved_count": ["academic_integrity.case.resolved"],
    "integrity_cases_evidence_requested_count": ["academic_integrity.case.evidence_requested"],
    "integrity_case_resolution_sla_risk_count": ["academic_integrity.case.review_required"],
    # A-018.3 Wave 6 event lineage — Access Control
    "access_denied_count": ["access.denied"],
    "unauthorized_attempts_count": ["access.denied", "security.anomaly"],
    "active_access_cards_count": ["card.issued", "card.reactivated"],
    "suspended_access_cards_count": ["card.suspended"],
    "security_access_anomaly_count": ["security.anomaly"],
    # A-018.4 Wave 6 event lineage — Events Management
    "events_published_count": ["event.published"],
    "events_started_count": ["event.started"],
    "events_completed_count": ["event.completed"],
    "events_cancelled_count": ["event.cancelled"],
    "events_registration_full_count": ["event.registration_full"],
    # A-018.6 Wave 6 event lineage — Visitor Management
    "visitor_requests_pending_count": ["visitor.registered"],
    "visitors_checked_in_count": ["visitor.checked_in"],
    "visitor_unauthorized_attempts_count": ["visitor.unauthorized_attempt"],
    # A-019.2 Wave 7 maturity — Visitor Management completion
    "visitor_visits_completed_count": ["visitor.checked_out"],
    "visitor_visits_cancelled_count": ["visitor.cancelled"],
    # A-018.6 Wave 6 event lineage — Security Operations
    "security_incidents_open_count": ["security.incident.opened"],
    "security_incidents_escalated_count": ["security.incident.escalated"],
    # A-019.5 Wave 7 event lineage — Security Operations completion
    "security_incidents_resolved_count": ["security.incident.resolved"],
    "security_incident_review_required_count": ["security.incident.opened"],
    "security_high_risk_incidents_count": ["security.incident.escalated"],
    # A-022.5 timetable workflow event lineage
    "timetable_change_proposals_count": [
        "scheduling.timetable_proposal.created",
    ],
    "timetable_change_pending_review_count": [
        "scheduling.timetable_proposal.submitted",
    ],
    "timetable_change_approved_count": [
        "scheduling.timetable_proposal.approved",
    ],
    "timetable_change_rejected_count": [
        "scheduling.timetable_proposal.rejected",
    ],
    "timetable_change_revision_requested_count": [
        "scheduling.timetable_proposal.revision_requested",
    ],
    "timetable_simulations_count": [
        "scheduling.timetable_simulation.computed",
    ],
    "timetable_simulations_review_required_count": [
        "scheduling.timetable_simulation.review_required",
    ],
    "timetable_simulation_conflicts_created_count": [
        "scheduling.timetable_simulation.conflicts_created",
    ],
    "timetable_simulation_conflicts_resolved_count": [
        "scheduling.timetable_simulation.conflicts_resolved",
    ],
    "timetable_approval_queue_count": [
        "scheduling.timetable_approval.queued",
    ],
    "timetable_approval_pending_count": [
        "scheduling.timetable_approval.queued",
        "scheduling.timetable_approval.in_review",
    ],
    "timetable_approval_approved_count": [
        "scheduling.timetable_approval.approved",
    ],
    "timetable_approval_rejected_count": [
        "scheduling.timetable_approval.rejected",
    ],
    "timetable_approval_revision_requested_count": [
        "scheduling.timetable_approval.revision_requested",
    ],
    "timetable_approval_high_risk_count": [
        "scheduling.timetable_approval.high_risk",
    ],
}


USAGE_DERIVED_METRICS: set[str] = {
    "analytics_events_reads_total",
    "analytics_kpi_reads_total",
    "analytics_reads_total",
    "analytics_kpi_reads_share_pct",
}

KPI_SURFACE_ID = "tenant_analytics_kpis"
KPI_CONTRACT_VERSION = "v1"
KPI_SURFACE_CAPABILITIES: dict[str, bool] = {
    "supports_cards": True,
    "supports_trends": True,
    "supports_insights": True,
    "supports_recommendations": True,
    "supports_refresh": True,
    "supports_refresh_history": True,
    "supports_change_digest": True,
    "supports_source_mix": True,
    "supports_lineage": True,
    "supports_source_breakdown": True,
    "supports_thresholds": True,
    "supports_actionability": True,
}

KPI_SURFACE_PROFILE: dict[str, Any] = {
    "audience_profiles": [
        "human_dashboard",
        "machine_client",
        "support_traceable",
    ],
    "primary_audience": "human_dashboard",
    "consumption_mode": "structured_read_model",
}

KPI_FIELD_SEMANTICS: dict[str, str] = {
    "capabilities": "supported surface features",
    "sections": "current response section presence and state",
    "contract_invariants": "guaranteed structural compatibility markers",
    "contract_fingerprint": "stable contract checksum identity",
    "surface_profile": "intended audience and use mode",
    "response_status": "current response readiness state",
    "request_id": "request correlation identifier",
    "served_at": "response generation timestamp",
}

KPI_CARD_FIELD_SEMANTICS: dict[str, str] = {
    "severity": "bounded operational severity",
    "threshold_basis": "threshold measurement basis",
    "policy_pack": "named evaluation profile",
    "actionability_state": "bounded urgency hint",
    "source_status": "primary source derivation mode",
}

KPI_RESPONSE_EXAMPLES: dict[str, dict[str, str]] = {
    "empty_shape": {
        "readiness_status": "empty",
        "cards": "empty",
        "summary": "present",
        "change_digest": "present",
        "source_mix_summary": "present",
        "capabilities": "present",
        "sections": "present",
    },
    "ready_shape": {
        "readiness_status": "ready",
        "cards": "populated",
        "summary": "populated",
        "change_digest": "populated",
        "source_mix_summary": "populated",
        "capabilities": "present",
        "sections": "present",
    },
}

KPI_SURFACE_MAP: dict[str, Any] = {
    "family_id": "tenant_analytics_endpoint_family_v1",
    "endpoints": [
        {"name": "kpis", "path": "/api/analytics/kpis", "role": "primary_read"},
        {"name": "kpi_trends", "path": "/api/analytics/kpis/trends", "role": "trend_read"},
        {"name": "kpi_insights", "path": "/api/analytics/kpis/insights", "role": "insight_read"},
        {
            "name": "kpi_recommendations",
            "path": "/api/analytics/kpis/recommendations",
            "role": "recommendation_read",
        },
        {"name": "kpi_refresh", "path": "/api/analytics/kpis/refresh", "role": "refresh_action"},
        {
            "name": "kpi_refresh_history",
            "path": "/api/analytics/kpis/refresh-history",
            "role": "refresh_history_read",
        },
        {"name": "events", "path": "/api/analytics/events", "role": "event_read"},
        {
            "name": "events_summary",
            "path": "/api/analytics/events/summary",
            "role": "event_summary_read",
        },
    ],
}

KPI_WORKFLOW_HINTS: dict[str, list[str]] = {
    "primary_flow": [
        "kpis",
        "kpi_trends",
        "kpi_insights",
        "kpi_recommendations",
    ],
    "operational_flow": [
        "kpi_refresh",
        "kpi_refresh_history",
    ],
    "observability_flow": [
        "events",
        "events_summary",
    ],
}

KPI_CONTRACT_FINGERPRINT_ALGORITHM = "sha256"
KPI_CONTRACT_FINGERPRINT_BASIS = "surface_contract_v1"
KPI_CONTRACT_COMPATIBILITY_MODE = "backward_additive_v1"
KPI_CONTRACT_COMPATIBILITY_FINGERPRINT_SCOPE = "stable_contract_basis"

KPI_STABILITY_TIERS: dict[str, list[str]] = {
    "stable_core_fields": [
        "surface_id",
        "contract_version",
        "tenant_id",
        "sections",
        "request_id",
        "served_at",
    ],
    "extensible_metadata_blocks": [
        "capabilities",
        "contract_invariants",
        "contract_fingerprint",
        "contract_compatibility",
        "surface_profile",
        "field_semantics",
        "card_field_semantics",
        "response_examples",
        "surface_map",
        "workflow_hints",
        "stability_tiers",
    ],
    "data_dependent_blocks": [
        "kpis",
        "summary",
        "change_digest",
        "source_mix_summary",
        "readiness_status",
        "snapshot_date",
        "generated_at",
        "freshness_status",
        "source_mode",
        "response_status",
    ],
    "stable_card_core_fields": [
        "key",
        "title",
        "description",
        "value",
        "readiness_status",
        "source_status",
        "trend",
    ],
    "optional_card_fields": [
        "lineage",
        "source_breakdown",
        "severity",
        "threshold_basis",
        "policy_pack",
        "actionability_state",
    ],
}

KPI_GUARANTEED_TOP_LEVEL_FIELDS: list[str] = [
    "surface_id",
    "contract_version",
    "capabilities",
    "sections",
    "surface_profile",
    "field_semantics",
    "card_field_semantics",
    "response_examples",
    "surface_map",
    "workflow_hints",
    "stability_tiers",
    "contract_fingerprint",
    "contract_compatibility",
    "request_id",
    "served_at",
    "response_status",
    "tenant_id",
    "snapshot_date",
    "generated_at",
    "readiness_status",
    "freshness_status",
    "source_mode",
    "kpis",
    "summary",
    "change_digest",
    "source_mix_summary",
    "contract_invariants",
]

KPI_ALWAYS_PRESENT_SECTIONS: list[str] = [
    "cards",
    "summary",
    "change_digest",
    "source_mix_summary",
    "capabilities",
    "contract_identity",
    "surface_profile",
    "field_semantics",
    "card_field_semantics",
    "response_examples",
    "surface_map",
    "workflow_hints",
    "stability_tiers",
    "contract_fingerprint",
    "contract_compatibility",
    "contract_invariants",
]

KPI_OPTIONAL_CARD_FIELDS: list[str] = [
    "lineage",
    "source_breakdown",
    "severity",
    "threshold_basis",
    "policy_pack",
    "actionability_state",
]


def _build_kpi_contract_invariants() -> dict[str, Any]:
    """Return bounded client-facing compatibility guarantees for the KPI surface."""
    return {
        "guaranteed_top_level_fields": list(KPI_GUARANTEED_TOP_LEVEL_FIELDS),
        "always_present_sections": list(KPI_ALWAYS_PRESENT_SECTIONS),
        "optional_card_fields": list(KPI_OPTIONAL_CARD_FIELDS),
        "empty_state_contract_stable": True,
    }


def _build_kpi_contract_compatibility() -> dict[str, Any]:
    """Return bounded compatibility assertions for stable KPI client integrations."""
    return {
        "compatibility_mode": KPI_CONTRACT_COMPATIBILITY_MODE,
        "backward_compatible_with": [KPI_CONTRACT_VERSION],
        "stable_core_enforced": True,
        "additive_metadata_extensions_allowed": True,
        "data_dependent_blocks_may_vary": True,
        "fingerprint_scope": KPI_CONTRACT_COMPATIBILITY_FINGERPRINT_SCOPE,
    }


def _build_kpi_surface_profile() -> dict[str, Any]:
    """Return bounded intended-consumption metadata for the KPI surface."""
    return {
        "audience_profiles": list(KPI_SURFACE_PROFILE["audience_profiles"]),
        "primary_audience": KPI_SURFACE_PROFILE["primary_audience"],
        "consumption_mode": KPI_SURFACE_PROFILE["consumption_mode"],
    }


def _build_kpi_field_semantics() -> dict[str, str]:
    """Return a minimal client guide for top-level KPI contract blocks."""
    return dict(KPI_FIELD_SEMANTICS)


def _build_kpi_card_field_semantics() -> dict[str, str]:
    """Return a minimal client guide for KPI card governance fields."""
    return dict(KPI_CARD_FIELD_SEMANTICS)


def _build_kpi_response_examples() -> dict[str, dict[str, str]]:
    """Return canonical empty/ready shape markers for client integration guidance."""
    return {
        "empty_shape": dict(KPI_RESPONSE_EXAMPLES["empty_shape"]),
        "ready_shape": dict(KPI_RESPONSE_EXAMPLES["ready_shape"]),
    }


def _build_kpi_surface_map() -> dict[str, Any]:
    """Return bounded endpoint-family map for related analytics endpoints."""
    return {
        "family_id": KPI_SURFACE_MAP["family_id"],
        "endpoints": [dict(endpoint) for endpoint in KPI_SURFACE_MAP["endpoints"]],
    }


def _build_kpi_workflow_hints() -> dict[str, list[str]]:
    """Return bounded recommended endpoint-consumption order for analytics clients."""
    return {
        "primary_flow": list(KPI_WORKFLOW_HINTS["primary_flow"]),
        "operational_flow": list(KPI_WORKFLOW_HINTS["operational_flow"]),
        "observability_flow": list(KPI_WORKFLOW_HINTS["observability_flow"]),
    }


def _build_kpi_stability_tiers() -> dict[str, list[str]]:
    """Return bounded stability and change-safety tiers for the KPI contract."""
    return {
        "stable_core_fields": list(KPI_STABILITY_TIERS["stable_core_fields"]),
        "extensible_metadata_blocks": list(KPI_STABILITY_TIERS["extensible_metadata_blocks"]),
        "data_dependent_blocks": list(KPI_STABILITY_TIERS["data_dependent_blocks"]),
        "stable_card_core_fields": list(KPI_STABILITY_TIERS["stable_card_core_fields"]),
        "optional_card_fields": list(KPI_STABILITY_TIERS["optional_card_fields"]),
    }


def _build_kpi_contract_fingerprint() -> dict[str, str]:
    """Return deterministic checksum for stable contract identity inputs."""
    basis_payload = {
        "fingerprint_basis": KPI_CONTRACT_FINGERPRINT_BASIS,
        "surface_id": KPI_SURFACE_ID,
        "contract_version": KPI_CONTRACT_VERSION,
        "guaranteed_top_level_fields": list(KPI_GUARANTEED_TOP_LEVEL_FIELDS),
        "always_present_sections": list(KPI_ALWAYS_PRESENT_SECTIONS),
        "capabilities": dict(KPI_SURFACE_CAPABILITIES),
        "contract_invariants": _build_kpi_contract_invariants(),
        "surface_profile": _build_kpi_surface_profile(),
        "surface_map": _build_kpi_surface_map(),
        "workflow_hints": _build_kpi_workflow_hints(),
        "stability_tiers": _build_kpi_stability_tiers(),
        "contract_compatibility": _build_kpi_contract_compatibility(),
    }
    canonical = json.dumps(basis_payload, sort_keys=True, separators=(",", ":"))
    value = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "algorithm": KPI_CONTRACT_FINGERPRINT_ALGORITHM,
        "value": value,
        "fingerprint_basis": KPI_CONTRACT_FINGERPRINT_BASIS,
    }


def attach_kpi_response_envelope(
    payload: dict[str, Any], *, request_id: str | None, served_at: str | None = None
) -> dict[str, Any]:
    """Attach bounded request/response envelope fields to an already-built KPI payload."""
    response_status = str(payload.get("readiness_status") or "unknown").strip().lower() or "unknown"
    enriched = dict(payload)
    enriched["request_id"] = request_id
    enriched["served_at"] = served_at or datetime.now(timezone.utc).isoformat()
    enriched["response_status"] = response_status
    enriched["contract_invariants"] = _build_kpi_contract_invariants()
    return enriched


def _lineage_for_metric(metric_key: str) -> dict[str, object] | None:
    event_types = EVENT_DERIVED_METRIC_LINEAGE.get(str(metric_key).strip().lower())
    if not event_types:
        return None
    return {
        "source_type": "platform_events",
        "source_event_types": list(event_types),
        "derived_from": "event_projection",
    }


def _breakdown_for_metric(
    metric_key: str, event_counts: dict[str, int]
) -> list[dict[str, Any]] | None:
    """Return per-event-type count breakdown for event-derived KPIs only.

    Returns None for metrics not in EVENT_DERIVED_METRIC_LINEAGE.
    """
    event_types = EVENT_DERIVED_METRIC_LINEAGE.get(str(metric_key).strip().lower())
    if not event_types:
        return None
    return [
        {"event_type": et, "count": int(event_counts.get(et, 0))}
        for et in event_types
    ]


def clear_kpi_state() -> None:
    _kpi_repository.clear_state()


def _compute_budget_kpi_values(event_counts: dict[str, int]) -> dict[str, int]:
    """Return budget-domain KPI values derived from raw event_counts.

    Extracted for unit-testability. Mirrors the Wave 3 budget computation in
    refresh_tenant_metrics() — keep in sync if that block changes.
    A-017.1: budget_variance_threshold_w3 contributes to overrun count and review actions.
    """
    budget_exceeded = int(event_counts.get("finance.expense.budget_exceeded", 0) or 0)
    overrun_risk = int(event_counts.get("campus.budget.overrun_risk_detected", 0) or 0)
    controls_exceeded = int(event_counts.get("campus.expense_controls.budget_exceeded_risk_detected", 0) or 0)
    variance_threshold = int(event_counts.get("finance.budget_variance.threshold_reached", 0) or 0)
    return {
        "budget_overrun_risk_count": budget_exceeded + overrun_risk + controls_exceeded + variance_threshold,
        "budget_overrun_amount_at_risk": budget_exceeded,
        "budget_review_actions_count": overrun_risk + controls_exceeded + variance_threshold,
    }


def refresh_tenant_metrics(*, tenant_id: int, uow: Any, snapshot_date: str | None = None) -> list[dict[str, Any]]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    day = snapshot_date or datetime.now(timezone.utc).date().isoformat()

    analytics_latest = uow.analytics_repository.get_latest_kpi_snapshot(tenant_id=int(tenant_id), conn=conn)
    analytics_counts = dict((analytics_latest or {}).get("event_counts_json", {}))
    analytics_events_ingested_total = int((analytics_latest or {}).get("total_events", 0) or 0)

    usage_rows = uow.usage_repository.list_for_tenant_period(
        int(tenant_id),
        period_key="current",
        conn=conn,
    )
    usage_by_metric = {
        str(item.get("metric", "")).strip().lower(): int(item.get("value", 0) or 0)
        for item in usage_rows
    }
    analytics_events_reads_total = int(usage_by_metric.get("analytics.events.read", 0) or 0)
    analytics_kpi_reads_total = int(usage_by_metric.get("analytics.kpi.read", 0) or 0)
    analytics_reads_total = analytics_events_reads_total + analytics_kpi_reads_total
    analytics_kpi_reads_share_pct = (
        int(round((analytics_kpi_reads_total * 100.0) / analytics_reads_total))
        if analytics_reads_total > 0
        else 0
    )

    metric_values: dict[str, int] = {}
    if conn is None:
        for event_type, metric_key in EVENT_METRIC_MAP.items():
            metric_values[metric_key] = len(
                uow.analytics_repository.list_event_projections(
                    tenant_id=int(tenant_id),
                    event_type=event_type,
                    limit=1_000_000,
                    conn=conn,
                )
            )
    else:
        for event_type, metric_key in EVENT_METRIC_MAP.items():
            metric_values[metric_key] = repo.count_events_by_type(
                tenant_id=int(tenant_id),
                event_type=event_type,
                conn=conn,
            )

    subscription = uow.billing_repository.get_subscription(int(tenant_id), conn=conn)
    metric_values["total_active_subscriptions"] = 1 if subscription and subscription.get("status") == "active" else 0
    if conn is None:
        failed_jobs = uow.job_repository.list_for_tenant(int(tenant_id), status="failed", limit=1_000_000, conn=conn)
        metric_values["total_failed_jobs"] = len(failed_jobs)

        notifications = uow.notification_repository.list_for_tenant(int(tenant_id), limit=1_000_000, conn=conn)
        metric_values["total_failed_notifications"] = sum(
            1 for row in notifications if str(row.get("status", "")).lower() == "failed"
        )
    else:
        metric_values["total_failed_jobs"] = repo.count_failed_jobs(tenant_id=int(tenant_id), conn=conn)
        metric_values["total_failed_notifications"] = repo.count_failed_notifications(tenant_id=int(tenant_id), conn=conn)

    metric_values["analytics_events_ingested_total"] = analytics_events_ingested_total
    metric_values["analytics_events_reads_total"] = analytics_events_reads_total
    metric_values["analytics_kpi_reads_total"] = analytics_kpi_reads_total
    metric_values["analytics_reads_total"] = analytics_reads_total
    metric_values["analytics_kpi_reads_share_pct"] = analytics_kpi_reads_share_pct

    # Event-to-KPI projection bridge v1: derive KPI-friendly counters from append-only platform_events.
    event_counts = event_ingestion_service.summary_for_tenant(int(tenant_id), uow=uow)
    metric_values["analytics_events_reads_from_events_total"] = int(event_counts.get(ANALYTICS_EVENT_READ, 0) or 0)
    metric_values["analytics_kpi_reads_from_events_total"] = int(event_counts.get(ANALYTICS_KPI_READ, 0) or 0)
    metric_values["billing_usage_recorded_from_events_total"] = int(event_counts.get(BILLING_USAGE_RECORDED, 0) or 0)

    # A-013.5 Wave 1 KPI extension: additive metrics derived from existing event stream + billing delinquency service.
    attendance_risk = int(event_counts.get("academic.attendance_risk.detected", 0) or 0)
    grade_risk = int(event_counts.get("academic.grade_risk.detected", 0) or 0)
    payment_overdue = int(event_counts.get("finance.payment_overdue.detected", 0) or 0)
    student_needs_intervention = int(event_counts.get("student.needs_intervention", 0) or 0)
    critical_overdue = int(event_counts.get("collections.delinquency.critical_overdue", 0) or 0)
    intervention_created = int(event_counts.get("interventions.case.created", 0) or 0)
    intervention_outcomes = int(event_counts.get("interventions.case_outcome.recorded", 0) or 0)
    intervention_auto = int(event_counts.get("interventions.auto_triggered", 0) or 0)
    scheduling_sections_created = int(event_counts.get("scheduling.section.created", 0) or 0)
    scheduling_conflicts = int(event_counts.get("scheduling.section.conflict_detected", 0) or 0)
    room_conflicts = int(event_counts.get("scheduling.room_conflict.detected", 0) or 0)
    room_allocation_required = int(event_counts.get("scheduling.room_allocation.required", 0) or 0)
    room_allocation_recommendations = int(event_counts.get("scheduling.room_allocation.recommendation_generated", 0) or 0)
    room_allocation_review_required = int(event_counts.get("scheduling.room_allocation.review_required", 0) or 0)
    room_allocation_no_viable_candidate = int(event_counts.get("scheduling.room_allocation.no_viable_candidate", 0) or 0)
    room_allocation_candidate_evaluated = int(event_counts.get("scheduling.room_allocation.candidate_ranked", 0) or 0)
    room_capacity_mismatch = int(event_counts.get("scheduling.capacity_mismatch.detected", 0) or 0)
    room_equipment_mismatch = int(event_counts.get("scheduling.equipment_mismatch.detected", 0) or 0)
    room_computer_shortage = int(event_counts.get("scheduling.computer_shortage.detected", 0) or 0)
    room_type_mismatch = int(event_counts.get("scheduling.room_type_mismatch.detected", 0) or 0)
    enrollment_capacity_risk = int(event_counts.get("enrollment.capacity_risk.detected", 0) or 0)

    # A-022.5 timetable workflow event counts
    timetable_proposals_created = int(event_counts.get("scheduling.timetable_proposal.created", 0) or 0)
    timetable_proposals_submitted = int(event_counts.get("scheduling.timetable_proposal.submitted", 0) or 0)
    timetable_proposals_approved = int(event_counts.get("scheduling.timetable_proposal.approved", 0) or 0)
    timetable_proposals_rejected = int(event_counts.get("scheduling.timetable_proposal.rejected", 0) or 0)
    timetable_proposals_revision_requested = int(
        event_counts.get("scheduling.timetable_proposal.revision_requested", 0) or 0
    )
    timetable_simulations_computed = int(event_counts.get("scheduling.timetable_simulation.computed", 0) or 0)
    timetable_simulations_review_required = int(
        event_counts.get("scheduling.timetable_simulation.review_required", 0) or 0
    )
    timetable_simulation_conflicts_created = int(
        event_counts.get("scheduling.timetable_simulation.conflicts_created", 0) or 0
    )
    timetable_simulation_conflicts_resolved = int(
        event_counts.get("scheduling.timetable_simulation.conflicts_resolved", 0) or 0
    )
    timetable_approval_queued = int(event_counts.get("scheduling.timetable_approval.queued", 0) or 0)
    timetable_approval_in_review = int(event_counts.get("scheduling.timetable_approval.in_review", 0) or 0)
    timetable_approval_approved = int(event_counts.get("scheduling.timetable_approval.approved", 0) or 0)
    timetable_approval_rejected = int(event_counts.get("scheduling.timetable_approval.rejected", 0) or 0)
    timetable_approval_revision_requested = int(
        event_counts.get("scheduling.timetable_approval.revision_requested", 0) or 0
    )
    timetable_approval_high_risk = int(event_counts.get("scheduling.timetable_approval.high_risk", 0) or 0)

    access_denied = int(event_counts.get("access.denied", 0) or 0)
    security_anomalies = int(event_counts.get("security.anomaly", 0) or 0)
    card_issued = int(event_counts.get("card.issued", 0) or 0)
    card_reactivated = int(event_counts.get("card.reactivated", 0) or 0)
    card_suspended = int(event_counts.get("card.suspended", 0) or 0)

    events_published = int(event_counts.get("event.published", 0) or 0)
    events_started = int(event_counts.get("event.started", 0) or 0)
    events_completed = int(event_counts.get("event.completed", 0) or 0)
    events_cancelled = int(event_counts.get("event.cancelled", 0) or 0)
    events_registration_full = int(event_counts.get("event.registration_full", 0) or 0)

    total_students = int(metric_values.get("total_students", 0) or 0)
    total_enrollments = int(event_counts.get("enrollment.created", 0) or 0)

    high_risk_students = attendance_risk + grade_risk + payment_overdue + student_needs_intervention
    metric_values["high_risk_students_count"] = high_risk_students
    metric_values["critical_risk_students_count"] = critical_overdue + student_needs_intervention
    metric_values["intervention_auto_created_count"] = intervention_auto
    metric_values["intervention_resolution_rate"] = (
        int(round((intervention_outcomes * 100.0) / intervention_created))
        if intervention_created > 0
        else 0
    )

    weighted_risk_sum = (
        attendance_risk * 35
        + grade_risk * 30
        + payment_overdue * 20
        + enrollment_capacity_risk * 15
    )
    metric_values["composite_risk_average"] = int(min(100, round(weighted_risk_sum / max(1, total_students))))
    metric_values["sweep_coverage_rate"] = int(min(100, round((high_risk_students * 100.0) / max(1, total_students))))

    metric_values["course_fill_rate"] = (
        int(min(100, round((total_enrollments * 100.0) / scheduling_sections_created)))
        if scheduling_sections_created > 0
        else 0
    )
    metric_values["capacity_risk_sections_count"] = enrollment_capacity_risk
    metric_values["scheduling_conflicts_count"] = scheduling_conflicts
    metric_values["room_conflict_count"] = room_conflicts + room_allocation_required
    metric_values["room_allocation_recommendations_count"] = room_allocation_recommendations
    metric_values["room_allocation_review_required_count"] = room_allocation_review_required
    metric_values["room_allocation_no_viable_candidate_count"] = room_allocation_no_viable_candidate
    metric_values["room_allocation_candidate_evaluated_count"] = room_allocation_candidate_evaluated
    metric_values["room_capacity_mismatch_count"] = room_capacity_mismatch
    metric_values["room_equipment_mismatch_count"] = room_equipment_mismatch
    metric_values["room_computer_shortage_count"] = room_computer_shortage
    metric_values["room_type_mismatch_count"] = room_type_mismatch

    metric_values["timetable_change_proposals_count"] = timetable_proposals_created
    metric_values["timetable_change_pending_review_count"] = timetable_proposals_submitted
    metric_values["timetable_change_approved_count"] = timetable_proposals_approved
    metric_values["timetable_change_rejected_count"] = timetable_proposals_rejected
    metric_values["timetable_change_revision_requested_count"] = timetable_proposals_revision_requested
    metric_values["timetable_simulations_count"] = timetable_simulations_computed
    metric_values["timetable_simulations_review_required_count"] = timetable_simulations_review_required
    metric_values["timetable_simulation_conflicts_created_count"] = timetable_simulation_conflicts_created
    metric_values["timetable_simulation_conflicts_resolved_count"] = timetable_simulation_conflicts_resolved
    metric_values["timetable_approval_queue_count"] = timetable_approval_queued
    metric_values["timetable_approval_pending_count"] = timetable_approval_queued + timetable_approval_in_review
    metric_values["timetable_approval_approved_count"] = timetable_approval_approved
    metric_values["timetable_approval_rejected_count"] = timetable_approval_rejected
    metric_values["timetable_approval_revision_requested_count"] = timetable_approval_revision_requested
    metric_values["timetable_approval_high_risk_count"] = timetable_approval_high_risk

    # A-020.5 compatibility values preserved for existing contracts
    metric_values["room_allocation_recommendations_generated_count"] = room_allocation_recommendations

    # A-018.5 Wave 6 consolidation: campus operations KPI counters from existing event stream.
    metric_values["access_denied_count"] = access_denied
    metric_values["unauthorized_attempts_count"] = access_denied + security_anomalies
    metric_values["active_access_cards_count"] = card_issued + card_reactivated
    metric_values["suspended_access_cards_count"] = card_suspended
    metric_values["security_access_anomaly_count"] = security_anomalies

    metric_values["events_published_count"] = events_published
    metric_values["events_started_count"] = events_started
    metric_values["events_completed_count"] = events_completed
    metric_values["events_cancelled_count"] = events_cancelled
    metric_values["events_registration_full_count"] = events_registration_full

    # A-018.6 Wave 6 consolidation: visitor management + security operations KPI counters.
    visitor_registered = int(event_counts.get("visitor.registered", 0) or 0)
    visitor_checked_in = int(event_counts.get("visitor.checked_in", 0) or 0)
    visitor_unauthorized = int(event_counts.get("visitor.unauthorized_attempt", 0) or 0)
    security_incidents_opened = int(event_counts.get("security.incident.opened", 0) or 0)
    security_incidents_escalated = int(event_counts.get("security.incident.escalated", 0) or 0)
    security_incidents_resolved = int(event_counts.get("security.incident.resolved", 0) or 0)

    visitor_checked_out = int(event_counts.get("visitor.checked_out", 0) or 0)
    visitor_cancelled = int(event_counts.get("visitor.cancelled", 0) or 0)

    metric_values["visitor_requests_pending_count"] = visitor_registered
    metric_values["visitors_checked_in_count"] = visitor_checked_in
    metric_values["visitor_unauthorized_attempts_count"] = visitor_unauthorized
    metric_values["visitor_visits_completed_count"] = visitor_checked_out
    metric_values["visitor_visits_cancelled_count"] = visitor_cancelled
    metric_values["security_incidents_open_count"] = security_incidents_opened
    metric_values["security_incidents_escalated_count"] = security_incidents_escalated
    metric_values["security_incidents_resolved_count"] = security_incidents_resolved
    metric_values["security_incident_review_required_count"] = security_incidents_opened
    metric_values["security_high_risk_incidents_count"] = security_incidents_escalated

    # A-014.6 Wave 2: derive KPI-friendly counters from Wave 2 event stream.
    grade_decline_risk = int(event_counts.get("academic.grade_risk.detected", 0) or 0)
    thesis_risk = int(event_counts.get("thesis.status_changed", 0) or 0)
    attendance_recovery = int(event_counts.get("academic.attendance_risk.detected", 0) or 0)
    graduation_risk = int(event_counts.get("degree_progress.graduation_risk.detected", 0) or 0)
    scholarship_risk = int(event_counts.get("scholarship.award.at_risk_detected", 0) or 0)
    financial_aid_risk = int(event_counts.get("financial_aid.warning.detected", 0) or 0)

    metric_values["grade_decline_risk_count"] = grade_decline_risk
    metric_values["grade_intervention_cases_count"] = intervention_created
    metric_values["thesis_completion_risk_count"] = thesis_risk
    metric_values["thesis_intervention_cases_count"] = intervention_created
    metric_values["attendance_recovery_actions_count"] = attendance_recovery
    metric_values["graduation_risk_students_count"] = graduation_risk
    metric_values["degree_progress_intervention_cases_count"] = intervention_created
    metric_values["scholarship_risk_cases_count"] = scholarship_risk
    metric_values["financial_aid_risk_cases_count"] = financial_aid_risk

    # A-015.6 Wave 3 KPI extension: finance/procurement/asset/inventory risk metrics
    # A-017.1 budget_planning maturity: budget variance drift signal included
    budget_exceeded_w3 = int(event_counts.get("finance.expense.budget_exceeded", 0) or 0)
    budget_overrun_risk_w3 = int(event_counts.get("campus.budget.overrun_risk_detected", 0) or 0)
    budget_controls_exceeded_w3 = int(event_counts.get("campus.expense_controls.budget_exceeded_risk_detected", 0) or 0)
    budget_variance_threshold_w3 = int(event_counts.get("finance.budget_variance.threshold_reached", 0) or 0)
    procurement_submitted_w3 = int(event_counts.get("procurement.request_submitted", 0) or 0)
    procurement_approval_required_w3 = int(event_counts.get("procurement.approval_required", 0) or 0)
    procurement_po_issued_w3 = int(event_counts.get("procurement.po_issued", 0) or 0)
    asset_created_w3 = int(event_counts.get("procurement.asset_created", 0) or 0)
    finance_health_check_w3 = int(event_counts.get("finance.operations.health_check", 0) or 0)
    finance_risk_detected_w3 = int(event_counts.get("finance.operations.risk_detected", 0) or 0)
    inv_low_stock_w3 = int(event_counts.get("inventory.low_stock.detected", 0) or 0)
    inv_reorder_needed_w3 = int(event_counts.get("inventory.reorder_needed", 0) or 0)
    supply_risk_w3 = int(event_counts.get("supply.risk.detected", 0) or 0)
    inv_gap_w3 = int(event_counts.get("procurement.inventory_gap.detected", 0) or 0)
    # Group A — Budget (A-017.1: budget_variance_threshold_w3 contributes to overrun count and review actions)
    metric_values["budget_overrun_risk_count"] = budget_exceeded_w3 + budget_overrun_risk_w3 + budget_controls_exceeded_w3 + budget_variance_threshold_w3
    metric_values["budget_overrun_amount_at_risk"] = budget_exceeded_w3
    metric_values["budget_review_actions_count"] = budget_overrun_risk_w3 + budget_controls_exceeded_w3 + budget_variance_threshold_w3
    # Group B — Procurement
    metric_values["procurement_requests_pending_approval"] = procurement_submitted_w3 + procurement_approval_required_w3
    metric_values["procurement_approval_automation_count"] = procurement_submitted_w3
    metric_values["procurement_po_issued_count"] = procurement_po_issued_w3
    # Group C — PO / Delivery / Asset
    metric_values["po_delivery_completion_rate"] = (
        int(min(100, round((asset_created_w3 * 100.0) / max(1, procurement_po_issued_w3))))
        if procurement_po_issued_w3 > 0 else 0
    )
    metric_values["delivered_po_asset_conversion_rate"] = metric_values["po_delivery_completion_rate"]
    metric_values["asset_conversion_gap_count"] = max(0, procurement_po_issued_w3 - asset_created_w3)
    # Group D — Finance Operations Health
    metric_values["finance_operations_health_score"] = finance_health_check_w3
    metric_values["budget_health_score"] = finance_health_check_w3
    metric_values["procurement_health_score"] = finance_risk_detected_w3
    metric_values["po_delivery_health_score"] = finance_risk_detected_w3
    metric_values["asset_conversion_health_score"] = finance_health_check_w3
    metric_values["active_finance_risk_signals_count"] = finance_risk_detected_w3
    metric_values["finance_operations_actionability_count"] = finance_risk_detected_w3 + finance_health_check_w3
    # Group E — Inventory / Supply
    metric_values["inventory_low_stock_items_count"] = inv_low_stock_w3
    metric_values["critical_supply_risk_count"] = inv_low_stock_w3 + supply_risk_w3
    metric_values["reorder_recommendations_count"] = inv_reorder_needed_w3
    metric_values["supply_risk_actions_count"] = supply_risk_w3 + inv_gap_w3

    # A-016.6 Wave 4 KPI extension: academic integrity / thesis governance / research ethics / case resolution
    # Group A — Academic Integrity
    ai_violation_w4 = int(event_counts.get("academic_integrity.violation.detected", 0) or 0)
    ai_risk_w4 = int(event_counts.get("academic_integrity.risk_detected", 0) or 0)
    ai_case_opened_w4 = int(event_counts.get("academic_integrity.case.opened", 0) or 0)
    ai_case_review_required_w4 = int(event_counts.get("academic_integrity.case.review_required", 0) or 0)
    metric_values["academic_integrity_risk_count"] = ai_violation_w4 + ai_risk_w4
    metric_values["academic_integrity_review_cases_count"] = ai_case_opened_w4 + ai_case_review_required_w4
    metric_values["academic_integrity_high_risk_count"] = ai_violation_w4 + ai_case_review_required_w4
    metric_values["academic_integrity_cases_pending_review"] = ai_case_review_required_w4
    # Group B — Exam Proctoring
    ep_governance_violation_w4 = int(event_counts.get("exam.violation_detected", 0) or 0)
    ep_violation_w4 = int(event_counts.get("exam.proctoring.violation_detected", 0) or 0)
    ep_faculty_w4 = int(event_counts.get("faculty.proctoring.violation_detected", 0) or 0)
    ep_suspicious_w4 = int(event_counts.get("exam.proctoring.suspicious_activity_detected", 0) or 0)
    ep_multi_face_w4 = int(event_counts.get("exam.proctoring.multiple_faces_detected", 0) or 0)
    ep_face_mismatch_w4 = int(event_counts.get("exam.proctoring.face_mismatch_detected", 0) or 0)
    ep_forbidden_app_w4 = int(event_counts.get("exam.proctoring.forbidden_app_detected", 0) or 0)
    ep_camera_absent_w4 = int(event_counts.get("exam.proctoring.camera_absent_detected", 0) or 0)
    metric_values["exam_proctoring_violations_count"] = ep_governance_violation_w4 + ep_violation_w4 + ep_faculty_w4
    metric_values["exam_integrity_reviews_count"] = (
        ep_suspicious_w4 + ep_multi_face_w4 + ep_face_mismatch_w4 + ep_forbidden_app_w4 + ep_camera_absent_w4
    )
    metric_values["exam_integrity_high_risk_count"] = ep_multi_face_w4 + ep_face_mismatch_w4
    metric_values["exam_integrity_requires_approval_count"] = ep_governance_violation_w4 + ep_violation_w4
    # Group C — Thesis Governance
    thesis_gov_risk_w4 = int(event_counts.get("thesis.governance.risk_detected", 0) or 0)
    thesis_supervisor_needed_w4 = int(event_counts.get("thesis.supervisor.assignment_needed", 0) or 0)
    thesis_review_delayed_w4 = int(event_counts.get("thesis.review.delayed", 0) or 0)
    thesis_supervisor_overloaded_w4 = int(event_counts.get("thesis.supervisor.overloaded", 0) or 0)
    metric_values["thesis_governance_risk_count"] = thesis_gov_risk_w4
    metric_values["thesis_supervisor_assignment_needed_count"] = thesis_supervisor_needed_w4
    metric_values["thesis_review_delayed_count"] = thesis_review_delayed_w4
    metric_values["thesis_governance_requires_approval_count"] = thesis_supervisor_overloaded_w4 + thesis_gov_risk_w4
    # Group D — Research Ethics / Compliance
    re_submitted_w4 = int(event_counts.get("research_ethics.application.submitted", 0) or 0)
    re_overdue_w4 = int(event_counts.get("research_ethics.review.overdue", 0) or 0)
    re_high_risk_w4 = int(event_counts.get("research_ethics.high_risk.detected", 0) or 0)
    re_missing_consent_w4 = int(event_counts.get("research_ethics.missing_consent.detected", 0) or 0)
    re_doc_missing_w4 = int(event_counts.get("research_ethics.document_missing.detected", 0) or 0)
    metric_values["research_ethics_review_cases_count"] = re_submitted_w4 + re_overdue_w4
    metric_values["research_ethics_high_risk_count"] = re_high_risk_w4 + re_missing_consent_w4
    metric_values["research_ethics_missing_documents_count"] = re_doc_missing_w4
    metric_values["research_ethics_requires_approval_count"] = re_high_risk_w4 + re_missing_consent_w4
    # Group E — Case Resolution
    cr_opened_w4 = int(event_counts.get("academic_integrity.case.opened", 0) or 0)
    cr_review_required_w4 = int(event_counts.get("academic_integrity.case.review_required", 0) or 0)
    cr_resolved_w4 = int(event_counts.get("academic_integrity.case.resolved", 0) or 0)
    cr_evidence_w4 = int(event_counts.get("academic_integrity.case.evidence_requested", 0) or 0)
    metric_values["integrity_cases_open_count"] = cr_opened_w4
    metric_values["integrity_cases_escalated_count"] = cr_review_required_w4
    metric_values["integrity_cases_resolved_count"] = cr_resolved_w4
    metric_values["integrity_cases_evidence_requested_count"] = cr_evidence_w4
    metric_values["integrity_case_resolution_sla_risk_count"] = cr_review_required_w4

    from app.modules.billing.service import get_delinquency_dashboard, list_delinquency_records  # noqa: PLC0415

    delinquency_dashboard = get_delinquency_dashboard(int(tenant_id))
    delinquency_records = list_delinquency_records(int(tenant_id))
    delinquency_total = len(delinquency_records)
    delinquency_resolved = sum(1 for item in delinquency_records if item.get("resolved_at"))

    open_total_raw = delinquency_dashboard.get("open_total")
    overdue_amount_raw = delinquency_dashboard.get("total_overdue_cents")
    metric_values["delinquency_cases_active"] = int(open_total_raw) if isinstance(open_total_raw, int | float) else 0
    metric_values["overdue_amount_at_risk"] = int(overdue_amount_raw) if isinstance(overdue_amount_raw, int | float) else 0
    metric_values["delinquency_recovery_rate"] = (
        int(round((delinquency_resolved * 100.0) / delinquency_total))
        if delinquency_total > 0
        else 0
    )

    rows: list[dict[str, Any]] = []
    for metric_key, metric_value in metric_values.items():
        lineage = _lineage_for_metric(metric_key)
        rows.append(
            repo.upsert_metric_snapshot(
                tenant_id=int(tenant_id),
                metric_key=metric_key,
                metric_value=int(metric_value),
                snapshot_date=day,
                metadata_json={
                    "title": METRIC_TITLES.get(metric_key, metric_key),
                    "source": "analytics_sink_v1" if metric_key in {
                        "total_students",
                        "total_enrollments",
                        "total_grades_submitted",
                        "analytics_events_ingested_total",
                        "analytics_events_reads_total",
                        "analytics_kpi_reads_total",
                        "analytics_reads_total",
                        "analytics_kpi_reads_share_pct",
                        "analytics_events_reads_from_events_total",
                        "analytics_kpi_reads_from_events_total",
                        "billing_usage_recorded_from_events_total",
                        "high_risk_students_count",
                        "intervention_resolution_rate",
                        "intervention_auto_created_count",
                        "composite_risk_average",
                        "critical_risk_students_count",
                        "sweep_coverage_rate",
                        "course_fill_rate",
                        "capacity_risk_sections_count",
                        "scheduling_conflicts_count",
                        "room_conflict_count",
                        # A-018.5 Wave 6 consolidation
                        "access_denied_count",
                        "unauthorized_attempts_count",
                        "active_access_cards_count",
                        "suspended_access_cards_count",
                        "security_access_anomaly_count",
                        "events_published_count",
                        "events_started_count",
                        "events_completed_count",
                        "events_cancelled_count",
                        "events_registration_full_count",
                        # A-014.6 Wave 2
                        "grade_decline_risk_count",
                        "grade_intervention_cases_count",
                        "thesis_completion_risk_count",
                        "thesis_intervention_cases_count",
                        "attendance_recovery_actions_count",
                        "graduation_risk_students_count",
                        "degree_progress_intervention_cases_count",
                        "scholarship_risk_cases_count",
                        "financial_aid_risk_cases_count",
                        # A-016.6 Wave 4
                        "academic_integrity_risk_count",
                        "academic_integrity_review_cases_count",
                        "academic_integrity_high_risk_count",
                        "academic_integrity_cases_pending_review",
                        "exam_proctoring_violations_count",
                        "exam_integrity_reviews_count",
                        "exam_integrity_high_risk_count",
                        "exam_integrity_requires_approval_count",
                        "thesis_governance_risk_count",
                        "thesis_supervisor_assignment_needed_count",
                        "thesis_review_delayed_count",
                        "thesis_governance_requires_approval_count",
                        "research_ethics_review_cases_count",
                        "research_ethics_high_risk_count",
                        "research_ethics_missing_documents_count",
                        "research_ethics_requires_approval_count",
                        "integrity_cases_open_count",
                        "integrity_cases_escalated_count",
                        "integrity_cases_resolved_count",
                        "integrity_cases_evidence_requested_count",
                        "integrity_case_resolution_sla_risk_count",
                        # A-018.6 Wave 6 — Visitor Management + Security Operations
                        "visitor_requests_pending_count",
                        "visitors_checked_in_count",
                        "visitor_unauthorized_attempts_count",
                        # A-019.2 Wave 7 — Visitor Management completion
                        "visitor_visits_completed_count",
                        "visitor_visits_cancelled_count",
                        "security_incidents_open_count",
                        "security_incidents_escalated_count",
                        "security_incidents_resolved_count",
                        "security_incident_review_required_count",
                        "security_high_risk_incidents_count",
                    }
                    else "platform_core",
                    "analytics_today": int(analytics_counts.get(_metric_key_to_event(metric_key), 0)),
                    "lineage": lineage,
                },
                conn=conn,
            )
        )

    rows.sort(key=lambda item: str(item["metric_key"]))
    return rows


def refresh_tenant_dashboard_snapshot(
    *,
    tenant_id: int,
    uow: Any,
    snapshot_date: str | None = None,
) -> dict[str, Any]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    day = snapshot_date or datetime.now(timezone.utc).date().isoformat()

    metrics = refresh_tenant_metrics(tenant_id=int(tenant_id), uow=uow, snapshot_date=day)

    cards: list[dict[str, Any]] = []
    for metric in metrics:
        metric_key = str(metric["metric_key"])
        history = repo.list_metric_history(
            tenant_id=int(tenant_id),
            metric_key=metric_key,
            days=7,
            conn=conn,
        )
        cards.append(
            {
                "metric_key": metric_key,
                "title": METRIC_TITLES.get(metric_key, metric_key),
                "value": int(metric["metric_value"]),
                "trend_7d": [
                    {"snapshot_date": str(point["snapshot_date"]), "value": int(point["metric_value"])}
                    for point in history
                ],
                "metadata_json": dict(metric.get("metadata_json") or {}),
            }
        )

    payload = {
        "tenant_id": int(tenant_id),
        "snapshot_date": day,
        "cards": cards,
        "drilldowns": _build_rector_kpi_evidence_drilldowns(cards=cards),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "kpi_metrics_engine_v1",
    }

    return repo.upsert_dashboard_snapshot(
        tenant_id=int(tenant_id),
        snapshot_date=day,
        snapshot_json=payload,
        conn=conn,
    )


def get_latest_tenant_metrics(*, tenant_id: int, uow: Any) -> list[dict[str, Any]]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    return repo.list_latest_metrics(tenant_id=int(tenant_id), conn=conn)


def get_tenant_product_kpis(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    rows = repo.list_latest_metrics(tenant_id=int(tenant_id), conn=conn)

    if not rows:
        cards: list[dict[str, Any]] = []
        summary = _build_kpi_portfolio_summary(cards)
        change_digest = _build_kpi_change_digest(cards)
        source_mix_summary = _build_kpi_source_mix_summary(cards)
        return {
            "surface_id": KPI_SURFACE_ID,
            "contract_version": KPI_CONTRACT_VERSION,
            "capabilities": dict(KPI_SURFACE_CAPABILITIES),
            "surface_profile": _build_kpi_surface_profile(),
            "field_semantics": _build_kpi_field_semantics(),
            "card_field_semantics": _build_kpi_card_field_semantics(),
            "response_examples": _build_kpi_response_examples(),
            "surface_map": _build_kpi_surface_map(),
            "workflow_hints": _build_kpi_workflow_hints(),
            "stability_tiers": _build_kpi_stability_tiers(),
            "contract_fingerprint": _build_kpi_contract_fingerprint(),
            "contract_compatibility": _build_kpi_contract_compatibility(),
            "tenant_id": int(tenant_id),
            "snapshot_date": None,
            "generated_at": None,
            "readiness_status": "empty",
            "freshness_status": "empty",
            "source_mode": "empty",
            "kpis": cards,
            "summary": summary,
            "change_digest": change_digest,
            "source_mix_summary": source_mix_summary,
            "sections": _build_kpi_sections_manifest(
                cards=cards,
                summary=summary,
                change_digest=change_digest,
                source_mix_summary=source_mix_summary,
                capabilities=dict(KPI_SURFACE_CAPABILITIES),
                surface_id=KPI_SURFACE_ID,
                contract_version=KPI_CONTRACT_VERSION,
                surface_profile=_build_kpi_surface_profile(),
                field_semantics=_build_kpi_field_semantics(),
                card_field_semantics=_build_kpi_card_field_semantics(),
                response_examples=_build_kpi_response_examples(),
                surface_map=_build_kpi_surface_map(),
                workflow_hints=_build_kpi_workflow_hints(),
                stability_tiers=_build_kpi_stability_tiers(),
                contract_fingerprint=_build_kpi_contract_fingerprint(),
                contract_compatibility=_build_kpi_contract_compatibility(),
            ),
        }

    snapshot_date = str(rows[0].get("snapshot_date")) if rows else None
    generated_at = max(str(item.get("updated_at") or "") for item in rows) or None

    # Fetch event counts once — reused for per-card source_breakdown without extra queries.
    event_counts: dict[str, int] = event_ingestion_service.summary_for_tenant(
        int(tenant_id), uow=uow
    )

    cards: list[dict[str, Any]] = []
    for row in rows:
        metric_key = str(row.get("metric_key") or "").strip().lower()
        metadata_json = dict(row.get("metadata_json") or {})
        title = str(metadata_json.get("title") or METRIC_TITLES.get(metric_key, metric_key))
        trend_rows = repo.list_metric_history(
            tenant_id=int(tenant_id),
            metric_key=metric_key,
            days=7,
            conn=conn,
        )
        metric_value = int(row.get("metric_value") or 0)
        severity, threshold_basis, policy_pack = _severity_for_metric(metric_key, metric_value)
        cards.append(
            {
                "key": metric_key,
                "title": title,
                "description": title,
                "value": metric_value,
                "lineage": metadata_json.get("lineage"),
                "readiness_status": "ready",
                "source_status": _card_source_status(metric_key=metric_key, lineage=metadata_json.get("lineage")),
                "source_breakdown": _breakdown_for_metric(metric_key, event_counts),
                "severity": severity,
                "threshold_basis": threshold_basis,
                "policy_pack": policy_pack,
                "actionability_state": _actionability_for_severity(severity),
                "trend": [
                    {
                        "snapshot_date": str(point.get("snapshot_date")),
                        "value": int(point.get("metric_value") or 0),
                    }
                    for point in trend_rows
                ],
            }
        )

    summary = _build_kpi_portfolio_summary(cards)
    change_digest = _build_kpi_change_digest(cards)
    source_mix_summary = _build_kpi_source_mix_summary(cards)

    return {
        "surface_id": KPI_SURFACE_ID,
        "contract_version": KPI_CONTRACT_VERSION,
        "capabilities": dict(KPI_SURFACE_CAPABILITIES),
        "surface_profile": _build_kpi_surface_profile(),
        "field_semantics": _build_kpi_field_semantics(),
        "card_field_semantics": _build_kpi_card_field_semantics(),
        "response_examples": _build_kpi_response_examples(),
        "surface_map": _build_kpi_surface_map(),
        "workflow_hints": _build_kpi_workflow_hints(),
        "stability_tiers": _build_kpi_stability_tiers(),
        "contract_fingerprint": _build_kpi_contract_fingerprint(),
        "contract_compatibility": _build_kpi_contract_compatibility(),
        "tenant_id": int(tenant_id),
        "snapshot_date": snapshot_date,
        "generated_at": generated_at,
        "readiness_status": "ready",
        "freshness_status": _freshness_status(snapshot_date=snapshot_date, generated_at=generated_at),
        "source_mode": _response_source_mode(cards),
        "kpis": cards,
        "summary": summary,
        "change_digest": change_digest,
        "source_mix_summary": source_mix_summary,
        "sections": _build_kpi_sections_manifest(
            cards=cards,
            summary=summary,
            change_digest=change_digest,
            source_mix_summary=source_mix_summary,
            capabilities=dict(KPI_SURFACE_CAPABILITIES),
            surface_id=KPI_SURFACE_ID,
            contract_version=KPI_CONTRACT_VERSION,
            surface_profile=_build_kpi_surface_profile(),
            field_semantics=_build_kpi_field_semantics(),
            card_field_semantics=_build_kpi_card_field_semantics(),
            response_examples=_build_kpi_response_examples(),
            surface_map=_build_kpi_surface_map(),
            workflow_hints=_build_kpi_workflow_hints(),
            stability_tiers=_build_kpi_stability_tiers(),
            contract_fingerprint=_build_kpi_contract_fingerprint(),
            contract_compatibility=_build_kpi_contract_compatibility(),
        ),
    }


def execute_tenant_product_kpi_refresh(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    normalized_tenant_id = int(tenant_id)
    try:
        refreshed_rows = refresh_tenant_metrics(tenant_id=normalized_tenant_id, uow=uow)
        latest = get_tenant_product_kpis(tenant_id=normalized_tenant_id, uow=uow)
        result = {
            "tenant_id": normalized_tenant_id,
            "refresh_executed": True,
            "snapshot_date": latest.get("snapshot_date"),
            "generated_at": latest.get("generated_at"),
            "readiness_status": latest.get("readiness_status"),
            "freshness_status": latest.get("freshness_status"),
            "source_mode": latest.get("source_mode"),
            "kpi_count": len(refreshed_rows),
        }
        event_ingestion_service.record_event(
            normalized_tenant_id,
            KPI_REFRESH_EXECUTED,
            {
                "status": "success",
                "snapshot_date": result.get("snapshot_date"),
                "generated_at": result.get("generated_at"),
                "kpi_count": int(result.get("kpi_count") or 0),
            },
            uow=uow,
        )
        return result
    except Exception:
        event_ingestion_service.record_event(
            normalized_tenant_id,
            KPI_REFRESH_EXECUTED,
            {
                "status": "failed",
                "snapshot_date": None,
                "generated_at": None,
                "kpi_count": 0,
            },
            uow=uow,
        )
        raise


def get_tenant_product_kpi_refresh_history(*, tenant_id: int, uow: Any, limit: int = 10) -> dict[str, Any]:
    normalized_tenant_id = int(tenant_id)
    normalized_limit = int(limit)
    if normalized_limit < 1 or normalized_limit > 50:
        normalized_limit = 10

    events = event_ingestion_service.list_events_for_tenant(
        normalized_tenant_id,
        event_type=KPI_REFRESH_EXECUTED,
        limit=normalized_limit,
        uow=uow,
    )
    recent_refreshes: list[dict[str, Any]] = []
    for event in events:
        payload = dict(event.get("payload_json") or {})
        recent_refreshes.append(
            {
                "event_id": int(event.get("id") or 0),
                "created_at": str(event.get("created_at") or ""),
                "status": str(payload.get("status") or "unknown"),
                "kpi_count": int(payload.get("kpi_count") or 0),
                "snapshot_date": payload.get("snapshot_date"),
                "generated_at": payload.get("generated_at"),
            }
        )

    last = recent_refreshes[0] if recent_refreshes else None
    return {
        "tenant_id": normalized_tenant_id,
        "limit": normalized_limit,
        "last_refresh_at": last.get("created_at") if last else None,
        "last_refresh_status": last.get("status") if last else None,
        "last_refresh_kpi_count": int(last.get("kpi_count") or 0) if last else None,
        "recent_refreshes": recent_refreshes,
    }


def get_tenant_product_kpi_trends(*, tenant_id: int, uow: Any, window_days: int = 30) -> dict[str, Any]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)
    rows = repo.list_latest_metrics(tenant_id=int(tenant_id), conn=conn)

    normalized_window_days = int(window_days)
    if normalized_window_days not in {7, 30, 90}:
        normalized_window_days = 30

    if not rows:
        return {
            "tenant_id": int(tenant_id),
            "window_days": normalized_window_days,
            "snapshot_date": None,
            "generated_at": None,
            "trends": [],
        }

    snapshot_date = str(rows[0].get("snapshot_date")) if rows else None
    generated_at = max(str(item.get("updated_at") or "") for item in rows) or None

    trends: list[dict[str, Any]] = []
    for row in rows:
        metric_key = str(row.get("metric_key") or "").strip().lower()
        title = str((row.get("metadata_json") or {}).get("title") or METRIC_TITLES.get(metric_key, metric_key))
        trend_rows = repo.list_metric_history(
            tenant_id=int(tenant_id),
            metric_key=metric_key,
            days=normalized_window_days,
            conn=conn,
        )
        points = [
            {
                "date": str(point.get("snapshot_date")),
                "value": int(point.get("metric_value") or 0),
            }
            for point in trend_rows
        ]
        latest_value = points[-1]["value"] if points else int(row.get("metric_value") or 0)
        previous_value = points[-2]["value"] if len(points) > 1 else None
        delta = (latest_value - previous_value) if previous_value is not None else None
        trends.append(
            {
                "key": metric_key,
                "title": title,
                "description": title,
                "latest_value": latest_value,
                "previous_value": previous_value,
                "delta": delta,
                "points": points,
            }
        )

    return {
        "tenant_id": int(tenant_id),
        "window_days": normalized_window_days,
        "snapshot_date": snapshot_date,
        "generated_at": generated_at,
        "trends": trends,
    }


def get_tenant_product_kpi_insights(*, tenant_id: int, uow: Any, window_days: int = 30) -> dict[str, Any]:
    trend_payload = get_tenant_product_kpi_trends(
        tenant_id=int(tenant_id),
        uow=uow,
        window_days=window_days,
    )
    trends = list(trend_payload.get("trends") or [])

    if not trends:
        return {
            "tenant_id": int(tenant_id),
            "window_days": int(trend_payload.get("window_days") or 30),
            "snapshot_date": None,
            "generated_at": None,
            "insights": [],
        }

    insights: list[dict[str, Any]] = []
    for trend in trends:
        insight = _build_insight_from_trend_row(trend)
        insights.append(insight)

    return {
        "tenant_id": int(tenant_id),
        "window_days": int(trend_payload.get("window_days") or 30),
        "snapshot_date": trend_payload.get("snapshot_date"),
        "generated_at": trend_payload.get("generated_at"),
        "insights": insights,
    }


def get_tenant_product_kpi_recommendations(*, tenant_id: int, uow: Any, window_days: int = 30) -> dict[str, Any]:
    insight_payload = get_tenant_product_kpi_insights(
        tenant_id=int(tenant_id),
        uow=uow,
        window_days=window_days,
    )
    insights = list(insight_payload.get("insights") or [])

    if not insights:
        return {
            "tenant_id": int(tenant_id),
            "window_days": int(insight_payload.get("window_days") or 30),
            "snapshot_date": None,
            "generated_at": None,
            "recommendations": [],
        }

    recommendations: list[dict[str, Any]] = []
    for insight in insights:
        recommendations.append(_build_recommendation_from_insight_row(insight))

    return {
        "tenant_id": int(tenant_id),
        "window_days": int(insight_payload.get("window_days") or 30),
        "snapshot_date": insight_payload.get("snapshot_date"),
        "generated_at": insight_payload.get("generated_at"),
        "recommendations": recommendations,
    }


def get_rector_dashboard(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)

    latest = repo.get_latest_dashboard_snapshot(tenant_id=int(tenant_id), conn=conn)
    if latest is None:
        latest = refresh_tenant_dashboard_snapshot(tenant_id=int(tenant_id), uow=uow)

    dashboard = dict(latest.get("snapshot_json") or {})
    if not dashboard:
        dashboard = {
            "tenant_id": int(tenant_id),
            "snapshot_date": str(latest["snapshot_date"]),
            "cards": [],
            "generated_at": latest.get("updated_at"),
            "source": "kpi_metrics_engine_v1",
        }

    # Attach evidence drilldowns if not already present in the snapshot payload
    if "drilldowns" not in dashboard:
        dashboard["drilldowns"] = _build_rector_kpi_evidence_drilldowns(
            cards=list(dashboard.get("cards") or [])
        )

    return dashboard


def get_rector_kpi_drilldown(*, tenant_id: int, uow: Any) -> dict[str, Any]:
    """Return read-only evidence drilldown summary for the rector KPI dashboard.

    Constraints:
    - Read-only: no DB mutation, no policy enforcement, no autonomous decision.
    - Tenant-scoped: tenant_id > 0 required; fail-closed on invalid input.
    - Deterministic: output derived solely from existing KPI metric snapshots.
    - Evidence completeness surfaced explicitly; unavailable metrics flagged as
      such rather than synthesised.
    """
    if int(tenant_id) <= 0:
        raise ValueError(f"tenant_id must be positive; got {tenant_id!r}")

    repo = uow.kpi_repository
    conn = getattr(uow, "conn", None)

    latest = repo.get_latest_dashboard_snapshot(tenant_id=int(tenant_id), conn=conn)
    if latest is None:
        latest = refresh_tenant_dashboard_snapshot(tenant_id=int(tenant_id), uow=uow)

    snapshot = dict(latest.get("snapshot_json") or {})
    cards: list[dict[str, Any]] = list(snapshot.get("cards") or [])

    drilldowns = _build_rector_kpi_evidence_drilldowns(cards=cards)

    total_domains = len(drilldowns)
    review_required_count = sum(1 for d in drilldowns if d.get("review_required"))
    unavailable_count = sum(1 for d in drilldowns if d.get("risk_level") == "unavailable")
    critical_count = sum(1 for d in drilldowns if d.get("risk_level") == "critical")
    high_count = sum(1 for d in drilldowns if d.get("risk_level") == "high")

    return {
        "tenant_id": int(tenant_id),
        "snapshot_date": str(snapshot.get("snapshot_date") or latest.get("snapshot_date") or ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "domains": drilldowns,
        "total_domains": total_domains,
        "review_required_count": review_required_count,
        "unavailable_domains_count": unavailable_count,
        "critical_domains_count": critical_count,
        "high_domains_count": high_count,
        "source": "kpi_metrics_engine_v1",
        "readonly": True,
        "tenant_scoped": True,
        "no_policy_enforcement": True,
        "no_autonomous_decision": True,
        "no_remediation_action": True,
    }


def refresh_all_tenants(*, uow: Any) -> dict[str, int]:
    conn = getattr(uow, "conn", None)
    tenants = uow.tenant_repository.list_tenant_profiles(conn=conn)

    refreshed = 0
    failed = 0
    for tenant in tenants:
        tenant_id = int(tenant["tenant_id"])
        try:
            refresh_tenant_dashboard_snapshot(tenant_id=tenant_id, uow=uow)
            refreshed += 1
        except Exception:
            failed += 1
    return {"tenants_total": len(tenants), "refreshed": refreshed, "failed": failed}


def _metric_key_to_event(metric_key: str) -> str:
    for event_type, key in EVENT_METRIC_MAP.items():
        if key == metric_key:
            return event_type
    return ""


def _freshness_status(*, snapshot_date: str | None, generated_at: str | None) -> str:
    if snapshot_date and generated_at:
        return "ready"
    return "partial_metadata"


def _card_source_status(*, metric_key: str, lineage: Any) -> str:
    if isinstance(lineage, dict) and str(lineage.get("source_type") or "").strip().lower() == "platform_events":
        return "derived_from_events"
    if str(metric_key).strip().lower() in USAGE_DERIVED_METRICS:
        return "derived_from_usage"
    return "derived_from_snapshot"


def _response_source_mode(cards: list[dict[str, Any]]) -> str:
    source_markers = {
        str(card.get("source_status") or "").strip().lower()
        for card in cards
        if str(card.get("source_status") or "").strip()
    }
    if not source_markers:
        return "empty"
    if len(source_markers) == 1:
        marker = next(iter(source_markers))
        if marker == "derived_from_events":
            return "derived_from_events"
        if marker == "derived_from_usage":
            return "derived_from_usage"
        return "derived_from_snapshot"
    return "mixed_source"


RECTOR_KPI_EVIDENCE_DRILLDOWN_CONFIG: list[dict[str, Any]] = [
    {
        "domain_id": "academic-governance",
        "domain_title": "Academic Governance",
        "title": "Academic governance evidence contract",
        "metric_keys": [
            "academic_integrity_high_risk_count",
            "academic_integrity_cases_pending_review",
            "exam_integrity_requires_approval_count",
            "thesis_governance_requires_approval_count",
            "research_ethics_requires_approval_count",
        ],
        "critical_metric_keys": ["academic_integrity_high_risk_count"],
        "high_metric_keys": ["exam_integrity_requires_approval_count"],
        "medium_metric_keys": ["thesis_governance_requires_approval_count", "research_ethics_requires_approval_count"],
        "review_metric_keys": [
            "academic_integrity_cases_pending_review",
            "exam_integrity_requires_approval_count",
            "thesis_governance_requires_approval_count",
            "research_ethics_requires_approval_count",
        ],
        "source_domains": ["Academic Integrity", "Exam Governance", "Thesis", "Research Ethics"],
        "explanation": "Academic governance signals require human review and are evidence-backed; no automatic disciplinary action is executed.",
        "data_quality_note": "Missing integrity/governance metrics are shown as unavailable instead of inferred.",
    },
    {
        "domain_id": "finance-procurement-assets",
        "domain_title": "Finance / Procurement / Assets",
        "title": "Finance and procurement evidence contract",
        "metric_keys": [
            "budget_overrun_risk_count",
            "budget_review_actions_count",
            "active_finance_risk_signals_count",
            "asset_conversion_gap_count",
            "procurement_requests_pending_approval",
        ],
        "critical_metric_keys": ["budget_overrun_risk_count"],
        "high_metric_keys": ["active_finance_risk_signals_count", "asset_conversion_gap_count"],
        "medium_metric_keys": ["budget_review_actions_count"],
        "review_metric_keys": ["budget_review_actions_count"],
        "source_domains": ["Finance", "Procurement", "Assets"],
        "explanation": "Finance and procurement signals are governance review indicators only; no automatic approval is executed.",
        "data_quality_note": "Source lineage remains limited to available tenant KPI metrics.",
    },
    {
        "domain_id": "campus-operations",
        "domain_title": "Campus Operations",
        "title": "Campus operations evidence contract",
        "metric_keys": [
            "scheduling_conflicts_count",
            "room_conflict_count",
            "capacity_risk_sections_count",
            "events_cancelled_count",
        ],
        "critical_metric_keys": ["capacity_risk_sections_count"],
        "high_metric_keys": ["scheduling_conflicts_count", "room_conflict_count"],
        "medium_metric_keys": ["events_cancelled_count"],
        "review_metric_keys": [],
        "source_domains": ["Scheduling", "Events", "Operations"],
        "explanation": "Campus operations signals summarize operational pressure and require operator review.",
        "data_quality_note": "Operational evidence is read-only and may be partial depending on tenant instrumentation.",
    },
    {
        "domain_id": "security-visitor-operations",
        "domain_title": "Security / Visitor Operations",
        "title": "Security and visitor evidence contract",
        "metric_keys": [
            "security_incident_review_required_count",
            "security_high_risk_incidents_count",
            "visitor_unauthorized_attempts_count",
            "access_denied_count",
        ],
        "critical_metric_keys": ["security_high_risk_incidents_count"],
        "high_metric_keys": ["security_incident_review_required_count"],
        "medium_metric_keys": ["visitor_unauthorized_attempts_count", "access_denied_count"],
        "review_metric_keys": ["security_incident_review_required_count", "visitor_unauthorized_attempts_count"],
        "source_domains": ["Security Operations", "Visitor Management", "Access Control"],
        "explanation": "Security signals are review/escalation evidence only; no automatic lockout or ban is executed.",
        "data_quality_note": "Unavailable security metrics are surfaced explicitly with no synthetic fallback.",
    },
    {
        "domain_id": "room-allocation-scheduling-intelligence",
        "domain_title": "Room Allocation / Scheduling Intelligence",
        "title": "Room allocation evidence contract",
        "metric_keys": [
            "room_allocation_review_required_count",
            "room_allocation_no_viable_candidate_count",
            "room_allocation_recommendations_count",
            "room_capacity_mismatch_count",
            "room_conflict_count",
        ],
        "critical_metric_keys": ["room_allocation_no_viable_candidate_count"],
        "high_metric_keys": ["room_capacity_mismatch_count", "room_conflict_count"],
        "medium_metric_keys": ["room_allocation_review_required_count"],
        "review_metric_keys": ["room_allocation_review_required_count"],
        "source_domains": ["Room Allocation", "Scheduling"],
        "explanation": "Room allocation recommendation evidence is advisory-only and requires human review for risk cases.",
        "data_quality_note": "No automatic room assignment or schedule mutation is available from this surface.",
    },
    {
        "domain_id": "brain-review-required",
        "domain_title": "Brain / Review Required",
        "title": "Brain review-required evidence contract",
        "metric_keys": [
            "academic_integrity_cases_pending_review",
            "exam_integrity_requires_approval_count",
            "thesis_governance_requires_approval_count",
            "research_ethics_requires_approval_count",
            "security_incident_review_required_count",
            "budget_review_actions_count",
        ],
        "critical_metric_keys": [],
        "high_metric_keys": ["security_incident_review_required_count"],
        "medium_metric_keys": [
            "academic_integrity_cases_pending_review",
            "exam_integrity_requires_approval_count",
            "thesis_governance_requires_approval_count",
            "research_ethics_requires_approval_count",
            "budget_review_actions_count",
        ],
        "review_metric_keys": [
            "academic_integrity_cases_pending_review",
            "exam_integrity_requires_approval_count",
            "thesis_governance_requires_approval_count",
            "research_ethics_requires_approval_count",
            "security_incident_review_required_count",
            "budget_review_actions_count",
        ],
        "source_domains": ["Brain Core", "Governance Review"],
        "explanation": "Brain signals are advisory and evidence-backed; decision authority remains with humans.",
        "data_quality_note": "Review-required entries always require explicit human closure.",
    },
    {
        "domain_id": "student-risk-interventions",
        "domain_title": "Student Risk / Interventions",
        "title": "Student intervention evidence contract",
        "metric_keys": ["critical_risk_students_count", "high_risk_students_count", "intervention_auto_created_count"],
        "critical_metric_keys": ["critical_risk_students_count"],
        "high_metric_keys": ["high_risk_students_count"],
        "medium_metric_keys": ["intervention_auto_created_count"],
        "review_metric_keys": [],
        "source_domains": ["Student Success", "Interventions"],
        "explanation": "Student-risk evidence supports human intervention prioritization.",
        "data_quality_note": "Optional domain; may be unavailable in tenants without intervention telemetry.",
        "optional": True,
    },
    {
        "domain_id": "research-accreditation-quality",
        "domain_title": "Research / Accreditation / Quality",
        "title": "Research and quality evidence contract",
        "metric_keys": ["research_ethics_high_risk_count", "research_ethics_review_cases_count", "research_ethics_requires_approval_count", "thesis_governance_risk_count"],
        "critical_metric_keys": ["research_ethics_high_risk_count"],
        "high_metric_keys": ["thesis_governance_risk_count"],
        "medium_metric_keys": ["research_ethics_requires_approval_count", "research_ethics_review_cases_count"],
        "review_metric_keys": ["research_ethics_requires_approval_count"],
        "source_domains": ["Research Ethics", "Accreditation", "Quality"],
        "explanation": "Research and quality evidence highlights review pressure and remains advisory-only.",
        "data_quality_note": "Optional domain; unavailable state is explicit when metrics are missing.",
        "optional": True,
    },
]


def _build_rector_kpi_evidence_drilldowns(*, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    card_by_metric_key = {
        str(card.get("metric_key") or "").strip().lower(): dict(card)
        for card in cards
        if str(card.get("metric_key") or "").strip()
    }

    def _read_metric_value(metric_key: str) -> int | None:
        card = card_by_metric_key.get(metric_key)
        if card is None:
            return None
        value = card.get("value")
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return None

    def _has_positive_value(metric_keys: list[str]) -> bool:
        return any((value := _read_metric_value(metric_key)) is not None and value > 0 for metric_key in metric_keys)

    drilldowns: list[dict[str, Any]] = []
    for config in RECTOR_KPI_EVIDENCE_DRILLDOWN_CONFIG:
        metric_keys = [str(metric_key) for metric_key in config["metric_keys"]]
        available_metric_keys = [metric_key for metric_key in metric_keys if metric_key in card_by_metric_key]
        has_evidence = bool(available_metric_keys)

        if not has_evidence:
            risk_level = "unavailable"
        elif _has_positive_value(list(config["critical_metric_keys"])):
            risk_level = "critical"
        elif _has_positive_value(list(config["high_metric_keys"])):
            risk_level = "high"
        elif _has_positive_value(list(config["medium_metric_keys"])) or _has_positive_value(list(config["review_metric_keys"])):
            risk_level = "medium"
        else:
            risk_level = "low"

        review_required = has_evidence and (
            _has_positive_value(list(config["review_metric_keys"]))
            or _has_positive_value(list(config["high_metric_keys"]))
            or _has_positive_value(list(config["critical_metric_keys"]))
        )

        evidence_sources: list[dict[str, Any]] = []
        for metric_key in metric_keys[:4]:
            card = card_by_metric_key.get(metric_key)
            value = _read_metric_value(metric_key)
            lineage = dict((card or {}).get("metadata_json") or {}).get("lineage")
            source_domain = config["source_domains"][0] if config["source_domains"] else config["domain_title"]
            evidence_sources.append(
                {
                    "metric_key": metric_key,
                    "label": str((card or {}).get("title") or metric_key),
                    "value_label": "Unavailable" if value is None else f"{value:,}",
                    "source_domain": source_domain,
                    "interpretation": (
                        "Evidence unavailable in current tenant snapshot."
                        if value is None
                        else "Evidence supports visibility of this KPI/risk/alert."
                        if value > 0
                        else "Evidence available with no elevated signal."
                    ),
                    "available": value is not None,
                    "lineage": lineage,
                }
            )

        positive_evidence_summary = " | ".join(
            [
                f"{source['label']}: {source['value_label']}"
                for source in evidence_sources
                if source["available"] and source["value_label"] != "0"
            ][:3]
        )
        evidence_summary = (
            positive_evidence_summary
            if positive_evidence_summary
            else "Evidence-backed metrics are present with no elevated value in this snapshot."
            if has_evidence
            else "Evidence unavailable in current tenant snapshot."
        )

        drilldowns.append(
            {
                "drilldown_id": f"kpi-evidence-{config['domain_id']}",
                "title": config["title"],
                "domain_id": config["domain_id"],
                "domain_title": config["domain_title"],
                "source_metrics": available_metric_keys,
                "source_domains": list(config["source_domains"]),
                "evidence_summary": evidence_summary,
                "explanation": config["explanation"],
                "risk_level": risk_level,
                "review_required": review_required,
                "data_quality_note": config["data_quality_note"],
                "readonly": True,
                "tenant_scoped": True,
                "optional": bool(config.get("optional", False)),
                "evidence_sources": evidence_sources,
            }
        )

    return drilldowns


# ---------------------------------------------------------------------------
# KPI threshold / severity rules v1
# ---------------------------------------------------------------------------
# KPI_SEVERITY_RULES: metric_key → {basis, semantics}
# count  → warning_gte / critical_gte thresholds on raw value
# percent → warning when value <= low_warning OR value >= high_warning
# ---------------------------------------------------------------------------

KPI_SEVERITY_RULES: dict[str, dict[str, Any]] = {
    "total_failed_jobs": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "default_ops_v1",
    },
    "total_failed_notifications": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "default_ops_v1",
    },
    "analytics_kpi_reads_share_pct": {
        "basis": "percentage",
        # <20% → adoption too low; >80% → KPI reads dominate heavily
        "low_warning_lte": 20,
        "high_warning_gte": 80,
        "policy_pack": "analytics_adoption_v1",
    },
    "high_risk_students_count": {
        "basis": "count",
        "warning_gte": 10,
        "critical_gte": 25,
        "policy_pack": "student_success_wave1_v1",
    },
    "critical_risk_students_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "early_warning_wave1_v1",
    },
    "delinquency_cases_active": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 10,
        "policy_pack": "finance_delinquency_wave1_v1",
    },
    "scheduling_conflicts_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "scheduling_wave1_v1",
    },
    "capacity_risk_sections_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "scheduling_wave1_v1",
    },
    # A-014.6 Wave 2 severity rules
    "grade_decline_risk_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 10,
        "policy_pack": "academic_risk_wave2_v1",
    },
    "grade_intervention_cases_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 10,
        "policy_pack": "academic_risk_wave2_v1",
    },
    "thesis_completion_risk_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "thesis_risk_wave2_v1",
    },
    "thesis_intervention_cases_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "thesis_risk_wave2_v1",
    },
    "attendance_recovery_actions_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 10,
        "policy_pack": "attendance_recovery_wave2_v1",
    },
    "graduation_risk_students_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "graduation_risk_wave2_v1",
    },
    "degree_progress_intervention_cases_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "graduation_risk_wave2_v1",
    },
    "scholarship_risk_cases_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "scholarship_risk_wave2_v1",
    },
    "financial_aid_risk_cases_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "financial_aid_risk_wave2_v1",
    },
    # A-015.6 Wave 3 severity rules — Budget
    "budget_overrun_risk_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "budget_risk_wave3_v1",
    },
    "budget_review_actions_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "budget_risk_wave3_v1",
    },
    # A-015.6 Wave 3 severity rules — Finance Operations
    "active_finance_risk_signals_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "finance_risk_wave3_v1",
    },
    "finance_operations_actionability_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "finance_risk_wave3_v1",
    },
    # A-015.6 Wave 3 severity rules — Asset Chain
    "asset_conversion_gap_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "asset_chain_wave3_v1",
    },
    # A-015.6 Wave 3 severity rules — Inventory / Supply
    "inventory_low_stock_items_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "supply_risk_wave3_v1",
    },
    "critical_supply_risk_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 3,
        "policy_pack": "supply_risk_wave3_v1",
    },
    "reorder_recommendations_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 10,
        "policy_pack": "supply_risk_wave3_v1",
    },
    "supply_risk_actions_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "supply_risk_wave3_v1",
    },
    # A-016.6 Wave 4 severity rules — Academic Integrity
    "academic_integrity_risk_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "academic_integrity_wave4_v1",
    },
    "academic_integrity_high_risk_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 3,
        "policy_pack": "academic_integrity_wave4_v1",
    },
    "academic_integrity_cases_pending_review": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "academic_integrity_wave4_v1",
    },
    # A-016.6 Wave 4 severity rules — Exam Proctoring
    "exam_proctoring_violations_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "exam_integrity_wave4_v1",
    },
    "exam_integrity_high_risk_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 3,
        "policy_pack": "exam_integrity_wave4_v1",
    },
    "exam_integrity_requires_approval_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "exam_integrity_wave4_v1",
    },
    # A-016.6 Wave 4 severity rules — Thesis Governance
    "thesis_governance_risk_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "thesis_governance_wave4_v1",
    },
    "thesis_supervisor_assignment_needed_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "thesis_governance_wave4_v1",
    },
    "thesis_review_delayed_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "thesis_governance_wave4_v1",
    },
    "thesis_governance_requires_approval_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 3,
        "policy_pack": "thesis_governance_wave4_v1",
    },
    # A-016.6 Wave 4 severity rules — Research Ethics / Compliance
    "research_ethics_review_cases_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "research_ethics_wave4_v1",
    },
    "research_ethics_high_risk_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 3,
        "policy_pack": "research_ethics_wave4_v1",
    },
    "research_ethics_missing_documents_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "research_ethics_wave4_v1",
    },
    "research_ethics_requires_approval_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 3,
        "policy_pack": "research_ethics_wave4_v1",
    },
    # A-016.6 Wave 4 severity rules — Case Resolution
    "integrity_cases_open_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 10,
        "policy_pack": "case_resolution_wave4_v1",
    },
    "integrity_cases_escalated_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 5,
        "policy_pack": "case_resolution_wave4_v1",
    },
    "integrity_case_resolution_sla_risk_count": {
        "basis": "count",
        "warning_gte": 1,
        "critical_gte": 3,
        "policy_pack": "case_resolution_wave4_v1",
    },
}


def _severity_for_metric(metric_key: str, value: int) -> tuple[str | None, str | None, str | None]:
    """Return (severity, threshold_basis, policy_pack) for a KPI card.

    Returns (None, None, None) for KPI without a threshold rule.
    Possible severity values: 'normal' | 'warning' | 'critical' | 'no_data'
    policy_pack is the named evaluation profile that produced the severity.
    """
    rule = KPI_SEVERITY_RULES.get(str(metric_key).strip().lower())
    if rule is None:
        return None, None, None

    basis = str(rule["basis"])
    policy_pack: str | None = rule.get("policy_pack")  # type: ignore[assignment]

    if basis == "count":
        v = int(value)
        if v >= int(rule["critical_gte"]):
            return "critical", basis, policy_pack
        if v >= int(rule["warning_gte"]):
            return "warning", basis, policy_pack
        return "normal", basis, policy_pack

    if basis == "percentage":
        v = int(value)
        if v == 0:
            return "no_data", basis, policy_pack
        if v <= int(rule["low_warning_lte"]) or v >= int(rule["high_warning_gte"]):
            return "warning", basis, policy_pack
        return "normal", basis, policy_pack

    return None, None, None


# ---------------------------------------------------------------------------
# KPI actionability state / escalation readiness v1
# ---------------------------------------------------------------------------
# Derived purely from severity — no additional rule duplication.
# severity → actionability_state:
#   critical  → act_now
#   warning   → review
#   normal    → observe
#   no_data   → no_action
#   None      → None  (non-thresholded KPI; no urgency semantics applicable)
# ---------------------------------------------------------------------------

_SEVERITY_TO_ACTIONABILITY: dict[str, str] = {
    "critical": "act_now",
    "warning": "review",
    "normal": "observe",
    "no_data": "no_action",
}


def _actionability_for_severity(severity: str | None) -> str | None:
    """Map pre-computed severity to bounded actionability_state.

    Returns None for non-thresholded KPI (severity is None).
    """
    if severity is None:
        return None
    return _SEVERITY_TO_ACTIONABILITY.get(str(severity).strip().lower())


def _build_kpi_portfolio_summary(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate already-computed card signals into a bounded portfolio overview."""
    severity_counts = {
        "normal": 0,
        "warning": 0,
        "critical": 0,
        "no_data": 0,
    }
    actionability_counts = {
        "no_action": 0,
        "observe": 0,
        "review": 0,
        "act_now": 0,
    }

    for card in cards:
        sev = str(card.get("severity") or "").strip().lower()
        if sev in severity_counts:
            severity_counts[sev] += 1

        action_state = str(card.get("actionability_state") or "").strip().lower()
        if action_state in actionability_counts:
            actionability_counts[action_state] += 1

    overall_status = "healthy"
    if severity_counts["critical"] > 0:
        overall_status = "urgent"
    elif severity_counts["warning"] > 0:
        overall_status = "attention_needed"

    return {
        "total_kpis": len(cards),
        "severity_counts": severity_counts,
        "actionability_counts": actionability_counts,
        "overall_portfolio_status": overall_status,
    }


def _build_kpi_change_digest(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate bounded change direction from existing card trend points.

    Uses only card-level trend data already assembled in get_tenant_product_kpis.
    """
    change_counts = {
        "improved": 0,
        "declined": 0,
        "unchanged": 0,
        "no_data": 0,
    }

    for card in cards:
        points = list(card.get("trend") or [])
        if len(points) < 2:
            change_counts["no_data"] += 1
            continue

        latest = int(points[-1].get("value") or 0)
        previous = int(points[-2].get("value") or 0)
        delta = latest - previous
        if delta > 0:
            change_counts["improved"] += 1
        elif delta < 0:
            change_counts["declined"] += 1
        else:
            change_counts["unchanged"] += 1

    total = len(cards)
    if total == 0 or change_counts["no_data"] == total:
        direction = "no_data"
    elif change_counts["improved"] > change_counts["declined"]:
        direction = "improving"
    elif change_counts["declined"] > change_counts["improved"]:
        direction = "declining"
    else:
        direction = "stable"

    return {
        "total_kpis": total,
        "change_counts": change_counts,
        "overall_change_direction": direction,
    }


def _build_kpi_source_mix_summary(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate portfolio source composition from already-computed card source_status."""
    source_mix_counts = {
        "derived_from_events": 0,
        "derived_from_usage": 0,
        "derived_from_snapshot": 0,
        "mixed_source": 0,
        "empty": 0,
    }

    for card in cards:
        status = str(card.get("source_status") or "").strip().lower()
        if status in {"derived_from_events", "derived_from_usage", "derived_from_snapshot"}:
            source_mix_counts[status] += 1
        elif status:
            source_mix_counts["mixed_source"] += 1
        else:
            source_mix_counts["empty"] += 1

    total = len(cards)
    if total == 0:
        dominant_source_mode = "empty"
    else:
        mode_candidates = {
            "events": source_mix_counts["derived_from_events"],
            "usage": source_mix_counts["derived_from_usage"],
            "snapshot": source_mix_counts["derived_from_snapshot"],
            "mixed": source_mix_counts["mixed_source"],
        }
        top_count = max(mode_candidates.values())
        top_modes = [mode for mode, count in mode_candidates.items() if count == top_count]
        dominant_source_mode = top_modes[0] if len(top_modes) == 1 and top_count > 0 else "mixed"

    return {
        "total_kpis": total,
        "source_mix_counts": source_mix_counts,
        "dominant_source_mode": dominant_source_mode,
    }


def _build_kpi_sections_manifest(
    *,
    cards: list[dict[str, Any]],
    summary: dict[str, Any] | None,
    change_digest: dict[str, Any] | None,
    source_mix_summary: dict[str, Any] | None,
    capabilities: dict[str, Any] | None,
    surface_id: str | None,
    contract_version: str | None,
    surface_profile: dict[str, Any] | None,
    field_semantics: dict[str, Any] | None,
    card_field_semantics: dict[str, Any] | None,
    response_examples: dict[str, Any] | None,
    surface_map: dict[str, Any] | None,
    workflow_hints: dict[str, Any] | None,
    stability_tiers: dict[str, Any] | None,
    contract_fingerprint: dict[str, Any] | None,
    contract_compatibility: dict[str, Any] | None,
) -> dict[str, str]:
    """Describe section presence/content for the current KPI payload."""

    summary_total = int((summary or {}).get("total_kpis") or 0)
    change_total = int((change_digest or {}).get("total_kpis") or 0)
    source_mix_total = int((source_mix_summary or {}).get("total_kpis") or 0)

    return {
        "cards": "populated" if len(cards) > 0 else "empty",
        "summary": "populated" if summary_total > 0 else "present",
        "change_digest": "populated" if change_total > 0 else "present",
        "source_mix_summary": "populated" if source_mix_total > 0 else "present",
        "capabilities": "present" if isinstance(capabilities, dict) and len(capabilities) > 0 else "empty",
        "contract_identity": "present" if surface_id and contract_version else "empty",
        "surface_profile": "present" if isinstance(surface_profile, dict) and len(surface_profile) > 0 else "empty",
        "field_semantics": "present" if isinstance(field_semantics, dict) and len(field_semantics) > 0 else "empty",
        "card_field_semantics": "present" if isinstance(card_field_semantics, dict) and len(card_field_semantics) > 0 else "empty",
        "response_examples": "present" if isinstance(response_examples, dict) and len(response_examples) > 0 else "empty",
        "surface_map": "present" if isinstance(surface_map, dict) and len(surface_map) > 0 else "empty",
        "workflow_hints": "present" if isinstance(workflow_hints, dict) and len(workflow_hints) > 0 else "empty",
        "stability_tiers": "present" if isinstance(stability_tiers, dict) and len(stability_tiers) > 0 else "empty",
        "contract_fingerprint": "present"
        if isinstance(contract_fingerprint, dict) and len(contract_fingerprint) > 0
        else "empty",
        "contract_compatibility": "present"
        if isinstance(contract_compatibility, dict) and len(contract_compatibility) > 0
        else "empty",
        "contract_invariants": "present",
    }


def _build_insight_from_trend_row(trend: dict[str, Any]) -> dict[str, Any]:
    metric_key = str(trend.get("key") or "").strip().lower()
    title = str(trend.get("title") or metric_key)
    latest_value = int(trend.get("latest_value") or 0)
    delta_raw = trend.get("delta")
    delta = int(delta_raw) if delta_raw is not None else None
    points = list(trend.get("points") or [])

    insight_type = "no_data"
    summary = f"{title}: no recent data available."

    if metric_key == "analytics_kpi_reads_share_pct" and points:
        if latest_value >= 70:
            insight_type = "high_share"
            summary = f"{title} is high at {latest_value}% in the latest snapshot."
        elif latest_value <= 30:
            insight_type = "low_share"
            summary = f"{title} is low at {latest_value}% in the latest snapshot."
        elif delta is None or delta == 0:
            insight_type = "no_change"
            summary = f"{title} is stable at {latest_value}% across the selected window."
        elif delta > 0:
            insight_type = "growth"
            summary = f"{title} increased by {delta} points to {latest_value}%."
        else:
            insight_type = "decline"
            summary = f"{title} decreased by {abs(delta)} points to {latest_value}%."
    elif points:
        if delta is None:
            insight_type = "no_data"
            summary = f"{title} has only one snapshot in the selected window."
        elif delta > 0:
            insight_type = "growth"
            summary = f"{title} increased by {delta} in the selected window."
        elif delta < 0:
            insight_type = "decline"
            summary = f"{title} decreased by {abs(delta)} in the selected window."
        else:
            insight_type = "no_change"
            summary = f"{title} remained unchanged in the selected window."

    return {
        "key": metric_key,
        "title": title,
        "type": insight_type,
        "summary": summary,
        "value": latest_value,
        "delta": delta,
    }


def _build_recommendation_from_insight_row(insight: dict[str, Any]) -> dict[str, Any]:
    metric_key = str(insight.get("key") or "").strip().lower()
    title = str(insight.get("title") or metric_key)
    insight_type = str(insight.get("type") or "no_data").strip().lower()

    recommendation_type = "no_action"
    priority = "low"
    summary = f"No immediate action required for {title.lower()}."

    if insight_type == "decline":
        recommendation_type = "investigate_decline"
        priority = "high"
        summary = f"Investigate recent decline in {title.lower()} and identify the main contributing factor."
    elif insight_type == "growth":
        recommendation_type = "sustain_growth"
        priority = "medium"
        summary = f"Sustain momentum in {title.lower()} by reinforcing the latest effective workflow."
    elif insight_type == "no_change":
        recommendation_type = "monitor_stability"
        priority = "low"
        summary = f"Monitor {title.lower()} and keep the current operating pattern stable."
    elif insight_type == "low_share" and metric_key == "analytics_kpi_reads_share_pct":
        recommendation_type = "increase_adoption"
        priority = "medium"
        summary = "Increase KPI usage adoption to raise the KPI share of analytics reads."
    elif insight_type == "high_share" and metric_key == "analytics_kpi_reads_share_pct":
        recommendation_type = "rebalance_usage"
        priority = "medium"
        summary = "Rebalance KPI and event-level reads to keep analytics usage aligned across workflows."

    return {
        "key": metric_key,
        "title": title,
        "type": recommendation_type,
        "priority": priority,
        "summary": summary,
        "based_on": insight_type,
    }
