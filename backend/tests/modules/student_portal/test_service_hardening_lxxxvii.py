"""LXXXVII — Student portal service hardening tests.

Focus:
1) Canonical tenant CRUD call signatures.
2) Persist-before-event ordering for submit/ready flows.
3) Fire-and-forget event publication (no rollback on broker failure).
4) Transition persistence fallback for non-persistent contexts.
"""
from __future__ import annotations

from unittest.mock import patch

from app.modules.student_portal import service as svc


def _request(*, status: str = "SUBMITTED") -> dict[str, object]:
    return {
        "id": "r-1",
        "student_id": "stu-1",
        "request_type": "CERTIFICATE",
        "details": "",
        "status": status,
        "tenant_id": "tenant-1",
    }


def test_submit_request_persists_before_event() -> None:
    order: list[str] = []

    def _create(entity_name: str, payload: dict[str, object], tenant_id: str) -> dict[str, object]:
        order.append("persist")
        return {"id": 101, **payload}

    class _Publisher:
        def publish_event(self, **kwargs):  # type: ignore[no-untyped-def]
            order.append("event")

    with (
        patch("app.modules.student_portal.service.create_entity_for_tenant", side_effect=_create),
        patch("app.modules.student_portal.service.EventPublisher", _Publisher),
    ):
        result = svc.submit_request("7", student_id="stu-1", request_type="CERTIFICATE")

    assert result["id"] == 101
    assert order == ["persist", "event"]


def test_submit_request_survives_publish_failure() -> None:
    class _Publisher:
        def publish_event(self, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("broker down")

    with (
        patch(
            "app.modules.student_portal.service.create_entity_for_tenant",
            return_value={**_request(), "id": 202},
        ) as mock_create,
        patch("app.modules.student_portal.service.EventPublisher", _Publisher),
    ):
        result = svc.submit_request("7", student_id="stu-1", request_type="CERTIFICATE")

    assert result["id"] == 202
    mock_create.assert_called_once_with(
        "portal_requests",
        {
            "student_id": "stu-1",
            "request_type": "CERTIFICATE",
            "details": "",
            "status": "SUBMITTED",
            "tenant_id": "7",
        },
        "7",
    )


def test_start_processing_uses_canonical_tenant_api_and_persists() -> None:
    req = _request(status="SUBMITTED")

    with (
        patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=[req]) as mock_list,
        patch(
            "app.modules.student_portal.service.update_entity_for_tenant",
            return_value={**req, "status": "PROCESSING"},
        ) as mock_update,
    ):
        result = svc.start_processing("tenant-1", request_id="r-1")

    assert result["status"] == "PROCESSING"
    mock_list.assert_called_once_with("portal_requests", "tenant-1")
    mock_update.assert_called_once_with(
        "portal_requests",
        "r-1",
        {**req, "status": "PROCESSING"},
        "tenant-1",
    )


def test_mark_ready_event_failure_does_not_rollback_persisted_status() -> None:
    req = _request(status="PROCESSING")

    class _Publisher:
        def publish_event(self, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("broker down")

    with (
        patch("app.modules.student_portal.service.list_entities_for_tenant", return_value=[req]),
        patch(
            "app.modules.student_portal.service.update_entity_for_tenant",
            return_value={**req, "status": "READY"},
        ) as mock_update,
        patch("app.modules.student_portal.service.EventPublisher", _Publisher),
    ):
        result = svc.mark_ready("7", request_id="r-1")

    assert result["status"] == "READY"
    mock_update.assert_called_once_with(
        "portal_requests",
        "r-1",
        {**req, "status": "READY"},
        "7",
    )
