"""Phase LVIII — Parent Portal service."""
from __future__ import annotations

from dataclasses import dataclass

from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

PARENT_STATUSES = {"active", "inactive"}
LINK_STATUSES = {"active", "inactive"}
ALERT_STATUSES = {"unread", "read"}
ALERT_SEVERITIES = {"low", "medium", "high", "critical"}
RELATIONSHIP_TYPES = {"mother", "father", "guardian", "sponsor"}


class ParentPortalError(Exception):
    """Raised on invalid Parent Portal operations."""


@dataclass
class ParentProfile:
    parent_profile_id: int
    tenant_id: int
    parent_external_id: str
    full_name: str
    email: str
    phone: str
    status: str


@dataclass
class ParentStudentLink:
    link_id: int
    tenant_id: int
    parent_profile_id: int
    student_id: int
    relationship: str
    status: str


@dataclass
class ParentAlert:
    alert_id: int
    tenant_id: int
    parent_profile_id: int
    student_id: int
    alert_type: str
    severity: str
    status: str


@dataclass
class ParentDashboard:
    parent_profile_id: int
    tenant_id: int
    active_children: int
    unread_alerts: int


def register_parent(
    parent_external_id: str,
    full_name: str,
    email: str,
    phone: str,
    tenant_id: int,
) -> ParentProfile:
    """Register a parent profile and publish parent_portal.parent_registered."""
    if not parent_external_id or not parent_external_id.strip():
        raise ParentPortalError("parent_external_id is required")
    if not full_name or not full_name.strip():
        raise ParentPortalError("full_name is required")
    if "@" not in email:
        raise ParentPortalError("email is invalid")

    row = create_entity_for_tenant(
        "parent_profiles",
        {
            "parent_external_id": parent_external_id.strip(),
            "full_name": full_name.strip(),
            "email": email.strip().lower(),
            "phone": (phone or "").strip(),
            "status": "active",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="parent_portal.parent_registered",
            payload={"parent_profile_id": row["id"], "parent_external_id": parent_external_id},
        )
    except Exception:
        pass

    return ParentProfile(
        parent_profile_id=row["id"],
        tenant_id=tenant_id,
        parent_external_id=row["parent_external_id"],
        full_name=row["full_name"],
        email=row["email"],
        phone=row["phone"],
        status=row["status"],
    )


def link_student(
    parent_profile_id: int,
    student_id: int,
    relationship: str,
    tenant_id: int,
) -> ParentStudentLink:
    """Link a parent to student and publish parent_portal.student_linked."""
    if relationship not in RELATIONSHIP_TYPES:
        raise ParentPortalError(f"relationship must be one of {sorted(RELATIONSHIP_TYPES)}")

    links = list_entities_for_tenant("parent_student_links", tenant_id)
    for link in links:
        if (
            link.get("parent_profile_id") == parent_profile_id
            and link.get("student_id") == student_id
            and link.get("status") == "active"
        ):
            raise ParentPortalError("active parent-student link already exists")

    row = create_entity_for_tenant(
        "parent_student_links",
        {
            "parent_profile_id": parent_profile_id,
            "student_id": student_id,
            "relationship": relationship,
            "status": "active",
            "unlink_reason": "",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="parent_portal.student_linked",
            payload={
                "parent_profile_id": parent_profile_id,
                "student_id": student_id,
                "relationship": relationship,
            },
        )
    except Exception:
        pass

    return ParentStudentLink(
        link_id=row["id"],
        tenant_id=tenant_id,
        parent_profile_id=row["parent_profile_id"],
        student_id=row["student_id"],
        relationship=row["relationship"],
        status=row["status"],
    )


def unlink_student(link_id: int, reason: str, tenant_id: int) -> ParentStudentLink:
    """Deactivate parent-student link."""
    if not reason or not reason.strip():
        raise ParentPortalError("reason is required")

    links = list_entities_for_tenant("parent_student_links", tenant_id)
    matched = [link for link in links if link.get("id") == link_id]
    if not matched:
        raise ParentPortalError(f"link {link_id} not found")

    link = matched[0]
    if link.get("status") != "active":
        raise ParentPortalError("link is not active")

    update_entity_for_tenant(
        "parent_student_links",
        link_id,
        {"status": "inactive", "unlink_reason": reason.strip()},
        tenant_id,
    )

    return ParentStudentLink(
        link_id=link_id,
        tenant_id=tenant_id,
        parent_profile_id=link["parent_profile_id"],
        student_id=link["student_id"],
        relationship=link["relationship"],
        status="inactive",
    )


def list_children(parent_profile_id: int, tenant_id: int) -> list[ParentStudentLink]:
    """List active and inactive children links for a parent."""
    links = list_entities_for_tenant("parent_student_links", tenant_id)
    return [
        ParentStudentLink(
            link_id=link["id"],
            tenant_id=tenant_id,
            parent_profile_id=link["parent_profile_id"],
            student_id=link["student_id"],
            relationship=link["relationship"],
            status=link["status"],
        )
        for link in links
        if link.get("parent_profile_id") == parent_profile_id
    ]


def push_alert(
    parent_profile_id: int,
    student_id: int,
    alert_type: str,
    message: str,
    severity: str,
    tenant_id: int,
) -> ParentAlert:
    """Create unread alert and publish parent_portal.alert_pushed."""
    if not alert_type or not alert_type.strip():
        raise ParentPortalError("alert_type is required")
    if not message or not message.strip():
        raise ParentPortalError("message is required")
    if severity not in ALERT_SEVERITIES:
        raise ParentPortalError(f"severity must be one of {sorted(ALERT_SEVERITIES)}")

    row = create_entity_for_tenant(
        "parent_alerts",
        {
            "parent_profile_id": parent_profile_id,
            "student_id": student_id,
            "alert_type": alert_type.strip(),
            "message": message.strip(),
            "severity": severity,
            "status": "unread",
        },
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="parent_portal.alert_pushed",
            payload={
                "alert_id": row["id"],
                "parent_profile_id": parent_profile_id,
                "student_id": student_id,
                "severity": severity,
            },
        )
    except Exception:
        pass

    return ParentAlert(
        alert_id=row["id"],
        tenant_id=tenant_id,
        parent_profile_id=row["parent_profile_id"],
        student_id=row["student_id"],
        alert_type=row["alert_type"],
        severity=row["severity"],
        status=row["status"],
    )


def list_alerts(
    parent_profile_id: int,
    tenant_id: int,
    unread_only: bool = False,
) -> list[ParentAlert]:
    """List parent alerts with optional unread filter."""
    alerts = list_entities_for_tenant("parent_alerts", tenant_id)

    filtered = [
        alert
        for alert in alerts
        if alert.get("parent_profile_id") == parent_profile_id
        and (not unread_only or alert.get("status") == "unread")
    ]

    return [
        ParentAlert(
            alert_id=alert["id"],
            tenant_id=tenant_id,
            parent_profile_id=alert["parent_profile_id"],
            student_id=alert["student_id"],
            alert_type=alert["alert_type"],
            severity=alert["severity"],
            status=alert["status"],
        )
        for alert in filtered
    ]


def acknowledge_alert(alert_id: int, parent_profile_id: int, tenant_id: int) -> ParentAlert:
    """Mark an alert as read and publish parent_portal.alert_acknowledged."""
    alerts = list_entities_for_tenant("parent_alerts", tenant_id)
    matched = [
        alert
        for alert in alerts
        if alert.get("id") == alert_id and alert.get("parent_profile_id") == parent_profile_id
    ]
    if not matched:
        raise ParentPortalError(f"alert {alert_id} not found")

    alert = matched[0]
    if alert.get("status") == "read":
        raise ParentPortalError("alert is already acknowledged")

    update_entity_for_tenant(
        "parent_alerts",
        alert_id,
        {"status": "read"},
        tenant_id,
    )

    try:
        EventPublisher.publish(
            tenant_id=tenant_id,
            event_type="parent_portal.alert_acknowledged",
            payload={"alert_id": alert_id, "parent_profile_id": parent_profile_id},
        )
    except Exception:
        pass

    return ParentAlert(
        alert_id=alert_id,
        tenant_id=tenant_id,
        parent_profile_id=parent_profile_id,
        student_id=alert["student_id"],
        alert_type=alert["alert_type"],
        severity=alert["severity"],
        status="read",
    )


def get_parent_dashboard(parent_profile_id: int, tenant_id: int) -> ParentDashboard:
    """Return dashboard counters for children and unread alerts."""
    links = list_entities_for_tenant("parent_student_links", tenant_id)
    alerts = list_entities_for_tenant("parent_alerts", tenant_id)

    active_children = sum(
        1
        for link in links
        if link.get("parent_profile_id") == parent_profile_id and link.get("status") == "active"
    )
    unread_alerts = sum(
        1
        for alert in alerts
        if alert.get("parent_profile_id") == parent_profile_id and alert.get("status") == "unread"
    )

    return ParentDashboard(
        parent_profile_id=parent_profile_id,
        tenant_id=tenant_id,
        active_children=active_children,
        unread_alerts=unread_alerts,
    )
