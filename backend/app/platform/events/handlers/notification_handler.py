from __future__ import annotations

from typing import Any

from app.platform.events.schemas import OutboxEventRead
from app.platform.uow import UnitOfWork


class NotificationEventHandler:
    name = "notification"

    _SUBJECTS = {
        "tenant.created": "Tenant created",
        "student.created": "Student created",
        "enrollment.created": "Enrollment created",
        "grade.submitted": "Grade submitted",
    }

    def handle(self, event: OutboxEventRead, *, uow: UnitOfWork) -> dict[str, Any]:
        subject = self._SUBJECTS.get(event.event_type)
        if subject is None:
            return {"handler": self.name, "status": "skipped"}

        notification = uow.notification_repository.dispatch(
            tenant_id=event.tenant_id,
            channel="in_app",
            target=f"tenant:{event.tenant_id}",
            subject=subject,
            payload={
                "event_type": event.event_type,
                "aggregate_type": event.aggregate_type,
                "aggregate_id": event.aggregate_id,
                "payload": event.payload_json,
            },
            conn=uow.conn,
        )
        uow.notification_repository.mark_status(
            int(notification["id"]),
            status="sent",
            last_error=None,
            increment_retry=False,
            conn=uow.conn,
        )
        return {
            "handler": self.name,
            "status": "processed",
            "notification_id": int(notification["id"]),
        }