"""Phase LI — Mobile App Backend Service (device tokens & push notifications)."""
from __future__ import annotations

from dataclasses import dataclass

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

DEVICE_PLATFORMS = {"ios", "android", "web"}
TOKEN_STATES = {"active", "inactive", "invalid"}
NOTIFICATION_TYPES = {
    "general",
    "grade_update",
    "assignment_due",
    "payment_due",
    "request_ready",
    "system",
}
NOTIFICATION_STATUSES = {"pending", "sent", "failed"}


class MobileAppError(Exception):
    """Raised on invalid mobile app service input."""


@dataclass
class DeviceToken:
    token_id: int
    student_id: int
    platform: str
    token: str
    status: str
    tenant_id: int


@dataclass
class PushNotification:
    notification_id: int
    student_id: int
    notification_type: str
    title: str
    body: str
    status: str
    tenant_id: int


# ---------------------------------------------------------------------------
# Device token management
# ---------------------------------------------------------------------------


def register_device_token(
    *,
    student_id: int,
    platform: str,
    token: str,
    tenant_id: int,
) -> DeviceToken:
    """Register a push-notification device token for a student."""
    if not student_id or student_id <= 0:
        raise MobileAppError("student_id is required")
    if platform not in DEVICE_PLATFORMS:
        raise MobileAppError(f"invalid platform: {platform!r}; must be one of {DEVICE_PLATFORMS}")
    if not token or not token.strip():
        raise MobileAppError("token is required")

    record = create_entity_for_tenant(
        "device_tokens",
        {
            "student_id": student_id,
            "platform": platform,
            "token": token.strip(),
            "status": "active",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="mobile.device_registered",
            payload={"student_id": student_id, "platform": platform},
        )
    except Exception:
        pass

    return DeviceToken(
        token_id=record["id"],
        student_id=student_id,
        platform=platform,
        token=token.strip(),
        status="active",
        tenant_id=tenant_id,
    )


def deactivate_device_token(
    *,
    token_id: int,
    tenant_id: int,
) -> DeviceToken:
    """Mark a device token as inactive."""
    if not token_id or token_id <= 0:
        raise MobileAppError("token_id is required")

    tokens = list_entities_for_tenant("device_tokens", tenant_id)
    matched = [t for t in tokens if t["id"] == token_id]
    if not matched:
        raise MobileAppError(f"device token {token_id} not found for tenant {tenant_id}")

    existing = matched[0]
    update_entity_for_tenant(
        "device_tokens",
        token_id,
        {"status": "inactive"},
        tenant_id,
    )

    return DeviceToken(
        token_id=token_id,
        student_id=existing["student_id"],
        platform=existing["platform"],
        token=existing["token"],
        status="inactive",
        tenant_id=tenant_id,
    )


def list_device_tokens(
    *,
    student_id: int,
    tenant_id: int,
) -> list[DeviceToken]:
    """Return all device tokens for a student."""
    rows = list_entities_for_tenant("device_tokens", tenant_id)
    result = []
    for row in rows:
        if row.get("student_id") == student_id:
            result.append(
                DeviceToken(
                    token_id=row["id"],
                    student_id=row["student_id"],
                    platform=row["platform"],
                    token=row["token"],
                    status=row["status"],
                    tenant_id=tenant_id,
                )
            )
    return result


# ---------------------------------------------------------------------------
# Push notification sending
# ---------------------------------------------------------------------------


def send_push_notification(
    *,
    student_id: int,
    notification_type: str,
    title: str,
    body: str,
    tenant_id: int,
    _force_fail: bool = False,
) -> PushNotification:
    """Send a push notification to a student (fire-and-forget delivery)."""
    if not student_id or student_id <= 0:
        raise MobileAppError("student_id is required")
    if notification_type not in NOTIFICATION_TYPES:
        raise MobileAppError(f"invalid notification_type: {notification_type!r}")
    if not title or not title.strip():
        raise MobileAppError("title is required")

    # Check that the student has at least one active token
    tokens = list_entities_for_tenant("device_tokens", tenant_id)
    active_tokens = [
        t for t in tokens if t.get("student_id") == student_id and t.get("status") == "active"
    ]
    status = "failed" if (_force_fail or not active_tokens) else "sent"

    record = create_entity_for_tenant(
        "push_notifications",
        {
            "student_id": student_id,
            "notification_type": notification_type,
            "title": title.strip(),
            "body": body or "",
            "status": status,
        },
        tenant_id,
    )

    try:
        event_type = "mobile.notification_sent" if status == "sent" else "mobile.notification_failed"
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type=event_type,
            payload={"student_id": student_id, "notification_type": notification_type},
        )
    except Exception:
        pass

    return PushNotification(
        notification_id=record["id"],
        student_id=student_id,
        notification_type=notification_type,
        title=title.strip(),
        body=body or "",
        status=status,
        tenant_id=tenant_id,
    )


def send_bulk_notification(
    *,
    student_ids: list[int],
    notification_type: str,
    title: str,
    body: str,
    tenant_id: int,
) -> list[PushNotification]:
    """Send the same push notification to multiple students."""
    if not student_ids:
        raise MobileAppError("student_ids must not be empty")

    results = []
    for sid in student_ids:
        notif = send_push_notification(
            student_id=sid,
            notification_type=notification_type,
            title=title,
            body=body,
            tenant_id=tenant_id,
        )
        results.append(notif)
    return results


def list_notifications(
    *,
    student_id: int,
    tenant_id: int,
) -> list[PushNotification]:
    """Return all push notifications for a student."""
    rows = list_entities_for_tenant("push_notifications", tenant_id)
    result = []
    for row in rows:
        if row.get("student_id") == student_id:
            result.append(
                PushNotification(
                    notification_id=row["id"],
                    student_id=row["student_id"],
                    notification_type=row["notification_type"],
                    title=row["title"],
                    body=row.get("body", ""),
                    status=row["status"],
                    tenant_id=tenant_id,
                )
            )
    return result
