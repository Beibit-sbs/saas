"""Phase VIII-1: Communications service."""
from __future__ import annotations

import logging

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.usage.service import record_usage_event
from app.platform.events.publisher import EventPublisher
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
)


logger = logging.getLogger("app.modules.communications")

# W37: cap on active (draft/pending/sending) messages per message_type
_MESSAGE_TYPE_MAX_ACTIVE: dict[str, int] = {
    "announcement": 10,
    "alert": 5,
    "newsletter": 3,
    "reminder": 20,
    "emergency": 2,
    "other": 15,
}

_ACTIVE_MESSAGE_STATUSES: frozenset[str] = frozenset({"draft", "pending", "sending"})

# W37: broadcast threshold requiring an audit log entry
_LARGE_AUDIENCE_THRESHOLD: int = 500

# W60: broadcast risk constant
_BROADCAST_RISK_STATUSES: frozenset[str] = frozenset({"sent", "delivered"})

# W117: student audience must be validated against active enrollment population
_STUDENT_AUDIENCE_TARGETS: frozenset[str] = frozenset({"students", "student", "all_students"})
_ACTIVE_ENROLLMENT_STATUSES: frozenset[str] = frozenset({"active", "enrolled", "registered"})


def _record_outcome(entity_id: int, outcome_type: str, actor_id: str = "system") -> None:
    try:
        from app.modules.brain_core import service as brain_core_service

        brain_core_service.record_dispatch_outcome(
            signal_id=str(entity_id),
            outcome=outcome_type,
            metadata={"actor_id": actor_id, "module": "communications"},
        )
    except Exception:
        logger.exception(
            "communications outcome failed entity_id=%s outcome=%s",
            entity_id,
            outcome_type,
        )


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:
        logger.exception("communications metric failed metric=%s", metric)


def _check_student_audience_population(
    *,
    tenant_id: int,
    target_audience: str,
    recipients_count: int,
    message_code: str,
) -> None:
    """W117: Cross-entity guard — communication_messages × enrollments.

    Student-targeted communications are only valid when there is a verifiable
    active enrollment population. This prevents ghost campaigns with fabricated
    recipient counts and protects delivery KPIs from synthetic inflation.

    FAIL-CLOSED: if enrollments lookup fails, message creation is blocked.
    """
    audience = str(target_audience or "").strip().lower()
    if audience not in _STUDENT_AUDIENCE_TARGETS:
        return

    try:
        enrollments = list_entities_for_tenant("enrollments", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            "Student-targeted communication blocked: enrollments lookup failed. "
            f"message_code='{message_code}', target_audience='{target_audience}'. "
            "Cannot verify active student population."
        ) from exc

    active_enrollments = [
        row
        for row in enrollments
        if str(row.get("status") or row.get("enrollment_status") or "").strip().lower()
        in _ACTIVE_ENROLLMENT_STATUSES
    ]
    active_population = len(active_enrollments)

    if active_population <= 0:
        raise DomainValidationError(
            "Student-targeted communication blocked: no active enrollments found for tenant. "
            f"message_code='{message_code}', target_audience='{target_audience}'. "
            "Cannot send to students when active population is zero."
        )

    if recipients_count > active_population:
        raise DomainValidationError(
            "Student-targeted communication blocked: recipients_count exceeds active "
            f"enrollment population (recipients_count={recipients_count}, active_population={active_population}). "
            f"message_code='{message_code}', target_audience='{target_audience}'."
        )


