from __future__ import annotations

import logging

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.advising.schemas import (
    AdvisingSessionCreateSchema,
    AdvisingSessionSchema,
    AdvisingSessionStatus,
    AdvisingSessionStatusUpdateSchema,
)
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
    return AdvisingSessionSchema.model_validate(created)


def update_advising_session_status(
    tenant_id: int,
    session_id: int,
    request: AdvisingSessionStatusUpdateSchema,
    actor: str,
) -> AdvisingSessionSchema:
    rows = list_entities_for_tenant("advising_sessions", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == session_id), None)
    if existing is None:
        raise ValueError(f"session {session_id} not found")

    current_status = str(existing.get("status") or "scheduled")
    if request.status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(
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

    return AdvisingSessionSchema.model_validate(updated)
