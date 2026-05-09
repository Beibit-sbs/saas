from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, ValidationError

from app.platform.events.schemas import (
    EnrollmentCreatedEventPayload,
    GradeSubmittedEventPayload,
    IntegrationUpdatedEventPayload,
    StudentCreatedEventPayload,
    TenantCreatedEventPayload,
)


class EventRegistryError(ValueError):
    pass


class AIChatExecutedEventPayload(BaseModel):
    model: str

    model_config = ConfigDict(extra="allow")


class GenericTenantEventPayload(BaseModel):
    model_config = ConfigDict(extra="allow")


class AutomationChainEventPayload(BaseModel):
    automation_action: str
    source_event_type: str
    source_aggregate_id: str
    event_payload: dict

    model_config = ConfigDict(extra="allow")


@dataclass(frozen=True)
class EventDefinition:
    payload_model: type[BaseModel]
    tenant_aware: bool = True


EXACT_EVENT_REGISTRY: dict[str, EventDefinition] = {
    "tenant.created": EventDefinition(TenantCreatedEventPayload),
    "student.created": EventDefinition(StudentCreatedEventPayload),
    "enrollment.created": EventDefinition(EnrollmentCreatedEventPayload),
    "grade.submitted": EventDefinition(GradeSubmittedEventPayload),
    "user.created": EventDefinition(GenericTenantEventPayload),
    "role.assigned": EventDefinition(GenericTenantEventPayload),
    "ai.chat.executed": EventDefinition(AIChatExecutedEventPayload),
    "integration.updated": EventDefinition(IntegrationUpdatedEventPayload),
    "workflow.approved": EventDefinition(GenericTenantEventPayload),
    "file.uploaded": EventDefinition(GenericTenantEventPayload),
    "course.completed": EventDefinition(GenericTenantEventPayload),
    # Admissions workflow events
    "admissions.application.submitted": EventDefinition(GenericTenantEventPayload),
    "admissions.application.stage_changed": EventDefinition(GenericTenantEventPayload),
    "admissions.application.decision_made": EventDefinition(GenericTenantEventPayload),
    "admissions.application.workflow_decision_finalized": EventDefinition(GenericTenantEventPayload),
    # Academic chain cross-domain events (Contour v1)
    "thesis.status_changed": EventDefinition(GenericTenantEventPayload),
    "accreditation.status_changed": EventDefinition(GenericTenantEventPayload),
    "academic.attendance_risk.detected": EventDefinition(GenericTenantEventPayload),
    "academic.grade_risk.detected": EventDefinition(GenericTenantEventPayload),
    "faculty.workload_overload.detected": EventDefinition(GenericTenantEventPayload),
    "faculty.quality_drop.detected": EventDefinition(GenericTenantEventPayload),
    "finance.payment_overdue.detected": EventDefinition(GenericTenantEventPayload),
    "financial_aid.warning.detected": EventDefinition(GenericTenantEventPayload),
    "housing.status.risk_detected": EventDefinition(GenericTenantEventPayload),
    "platform.integration.degraded": EventDefinition(GenericTenantEventPayload),
    # Research & Innovation cross-domain events (Contour v2)
    "research.grant_deadline.approaching": EventDefinition(GenericTenantEventPayload),
    "research.publication_stagnant": EventDefinition(GenericTenantEventPayload),
    # Student Services module events
    "student_services.ticket.escalated": EventDefinition(GenericTenantEventPayload),
    "campus.student_services.ticket_unresolved_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Career Services module events
    "campus.career_services.opportunity_stalled_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Interventions module events
    "interventions.case.created": EventDefinition(GenericTenantEventPayload),
    "interventions.case.status_changed": EventDefinition(GenericTenantEventPayload),
    "interventions.case_outcome.recorded": EventDefinition(GenericTenantEventPayload),
    # Campus SLA module events
    "campus.sla.breach_detected": EventDefinition(GenericTenantEventPayload),
    # Equipment booking module events
    "research.equipment.booking_conflict_detected": EventDefinition(GenericTenantEventPayload),
    # Scholarship module events
    "scholarship.award.at_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Faculty Performance KPI module events (Phase X)
    "faculty_performance.kpi.warning_detected": EventDefinition(GenericTenantEventPayload),
    # HR/Payroll module events (Phase X)
    "hr.employee.offboarding_initiated": EventDefinition(GenericTenantEventPayload),
    "collections.delinquency.critical_overdue": EventDefinition(GenericTenantEventPayload),
    # Facilities Work Orders module events (Phase XI)
    "facilities.work_order.critical_priority": EventDefinition(GenericTenantEventPayload),
    "campus.facilities.work_order_overdue_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Asset Inventory module events (Phase XI)
    "asset_inventory.item.condemned_asset": EventDefinition(GenericTenantEventPayload),
    "campus.asset_inventory.condemned_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Student Life module events (Phase XI / W57)
    "campus.student_life.disciplinary_escalation_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Alumni module events (W58)
    "campus.alumni.disengagement_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Campus SLA module events (W59)
    "campus.campus_sla.breach_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Communications module events (W60)
    "campus.communications.broadcast_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Security Operations module events (Phase XI)
    "campus.security_incident.detected": EventDefinition(GenericTenantEventPayload),
    # Dining module events (Phase XI)
    "campus.dining.capacity_exceeded": EventDefinition(GenericTenantEventPayload),
    # Expense Controls module events (W62)
    "campus.expense_controls.budget_exceeded_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Transport module events (Phase XI)
    "campus.transport.disruption_detected": EventDefinition(GenericTenantEventPayload),
    # IP management module events (W31)
    "campus.ip_management.asset_commercialized": EventDefinition(GenericTenantEventPayload),
    # Student life module events (W32)
    "campus.student_life.serious_concern_detected": EventDefinition(GenericTenantEventPayload),
    # Research ethics module events (W33)
    "campus.research_ethics.high_risk_flagged": EventDefinition(GenericTenantEventPayload),
    # Procurement module events (W34)
    "campus.procurement.high_risk_vendor_detected": EventDefinition(GenericTenantEventPayload),
    # Exam governance module events (W35)
    "campus.exam_governance.proctoring_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Syllabus governance module events (W36)
    "campus.syllabus_governance.review_backlog_detected": EventDefinition(GenericTenantEventPayload),
    # Communications module events (W37)
    "campus.communications.large_broadcast_detected": EventDefinition(GenericTenantEventPayload),
    # Faculty performance KPI module events (W38)
    "campus.faculty_performance.low_score_alert_detected": EventDefinition(GenericTenantEventPayload),
    # Financial aid module events (W39)
    "campus.financial_aid.high_value_disbursement_detected": EventDefinition(GenericTenantEventPayload),
    # Financial aid disbursement risk events (W64)
    "campus.financial_aid.disbursement_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Housing maintenance risk events (W65)
    "campus.housing.maintenance_overdue_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Advising module events (W40)
    "campus.advising.personal_support_alert_detected": EventDefinition(GenericTenantEventPayload),
    "advising.session.status_changed": EventDefinition(GenericTenantEventPayload),
    "advising.session.outcome.recorded": EventDefinition(GenericTenantEventPayload),
    # Advising no-show risk events (W68)
    "campus.advising.no_show_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Thesis module events (W41)
    "campus.thesis.overdue_review_alert_detected": EventDefinition(GenericTenantEventPayload),
    # Thesis rejection risk events (W69)
    "campus.thesis.rejection_risk_detected": EventDefinition(GenericTenantEventPayload),
    # A-016.2 Thesis Governance + Supervisor Assignment events
    "thesis.submission.created": EventDefinition(GenericTenantEventPayload),
    "thesis.submission.pending_review": EventDefinition(GenericTenantEventPayload),
    "thesis.supervisor.assignment_needed": EventDefinition(GenericTenantEventPayload),
    "thesis.supervisor.overloaded": EventDefinition(GenericTenantEventPayload),
    "thesis.review.delayed": EventDefinition(GenericTenantEventPayload),
    "thesis.governance.risk_detected": EventDefinition(GenericTenantEventPayload),
    # Accreditation module events (W42)
    "campus.accreditation.high_risk_record_detected": EventDefinition(GenericTenantEventPayload),
    # HR/Payroll module events (W43)
    "campus.hr.offboarding_risk_detected": EventDefinition(GenericTenantEventPayload),
    # HR/Payroll cycle risk events (W66)
    "campus.hr.payroll_cycle_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Delinquency collections legal escalation risk events (W67)
    "campus.delinquency_collections.legal_escalation_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Programs module events (W44)
    "campus.programs.sunset_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Courses module events (W45)
    "campus.courses.retirement_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Budget planning module events (W46)
    "campus.budget.overrun_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Academic records module events (W47)
    "campus.academic_records.withdrawal_risk_detected": EventDefinition(GenericTenantEventPayload),
    "academic_records.record.created": EventDefinition(GenericTenantEventPayload),
    "academic_records.record.updated": EventDefinition(GenericTenantEventPayload),
    "academic_records.record.deleted": EventDefinition(GenericTenantEventPayload),
    # Faculty module events (W48)
    "campus.faculty.contract_termination_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Scholarship module events (W49)
    "campus.scholarship.award_revocation_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Equipment booking module events (W50)
    "campus.equipment_booking.overdue_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Academic integrity module events (W51)
    "campus.academic_integrity.escalation_risk_detected": EventDefinition(GenericTenantEventPayload),
    "academic_integrity.case.created": EventDefinition(GenericTenantEventPayload),
    "academic_integrity.case.status_changed": EventDefinition(GenericTenantEventPayload),
    "academic_integrity.case.escalated": EventDefinition(GenericTenantEventPayload),
    "academic_integrity.case.outcome_recorded": EventDefinition(GenericTenantEventPayload),
    # A-016.1 Academic Integrity Violation Detection Brain events
    "academic_integrity.violation.detected": EventDefinition(GenericTenantEventPayload),
    "academic_integrity.risk_detected": EventDefinition(GenericTenantEventPayload),
    "plagiarism.similarity.high_detected": EventDefinition(GenericTenantEventPayload),
    "exam.proctoring.violation_detected": EventDefinition(GenericTenantEventPayload),
    # A-016.3 Exam Proctoring Violation Workflow dedicated events
    "exam.proctoring.suspicious_activity_detected": EventDefinition(GenericTenantEventPayload),
    "exam.proctoring.multiple_faces_detected": EventDefinition(GenericTenantEventPayload),
    "exam.proctoring.face_mismatch_detected": EventDefinition(GenericTenantEventPayload),
    "exam.proctoring.forbidden_app_detected": EventDefinition(GenericTenantEventPayload),
    "exam.proctoring.camera_absent_detected": EventDefinition(GenericTenantEventPayload),
    "coursework.submission.suspicious_detected": EventDefinition(GenericTenantEventPayload),
    "ai_plagiarism.risk_detected": EventDefinition(GenericTenantEventPayload),
    # A-016.4 Research Ethics / Compliance Review events
    "research_ethics.application.submitted": EventDefinition(GenericTenantEventPayload),
    "research_ethics.review.overdue": EventDefinition(GenericTenantEventPayload),
    "research_ethics.high_risk.detected": EventDefinition(GenericTenantEventPayload),
    "research_ethics.missing_consent.detected": EventDefinition(GenericTenantEventPayload),
    "research_ethics.document_missing.detected": EventDefinition(GenericTenantEventPayload),
    "research_ethics.conflict_of_interest.detected": EventDefinition(GenericTenantEventPayload),
    "research_ethics.violation.reported": EventDefinition(GenericTenantEventPayload),
    "research.compliance.risk_detected": EventDefinition(GenericTenantEventPayload),
    "research.data_privacy.risk_detected": EventDefinition(GenericTenantEventPayload),
    "compliance.review.required": EventDefinition(GenericTenantEventPayload),
    # A-016.5 Academic Integrity Case Resolution Automation events
    "academic_integrity.case.opened": EventDefinition(GenericTenantEventPayload),
    "academic_integrity.case.evidence_requested": EventDefinition(GenericTenantEventPayload),
    "academic_integrity.case.review_required": EventDefinition(GenericTenantEventPayload),
    "academic_integrity.case.resolved": EventDefinition(GenericTenantEventPayload),
    "academic_integrity.case.dismissed": EventDefinition(GenericTenantEventPayload),
    "integrity.resolution.workflow_needed": EventDefinition(GenericTenantEventPayload),
    # Research module events (W52)
    "campus.research.grant_delay_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Exam governance lifecycle events (XXXIV.1)
    "exam.created": EventDefinition(GenericTenantEventPayload),
    "exam.started": EventDefinition(GenericTenantEventPayload),
    "exam.submitted": EventDefinition(GenericTenantEventPayload),
    "exam.graded": EventDefinition(GenericTenantEventPayload),
    "exam.violation_detected": EventDefinition(GenericTenantEventPayload),
    # Procurement lifecycle events (XXXIV.2)
    "procurement.request_created": EventDefinition(GenericTenantEventPayload),
    "procurement.request_submitted": EventDefinition(GenericTenantEventPayload),  # A-015.2
    "procurement.approval_required": EventDefinition(GenericTenantEventPayload),  # A-015.2
    "procurement.approved": EventDefinition(GenericTenantEventPayload),
    "procurement.rejected": EventDefinition(GenericTenantEventPayload),
    "procurement.po_issued": EventDefinition(GenericTenantEventPayload),
    "procurement.delivered": EventDefinition(GenericTenantEventPayload),
    "procurement.asset_created": EventDefinition(GenericTenantEventPayload),
    # A-015.4 Finance Operations Health Brain events
    "finance.operations.health_check": EventDefinition(GenericTenantEventPayload),
    "finance.operations.risk_detected": EventDefinition(GenericTenantEventPayload),
    # A-015.5 Inventory Low Stock / Supply Risk Brain events
    "inventory.low_stock.detected": EventDefinition(GenericTenantEventPayload),
    "inventory.reorder_needed": EventDefinition(GenericTenantEventPayload),
    "supply.risk.detected": EventDefinition(GenericTenantEventPayload),
    "procurement.inventory_gap.detected": EventDefinition(GenericTenantEventPayload),
    # Budget planning lifecycle events (XXXIV.3)
    "budget_plan.created": EventDefinition(GenericTenantEventPayload),
    "budget_plan.review_requested": EventDefinition(GenericTenantEventPayload),
    "budget_plan.approved": EventDefinition(GenericTenantEventPayload),
    "budget_plan.locked": EventDefinition(GenericTenantEventPayload),
    "budget_plan.rejected": EventDefinition(GenericTenantEventPayload),
    "budget_plan.outcome_recorded": EventDefinition(GenericTenantEventPayload),
    "budget_allocation.created": EventDefinition(GenericTenantEventPayload),
    "finance.budget_variance.threshold_reached": EventDefinition(GenericTenantEventPayload),
    # Syllabus governance lifecycle events (XXXIV.4)
    "syllabus.created": EventDefinition(GenericTenantEventPayload),
    "syllabus.review_requested": EventDefinition(GenericTenantEventPayload),
    "syllabus.approved": EventDefinition(GenericTenantEventPayload),
    "syllabus.published": EventDefinition(GenericTenantEventPayload),
    "syllabus.archived": EventDefinition(GenericTenantEventPayload),
    "syllabus.outcome_recorded": EventDefinition(GenericTenantEventPayload),
    # Scheduling lifecycle events (XXXIV.5)
    "scheduling.section.created": EventDefinition(GenericTenantEventPayload),
    "scheduling.section.scheduled": EventDefinition(GenericTenantEventPayload),
    "scheduling.section.rescheduled": EventDefinition(GenericTenantEventPayload),
    "scheduling.section.cancelled": EventDefinition(GenericTenantEventPayload),
    "scheduling.instructor.assigned": EventDefinition(GenericTenantEventPayload),
    # A-013.3/A-018.1: Scheduling conflict + enrollment/room capacity risk signals
    "scheduling.section.conflict_detected": EventDefinition(GenericTenantEventPayload),
    "scheduling.room_conflict.detected": EventDefinition(GenericTenantEventPayload),
    "scheduling.room_allocation.required": EventDefinition(GenericTenantEventPayload),
    "scheduling.room_allocation.recommendation_generated": EventDefinition(GenericTenantEventPayload),
    "scheduling.room_allocation.review_required": EventDefinition(GenericTenantEventPayload),
    "scheduling.room_allocation.no_viable_candidate": EventDefinition(GenericTenantEventPayload),
    "scheduling.room_allocation.candidate_ranked": EventDefinition(GenericTenantEventPayload),
    "scheduling.equipment_mismatch.detected": EventDefinition(GenericTenantEventPayload),
    "scheduling.room_type_mismatch.detected": EventDefinition(GenericTenantEventPayload),
    "scheduling.computer_shortage.detected": EventDefinition(GenericTenantEventPayload),
    "scheduling.capacity_mismatch.detected": EventDefinition(GenericTenantEventPayload),
        # Timetable change proposal lifecycle events (A-022.1)
        "scheduling.timetable_proposal.created": EventDefinition(GenericTenantEventPayload),
        "scheduling.timetable_proposal.submitted": EventDefinition(GenericTenantEventPayload),
        "scheduling.timetable_proposal.approved": EventDefinition(GenericTenantEventPayload),
        "scheduling.timetable_proposal.rejected": EventDefinition(GenericTenantEventPayload),
        "scheduling.timetable_proposal.revision_requested": EventDefinition(GenericTenantEventPayload),
        "scheduling.timetable_proposal.cancelled": EventDefinition(GenericTenantEventPayload),
        # Timetable change simulation lifecycle events (A-022.2)
        "scheduling.timetable_simulation.created": EventDefinition(GenericTenantEventPayload),
        "scheduling.timetable_simulation.computed": EventDefinition(GenericTenantEventPayload),
        "scheduling.timetable_simulation.invalid": EventDefinition(GenericTenantEventPayload),
        "scheduling.timetable_simulation.stale": EventDefinition(GenericTenantEventPayload),
    "enrollment.capacity_risk.detected": EventDefinition(GenericTenantEventPayload),
    # Teaching quality lifecycle events (XXXIV.6)
    "teaching_quality.evaluation.submitted": EventDefinition(GenericTenantEventPayload),
    "teaching_quality.score.updated": EventDefinition(GenericTenantEventPayload),
    "teaching_quality.low_score.alert": EventDefinition(GenericTenantEventPayload),
    # Research ethics lifecycle events (XXXIV.7)
    "research_ethics.submission.created": EventDefinition(GenericTenantEventPayload),
    "research_ethics.review.approved": EventDefinition(GenericTenantEventPayload),
    "research_ethics.review.rejected": EventDefinition(GenericTenantEventPayload),
    "research_ethics.review.high_risk_flagged": EventDefinition(GenericTenantEventPayload),
    # Equipment booking lifecycle events (XXXIV.8)
    "equipment_booking.booking.created": EventDefinition(GenericTenantEventPayload),
    "equipment_booking.booking.confirmed": EventDefinition(GenericTenantEventPayload),
    "equipment_booking.booking.cancelled": EventDefinition(GenericTenantEventPayload),
    "equipment_booking.booking.returned": EventDefinition(GenericTenantEventPayload),
    "equipment_booking.booking.overdue": EventDefinition(GenericTenantEventPayload),
    "equipment_booking.equipment.created": EventDefinition(GenericTenantEventPayload),
    # IP management lifecycle events (XXXIV.9)
    "ip_management.asset.created": EventDefinition(GenericTenantEventPayload),
    "ip_management.asset.filed": EventDefinition(GenericTenantEventPayload),
    "ip_management.asset.granted": EventDefinition(GenericTenantEventPayload),
    "ip_management.asset.licensed": EventDefinition(GenericTenantEventPayload),
    # Personnel orders lifecycle events (XXXV.1)
    "hr.personnel_order.created": EventDefinition(GenericTenantEventPayload),
    "hr.personnel_order.signed": EventDefinition(GenericTenantEventPayload),
    "hr.personnel_order.approved": EventDefinition(GenericTenantEventPayload),
    "hr.personnel_order.executed": EventDefinition(GenericTenantEventPayload),
    # Interventions cohort analytics events (XXXV.2)
    "interventions.cohort.analyzed": EventDefinition(GenericTenantEventPayload),
    "interventions.auto_triggered": EventDefinition(GenericTenantEventPayload),
    # Library module events (XXXVI)
    "library.book.issued": EventDefinition(GenericTenantEventPayload),
    "library.book.returned": EventDefinition(GenericTenantEventPayload),
    "library.book.reserved": EventDefinition(GenericTenantEventPayload),
    "library.reservation.cancelled": EventDefinition(GenericTenantEventPayload),
    "library.item.overdue": EventDefinition(GenericTenantEventPayload),
    "library.fine.calculated": EventDefinition(GenericTenantEventPayload),
    # Attendance module events (XXXVII)
    "attendance.record.marked": EventDefinition(GenericTenantEventPayload),
    "attendance.absence.recorded": EventDefinition(GenericTenantEventPayload),
    "attendance.absence.excused": EventDefinition(GenericTenantEventPayload),
    "attendance.threshold.breached": EventDefinition(GenericTenantEventPayload),
    # LMS Content module events (XXXVIII)
    "lms.lesson.completed": EventDefinition(GenericTenantEventPayload),
    "lms.assignment.submitted": EventDefinition(GenericTenantEventPayload),
    "lms.grade.posted": EventDefinition(GenericTenantEventPayload),
    "lms.student.falling_behind": EventDefinition(GenericTenantEventPayload),
    # Online Payments module events (XXXIX)
    "payment.initiated": EventDefinition(GenericTenantEventPayload),
    "payment.completed": EventDefinition(GenericTenantEventPayload),
    "payment.failed": EventDefinition(GenericTenantEventPayload),
    "payment.refunded": EventDefinition(GenericTenantEventPayload),
    "payment.failure_pattern": EventDefinition(GenericTenantEventPayload),
    # Student Feedback module events (XL)
    "feedback.submitted": EventDefinition(GenericTenantEventPayload),
    "feedback.analysis_complete": EventDefinition(GenericTenantEventPayload),
    "feedback.low_satisfaction": EventDefinition(GenericTenantEventPayload),
    # Internship module events (XLI)
    "internship.application_submitted": EventDefinition(GenericTenantEventPayload),
    "internship.offer_received": EventDefinition(GenericTenantEventPayload),
    "internship.contract_signed": EventDefinition(GenericTenantEventPayload),
    "internship.completed": EventDefinition(GenericTenantEventPayload),
    "internship.completion_risk": EventDefinition(GenericTenantEventPayload),
    # Events Management + Room Booking (XLII)
    "event.created": EventDefinition(GenericTenantEventPayload),
    "event.published": EventDefinition(GenericTenantEventPayload),
    "event.registration_opened": EventDefinition(GenericTenantEventPayload),
    "event.registration_full": EventDefinition(GenericTenantEventPayload),
    "event.started": EventDefinition(GenericTenantEventPayload),
    "event.completed": EventDefinition(GenericTenantEventPayload),
    "event.cancelled": EventDefinition(GenericTenantEventPayload),
    "booking.approved": EventDefinition(GenericTenantEventPayload),
    "booking.conflict_detected": EventDefinition(GenericTenantEventPayload),
    "room.released": EventDefinition(GenericTenantEventPayload),
    "resource.overload": EventDefinition(GenericTenantEventPayload),
    # Visitor Management + Access Control (XLIII / A-018.6)
    "visitor.arrived": EventDefinition(GenericTenantEventPayload),
    "visitor.registered": EventDefinition(GenericTenantEventPayload),
    "visitor.approved": EventDefinition(GenericTenantEventPayload),
    "visitor.rejected": EventDefinition(GenericTenantEventPayload),
    "visitor.checked_in": EventDefinition(GenericTenantEventPayload),
    "visitor.checked_out": EventDefinition(GenericTenantEventPayload),
    "visitor.expired": EventDefinition(GenericTenantEventPayload),
    "visitor.cancelled": EventDefinition(GenericTenantEventPayload),
    "visitor.unauthorized_attempt": EventDefinition(GenericTenantEventPayload),
    # Security Operations incident lifecycle (A-018.6)
    "security.incident.opened": EventDefinition(GenericTenantEventPayload),
    "security.incident.acknowledged": EventDefinition(GenericTenantEventPayload),
    "security.incident.escalated": EventDefinition(GenericTenantEventPayload),
    "security.incident.resolved": EventDefinition(GenericTenantEventPayload),
    "security.incident.dismissed": EventDefinition(GenericTenantEventPayload),
    "access.granted": EventDefinition(GenericTenantEventPayload),
    "access.denied": EventDefinition(GenericTenantEventPayload),
    "card.issued": EventDefinition(GenericTenantEventPayload),
    "card.suspended": EventDefinition(GenericTenantEventPayload),
    "card.revoked": EventDefinition(GenericTenantEventPayload),
    "card.reactivated": EventDefinition(GenericTenantEventPayload),
    "security.anomaly": EventDefinition(GenericTenantEventPayload),
    # Parking Module (XLIV)
    "parking.permit_issued": EventDefinition(GenericTenantEventPayload),
    "parking.violation_recorded": EventDefinition(GenericTenantEventPayload),
    "parking.lot_full": EventDefinition(GenericTenantEventPayload),
    "parking.capacity_risk": EventDefinition(GenericTenantEventPayload),
    # Publications + Patents + Conference (XLV)
    "publication.submitted": EventDefinition(GenericTenantEventPayload),
    "publication.accepted": EventDefinition(GenericTenantEventPayload),
    "publication.published": EventDefinition(GenericTenantEventPayload),
    "publication.citation_added": EventDefinition(GenericTenantEventPayload),
    "patent.filed": EventDefinition(GenericTenantEventPayload),
    "patent.granted": EventDefinition(GenericTenantEventPayload),
    "patent.licensed": EventDefinition(GenericTenantEventPayload),
    "conference.paper_accepted": EventDefinition(GenericTenantEventPayload),
    "conference.presentation_scheduled": EventDefinition(GenericTenantEventPayload),
    # AI Modules (XLVI)
    "tutor_session.started": EventDefinition(GenericTenantEventPayload),
    "learning.breakthrough_detected": EventDefinition(GenericTenantEventPayload),
    "student.needs_intervention": EventDefinition(GenericTenantEventPayload),
    "scan.complete": EventDefinition(GenericTenantEventPayload),
    "plagiarism.detected": EventDefinition(GenericTenantEventPayload),
    "admissions.score_generated": EventDefinition(GenericTenantEventPayload),
    "admissions.anomaly_detected": EventDefinition(GenericTenantEventPayload),
    # Digital Signature + Certificate (XLVII)
    "document.signed": EventDefinition(GenericTenantEventPayload),
    "certificate.issued": EventDefinition(GenericTenantEventPayload),
    "verification.requested": EventDefinition(GenericTenantEventPayload),
    # Personnel Orders + Contracts HR (XLVIII)
    "order.created": EventDefinition(GenericTenantEventPayload),
    "order.signed": EventDefinition(GenericTenantEventPayload),
    "order.executed": EventDefinition(GenericTenantEventPayload),
    "hr.anomaly_detected": EventDefinition(GenericTenantEventPayload),
    # Student Portal (XLIX)
    "request.submitted": EventDefinition(GenericTenantEventPayload),
    "request.ready": EventDefinition(GenericTenantEventPayload),
    # Mobile App (LI)
    "mobile.device_registered": EventDefinition(GenericTenantEventPayload),
    "mobile.notification_sent": EventDefinition(GenericTenantEventPayload),
    "mobile.notification_failed": EventDefinition(GenericTenantEventPayload),
    # Student ID Card (LII)
    "id_card.issued": EventDefinition(GenericTenantEventPayload),
    "id_card.suspended": EventDefinition(GenericTenantEventPayload),
    "id_card.revoked": EventDefinition(GenericTenantEventPayload),
    "id_card.access_denied": EventDefinition(GenericTenantEventPayload),
    # Counseling / Mental Health (LIII)
    "counseling.appointment_requested": EventDefinition(GenericTenantEventPayload),
    "counseling.session_completed": EventDefinition(GenericTenantEventPayload),
    "counseling.high_risk_case_opened": EventDefinition(GenericTenantEventPayload),
    "counseling.case_escalated": EventDefinition(GenericTenantEventPayload),
    "counseling.crisis_reported": EventDefinition(GenericTenantEventPayload),
    # 2FA SMS + TOTP (LIV)
    "twofa.enrollment_started": EventDefinition(GenericTenantEventPayload),
    "twofa.enrollment_activated": EventDefinition(GenericTenantEventPayload),
    "twofa.verified": EventDefinition(GenericTenantEventPayload),
    "twofa.verification_failed": EventDefinition(GenericTenantEventPayload),
    # SSO SAML 2.0 (LV)
    "sso.idp_registered": EventDefinition(GenericTenantEventPayload),
    "sso.login_success": EventDefinition(GenericTenantEventPayload),
    "sso.logout": EventDefinition(GenericTenantEventPayload),
    # Exam Proctoring (LVI)
    "proctoring.session_started": EventDefinition(GenericTenantEventPayload),
    "proctoring.session_ended": EventDefinition(GenericTenantEventPayload),
    "proctoring.violation_detected": EventDefinition(GenericTenantEventPayload),
    # Blockchain Diploma Verification (LVII)
    "blockchain_diploma.issued": EventDefinition(GenericTenantEventPayload),
    "blockchain_diploma.revoked": EventDefinition(GenericTenantEventPayload),
    "blockchain_diploma.verified": EventDefinition(GenericTenantEventPayload),
    # Parent Portal (LVIII)
    "parent_portal.parent_registered": EventDefinition(GenericTenantEventPayload),
    "parent_portal.student_linked": EventDefinition(GenericTenantEventPayload),
    "parent_portal.alert_pushed": EventDefinition(GenericTenantEventPayload),
    "parent_portal.alert_acknowledged": EventDefinition(GenericTenantEventPayload),
    # Alumni Donation Portal (LIX)
    "alumni_donation.campaign_created": EventDefinition(GenericTenantEventPayload),
    "alumni_donation.donation_recorded": EventDefinition(GenericTenantEventPayload),
    "alumni_donation.donation_paid": EventDefinition(GenericTenantEventPayload),
    "alumni_donation.campaign_closed": EventDefinition(GenericTenantEventPayload),
    # Multi-currency / Multi-language (LX)
    "localization.exchange_rate_updated": EventDefinition(GenericTenantEventPayload),
    "localization.locale_updated": EventDefinition(GenericTenantEventPayload),
    "localization.amount_converted": EventDefinition(GenericTenantEventPayload),
    # A-009 CRITICAL: Brain Core Missing Event Registrations (emitted but not previously registered)
    "alumni.engagement.risk_detected": EventDefinition(GenericTenantEventPayload),
    "career_services.opportunity.at_risk": EventDefinition(GenericTenantEventPayload),
    "degree_progress.graduation_risk.detected": EventDefinition(GenericTenantEventPayload),
    "enrollments.dropout_risk.detected": EventDefinition(GenericTenantEventPayload),
    "faculty.office_hours.no_show_detected": EventDefinition(GenericTenantEventPayload),
    "faculty.proctoring.violation_detected": EventDefinition(GenericTenantEventPayload),
    "finance.expense.budget_exceeded": EventDefinition(GenericTenantEventPayload),
    "programs.status.risk_detected": EventDefinition(GenericTenantEventPayload),
    "transcripts.inconsistency.detected": EventDefinition(GenericTenantEventPayload),
}

