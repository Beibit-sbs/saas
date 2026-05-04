"""XCV — Student Services Service Hardening Tests.

Verifies:
1. create_student_service_ticket uses canonical EventPublisher constructor and records metric.
2. create_student_service_ticket uses canonical tenant API positional arguments.
3. update_student_service_ticket_status survives publish failure (fire-and-forget) and still records metric.
4. update_student_service_ticket_status survives outcome failure for resolved transition.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.modules.student_services.schemas import (
    StudentServiceTicketCreateSchema,
    StudentServiceTicketStatusUpdateSchema,
)

MODULE = "app.modules.student_services.service"


def _seed_enrollments(student_id: int = 1) -> list[dict[str, object]]:
    return [
        {
            "id": 1,
            "student_id": student_id,
            "status": "enrolled",
        }
    ]


def _created_ticket(ticket_id: int, *, student_id: int, category: str, subject: str, description: str, priority: str) -> dict[str, object]:
    return {
        "id": ticket_id,
        "student_id": student_id,
        "category": category,
        "subject": subject,
        "description": description,
        "priority": priority,
        "status": "open",
        "owner_id": "unassigned",
        "channel": "portal",
        "resolution_notes": "pending",
    }


def test_create_ticket_uses_canonical_event_publisher_and_metric() -> None:
    request = StudentServiceTicketCreateSchema(
        student_id=1,
        category="academic",
        subject="Need certificate",
        description="Please issue enrollment certificate",
        priority="high",
    )

    with (
        patch(
            f"{MODULE}.list_entities_for_tenant",
            side_effect=lambda entity, tenant_id: _seed_enrollments() if entity == "enrollments" else [],
        ),
        patch(
            f"{MODULE}.create_entity_for_tenant",
            return_value=_created_ticket(
                99,
                student_id=1,
                category="academic",
                subject="Need certificate",
                description="Please issue enrollment certificate",
                priority="high",
            ),
        ),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
    ):
        from app.modules.student_services import service as svc

        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        result = svc.create_student_service_ticket(tenant_id=1, request=request, actor="admin@test.com")

    assert result.id == 99
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    mock_metric.assert_called_once_with(tenant_id=1, metric="student_service_tickets_created", value=1)


def test_create_ticket_uses_canonical_tenant_api_positional_args() -> None:
    request = StudentServiceTicketCreateSchema(
        student_id=1,
        category="general",
        subject="Question",
        description="Need help",
        priority="medium",
    )

    mock_list = MagicMock(side_effect=lambda entity, tenant_id: _seed_enrollments() if entity == "enrollments" else [])
    mock_create = MagicMock(
        return_value=_created_ticket(
            5,
            student_id=1,
            category="general",
            subject="Question",
            description="Need help",
            priority="medium",
        )
    )

    with (
        patch(f"{MODULE}.list_entities_for_tenant", mock_list),
        patch(f"{MODULE}.create_entity_for_tenant", mock_create),
        patch(f"{MODULE}.record_usage_event"),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        from app.modules.student_services import service as svc

        svc.create_student_service_ticket(tenant_id=1, request=request, actor="admin@test.com")

    create_args, create_kwargs = mock_create.call_args
    assert len(create_args) == 3
    assert create_args[0] == "student_service_tickets"
    assert create_args[2] == 1
    assert "tenant_id" not in create_kwargs


def test_update_status_survives_publish_failure_and_records_metric() -> None:
    existing_ticket = {
        "id": 7,
        "student_id": 1,
        "category": "general",
        "subject": "Need help",
        "description": "desc",
        "priority": "high",
        "status": "open",
        "owner_id": "advisor-1",
        "channel": "portal",
        "resolution_notes": "pending",
    }

    def fake_list(entity: str, tenant_id: int):
        if entity == "student_service_tickets":
            return [existing_ticket]
        if entity == "student_service_unresolved_alerts":
            return []
        return []

    with (
        patch(f"{MODULE}.list_entities_for_tenant", side_effect=fake_list),
        patch(
            f"{MODULE}.update_entity_for_tenant",
            return_value={**existing_ticket, "status": "in_progress", "id": 7},
        ),
        patch(f"{MODULE}.create_entity_for_tenant", return_value={"id": 70}),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch(f"{MODULE}.record_usage_event") as mock_metric,
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        from app.modules.student_services import service as svc

        pub = MagicMock()
        pub.publish_event.side_effect = RuntimeError("broker down")
        mock_ep.return_value = pub

        result = svc.update_student_service_ticket_status(
            tenant_id=1,
            ticket_id=7,
            request=StudentServiceTicketStatusUpdateSchema(status="in_progress", resolution_notes="started"),
            actor="admin@test.com",
        )

    assert result.id == 7
    mock_ep.assert_called_once_with()
    mock_metric.assert_called_once_with(tenant_id=1, metric="student_service_ticket_status_updates", value=1)


def test_update_status_survives_outcome_failure_for_resolved_transition() -> None:
    existing_ticket = {
        "id": 8,
        "student_id": 1,
        "category": "general",
        "subject": "Need help",
        "description": "desc",
        "priority": "medium",
        "status": "in_progress",
        "owner_id": "advisor-1",
        "channel": "portal",
        "resolution_notes": "pending",
    }

    with (
        patch(f"{MODULE}.list_entities_for_tenant", return_value=[existing_ticket]),
        patch(
            f"{MODULE}.update_entity_for_tenant",
            return_value={**existing_ticket, "status": "resolved", "resolution_notes": "done", "id": 8},
        ),
        patch(f"{MODULE}.record_usage_event"),
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
    ):
        from app.modules.student_services import service as svc

        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        result = svc.update_student_service_ticket_status(
            tenant_id=1,
            ticket_id=8,
            request=StudentServiceTicketStatusUpdateSchema(status="resolved", resolution_notes="done"),
            actor="admin@test.com",
        )

    assert result.id == 8
    assert result.status == "resolved"
