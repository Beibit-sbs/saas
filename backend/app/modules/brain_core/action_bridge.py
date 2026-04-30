"""Brain Core → Module Action Bridge.

Registers real DB-backed module handlers on the ActionDispatcher so that Brain
Core decisions produce tangible side-effects (e.g. intervention cases) rather
than only updating in-memory stubs.

Usage (called once at app startup after the DB engine is available)::

    from app.modules.brain_core.action_bridge import wire_action_handlers
    wire_action_handlers(
        dispatcher=brain_core_service._dispatcher,
        session_factory=app.state.admissions_session_factory,
    )

When ``session_factory`` is ``None`` (no DB configured) the function is a no-op
and the existing in-memory sinks remain active.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _message_code(prefix: str, decision_id: str) -> str:
    return f"{prefix}-{decision_id}"[-32:]


def _make_entity_action_handler(
    *,
    action_name: str,
    entity_name: str,
    payload_builder: Callable[[int, str, dict[str, Any]], dict[str, Any]],
) -> Callable[[int, str, dict[str, Any]], dict[str, Any]]:
    """Create a generic tenant-entity backed action handler."""

    def handler(tenant_id: int, decision_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        from app.modules.university_core.tenant_entity_service import create_entity_for_tenant

        try:
            row = create_entity_for_tenant(
                entity_name,
                payload_builder(tenant_id, decision_id, payload),
                int(tenant_id),
            )
            logger.info(
                "brain_core_action_entity_created",
                extra={
                    "tenant_id": tenant_id,
                    "decision_id": decision_id,
                    "action": action_name,
                    "entity": entity_name,
                    "record_id": str(row.get("id")),
                },
            )
            return {
                "status": "created",
                "item": {
                    "id": str(row.get("id")),
                    "entity": entity_name,
                    "source": "module_entity",
                },
            }
        except Exception as exc:
            logger.warning(
                "brain_core_action_entity_failed",
                extra={
                    "tenant_id": tenant_id,
                    "decision_id": decision_id,
                    "action": action_name,
                    "entity": entity_name,
                    "error": str(exc),
                },
            )
            return {"status": "failed", "reason": str(exc)}

    return handler


def _make_create_intervention_case_handler(
    session_factory: Callable,
) -> Callable[[int, str, dict[str, Any]], dict[str, Any]]:
    """Return a real DB-backed handler for the ``create_intervention_case`` action."""

    def handler(tenant_id: int, decision_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        from app.modules.interventions.models import (
            InterventionAssigneeType,
            InterventionCaseModel,
            InterventionCaseSeverity,
            InterventionCaseStatus,
            InterventionCaseType,
        )

        session = session_factory()
        try:
            risk_level = str(payload.get("risk_level") or "medium").lower()
            severity = InterventionCaseSeverity(
                risk_level if risk_level in {"high", "medium", "low"} else "medium"
            )
            event_label = str(payload.get("event_type") or "academic_risk").replace(".", "_")
            now = datetime.now(UTC)

            case = InterventionCaseModel(
                tenant_id=tenant_id,
                case_type=InterventionCaseType.ACADEMIC_RISK,
                student_profile_id=payload.get("student_id"),
                severity=severity,
                status=InterventionCaseStatus.OPEN,
                title=f"Brain Core auto-intervention [{event_label}]",
                description=(
                    f"Automatically created by Brain Core decision engine. "
                    f"Decision ID: {decision_id}"
                ),
                risk_snapshot_json={"brain_decision_id": decision_id, **payload},
                assignee_type=InterventionAssigneeType.GROUP,
                assignee_ref="advising",
                due_at=now + timedelta(days=7),
                opened_at=now,
                metadata_json={"source": "brain_core", "decision_id": decision_id},
                created_by="brain_core",
                updated_by="brain_core",
            )
            session.add(case)
            session.commit()
            session.refresh(case)
            logger.info(
                "brain_core_action_intervention_case_created",
                extra={
                    "tenant_id": tenant_id,
                    "decision_id": decision_id,
                    "case_id": str(case.id),
                    "severity": severity.value,
                },
            )
            return {"status": "created", "item": {"case_id": str(case.id), "source": "real_db"}}
        except Exception as exc:
            try:
                session.rollback()
            except Exception:
                pass
            logger.warning(
                "brain_core_action_intervention_case_failed",
                extra={
                    "tenant_id": tenant_id,
                    "decision_id": decision_id,
                    "error": str(exc),
                },
            )
            return {"status": "failed", "reason": str(exc)}
        finally:
            try:
                session.close()
            except Exception:
                pass

    return handler


def _make_create_student_support_case_handler() -> Callable[[int, str, dict[str, Any]], dict[str, Any]]:
    """Return a module-backed handler for ``create_student_support_case``.

    The action is materialized as a real student-life counseling case so
    student-support recommendations generated by Brain Core are not limited to
    in-memory workflow stubs.
    """

    def handler(tenant_id: int, decision_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        from app.modules.university_core.tenant_entity_service import create_entity_for_tenant

        try:
            student_id = str(payload.get("student_id") or "").strip()
            if not student_id:
                return {"status": "failed", "reason": "student_id is required"}

            concern_type = str(payload.get("concern_type") or payload.get("event_type") or "brain_support").strip()
            case_code = f"BRAIN-{decision_id}"[-32:]

            created = create_entity_for_tenant(
                "student_life_counseling_cases",
                {
                    "case_code": case_code,
                    "student_id": student_id,
                    "concern_type": concern_type,
                    "status": "open",
                },
                int(tenant_id),
            )

            logger.info(
                "brain_core_action_student_support_case_created",
                extra={
                    "tenant_id": tenant_id,
                    "decision_id": decision_id,
                    "case_id": str(created.get("id")),
                },
            )
            return {
                "status": "created",
                "item": {
                    "case_id": str(created.get("id")),
                    "source": "student_life_module",
                },
            }
        except Exception as exc:
            logger.warning(
                "brain_core_action_student_support_case_failed",
                extra={
                    "tenant_id": tenant_id,
                    "decision_id": decision_id,
                    "error": str(exc),
                },
            )
            return {"status": "failed", "reason": str(exc)}

    return handler


def _module_action_handlers() -> dict[str, Callable[[int, str, dict[str, Any]], dict[str, Any]]]:
    """Return module-backed handlers for Brain workflow actions."""

    return {
        "create_student_support_case": _make_create_student_support_case_handler(),
        "create_disciplinary_review_case": _make_entity_action_handler(
            action_name="create_disciplinary_review_case",
            entity_name="student_life_disciplinary_cases",
            payload_builder=lambda _tid, did, pl: {
                "incident_code": _message_code("DISC", did),
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "incident_type": str(pl.get("incident_type") or pl.get("event_type") or "behavioral"),
                "severity": str(pl.get("incident_severity") or pl.get("severity") or "medium"),
                "status": "reported",
            },
        ),
        "create_supervision_task": _make_entity_action_handler(
            action_name="create_supervision_task",
            entity_name="thesis_records",
            payload_builder=lambda _tid, did, pl: {
                "thesis_code": _message_code("THS", did),
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "title": str(pl.get("title") or "Brain supervision task"),
                "advisor_faculty_id": str(pl.get("advisor_faculty_id") or pl.get("faculty_id") or "AUTO-ADVISOR"),
                "status": "in_progress",
            },
        ),
        "create_workload_review_task": _make_entity_action_handler(
            action_name="create_workload_review_task",
            entity_name="faculty_performance_kpis",
            payload_builder=lambda _tid, did, pl: {
                "faculty_id": str(pl.get("faculty_id") or "AUTO-FACULTY"),
                "name": f"Brain Workload Review {did[:8]}",
                "department_id": str(pl.get("department_id") or "AUTO-DEPT"),
                "kpi_period": str(pl.get("kpi_period") or "auto"),
                "teaching_score": float(pl.get("teaching_score") or 0),
                "research_score": float(pl.get("research_score") or 0),
                "service_score": float(pl.get("service_score") or 0),
                "overall_score": float(pl.get("overall_score") or 0),
                "status": "needs_improvement",
            },
        ),
        "create_collections_case": _make_entity_action_handler(
            action_name="create_collections_case",
            entity_name="delinquency_records",
            payload_builder=lambda _tid, did, pl: {
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "invoice_code": _message_code("INV", did),
                "amount_due": float(pl.get("balance_due") or 0),
                "days_overdue": int(pl.get("delinquency_days") or 0),
                "escalation_stage": "stage_1",
                "status": "open",
            },
        ),
        "create_replenishment_task": _make_entity_action_handler(
            action_name="create_replenishment_task",
            entity_name="procurement_inventory_items",
            payload_builder=lambda _tid, did, pl: {
                "item_code": _message_code("INVIT", did),
                "title": str(pl.get("stock_item_id") or "Brain replenishment item"),
                "current_stock": int(pl.get("stock_level") or 0),
                "reorder_point": int(pl.get("threshold") or 0),
                "daily_usage_rate": float(pl.get("projected_daily_usage") or 0),
                "lead_time_days": int(pl.get("lead_time_days") or 1),
                "auto_reorder_enabled": bool(pl.get("auto_reorder") or False),
                "status": "active",
            },
        ),
        "initiate_procurement_request": _make_entity_action_handler(
            action_name="initiate_procurement_request",
            entity_name="procurement_contracts",
            payload_builder=lambda _tid, did, pl: {
                "contract_code": _message_code("PRC", did),
                "vendor_code": str(pl.get("vendor_code") or "AUTO-VENDOR"),
                "title": str(pl.get("title") or "Brain procurement request"),
                "risk_score": float(pl.get("risk_score") or 0),
                "sla_target_met": bool(pl.get("sla_target_met") or False),
                "status": "draft",
            },
        ),
        "create_accreditation_remediation_workflow": _make_entity_action_handler(
            action_name="create_accreditation_remediation_workflow",
            entity_name="accreditation_records",
            payload_builder=lambda _tid, did, pl: {
                "standard_code": str(pl.get("standard_code") or _message_code("STD", did)),
                "standard_type": "accreditation",
                "title": "Brain remediation workflow",
                "owner_department": str(pl.get("owner_department") or "AUTO-DEPT"),
                "review_cycle_year": int(datetime.now(UTC).year),
                "due_date": str(pl.get("due_date") or "2026-12-31"),
                "evidence_summary": str(pl.get("new_status") or "requires remediation"),
                "risk_level": str(pl.get("risk_level") or "medium"),
                "status": "needs_attention",
            },
        ),
        "create_research_remediation_workflow": _make_entity_action_handler(
            action_name="create_research_remediation_workflow",
            entity_name="research_experiments",
            payload_builder=lambda _tid, did, pl: {
                "experiment_code": _message_code("EXP", did),
                "title": str(pl.get("title") or "Brain research remediation"),
                "lab_code": str(pl.get("lab_code") or "AUTO-LAB"),
                "principal_investigator_id": str(pl.get("principal_investigator_id") or "AUTO-PI"),
                "status": "active",
            },
        ),
        "create_facility_incident_workflow": _make_entity_action_handler(
            action_name="create_facility_incident_workflow",
            entity_name="operations_facility_issues",
            payload_builder=lambda _tid, _did, pl: {
                "facility_code": str(pl.get("facility_code") or "AUTO-FACILITY"),
                "issue_type": str(pl.get("issue_type") or pl.get("event_type") or "operations_issue"),
                "severity": str(pl.get("severity") or "medium"),
                "status": "reported",
            },
        ),
        "create_cleaning_recovery_task": _make_entity_action_handler(
            action_name="create_cleaning_recovery_task",
            entity_name="operations_cleaning_checks",
            payload_builder=lambda _tid, _did, pl: {
                "room_code": str(pl.get("room_code") or "AUTO-ROOM"),
                "scheduled_slot": str(pl.get("scheduled_slot") or "immediate"),
                "status": "missed",
            },
        ),
        "create_dropout_intervention": _make_entity_action_handler(
            action_name="create_dropout_intervention",
            entity_name="student_life_counseling_cases",
            payload_builder=lambda _tid, did, pl: {
                "case_code": _message_code("DROP", did),
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "concern_type": "dropout_risk",
                "status": "open",
            },
        ),
        "create_integrity_review_case": _make_entity_action_handler(
            action_name="create_integrity_review_case",
            entity_name="student_life_disciplinary_cases",
            payload_builder=lambda _tid, did, pl: {
                "incident_code": _message_code("INTG", did),
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "incident_type": "academic_integrity",
                "severity": str(pl.get("severity") or "high"),
                "status": "under_review",
            },
        ),
        "create_program_review_task": _make_entity_action_handler(
            action_name="create_program_review_task",
            entity_name="programs",
            payload_builder=lambda _tid, did, pl: {
                "program_code": _message_code("PRG", did),
                "title": str(pl.get("title") or "Brain program review"),
                "degree_type": str(pl.get("degree_type") or "bachelor"),
                "faculty": str(pl.get("faculty") or "AUTO-FACULTY"),
                "status": "under_review",
            },
        ),
        "create_platform_reliability_incident": _make_entity_action_handler(
            action_name="create_platform_reliability_incident",
            entity_name="security_incidents",
            payload_builder=lambda _tid, did, pl: {
                "incident_code": _message_code("PLAT", did),
                "facility_code": str(pl.get("facility_code") or "NOC"),
                "category": "platform_reliability",
                "severity": str(pl.get("severity") or "medium"),
                "status": "open",
            },
        ),
        "notify_advisor": _make_entity_action_handler(
            action_name="notify_advisor",
            entity_name="advising_sessions",
            payload_builder=lambda _tid, did, pl: {
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "advisor_id": str(pl.get("advisor_id") or "AUTO-ADVISOR"),
                "session_type": "brain_notification",
                "status": "scheduled",
                "scheduled_at": str(pl.get("scheduled_at") or datetime.now(UTC).isoformat()),
                "notes": f"Brain notification {did}",
                "outcome": "pending",
            },
        ),
        "notify_student_success_team": _make_entity_action_handler(
            action_name="notify_student_success_team",
            entity_name="student_service_tickets",
            payload_builder=lambda _tid, did, pl: {
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "category": "brain_alert",
                "subject": str(pl.get("subject") or f"Brain signal {did[:8]}"),
                "description": str(pl.get("description") or "Auto-generated by Brain Core"),
                "priority": str(pl.get("priority") or "medium"),
                "status": "open",
                "owner_id": str(pl.get("owner_id") or "student-success"),
                "channel": "internal",
            },
        ),
        "notify_finance": _make_entity_action_handler(
            action_name="notify_finance",
            entity_name="budget_plans",
            payload_builder=lambda _tid, _did, pl: {
                "department_id": str(pl.get("department_id") or "FINANCE"),
                "fiscal_year": int(pl.get("fiscal_year") or datetime.now(UTC).year),
                "total_amount": float(pl.get("total_amount") or 0),
                "currency": str(pl.get("currency") or "USD"),
                "status": "draft",
                "description": str(pl.get("description") or "Brain finance notification"),
            },
        ),
        "notify_compliance": _make_entity_action_handler(
            action_name="notify_compliance",
            entity_name="accreditation_records",
            payload_builder=lambda _tid, did, pl: {
                "standard_code": str(pl.get("standard_code") or _message_code("CMP", did)),
                "standard_type": "compliance",
                "title": "Brain compliance alert",
                "owner_department": str(pl.get("owner_department") or "COMPLIANCE"),
                "review_cycle_year": int(datetime.now(UTC).year),
                "due_date": str(pl.get("due_date") or "2026-12-31"),
                "evidence_summary": str(pl.get("description") or "Auto-generated compliance alert"),
                "risk_level": str(pl.get("risk_level") or "medium"),
                "status": "needs_attention",
            },
        ),
        "notify_platform": _make_entity_action_handler(
            action_name="notify_platform",
            entity_name="communication_messages",
            payload_builder=lambda _tid, did, pl: {
                "message_code": _message_code("PLMSG", did),
                "title": str(pl.get("title") or "Brain platform notification"),
                "message_type": "platform_alert",
                "target_audience": "platform_ops",
                "status": "queued",
                "recipients_count": int(pl.get("recipients_count") or 1),
                "delivered_count": int(pl.get("delivered_count") or 0),
                "opened_count": int(pl.get("opened_count") or 0),
                "integration_source": "brain_core",
            },
        ),
        # ── financial_aid ─────────────────────────────────────────────────────
        "create_financial_aid_review": _make_entity_action_handler(
            action_name="create_financial_aid_review",
            entity_name="financial_aid_records",
            payload_builder=lambda _tid, _did, pl: {
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "aid_type": str(pl.get("aid_type") or "emergency"),
                "amount": float(pl.get("amount") or 0),
                "currency": str(pl.get("currency") or "USD"),
                "status": "under_review",
                "term": str(pl.get("term") or "auto"),
            },
        ),
        # ── housing ───────────────────────────────────────────────────────────
        "create_housing_request": _make_entity_action_handler(
            action_name="create_housing_request",
            entity_name="housing_requests",
            payload_builder=lambda _tid, _did, pl: {
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "request_type": str(pl.get("request_type") or "emergency"),
                "dormitory": str(pl.get("dormitory") or "AUTO-DORM"),
                "status": "pending",
            },
        ),
        # ── alumni ────────────────────────────────────────────────────────────
        "create_alumni_engagement_task": _make_entity_action_handler(
            action_name="create_alumni_engagement_task",
            entity_name="alumni_records",
            payload_builder=lambda _tid, _did, pl: {
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "graduation_year": int(pl.get("graduation_year") or datetime.now(UTC).year),
                "status": "active",
                "engagement_type": str(pl.get("engagement_type") or "outreach"),
            },
        ),
        # ── career_services ───────────────────────────────────────────────────
        "create_career_opportunity": _make_entity_action_handler(
            action_name="create_career_opportunity",
            entity_name="career_opportunities",
            payload_builder=lambda _tid, _did, pl: {
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "title": str(pl.get("title") or "Brain career opportunity"),
                "company": str(pl.get("company") or "AUTO-COMPANY"),
                "opportunity_type": str(pl.get("opportunity_type") or "internship"),
                "status": "open",
            },
        ),
        # ── hr_payroll ────────────────────────────────────────────────────────
        "create_hr_review_case": _make_entity_action_handler(
            action_name="create_hr_review_case",
            entity_name="hr_employees",
            payload_builder=lambda _tid, did, pl: {
                "employee_code": _message_code("EMP", did),
                "full_name": str(pl.get("full_name") or "AUTO-EMPLOYEE"),
                "department_id": str(pl.get("department_id") or "AUTO-DEPT"),
                "role_title": str(pl.get("role_title") or "under_review"),
                "status": "under_review",
            },
        ),
        # ── facilities_work_orders ────────────────────────────────────────────
        "create_facilities_work_order": _make_entity_action_handler(
            action_name="create_facilities_work_order",
            entity_name="facilities_work_orders",
            payload_builder=lambda _tid, did, pl: {
                "order_code": _message_code("WO", did),
                "facility_code": str(pl.get("facility_code") or "AUTO-FACILITY"),
                "title": str(pl.get("title") or "Brain work order"),
                "work_type": str(pl.get("work_type") or "maintenance"),
                "priority": str(pl.get("priority") or "medium"),
                "status": "open",
            },
        ),
        # ── asset_inventory ───────────────────────────────────────────────────
        "create_asset_inspection": _make_entity_action_handler(
            action_name="create_asset_inspection",
            entity_name="asset_inventory_items",
            payload_builder=lambda _tid, did, pl: {
                "asset_code": _message_code("AST", did),
                "name": str(pl.get("name") or "Brain asset inspection"),
                "category": str(pl.get("category") or "equipment"),
                "location": str(pl.get("location") or "AUTO-LOCATION"),
                "condition": str(pl.get("condition") or "requires_inspection"),
                "purchase_year": int(pl.get("purchase_year") or datetime.now(UTC).year),
                "status": "active",
            },
        ),
        # ── research_ethics ───────────────────────────────────────────────────
        "create_ethics_review": _make_entity_action_handler(
            action_name="create_ethics_review",
            entity_name="ethics_reviews",
            payload_builder=lambda _tid, did, pl: {
                "review_code": _message_code("ETH", did),
                "project_title": str(pl.get("project_title") or "Brain ethics review"),
                "principal_investigator_id": str(pl.get("principal_investigator_id") or "AUTO-PI"),
                "status": "pending",
            },
        ),
        # ── equipment_booking ─────────────────────────────────────────────────
        "create_equipment_booking": _make_entity_action_handler(
            action_name="create_equipment_booking",
            entity_name="equipment_bookings",
            payload_builder=lambda _tid, _did, pl: {
                "equipment_code": str(pl.get("equipment_code") or "AUTO-EQ"),
                "requester_id": str(pl.get("requester_id") or "AUTO-REQ"),
                "start_time": str(pl.get("start_time") or datetime.now(UTC).isoformat()),
                "end_time": str(pl.get("end_time") or datetime.now(UTC).isoformat()),
                "booking_status": "pending",
                "integration_source": "brain_core",
            },
        ),
        # ── scholarship ───────────────────────────────────────────────────────
        "create_scholarship_review": _make_entity_action_handler(
            action_name="create_scholarship_review",
            entity_name="scholarship_applications",
            payload_builder=lambda _tid, did, pl: {
                "application_code": _message_code("SCH", did),
                "student_id": str(pl.get("student_id") or "UNKNOWN-STUDENT"),
                "scholarship_type": str(pl.get("scholarship_type") or "merit"),
                "status": "under_review",
                "gpa": float(pl.get("gpa") or 0),
                "requested_amount": float(pl.get("requested_amount") or 0),
                "integration_source": "brain_core",
            },
        ),
        # ── transport ─────────────────────────────────────────────────────────
        "create_transport_disruption_alert": _make_entity_action_handler(
            action_name="create_transport_disruption_alert",
            entity_name="transport_routes",
            payload_builder=lambda _tid, did, pl: {
                "route_code": _message_code("RT", did),
                "route_name": str(pl.get("route_name") or "Brain alert route"),
                "status": "disrupted",
            },
        ),
        # ── ip_management ─────────────────────────────────────────────────────
        "create_ip_asset_record": _make_entity_action_handler(
            action_name="create_ip_asset_record",
            entity_name="ip_assets",
            payload_builder=lambda _tid, did, pl: {
                "asset_code": _message_code("IP", did),
                "title": str(pl.get("title") or "Brain IP record"),
                "ip_type": str(pl.get("ip_type") or "patent"),
                "status": "pending",
                "integration_source": "brain_core",
            },
        ),
        # ── campus_sla ────────────────────────────────────────────────────────
        "create_sla_breach_record": _make_entity_action_handler(
            action_name="create_sla_breach_record",
            entity_name="campus_sla_records",
            payload_builder=lambda _tid, _did, pl: {
                "service_type": str(pl.get("service_type") or "facilities"),
                "facility_code": str(pl.get("facility_code") or "AUTO-FACILITY"),
                "target_sla_minutes": int(pl.get("target_sla_minutes") or 60),
                "actual_minutes": int(pl.get("actual_minutes") or 0),
                "status": "breached",
                "reported_at": datetime.now(UTC).isoformat(),
                "integration_source": "brain_core",
            },
        ),
    }


def wire_action_handlers(
    *,
    dispatcher: Any,
    session_factory: Callable | None,
) -> None:
    """Register real module callbacks on *dispatcher*.

    Safe to call with ``session_factory=None`` — becomes a no-op so tests and
    environments without a DB remain unaffected.
    """
    if session_factory is None:
        return

    dispatcher.register_module_handler(
        "create_intervention_case",
        _make_create_intervention_case_handler(session_factory),
    )
    handlers = _module_action_handlers()
    for action_name, handler in handlers.items():
        dispatcher.register_module_handler(action_name, handler)

    logger.info(
        "brain_core_action_bridge_wired",
        extra={
            "handlers_count": 1 + len(handlers),
            "handlers": ["create_intervention_case", *sorted(handlers.keys())],
        },
    )
