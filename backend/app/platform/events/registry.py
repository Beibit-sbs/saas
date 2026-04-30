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
    # Advising no-show risk events (W68)
    "campus.advising.no_show_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Thesis module events (W41)
    "campus.thesis.overdue_review_alert_detected": EventDefinition(GenericTenantEventPayload),
    # Thesis rejection risk events (W69)
    "campus.thesis.rejection_risk_detected": EventDefinition(GenericTenantEventPayload),
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
    # Faculty module events (W48)
    "campus.faculty.contract_termination_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Scholarship module events (W49)
    "campus.scholarship.award_revocation_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Equipment booking module events (W50)
    "campus.equipment_booking.overdue_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Academic integrity module events (W51)
    "campus.academic_integrity.escalation_risk_detected": EventDefinition(GenericTenantEventPayload),
    # Research module events (W52)
    "campus.research.grant_delay_risk_detected": EventDefinition(GenericTenantEventPayload),
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