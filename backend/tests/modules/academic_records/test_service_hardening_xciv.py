"""XCIV — Academic Records Service Hardening Tests.

Verifies:
1. create_record uses canonical EventPublisher constructor and records metric.
2. create_record uses canonical tenant API positional arguments.
3. update_record survives publish failure (fire-and-forget) and still records metric.
4. delete_record uses canonical EventPublisher constructor and records metric.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

MODULE = "app.modules.academic_records.service"


def test_create_record_uses_canonical_event_publisher_and_metric() -> None:
    payload = {
        "student_id": 1,
        "course_id": 1,
        "semester": "Fall 2025",
        "status": "draft",
    }

    with (
        patch(f"{MODULE}._check_enrollment_exists_for_academic_record", return_value=None),
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[]),
        patch(f"{MODULE}.create_entity_for_tenant", return_value={"id": 11, **payload}),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
    ):
        from app.modules.academic_records import service as svc

        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        result = svc.create_record(payload, tenant_id=1, actor="admin@test.com")

    assert result["id"] == 11
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    mock_metric.assert_called_once_with(tenant_id=1, metric="academic_records_created", value=1)


def test_create_record_uses_canonical_tenant_api_positional_args() -> None:
    payload = {
        "student_id": 2,
        "course_id": 3,
        "semester": "Fall 2025",
        "status": "pending",
    }

    mock_list = MagicMock(return_value=[])
    mock_create = MagicMock(return_value={"id": 12, **payload})

    with (
        patch(f"{MODULE}._check_enrollment_exists_for_academic_record", return_value=None),
        patch(f"{MODULE}.list_entities_for_tenant", mock_list),
        patch(f"{MODULE}.create_entity_for_tenant", mock_create),
        patch(f"{MODULE}.EventPublisher.publish_event", return_value=None),
        patch(f"{MODULE}.record_usage_event"),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        from app.modules.academic_records import service as svc

        svc.create_record(payload, tenant_id=1)

    list_args, list_kwargs = mock_list.call_args
    assert len(list_args) == 2
    assert list_args[0] == "academic_records"
    assert list_args[1] == 1
    assert "tenant_id" not in list_kwargs

    create_args, create_kwargs = mock_create.call_args
    assert len(create_args) == 3
    assert create_args[0] == "academic_records"
    assert create_args[2] == 1
    assert "tenant_id" not in create_kwargs


def test_update_record_survives_publish_failure_and_records_metric() -> None:
    updated = {"id": 77, "status": "draft", "grade": "B+"}

    with (
        patch(f"{MODULE}._check_record_not_published", return_value=None),
        patch(f"{MODULE}.update_entity_for_tenant", return_value=updated),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        from app.modules.academic_records import service as svc

        pub = MagicMock()
        pub.publish_event.side_effect = RuntimeError("broker down")
        mock_ep.return_value = pub

        result = svc.update_record(77, {"grade": "B+", "status": "draft"}, tenant_id=1, actor="admin@test.com")

    assert result["id"] == 77
    mock_ep.assert_called_once_with()
    mock_metric.assert_called_once_with(tenant_id=1, metric="academic_records_updated", value=1)


def test_delete_record_uses_canonical_event_publisher_and_metric() -> None:
    deleted = {"id": 55, "student_id": 1, "course_id": 2}

    with (
        patch(f"{MODULE}.delete_entity_for_tenant", return_value=deleted),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        from app.modules.academic_records import service as svc

        result = svc.delete_record(55, tenant_id=1, actor="admin@test.com")

    assert result["id"] == 55
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    mock_metric.assert_called_once_with(tenant_id=1, metric="academic_records_deleted", value=1)
