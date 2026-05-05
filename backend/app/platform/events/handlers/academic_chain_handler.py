"""Academic chain event handler — Contour v1.

Listens to domain events from A (Academic Core) and automatically creates
intervention cases in B (Student Success) when risk-triggering status changes occur:

  thesis.status_changed          → open intervention case if to_status == "rejected"
  accreditation.status_changed   → open intervention case if to_status == "remediation_required"

This implements the first delivery package of Contour v1 (A→B cross-domain chain).
"""
from __future__ import annotations

import logging
from typing import Any

from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork

logger = logging.getLogger("app.platform.events.academic_chain")

_THESIS_TRIGGER_STATUSES: frozenset[str] = frozenset({"rejected"})
_ACCREDITATION_TRIGGER_STATUSES: frozenset[str] = frozenset({"remediation_required"})


class AcademicChainEventHandler:
    """Translates A-domain status events into B-domain intervention cases."""

    name = "academic_chain"

    def handle(self, event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, Any]:
        etype = str(event.event_type).lower()

        if etype == "thesis.status_changed":
            return self._handle_thesis(event)
        if etype == "accreditation.status_changed":
            return self._handle_accreditation(event)

        return {"handler": self.name, "status": "skipped", "reason": "irrelevant_event_type"}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _handle_thesis(self, event: OutboxEventRead) -> dict[str, Any]:
        payload = dict(event.payload_json or {})
        if payload.get("brain_core_routed") is True:
            return {"handler": self.name, "status": "skipped", "reason": "brain_core_routed"}

        to_status = str(payload.get("to_status") or "")
        if to_status not in _THESIS_TRIGGER_STATUSES:
            return {"handler": self.name, "status": "skipped", "reason": "non_risk_status", "to_status": to_status}

        thesis_id = payload.get("thesis_id")
        student_id = payload.get("student_id")
        advisor_faculty_id = payload.get("advisor_faculty_id") or ""
        from_status = str(payload.get("from_status") or "")

        result = _create_intervention_case(
            tenant_id=event.tenant_id,
            title=f"Thesis rejected — student {student_id} requires advising support",
            description=(
                f"Thesis record #{thesis_id} was transitioned from '{from_status}' to 'rejected'. "
                f"Advisor faculty: {advisor_faculty_id}. "
                "An advising session is required to determine next steps."
            ),
            severity="medium",
            case_type="academic_risk",
            metadata={
                "source_event": "thesis.status_changed",
                "thesis_id": thesis_id,
                "student_id": student_id,
                "advisor_faculty_id": advisor_faculty_id,
                "from_status": from_status,
                "to_status": to_status,
                "correlation_id": event.correlation_id,
            },
            student_id=int(student_id) if student_id else None,
        )

        return {"handler": self.name, "status": "processed", "action": "intervention_case_opened", **result}

    def _handle_accreditation(self, event: OutboxEventRead) -> dict[str, Any]:
        payload = dict(event.payload_json or {})
        to_status = str(payload.get("to_status") or "")
        if to_status not in _ACCREDITATION_TRIGGER_STATUSES:
            return {"handler": self.name, "status": "skipped", "reason": "non_risk_status", "to_status": to_status}

        record_id = payload.get("accreditation_id")
        standard_code = str(payload.get("standard_code") or "")
        owner_department = str(payload.get("owner_department") or "")
        from_status = str(payload.get("from_status") or "")

        result = _create_intervention_case(
            tenant_id=event.tenant_id,
            title=f"Accreditation remediation required — {standard_code}",
            description=(
                f"Accreditation record #{record_id} (standard: {standard_code}, "
                f"department: {owner_department}) transitioned from '{from_status}' to 'remediation_required'. "
                "A faculty remediation action item and student-impact review are required."
            ),
            severity="high",
            case_type="academic_risk",
            metadata={
                "source_event": "accreditation.status_changed",
                "accreditation_id": record_id,
                "standard_code": standard_code,
                "owner_department": owner_department,
                "from_status": from_status,
                "to_status": to_status,
                "correlation_id": event.correlation_id,
            },
            student_id=None,
        )

        return {"handler": self.name, "status": "processed", "action": "intervention_case_opened", **result}


def _create_intervention_case(
    *,
    tenant_id: int,
    title: str,
    description: str,
    severity: str,
    case_type: str,
    metadata: dict[str, Any],
    student_id: int | None,
) -> dict[str, Any]:
    """Create an intervention case using SQLAlchemy — synchronous path for outbox worker."""
    try:
        from app.core.db import _get_shared_engine, make_session_factory
        from app.modules.interventions.models import (
            InterventionActionModel,
            InterventionActionType,
            InterventionAssigneeType,
            InterventionCaseModel,
            InterventionCaseSeverity,
            InterventionCaseStatus,
            InterventionCaseType,
        )

        engine = _get_shared_engine()
        if engine is None:
            logger.warning("academic_chain: no DB engine available — intervention case skipped")
            return {"case_id": None, "skipped": True, "reason": "no_db_engine"}

        session_factory = make_session_factory(engine)

        severity_enum = InterventionCaseSeverity(severity)
        case_type_enum = InterventionCaseType(case_type)

        # Default assignment based on severity
        if severity_enum == InterventionCaseSeverity.HIGH:
            assignee_type = InterventionAssigneeType.GROUP
            assignee_ref = "dean_office"
        elif severity_enum == InterventionCaseSeverity.MEDIUM:
            assignee_type = InterventionAssigneeType.GROUP
            assignee_ref = "faculty_advisor"
        else:
            assignee_type = InterventionAssigneeType.GROUP
            assignee_ref = "student_support"

        from datetime import UTC, datetime, timedelta
        days_map = {
            InterventionCaseSeverity.HIGH: 3,
            InterventionCaseSeverity.MEDIUM: 5,
            InterventionCaseSeverity.LOW: 7,
        }
        due_at = datetime.now(UTC) + timedelta(days=days_map[severity_enum])

        with session_factory() as db:
            case = InterventionCaseModel(
                tenant_id=tenant_id,
                case_type=case_type_enum,
                student_profile_id=student_id,
                severity=severity_enum,
                status=InterventionCaseStatus.OPEN,
                title=title,
                description=description,
                risk_snapshot_json={},
                assignee_type=assignee_type,
                assignee_ref=assignee_ref,
                due_at=due_at,
                metadata_json=metadata,
                created_by="academic_chain_handler",
                updated_by="academic_chain_handler",
            )
            db.add(case)
            db.flush()

            db.add(
                InterventionActionModel(
                    tenant_id=tenant_id,
                    case_id=case.id,
                    action_type=InterventionActionType.ASSIGNMENT,
                    description=f"Auto-assigned by academic_chain_handler to {assignee_type.value}:{assignee_ref}",
                    outcome_note=None,
                    performed_by="academic_chain_handler",
                    metadata_json={"auto_assignment": True, "source": "academic_chain"},
                )
            )
            db.flush()
            db.commit()
            db.refresh(case)

            case_id = int(case.id)

        logger.info(
            "academic_chain: intervention case #%s opened for tenant_id=%s source_event=%s",
            case_id,
            tenant_id,
            metadata.get("source_event"),
        )
        return {"case_id": case_id}

    except Exception:  # noqa: BLE001
        logger.exception("academic_chain: failed to create intervention case for tenant_id=%s", tenant_id)
        return {"case_id": None, "error": "creation_failed"}
