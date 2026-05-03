"""Phase LI — Mobile App backend tests (20 tests)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MODULE = "app.modules.mobile_app.service"


def _make_token_row(
    token_id: int = 1,
    student_id: int = 101,
    platform: str = "ios",
    token: str = "tok-abc",
    status: str = "active",
) -> dict:
    return {
        "id": token_id,
        "student_id": student_id,
        "platform": platform,
        "token": token,
        "status": status,
    }


def _make_notif_row(
    notif_id: int = 10,
    student_id: int = 101,
    notification_type: str = "general",
    title: str = "Hello",
    body: str = "World",
    status: str = "sent",
) -> dict:
    return {
        "id": notif_id,
        "student_id": student_id,
        "notification_type": notification_type,
        "title": title,
        "body": body,
        "status": status,
    }


# ---------------------------------------------------------------------------
# register_device_token
# ---------------------------------------------------------------------------


def test_register_device_token_success():
    from app.modules.mobile_app.service import register_device_token, DeviceToken

    created = _make_token_row()
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=created) as mock_create,
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        result = register_device_token(
            student_id=101, platform="ios", token="tok-abc", tenant_id=5
        )

    assert isinstance(result, DeviceToken)
    assert result.token_id == 1
    assert result.platform == "ios"
    assert result.status == "active"
    mock_create.assert_called_once()
    mock_ep.publish.assert_called_once()
    assert mock_ep.publish.call_args.kwargs["event_type"] == "mobile.device_registered"


def test_register_device_token_invalid_platform():
    from app.modules.mobile_app.service import register_device_token, MobileAppError

    with pytest.raises(MobileAppError, match="invalid platform"):
        register_device_token(
            student_id=101, platform="blackberry", token="tok-abc", tenant_id=5
        )


def test_register_device_token_missing_token():
    from app.modules.mobile_app.service import register_device_token, MobileAppError

    with pytest.raises(MobileAppError, match="token is required"):
        register_device_token(
            student_id=101, platform="android", token="   ", tenant_id=5
        )


def test_register_device_token_missing_student_id():
    from app.modules.mobile_app.service import register_device_token, MobileAppError

    with pytest.raises(MobileAppError, match="student_id is required"):
        register_device_token(
            student_id=0, platform="android", token="tok-xyz", tenant_id=5
        )


def test_register_device_token_event_failure_swallowed():
    """Event publish errors must not propagate."""
    from app.modules.mobile_app.service import register_device_token

    created = _make_token_row()
    with (
        patch(f"{MODULE}.create_entity_for_tenant", return_value=created),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        mock_ep.publish.side_effect = RuntimeError("kafka down")
        result = register_device_token(
            student_id=101, platform="web", token="tok-web", tenant_id=5
        )

    assert result.status == "active"


# ---------------------------------------------------------------------------
# deactivate_device_token
# ---------------------------------------------------------------------------


def test_deactivate_device_token_success():
    from app.modules.mobile_app.service import deactivate_device_token, DeviceToken

    rows = [_make_token_row(token_id=1)]
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=rows),
        patch(f"{MODULE}.update_entity_for_tenant") as mock_update,
    ):
        result = deactivate_device_token(token_id=1, tenant_id=5)

    assert isinstance(result, DeviceToken)
    assert result.status == "inactive"
    mock_update.assert_called_once_with("device_tokens", 1, {"status": "inactive"}, 5)


def test_deactivate_device_token_not_found():
    from app.modules.mobile_app.service import deactivate_device_token, MobileAppError

    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        with pytest.raises(MobileAppError, match="not found"):
            deactivate_device_token(token_id=99, tenant_id=5)


def test_deactivate_device_token_wrong_tenant():
    from app.modules.mobile_app.service import deactivate_device_token, MobileAppError

    # tenant 5 has no token with id=99
    rows = [_make_token_row(token_id=1)]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        with pytest.raises(MobileAppError, match="not found"):
            deactivate_device_token(token_id=99, tenant_id=5)


def test_deactivate_device_token_invalid_id():
    from app.modules.mobile_app.service import deactivate_device_token, MobileAppError

    with pytest.raises(MobileAppError, match="token_id is required"):
        deactivate_device_token(token_id=0, tenant_id=5)


# ---------------------------------------------------------------------------
# list_device_tokens
# ---------------------------------------------------------------------------


def test_list_device_tokens_returns_student_tokens():
    from app.modules.mobile_app.service import list_device_tokens

    rows = [
        _make_token_row(token_id=1, student_id=101),
        _make_token_row(token_id=2, student_id=202),
    ]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        result = list_device_tokens(student_id=101, tenant_id=5)

    assert len(result) == 1
    assert result[0].token_id == 1


def test_list_device_tokens_empty():
    from app.modules.mobile_app.service import list_device_tokens

    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        result = list_device_tokens(student_id=101, tenant_id=5)

    assert result == []


# ---------------------------------------------------------------------------
# send_push_notification
# ---------------------------------------------------------------------------


def test_send_push_notification_success():
    from app.modules.mobile_app.service import send_push_notification, PushNotification

    token_rows = [_make_token_row(status="active")]
    notif_row = _make_notif_row(notif_id=10, status="sent")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=token_rows),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=notif_row),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        result = send_push_notification(
            student_id=101,
            notification_type="general",
            title="Hello",
            body="World",
            tenant_id=5,
        )

    assert isinstance(result, PushNotification)
    assert result.status == "sent"
    mock_ep.publish.assert_called_once()
    assert mock_ep.publish.call_args.kwargs["event_type"] == "mobile.notification_sent"


def test_send_push_notification_invalid_type():
    from app.modules.mobile_app.service import send_push_notification, MobileAppError

    with pytest.raises(MobileAppError, match="invalid notification_type"):
        send_push_notification(
            student_id=101,
            notification_type="unknown_type",
            title="Test",
            body="",
            tenant_id=5,
        )


def test_send_push_notification_missing_title():
    from app.modules.mobile_app.service import send_push_notification, MobileAppError

    with pytest.raises(MobileAppError, match="title is required"):
        send_push_notification(
            student_id=101,
            notification_type="general",
            title="",
            body="body",
            tenant_id=5,
        )


def test_send_push_notification_no_active_tokens_yields_failed():
    from app.modules.mobile_app.service import send_push_notification

    # All tokens inactive → status = failed
    token_rows = [_make_token_row(status="inactive")]
    notif_row = _make_notif_row(status="failed")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=token_rows),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=notif_row),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        result = send_push_notification(
            student_id=101,
            notification_type="system",
            title="Notice",
            body="",
            tenant_id=5,
        )

    assert result.status == "failed"
    assert mock_ep.publish.call_args.kwargs["event_type"] == "mobile.notification_failed"


def test_send_push_notification_force_fail_event():
    from app.modules.mobile_app.service import send_push_notification

    token_rows = [_make_token_row(status="active")]
    notif_row = _make_notif_row(status="failed")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=token_rows),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=notif_row),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
    ):
        result = send_push_notification(
            student_id=101,
            notification_type="grade_update",
            title="Grade",
            body="",
            tenant_id=5,
            _force_fail=True,
        )

    assert mock_ep.publish.call_args.kwargs["event_type"] == "mobile.notification_failed"


# ---------------------------------------------------------------------------
# send_bulk_notification
# ---------------------------------------------------------------------------


def test_send_bulk_notification_success():
    from app.modules.mobile_app.service import send_bulk_notification

    token_rows = [_make_token_row(status="active")]
    notif_row = _make_notif_row(status="sent")
    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=token_rows),
        patch(f"{MODULE}.create_entity_for_tenant", return_value=notif_row),
        patch(f"{MODULE}.EventPublisher"),
    ):
        results = send_bulk_notification(
            student_ids=[101, 102],
            notification_type="general",
            title="Bulk",
            body="msg",
            tenant_id=5,
        )

    assert len(results) == 2


def test_send_bulk_notification_empty_list():
    from app.modules.mobile_app.service import send_bulk_notification, MobileAppError

    with pytest.raises(MobileAppError, match="student_ids must not be empty"):
        send_bulk_notification(
            student_ids=[],
            notification_type="general",
            title="Bulk",
            body="msg",
            tenant_id=5,
        )


# ---------------------------------------------------------------------------
# list_notifications
# ---------------------------------------------------------------------------


def test_list_notifications_success():
    from app.modules.mobile_app.service import list_notifications

    rows = [
        _make_notif_row(notif_id=10, student_id=101),
        _make_notif_row(notif_id=11, student_id=202),
    ]
    with patch(f"{MODULE}.list_entities_for_tenant", return_value=rows):
        result = list_notifications(student_id=101, tenant_id=5)

    assert len(result) == 1
    assert result[0].notification_id == 10


def test_list_notifications_empty():
    from app.modules.mobile_app.service import list_notifications

    with patch(f"{MODULE}.list_entities_for_tenant", return_value=[]):
        result = list_notifications(student_id=101, tenant_id=5)

    assert result == []
