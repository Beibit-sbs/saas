from __future__ import annotations

import logging

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.audit.service import log_admin_action
from app.modules.advising.schemas import (
    AdvisingSessionCreateSchema,
    AdvisingSessionSchema,
    AdvisingSessionStatus,
    AdvisingSessionStatusUpdateSchema,
)
from app.modules.usage.service import record_usage_event
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "scheduled": {"completed", "cancelled", "no_show"},
    "completed": set(),
    "cancelled": set(),
    "no_show": {"scheduled"},
}

# W40: cap on active (scheduled) sessions per session_type
_SESSION_TYPE_MAX_ACTIVE: dict[str, int] = {
    "academic": 100,
    "career": 80,
    "personal": 60,
    "mentoring": 120,
}

_ACTIVE_SESSION_STATUSES: frozenset[str] = frozenset({"scheduled"})

# W40: high-frequency threshold — personal sessions requiring an alert record
_HIGH_FREQUENCY_SESSION_TYPES: frozenset[str] = frozenset({"personal"})

# ---------------------------------------------------------------------------
# W100: advising session enrollment guard
# An advising session cannot be created for a student who is not actively enrolled.
# Scheduling advisor time for a withdrawn/expelled student wastes institutional
# resources and corrupts Brain Core engagement signals with phantom sessions.
# ---------------------------------------------------------------------------
_ADVISING_ACTIVE_ENROLLMENT_STATUSES: frozenset[str] = frozenset(
    {"enrolled", "active", "registered"}
)


def _check_student_has_active_enrollment_for_advising(
    tenant_id: int,
    student_id: int,
) -> None:
    """W100: Cross-entity guard — advising_sessions × enrollments.

    An advising session cannot be created for a student with no active enrollment.
    A student whose enrollment status is 'withdrawn', 'graduated', 'expelled', or
    otherwise inactive has no academic standing to advise against.

    Scheduling advisor time for such a student:
      - wastes advisor capacity
      - produces false 'student engagement' signals in Brain Core
      - corrupts advising outcome metrics used for institutional reporting

    HARDENING: fail-closed — any enrollment query failure blocks session creation.
    No silent fallback: if enrollment data is unavailable the safe answer is to block.
    """
    from app.core.module_helpers.service_validation import DomainValidationError

    try:
        all_enrollments = list_entities_for_tenant("enrollments", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Cannot create advising session: enrollments query failed for "
            f"student_id={student_id}. Cannot verify active enrollment. "
            f"Reason: {exc}"
        ) from exc

    student_enrollments = [
        row for row in all_enrollments
        if int(row.get("student_id") or 0) == student_id
    ]

    has_active = any(
        str(row.get("status") or "").strip().lower() in _ADVISING_ACTIVE_ENROLLMENT_STATUSES
        for row in student_enrollments
    )

    if not has_active:
        raise DomainValidationError(
            f"Cannot create advising session: student_id={student_id} has no active "
            f"enrollment (checked statuses: {sorted(_ADVISING_ACTIVE_ENROLLMENT_STATUSES)}). "
            f"Advising sessions are reserved for currently enrolled students. "
            f"A withdrawn or graduated student cannot receive academic advising."
        )

# W68: no-show sessions represent student dropout risk
_NO_SHOW_RISK_STATUSES: frozenset[str] = frozenset({"no_show"})

# W127: advisor must be an active faculty member
_ADVISOR_FACULTY_ACTIVE_STATUSES: frozenset[str] = frozenset({"active"})


def _check_advisor_is_active_faculty_for_advising(
    *,
    tenant_id: int,
    advisor_id: str,
) -> None:
    """W127: Cross-entity guard — advising_sessions × faculty.

    An advising session cannot be created when the advisor is not an active faculty member.
    A terminated, resigned, or otherwise inactive faculty member scheduling advising sessions:
    - creates phantom workload records with no real advising relationship
    - corrupts advisor capacity and outcome analytics in Brain Core
    - may violate student-facing service commitments
    - risks FERPA data exposure to non-employees

    Fail-closed: any faculty lookup failure blocks session creation.
    """
    from app.core.module_helpers.service_validation import DomainValidationError

    normalized_id = advisor_id.strip()

    try:
        faculty_rows = list_entities_for_tenant("faculty", tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise DomainValidationError(
            f"Cannot create advising session: faculty lookup failed for advisor_id='{normalized_id}'. "
            f"Advisor eligibility cannot be verified. Reason: {exc}"
        ) from exc

    advisor = next(
        (
            r for r in faculty_rows
            if (str(r.get("faculty_id") or "").strip() == normalized_id
                or str(r.get("employee_id") or "").strip() == normalized_id)
            and str(r.get("status") or "").strip().lower() in _ADVISOR_FACULTY_ACTIVE_STATUSES
        ),
        None,
    )

    # Check if advisor exists at all (for the not-found error)
    advisor_exists = any(
        str(r.get("faculty_id") or "").strip() == normalized_id
        or str(r.get("employee_id") or "").strip() == normalized_id
        for r in faculty_rows
    )

    if not advisor_exists:
        raise DomainValidationError(
            f"Cannot create advising session: advisor_id='{normalized_id}' not found in faculty registry. "
            f"Only registered faculty may serve as advisors."
        )

    if advisor is None:
        raise DomainValidationError(
            f"Cannot create advising session: advisor_id='{normalized_id}' has no active faculty status "
            f"— terminated or resigned advisors cannot schedule advising sessions."
        )

logger = logging.getLogger("app.modules.advising")


def _emit_outcome_signal(
    *,
    tenant_id: int,
    session_id: int,
    student_id: int,
    advisor_id: str,
    session_type: str,
    outcome_status: str,
    outcome: str,
) -> None:
    """Fire-and-forget: publish advising.session.outcome.recorded for Brain Core feedback loop."""
    try:
        from app.platform.events.publisher import EventPublisher

        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="advising.session.outcome.recorded",
            aggregate_type="advising_session",
            aggregate_id=session_id,
            payload_json={
                "session_id": str(session_id),
                "student_id": str(student_id),
                "advisor_id": advisor_id,
                "session_type": session_type,
                "outcome_status": outcome_status,
                "outcome": outcome,
                "source_entity_type": "advising_session",
                "source_entity_id": str(session_id),
            },
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "advising.session.outcome.recorded event failed silently for tenant_id=%s session_id=%s",
            tenant_id,
            session_id,
        )