def list_messages(
    tenant_id: int,
    message_type: str | None = None,
    status: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("communication_messages", tenant_id)
    type_filter = str(message_type or "").strip().lower()
    status_filter = str(status or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if type_filter and str(row.get("message_type") or "").strip().lower() != type_filter:
            continue
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        result.append(row)
    return result


def create_message(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    recipients = int(payload.get("recipients_count") or 0)
    _check_student_audience_population(
        tenant_id=tenant_id,
        target_audience=str(payload.get("target_audience") or ""),
        recipients_count=recipients,
        message_code=str(payload.get("message_code") or ""),
    )

    msg_type = str(payload.get("message_type") or "other").strip().lower()
    cap = _MESSAGE_TYPE_MAX_ACTIVE.get(msg_type, _MESSAGE_TYPE_MAX_ACTIVE["other"])
    existing = list_entities_for_tenant("communication_messages", tenant_id)
    active_count = sum(
        1
        for m in existing
        if str(m.get("message_type") or "").strip().lower() == msg_type
        and str(m.get("status") or "") in _ACTIVE_MESSAGE_STATUSES
    )
    if active_count >= cap:
        raise ValueError(
            f"Active message cap ({cap}) reached for message_type '{msg_type}'"
        )

    record = create_entity_for_tenant("communication_messages", payload, tenant_id)
    _record_outcome(int(record.get("id") or 0), "communication_message_created")
    _metric(tenant_id, "communication_messages_created", 1)

    if recipients >= _LARGE_AUDIENCE_THRESHOLD:
        _ensure_broadcast_audit_record(
            tenant_id=tenant_id,
            message_id=int(record.get("id") or 0),
            message_data={
                "message_code": payload.get("message_code"),
                "message_type": payload.get("message_type"),
                "recipients_count": recipients,
            },
        )
        _ensure_broadcast_risk_alert(
            tenant_id=tenant_id,
            message_id=int(record.get("id") or 0),
            message_data={
                "message_code": payload.get("message_code"),
                "message_type": payload.get("message_type"),
                "recipients_count": recipients,
                "status": payload.get("status", "draft"),
            },
        )

    return record


def _ensure_broadcast_audit_record(
    tenant_id: int,
    message_id: int,
    message_data: dict,
) -> None:
    """Idempotent: create a communication_broadcast_audits entry for large-audience messages."""
    existing = list_entities_for_tenant("communication_broadcast_audits", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "communications_broadcast"
            and str(rec.get("source_entity_id")) == str(message_id)
        ):
            return  # already exists
    create_entity_for_tenant(
        "communication_broadcast_audits",
        {
            "message_id": message_id,
            "message_code": str(message_data.get("message_code") or ""),
            "message_type": str(message_data.get("message_type") or ""),
            "recipients_count": int(message_data.get("recipients_count") or 0),
            "audit_status": "logged",
            "integration_source": "communications_broadcast",
            "source_entity_id": str(message_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def _ensure_broadcast_risk_alert(
    tenant_id: int,
    message_id: int,
    message_data: dict,
) -> None:
    """Idempotent: creates one broadcast risk alert per large-audience message."""
    existing = list_entities_for_tenant("communication_broadcast_risk_alerts", tenant_id)
    already_exists = any(
        str(r.get("integration_source")) == "communications_broadcast_risk_queue"
        and str(r.get("source_entity_id")) == str(message_id)
        for r in existing
    )
    if already_exists:
        return
    create_entity_for_tenant(
        "communication_broadcast_risk_alerts",
        {
            "message_id": message_id,
            "message_code": message_data.get("message_code"),
            "message_type": message_data.get("message_type"),
            "recipients_count": message_data.get("recipients_count"),
            "status": message_data.get("status"),
            "alert_level": "high",
            "risk_status": "large_audience",
            "integration_source": "communications_broadcast_risk_queue",
            "source_entity_id": str(message_id),
        },
        tenant_id,
    )
    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.communications.broadcast_risk_detected",
        aggregate_type="communication_message",
        aggregate_id=str(message_id),
        payload_json={
            "message_code": message_data.get("message_code"),
            "message_type": message_data.get("message_type"),
            "recipients_count": message_data.get("recipients_count"),
            "risk_status": "large_audience",
            "source_entity_id": str(message_id),
        },
    )


def get_communications_brain_context(tenant_id: int) -> dict[str, object]:
    messages = list_entities_for_tenant("communication_messages", tenant_id)

    total_messages = len(messages)
    sent_messages = sum(
        1 for r in messages if str(r.get("status") or "").strip().lower() in {"sent", "delivered"}
    )

    total_recipients = sum(int(r.get("recipients_count") or 0) for r in messages)
    total_delivered = sum(int(r.get("delivered_count") or 0) for r in messages)
    total_opened = sum(int(r.get("opened_count") or 0) for r in messages)

    delivery_rate = round(total_delivered / total_recipients, 4) if total_recipients > 0 else 0.0
    open_rate = round(total_opened / total_delivered, 4) if total_delivered > 0 else 0.0

    if delivery_rate < 0.5:
        delivery_health = "poor"
    elif delivery_rate < 0.8:
        delivery_health = "fair"
    else:
        delivery_health = "good"

    return {
        "module": "communications",
        "tenant_id": tenant_id,
        "total_messages": total_messages,
        "sent_messages": sent_messages,
        "delivery_rate": delivery_rate,
        "open_rate": open_rate,
        "delivery_health": delivery_health,
    }
