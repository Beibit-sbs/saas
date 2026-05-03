"""Phase LVIII — Parent Portal tests (24 tests)."""
from __future__ import annotations

from unittest.mock import patch

import pytest

MODULE = "app.modules.parent_portal.service"


def _profile(
    id: int = 1,
    parent_external_id: str = "P-001",
    full_name: str = "Parent One",
    email: str = "parent@example.com",
    phone: str = "+77010000000",
    status: str = "active",
) -> dict:
    return {
        "id": id,
        "parent_external_id": parent_external_id,
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "status": status,
    }


def _link(
    id: int = 10,
    parent_profile_id: int = 1,
    student_id: int = 100,
    relationship: str = "mother",
    status: str = "active",
    unlink_reason: str = "",
) -> dict:
    return {
        "id": id,
        "parent_profile_id": parent_profile_id,
        "student_id": student_id,
        "relationship": relationship,
        "status": status,
        "unlink_reason": unlink_reason,
    }


def _alert(
    id: int = 50,
    parent_profile_id: int = 1,
    student_id: int = 100,
    alert_type: str = "attendance_low",
    message: str = "Attendance below threshold",
    severity: str = "high",
    status: str = "unread",
) -> dict:
    return {
        "id": id,
        "parent_profile_id": parent_profile_id,
        "student_id": student_id,
        "alert_type": alert_type,
        "message": message,
        "severity": severity,
        "status": status,
    }


def test_register_parent_success():
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_profile()) as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.parent_portal import service

        result = service.register_parent("P-001", "Parent One", "Parent@EXAMPLE.com", "+7", 1)

    assert result.parent_profile_id == 1
    assert result.email == "parent@example.com"
    mock_create.assert_called_once()
    mock_pub.publish.assert_called_once()


def test_register_parent_invalid_external_id():
    from app.modules.parent_portal.service import ParentPortalError, register_parent

    with pytest.raises(ParentPortalError, match="parent_external_id"):
        register_parent("", "Parent", "p@example.com", "+7", 1)


def test_register_parent_invalid_name():
    from app.modules.parent_portal.service import ParentPortalError, register_parent

    with pytest.raises(ParentPortalError, match="full_name"):
        register_parent("P-1", "", "p@example.com", "+7", 1)


def test_register_parent_invalid_email():
    from app.modules.parent_portal.service import ParentPortalError, register_parent

    with pytest.raises(ParentPortalError, match="email"):
        register_parent("P-1", "Parent", "invalid", "+7", 1)


def test_register_parent_event_failure_suppressed():
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_profile()),
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        mock_pub.publish.side_effect = RuntimeError("down")
        from app.modules.parent_portal import service

        result = service.register_parent("P-001", "Parent One", "p@example.com", "+7", 1)

    assert result.parent_profile_id == 1


def test_link_student_success():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_link()) as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.parent_portal import service

        result = service.link_student(1, 100, "mother", 1)

    assert result.link_id == 10
    assert result.relationship == "mother"
    mock_create.assert_called_once()
    mock_pub.publish.assert_called_once()


def test_link_student_invalid_relationship():
    from app.modules.parent_portal.service import ParentPortalError, link_student

    with pytest.raises(ParentPortalError, match="relationship"):
        link_student(1, 100, "neighbor", 1)


def test_link_student_duplicate_active():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_link()]):
        from app.modules.parent_portal.service import ParentPortalError, link_student

        with pytest.raises(ParentPortalError, match="already exists"):
            link_student(1, 100, "mother", 1)


def test_link_student_event_failure_suppressed():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_link()),
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        mock_pub.publish.side_effect = RuntimeError("down")
        from app.modules.parent_portal import service

        result = service.link_student(1, 100, "mother", 1)

    assert result.status == "active"


def test_unlink_student_success():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[_link()]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        from app.modules.parent_portal import service

        result = service.unlink_student(10, "graduated", 1)

    assert result.status == "inactive"
    mock_update.assert_called_once_with(
        "parent_student_links",
        10,
        {"status": "inactive", "unlink_reason": "graduated"},
        1,
    )


def test_unlink_student_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.parent_portal.service import ParentPortalError, unlink_student

        with pytest.raises(ParentPortalError, match="not found"):
            unlink_student(999, "x", 1)