def _emit_status_changed_event(
    *,
    tenant_id: int,
    session_id: int,
    student_id: int,
    advisor_id: str,
    session_type: str,
    from_status: str,
    to_status: str,
) -> None:
    from app.platform.events.publisher import EventPublisher

    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="advising.session.status_changed",
        aggregate_type="advising_session",
        aggregate_id=session_id,
        payload_json={
            "session_id": str(session_id),
            "student_id": str(student_id),
            "advisor_id": advisor_id,
            "session_type": session_type,
            "from_status": from_status,
            "to_status": to_status,
            "source_entity_type": "advising_session",
            "source_entity_id": str(session_id),
        },
    )


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="advising_session",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def list_advising_sessions(
    tenant_id: int,
    status: AdvisingSessionStatus | None = None,
    student_id: int | None = None,
) -> list[AdvisingSessionSchema]:
    rows = list_entities_for_tenant("advising_sessions", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if student_id is not None:
        rows = [r for r in rows if int(r.get("student_id") or 0) == student_id]
    return [AdvisingSessionSchema.model_validate(r) for r in rows]


def create_advising_session(
    tenant_id: int,
    request: AdvisingSessionCreateSchema,
    actor: str,
) -> AdvisingSessionSchema:
    # W127: cross-entity guard — advisor must be active faculty (FIRST, before cap and enrollment)
    _check_advisor_is_active_faculty_for_advising(
        tenant_id=tenant_id,
        advisor_id=request.advisor_id.strip(),
    )

    session_type = str(request.session_type or "academic").strip().lower()
    cap = _SESSION_TYPE_MAX_ACTIVE.get(session_type, 100)
    existing = list_entities_for_tenant("advising_sessions", tenant_id)
    active_count = sum(
        1
        for s in existing
        if str(s.get("session_type") or "").strip().lower() == session_type
        and str(s.get("status") or "") in _ACTIVE_SESSION_STATUSES
    )
    if active_count >= cap:
        raise ValueError(
            f"Active advising session cap ({cap}) reached for session_type '{session_type}'"
        )

    # W100: enrollment guard — must be BEFORE persist
    _check_student_has_active_enrollment_for_advising(tenant_id, int(request.student_id))

    created = create_entity_for_tenant(
        "advising_sessions",
        {
            "student_id": int(request.student_id),
            "advisor_id": request.advisor_id.strip(),
            "session_type": request.session_type,
            "status": "scheduled",
            "scheduled_at": (request.scheduled_at or "unscheduled").strip() or "unscheduled",
            "notes": (request.notes or "n/a").strip() or "n/a",
            "outcome": "pending",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("advising", "session", "create"),
        path="/internal/advising/sessions",
        metadata={
            "resource_id": str(created.get("id")),
            "student_id": str(request.student_id),
            "advisor_id": request.advisor_id,
        },
        tenant_id=tenant_id,
    )

    # W40: side-effect alert for high-frequency session types
    if session_type in _HIGH_FREQUENCY_SESSION_TYPES:
        _ensure_support_alert_record(
            tenant_id=tenant_id,
            session_id=int(created.get("id") or 0),
            session_data={
                "student_id": request.student_id,
                "advisor_id": request.advisor_id,
                "session_type": session_type,
            },
        )

    return AdvisingSessionSchema.model_validate(created)


def _ensure_support_alert_record(
    tenant_id: int,
    session_id: int,
    session_data: dict,
) -> None:
    """Idempotent: create an advising_support_alerts entry for high-frequency personal sessions."""
    existing = list_entities_for_tenant("advising_support_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "advising_support"
            and str(rec.get("source_entity_id")) == str(session_id)
        ):
            return  # already exists
    create_entity_for_tenant(
        "advising_support_alerts",
        {
            "session_id": session_id,
            "student_id": int(session_data.get("student_id") or 0),
            "advisor_id": str(session_data.get("advisor_id") or ""),
            "session_type": str(session_data.get("session_type") or ""),
            "alert_status": "open",
            "integration_source": "advising_support",
            "source_entity_id": str(session_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def _ensure_no_show_risk_alert(
    tenant_id: int,
    session_id: int,
    session_data: dict,
) -> None:
    """Idempotent: create an advising_no_show_risk_alerts entry when session → no_show."""
    src = "advising_no_show_queue"
    src_id = str(session_id)
    existing = list_entities_for_tenant("advising_no_show_risk_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == src
            and str(rec.get("source_entity_id")) == src_id
        ):
            return  # idempotent
    create_entity_for_tenant(
        "advising_no_show_risk_alerts",
        {
            "session_id": session_id,
            "student_id": int(session_data.get("student_id") or 0),
            "advisor_id": str(session_data.get("advisor_id") or ""),
            "session_type": str(session_data.get("session_type") or "academic"),
            "alert_status": "open",
            "integration_source": src,
            "source_entity_id": src_id,
        },
        tenant_id,
    )
    try:
        from app.platform.events.publisher import EventPublisher

        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="campus.advising.no_show_risk_detected",
            aggregate_type="advising_sessions",
            aggregate_id=src_id,
            payload_json={
                "session_id": session_id,
                "student_id": int(session_data.get("student_id") or 0),
                "advisor_id": str(session_data.get("advisor_id") or ""),
                "session_type": str(session_data.get("session_type") or "academic"),
            },
        )
    except Exception:  # noqa: BLE001
        pass


def update_advising_session_status(
    tenant_id: int,
    session_id: int,
    request: AdvisingSessionStatusUpdateSchema,
    actor: str,
) -> AdvisingSessionSchema:
    rows = list_entities_for_tenant("advising_sessions", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == session_id), None)
    if existing is None:
        raise DomainValidationError(f"session {session_id} not found")

    current_status = str(existing.get("status") or "scheduled")
    if request.status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise DomainValidationError(
            f"transition from '{current_status}' to '{request.status}' is not allowed"
        )

    updated = update_entity_for_tenant(
        "advising_sessions",
        session_id,
        {
            "student_id": int(existing.get("student_id") or 0),
            "advisor_id": str(existing.get("advisor_id") or ""),
            "session_type": str(existing.get("session_type") or "academic"),
            "status": request.status,
            "scheduled_at": str(existing.get("scheduled_at") or "unscheduled"),
            "notes": str(existing.get("notes") or "n/a"),
            "outcome": (request.outcome or str(existing.get("outcome") or "pending")).strip() or "pending",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("advising", "session", "status_update"),
        path=f"/internal/advising/sessions/{session_id}/status",
        metadata={
            "resource_id": str(session_id),
            "old_status": current_status,
            "new_status": request.status,
        },
        tenant_id=tenant_id,
    )

    _emit_status_changed_event(
        tenant_id=tenant_id,
        session_id=session_id,
        student_id=int(existing.get("student_id") or 0),
        advisor_id=str(existing.get("advisor_id") or ""),
        session_type=str(existing.get("session_type") or "academic"),
        from_status=current_status,
        to_status=request.status,
    )
    record_usage_event(tenant_id=tenant_id, metric="advising_sessions_status_updated", value=1)

    # Emit brain feedback signal when session outcome is recorded
    if request.status in {"completed", "no_show", "cancelled"}:
        _emit_outcome_signal(
            tenant_id=tenant_id,
            session_id=session_id,
            student_id=int(existing.get("student_id") or 0),
            advisor_id=str(existing.get("advisor_id") or ""),
            session_type=str(existing.get("session_type") or "academic"),
            outcome_status=request.status,
            outcome=str(updated.get("outcome") or "pending"),
        )

        try:
            from app.modules.brain_core.service import brain_core_service

            brain_core_service.record_dispatch_outcome(
                str(session_id),
                payload={
                    "source_module": "advising",
                    "entity_type": "advising_session",
                    "outcome_type": request.status,
                    "outcome": str(updated.get("outcome") or "pending"),
                    "student_id": int(existing.get("student_id") or 0),
                    "advisor_id": str(existing.get("advisor_id") or ""),
                },
                actor=actor,
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "Failed to record advising session outcome in Brain Core for tenant_id=%s session_id=%s",
                tenant_id,
                session_id,
            )

        record_usage_event(tenant_id=tenant_id, metric="advising_session_outcomes_recorded", value=1)

    # W68: no-show risk alert side-effect
    if request.status in _NO_SHOW_RISK_STATUSES:
        _ensure_no_show_risk_alert(
            tenant_id=tenant_id,
            session_id=session_id,
            session_data={
                "student_id": int(existing.get("student_id") or 0),
                "advisor_id": str(existing.get("advisor_id") or ""),
                "session_type": str(existing.get("session_type") or "academic"),
            },
        )

    return AdvisingSessionSchema.model_validate(updated)
