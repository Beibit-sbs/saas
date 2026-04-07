"""
Automation action executors.

Each action takes:
- action: dict  — the action definition from rule.actions_json
- event: OutboxEventRead
- uow: UnitOfWork

Returns a dict describing what happened. Raises on hard failure.
"""
from __future__ import annotations

import logging
from typing import Any

from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork

logger = logging.getLogger("app.platform.automation.actions")


# ------------------------------------------------------------------ #
#  Individual action executors                                         #
# ------------------------------------------------------------------ #

def send_notification(
    action: dict[str, Any],
    event: OutboxEventRead,
    *,
    uow: UnitOfWork,
) -> dict[str, Any]:
    """
    Dispatch an in-app or email notification.

    Expected action shape:
        {"type": "send_notification", "channel": "email", "template": "student_risk"}
    """
    channel = str(action.get("channel", "in_app")).lower()
    template = str(action.get("template", "automation_alert"))

    notification = uow.notification_repository.dispatch(
        tenant_id=event.tenant_id,
        channel=channel if channel in {"email", "in_app", "webhook"} else "in_app",
        target=f"tenant:{event.tenant_id}",
        subject=template,
        payload={
            "automation_action": "send_notification",
            "template": template,
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": event.aggregate_id,
            "event_payload": event.payload_json,
        },
        conn=uow.conn,
    )
    notification_id = int(notification["id"])
    uow.notification_repository.mark_status(
        notification_id,
        status="sent",
        last_error=None,
        increment_retry=False,
        conn=uow.conn,
    )
    logger.info(
        "automation_action_send_notification",
        extra={"notification_id": notification_id, "template": template},
    )
    return {"action": "send_notification", "notification_id": notification_id, "template": template}


def create_task(
    action: dict[str, Any],
    event: OutboxEventRead,
    *,
    uow: UnitOfWork,
) -> dict[str, Any]:
    """
    Enqueue a background job/task.

    Expected action shape:
        {"type": "create_task", "job_type": "remediation_review", "max_retries": 3}
    """
    job_type = str(action.get("job_type", "automation_task"))
    max_retries = int(action.get("max_retries", 3))

    job = uow.job_repository.enqueue(
        tenant_id=event.tenant_id,
        job_type=job_type,
        payload={
            "automation_action": "create_task",
            "event_type": event.event_type,
            "aggregate_type": event.aggregate_type,
            "aggregate_id": event.aggregate_id,
            "event_payload": event.payload_json,
        },
        max_retries=max_retries,
        conn=uow.conn,
    )
    job_id = int(job["id"])
    logger.info(
        "automation_action_create_task",
        extra={"job_id": job_id, "job_type": job_type},
    )
    return {"action": "create_task", "job_id": job_id, "job_type": job_type}


def emit_event(
    action: dict[str, Any],
    event: OutboxEventRead,
    *,
    uow: UnitOfWork,
) -> dict[str, Any]:
    """
    Emit a new outbox event (chained workflow step).

    Expected action shape:
        {"type": "emit_event", "event_type": "academic_alert.created",
         "aggregate_type": "academic_alert"}
    """
    from app.platform.events.publisher import EventPublisher

    new_event_type = str(action.get("event_type", "automation.action_executed"))
    aggregate_type = str(action.get("aggregate_type", event.aggregate_type))

    publisher = EventPublisher(uow=uow)
    new_event = publisher.publish_event(
        tenant_id=event.tenant_id,
        event_type=new_event_type,
        aggregate_type=aggregate_type,
        aggregate_id=event.aggregate_id,
        payload_json={
            "automation_action": "emit_event",
            "source_event_type": event.event_type,
            "source_aggregate_id": event.aggregate_id,
            "event_payload": event.payload_json,
        },
        causation_id=str(event.id),
        correlation_id=event.correlation_id,
    )
    new_event_id = int(new_event["id"])
    logger.info(
        "automation_action_emit_event",
        extra={"new_event_id": new_event_id, "new_event_type": new_event_type},
    )
    return {"action": "emit_event", "new_event_id": new_event_id, "new_event_type": new_event_type}


# ------------------------------------------------------------------ #
#  Registry                                                            #
# ------------------------------------------------------------------ #

_ACTION_REGISTRY: dict[str, Any] = {
    "send_notification": send_notification,
    "create_task": create_task,
    "emit_event": emit_event,
}


def execute_action(
    action: dict[str, Any],
    event: OutboxEventRead,
    *,
    uow: UnitOfWork,
) -> dict[str, Any]:
    """Dispatch a single action dict to the correct executor."""
    action_type = str(action.get("type", ""))
    executor = _ACTION_REGISTRY.get(action_type)
    if executor is None:
        raise ValueError(f"Unknown automation action type: {action_type!r}")
    return executor(action, event, uow=uow)