def test_unlink_student_not_active():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_link(status="inactive")]):
        from app.modules.parent_portal.service import ParentPortalError, unlink_student

        with pytest.raises(ParentPortalError, match="not active"):
            unlink_student(10, "x", 1)


def test_unlink_student_missing_reason():
    from app.modules.parent_portal.service import ParentPortalError, unlink_student

    with pytest.raises(ParentPortalError, match="reason"):
        unlink_student(10, "", 1)


def test_list_children_filters_parent():
    rows = [_link(id=10, parent_profile_id=1), _link(id=11, parent_profile_id=2), _link(id=12, parent_profile_id=1)]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        from app.modules.parent_portal import service

        links = service.list_children(1, 1)

    assert len(links) == 2
    assert all(item.parent_profile_id == 1 for item in links)


def test_push_alert_success():
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_alert()) as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.parent_portal import service

        result = service.push_alert(1, 100, "attendance_low", "msg", "high", 1)

    assert result.alert_id == 50
    assert result.status == "unread"
    mock_create.assert_called_once()
    mock_pub.publish.assert_called_once()


def test_push_alert_invalid_type():
    from app.modules.parent_portal.service import ParentPortalError, push_alert

    with pytest.raises(ParentPortalError, match="alert_type"):
        push_alert(1, 100, "", "msg", "high", 1)


def test_push_alert_invalid_message():
    from app.modules.parent_portal.service import ParentPortalError, push_alert

    with pytest.raises(ParentPortalError, match="message"):
        push_alert(1, 100, "attendance_low", "", "high", 1)


def test_push_alert_invalid_severity():
    from app.modules.parent_portal.service import ParentPortalError, push_alert

    with pytest.raises(ParentPortalError, match="severity"):
        push_alert(1, 100, "attendance_low", "msg", "urgent", 1)


def test_push_alert_event_failure_suppressed():
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=_alert()),
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        mock_pub.publish.side_effect = RuntimeError("down")
        from app.modules.parent_portal import service

        result = service.push_alert(1, 100, "attendance_low", "msg", "high", 1)

    assert result.status == "unread"


def test_list_alerts_filters_parent():
    rows = [_alert(id=1, parent_profile_id=1), _alert(id=2, parent_profile_id=2), _alert(id=3, parent_profile_id=1)]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        from app.modules.parent_portal import service

        alerts = service.list_alerts(1, 1)

    assert len(alerts) == 2
    assert all(item.parent_profile_id == 1 for item in alerts)


def test_list_alerts_unread_only():
    rows = [_alert(id=1, status="unread"), _alert(id=2, status="read"), _alert(id=3, status="unread")]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        from app.modules.parent_portal import service

        alerts = service.list_alerts(1, 1, unread_only=True)

    assert len(alerts) == 2
    assert all(item.status == "unread" for item in alerts)


def test_acknowledge_alert_success():
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[_alert()]),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
        patch(f"{MODULE}.EventPublisher") as mock_pub,
    ):
        from app.modules.parent_portal import service

        result = service.acknowledge_alert(50, 1, 1)

    assert result.status == "read"
    mock_update.assert_called_once_with("parent_alerts", 50, {"status": "read"}, 1)
    mock_pub.publish.assert_called_once()


def test_acknowledge_alert_not_found():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        from app.modules.parent_portal.service import ParentPortalError, acknowledge_alert

        with pytest.raises(ParentPortalError, match="not found"):
            acknowledge_alert(50, 1, 1)


def test_acknowledge_alert_already_read():
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[_alert(status="read")]):
        from app.modules.parent_portal.service import ParentPortalError, acknowledge_alert

        with pytest.raises(ParentPortalError, match="already acknowledged"):
            acknowledge_alert(50, 1, 1)


def test_get_parent_dashboard_counts_children_and_unread():
    links = [_link(id=1, parent_profile_id=1, status="active"), _link(id=2, parent_profile_id=1, status="inactive"), _link(id=3, parent_profile_id=1, status="active")]
    alerts = [_alert(id=1, parent_profile_id=1, status="unread"), _alert(id=2, parent_profile_id=1, status="read"), _alert(id=3, parent_profile_id=1, status="unread")]

    with patch(f"{MODULE}.list_entities_for_tenant", side_effect=[links, alerts]):
        from app.modules.parent_portal import service

        dashboard = service.get_parent_dashboard(1, 1)

    assert dashboard.active_children == 2
    assert dashboard.unread_alerts == 2
