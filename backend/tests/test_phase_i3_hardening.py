"""Phase I3 hardening tests.

Covers:
  I3.1 — academic_integrity escalation signal emission
  I3.2 — academic_records inconsistency signal emission
  I3.3 — programs status risk signal emission
  I3.4 — courses status risk signal emission
  I3.5 — transcripts inconsistency signal emission
  I3.6 — student_services high-priority ticket escalation signal emission
  I3.7 — Brain Core pipeline processes all 6 new event types
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakePublisher:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def publish_event(self, **kwargs: object) -> dict:
        self.events.append(dict(kwargs))
        return {}


# ---------------------------------------------------------------------------
# I3.1 — Academic Integrity escalation signal
# ---------------------------------------------------------------------------


def test_academic_integrity_signal_emitted_on_escalated() -> None:
    """update_integrity_case_status → ESCALATED must emit academic_integrity.case.escalated."""
    from app.modules.academic_integrity.service import AcademicIntegrityService
    from app.modules.academic_integrity.schemas import IntegrityCaseStatus, IntegrityCaseStatusUpdateSchema

    fake_pub = _FakePublisher()
    existing_case = {
        "id": "case-001",
        "status": IntegrityCaseStatus.UNDER_REVIEW.value,
        "case_type": "plagiarism",
        "student_id": "student-42",
    }

    mock_entity_service = MagicMock()
    mock_entity_service.get_entity = AsyncMock(return_value=existing_case)
    mock_entity_service.update_entity = AsyncMock(return_value=None)

    svc = AcademicIntegrityService(tenant_entity_service=mock_entity_service)

    async def _run_update():
        return await svc.update_integrity_case_status(
            tenant_id="tenant-1",
            case_id="case-001",
            actor="admin@example.com",
            payload=IntegrityCaseStatusUpdateSchema(
                status=IntegrityCaseStatus.ESCALATED,
                resolution_notes=None,
                recommended_action="Formal hearing",
            ),
        )

    with patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub):
        asyncio.run(_run_update())

    assert len(fake_pub.events) == 1
    ev = fake_pub.events[0]
    assert ev["event_type"] == "academic_integrity.case.escalated"
    assert ev["payload_json"]["case_type"] == "plagiarism"
    assert ev["payload_json"]["student_id"] == "student-42"


def test_academic_integrity_signal_not_emitted_on_resolved() -> None:
    """update_integrity_case_status → RESOLVED must NOT emit signal."""
    from app.modules.academic_integrity.service import AcademicIntegrityService
    from app.modules.academic_integrity.schemas import IntegrityCaseStatus, IntegrityCaseStatusUpdateSchema

    fake_pub = _FakePublisher()
    existing_case = {
        "id": "case-002",
        "status": IntegrityCaseStatus.ESCALATED.value,
        "case_type": "plagiarism",
        "student_id": "student-99",
    }

    mock_entity_service = MagicMock()
    mock_entity_service.get_entity = AsyncMock(return_value=existing_case)
    mock_entity_service.update_entity = AsyncMock(return_value=None)

    svc = AcademicIntegrityService(tenant_entity_service=mock_entity_service)

    async def _run_update():
        return await svc.update_integrity_case_status(
            tenant_id="tenant-1",
            case_id="case-002",
            actor="admin@example.com",
            payload=IntegrityCaseStatusUpdateSchema(
                status=IntegrityCaseStatus.RESOLVED,
                resolution_notes="Case closed",
                recommended_action=None,
            ),
        )

    with patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub):
        asyncio.run(_run_update())

    assert len(fake_pub.events) == 0


# ---------------------------------------------------------------------------
# I3.2 — Academic Records inconsistency signal
# ---------------------------------------------------------------------------


def test_emit_academic_records_inconsistency_signal_fields() -> None:
    """emit_academic_records_inconsistency_signal must publish correct event_type and payload."""
    from app.modules.academic_records.service import emit_academic_records_inconsistency_signal

    fake_pub = _FakePublisher()
    with patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub):
        emit_academic_records_inconsistency_signal(tenant_id=5, issue_count=7)

    assert len(fake_pub.events) == 1
    ev = fake_pub.events[0]
    assert ev["event_type"] == "academic_records.inconsistency.detected"
    assert ev["payload_json"]["issue_count"] == 7
    assert ev["tenant_id"] == 5


# ---------------------------------------------------------------------------
# I3.3 — Programs status risk signal
# ---------------------------------------------------------------------------


def test_programs_archived_status_emits_signal() -> None:
    """update_program with status=archived must emit programs.status.risk_detected."""
    from app.modules.programs.service import update_program

    fake_pub = _FakePublisher()
    with patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub):
        with patch("app.modules.programs.service.update_entity_for_tenant", return_value={"id": 1, "status": "archived"}):
            update_program(program_id=1, payload={"status": "archived", "title": "Old Program"}, tenant_id=10)

    assert len(fake_pub.events) == 1
    ev = fake_pub.events[0]
    assert ev["event_type"] == "programs.status.risk_detected"
    assert ev["payload_json"]["to_status"] == "archived"
    assert ev["payload_json"]["program_id"] == 1


def test_programs_inactive_status_emits_signal() -> None:
    """update_program with status=inactive must emit signal."""
    from app.modules.programs.service import update_program

    fake_pub = _FakePublisher()
    with patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub):
        with patch("app.modules.programs.service.update_entity_for_tenant", return_value={"id": 2, "status": "inactive"}):
            update_program(program_id=2, payload={"status": "inactive"}, tenant_id=10)

    assert len(fake_pub.events) == 1
    assert fake_pub.events[0]["event_type"] == "programs.status.risk_detected"
    assert fake_pub.events[0]["payload_json"]["to_status"] == "inactive"


def test_programs_active_status_does_not_emit_signal() -> None:
    """update_program with status=active must NOT emit signal."""
    from app.modules.programs.service import update_program

    fake_pub = _FakePublisher()
    with patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub):
        with patch("app.modules.programs.service._check_program_has_active_requirements", return_value=None):
            with patch("app.modules.programs.service.update_entity_for_tenant", return_value={"id": 3, "status": "active"}):
                update_program(program_id=3, payload={"status": "active"}, tenant_id=10)

    assert len(fake_pub.events) == 0


# ---------------------------------------------------------------------------
# I3.4 — Courses status risk signal
# ---------------------------------------------------------------------------


def test_courses_archived_status_emits_signal() -> None:
    """update_course with status=archived must emit courses.status.risk_detected."""
    from app.modules.courses.service import update_course

    fake_pub = _FakePublisher()
    with patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub):
        with patch("app.modules.courses.service.update_entity_for_tenant", return_value={"id": 7, "status": "archived"}):
            with patch("app.modules.courses.service.assert_billing_write_allowed"):
                update_course(course_id=7, payload={"status": "archived"}, tenant_id=10)

    assert len(fake_pub.events) == 1
    ev = fake_pub.events[0]
    assert ev["event_type"] == "courses.status.risk_detected"
    assert ev["payload_json"]["to_status"] == "archived"
    assert ev["payload_json"]["course_id"] == 7


def test_courses_active_status_does_not_emit_signal() -> None:
    """update_course with status=active must NOT emit signal."""
    from app.modules.courses.service import update_course

    fake_pub = _FakePublisher()
    with patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub):
        with patch("app.modules.courses.service.update_entity_for_tenant", return_value={"id": 8, "status": "active"}):
            with patch("app.modules.courses.service.assert_billing_write_allowed"):
                update_course(course_id=8, payload={"status": "active"}, tenant_id=10)

    assert len(fake_pub.events) == 0


# ---------------------------------------------------------------------------
# I3.5 — Transcripts inconsistency signal
# ---------------------------------------------------------------------------


def test_emit_transcript_inconsistency_signal_fields() -> None:
    """emit_transcript_inconsistency_signal must publish correct event_type and payload."""
    from app.modules.transcripts.service import emit_transcript_inconsistency_signal

    fake_pub = _FakePublisher()
    with patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub):
        emit_transcript_inconsistency_signal(tenant_id=3, issue_count=4)

    assert len(fake_pub.events) == 1
    ev = fake_pub.events[0]
    assert ev["event_type"] == "transcripts.inconsistency.detected"
    assert ev["payload_json"]["issue_count"] == 4
    assert ev["tenant_id"] == 3


# ---------------------------------------------------------------------------
# I3.6 — Student Services high-priority ticket signal
# ---------------------------------------------------------------------------


def test_student_services_high_priority_ticket_emits_signal() -> None:
    """create_student_service_ticket with priority=high must emit student_services.ticket.escalated."""
    from app.modules.student_services.service import create_student_service_ticket
    from app.modules.student_services.schemas import StudentServiceTicketCreateSchema

    fake_pub = _FakePublisher()
    with patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub):
        with patch("app.modules.student_services.service._check_student_is_enrolled_for_service_ticket", return_value=None):
            with patch("app.modules.student_services.service.create_entity_for_tenant", return_value={
                "id": 99,
                "student_id": 42,
                "category": "academic",
                "subject": "Need help",
                "description": "Urgent",
                "priority": "high",
                "status": "open",
                "owner_id": "unassigned",
                "channel": "portal",
                "resolution_notes": "pending",
            }):
                with patch("app.modules.student_services.service._emit_audit"):
                    create_student_service_ticket(
                        tenant_id=1,
                        request=StudentServiceTicketCreateSchema(
                            student_id=42,
                            category="academic",
                            subject="Need help",
                            description="Urgent",
                            priority="high",
                            owner_id=None,
                            channel="portal",
                        ),
                        actor="admin@example.com",
                    )

    assert len(fake_pub.events) == 1
    ev = fake_pub.events[0]
    assert ev["event_type"] == "student_services.ticket.escalated"
    assert ev["payload_json"]["priority"] == "high"
    assert ev["payload_json"]["student_id"] == 42


def test_student_services_medium_priority_ticket_no_signal() -> None:
    """create_student_service_ticket with priority=medium must NOT emit signal."""
    from app.modules.student_services.service import create_student_service_ticket
    from app.modules.student_services.schemas import StudentServiceTicketCreateSchema

    fake_pub = _FakePublisher()
    with patch("app.platform.events.publisher.EventPublisher", return_value=fake_pub):
        with patch("app.modules.student_services.service._check_student_is_enrolled_for_service_ticket", return_value=None):
            with patch("app.modules.student_services.service.create_entity_for_tenant", return_value={
                "id": 100,
                "student_id": 43,
                "category": "registrar",
                "subject": "Question",
                "description": "No rush",
                "priority": "medium",
                "status": "open",
                "owner_id": "unassigned",
                "channel": "portal",
                "resolution_notes": "pending",
            }):
                with patch("app.modules.student_services.service._emit_audit"):
                    create_student_service_ticket(
                        tenant_id=1,
                        request=StudentServiceTicketCreateSchema(
                            student_id=43,
                            category="registrar",
                            subject="Question",
                            description="No rush",
                            priority="medium",
                            owner_id=None,
                            channel="portal",
                        ),
                        actor="admin@example.com",
                    )

    assert len(fake_pub.events) == 0


# ---------------------------------------------------------------------------
# I3.7 — Brain Core pipeline integration for all 6 new event types
# ---------------------------------------------------------------------------


def test_brain_core_registry_supports_academic_integrity_event() -> None:
    from app.modules.brain_core.registry import SignalRegistry

    assert SignalRegistry.is_supported("academic_integrity.case.escalated")
    sig = SignalRegistry.signals["academic_integrity.case.escalated"]
    assert sig["scenario"] == "academic_integrity_escalation"


def test_brain_core_classifier_academic_integrity_plagiarism_is_high() -> None:
    from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier

    clf = RiskClassifier()
    result = clf.classify(
        signal={
            "event_type": "academic_integrity.case.escalated",
            "payload": {"case_type": "plagiarism"},
        },
        context={},
    )
    assert result["severity"] == "high"
    assert result["reasoning_path"] == "academic_integrity_high"


def test_brain_core_classifier_academic_integrity_unknown_type_is_medium() -> None:
    from app.modules.brain_core.classifiers.risk_classifier import RiskClassifier

    clf = RiskClassifier()
    result = clf.classify(
        signal={
            "event_type": "academic_integrity.case.escalated",
            "payload": {"case_type": "misconduct"},
        },
        context={},
    )
    assert result["severity"] == "medium"
    assert result["reasoning_path"] == "academic_integrity_medium"


def test_brain_core_processes_academic_integrity_signal() -> None:
    from app.modules.brain_core.service import brain_core_service

    result = brain_core_service.process_signal(
        signal={
            "event_type": "academic_integrity.case.escalated",
            "tenant_id": 1,
            "payload": {
                "case_id": "case-001",
                "case_type": "cheating",
                "student_id": "student-42",
                "source_module": "academic_integrity",
            },
        },
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "compliance"
    assert "create_integrity_review_case" in result["decision"]["recommended_actions"]


def test_brain_core_processes_academic_records_signal_high() -> None:
    from app.modules.brain_core.service import brain_core_service

    result = brain_core_service.process_signal(
        signal={
            "event_type": "academic_records.inconsistency.detected",
            "tenant_id": 1,
            "payload": {
                "issue_count": 8,
                "source_module": "academic_records",
            },
        },
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "compliance"
    assert result["decision"]["priority"] == "high"
    assert "create_records_review_task" in result["decision"]["recommended_actions"]


def test_brain_core_processes_programs_status_archived() -> None:
    from app.modules.brain_core.service import brain_core_service

    result = brain_core_service.process_signal(
        signal={
            "event_type": "programs.status.risk_detected",
            "tenant_id": 1,
            "payload": {
                "program_id": 7,
                "to_status": "archived",
                "source_module": "programs",
            },
        },
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "risk"
    assert result["decision"]["priority"] == "high"
    assert "create_program_review_task" in result["decision"]["recommended_actions"]


def test_brain_core_processes_courses_status_archived() -> None:
    from app.modules.brain_core.service import brain_core_service

    result = brain_core_service.process_signal(
        signal={
            "event_type": "courses.status.risk_detected",
            "tenant_id": 1,
            "payload": {
                "course_id": 3,
                "to_status": "archived",
                "source_module": "courses",
            },
        },
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "risk"
    assert result["decision"]["priority"] == "high"
    assert "create_course_review_task" in result["decision"]["recommended_actions"]


def test_brain_core_processes_transcripts_signal_high() -> None:
    from app.modules.brain_core.service import brain_core_service

    result = brain_core_service.process_signal(
        signal={
            "event_type": "transcripts.inconsistency.detected",
            "tenant_id": 1,
            "payload": {
                "issue_count": 5,
                "source_module": "transcripts",
            },
        },
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "compliance"
    assert result["decision"]["priority"] == "high"
    assert "create_transcript_review_task" in result["decision"]["recommended_actions"]


def test_brain_core_processes_student_services_escalation() -> None:
    from app.modules.brain_core.service import brain_core_service

    result = brain_core_service.process_signal(
        signal={
            "event_type": "student_services.ticket.escalated",
            "tenant_id": 1,
            "payload": {
                "ticket_id": 99,
                "student_id": 42,
                "category": "academic",
                "priority": "high",
                "source_module": "student_services",
            },
        },
    )
    assert result["status"] == "processed"
    assert result["decision"]["decision_type"] == "risk"
    assert result["decision"]["priority"] == "high"
    assert "create_student_support_case" in result["decision"]["recommended_actions"]