PREFIX_EVENT_REGISTRY: dict[str, EventDefinition] = {
    "automation.": EventDefinition(AutomationChainEventPayload),
    "academic_alert.": EventDefinition(AutomationChainEventPayload),
}


def normalize_event_type(event_type: str) -> str:
    normalized = str(event_type).strip().lower()
    if not normalized:
        raise EventRegistryError("event_type is required")
    return normalized


def get_event_definition(event_type: str) -> EventDefinition:
    normalized = normalize_event_type(event_type)
    definition = EXACT_EVENT_REGISTRY.get(normalized)
    if definition is not None:
        return definition
    for prefix, prefix_definition in PREFIX_EVENT_REGISTRY.items():
        if normalized.startswith(prefix):
            return prefix_definition
    raise EventRegistryError(f"unknown event_type: {normalized}")


def is_registered_event_type(event_type: str) -> bool:
    try:
        get_event_definition(event_type)
    except EventRegistryError:
        return False
    return True


def is_tenant_aware_event_type(event_type: str) -> bool:
    return get_event_definition(event_type).tenant_aware


def validate_event_payload(event_type: str, payload: dict) -> None:
    definition = get_event_definition(event_type)
    try:
        definition.payload_model.model_validate(dict(payload or {}))
    except ValidationError as exc:
        raise EventRegistryError(f"invalid payload for event_type {normalize_event_type(event_type)}") from exc


def validate_event_publish_inputs(*, tenant_id: int | None, event_type: str, payload: dict) -> str:
    normalized = normalize_event_type(event_type)
    if is_tenant_aware_event_type(normalized):
        if tenant_id is None or int(tenant_id) <= 0:
            raise EventRegistryError("tenant-aware event requires tenant_id")
    validate_event_payload(normalized, payload)
    return normalized


def registered_tenant_aware_event_types() -> set[str]:
    return {
        event_type
        for event_type, definition in EXACT_EVENT_REGISTRY.items()
        if definition.tenant_aware
    }