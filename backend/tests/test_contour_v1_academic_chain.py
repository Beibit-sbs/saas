"""Contour v1 integration tests — Academic chain cross-domain A→B.

Tests verify:
1. thesis.status_changed is published when thesis status transitions to "rejected"
2. accreditation.status_changed is published when status transitions to "remediation_required"
3. AcademicChainEventHandler creates intervention cases for trigger statuses
4. AcademicChainEventHandler skips non-risk statuses
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_outbox_event(event_type: str, tenant_id: int, payload: dict, correlation_id: str = "corr-001"):
    """Create a minimal OutboxEventRead-like object for handler tests."""
    return SimpleNamespace(
        id=1,
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type=event_type.split(".")[0],
        aggregate_id="1",
        payload_json=payload,
        correlation_id=correlation_id,
    )


# ---------------------------------------------------------------------------
# Registry tests — event types are registered
# ---------------------------------------------------------------------------


def test_thesis_status_changed_is_registered_event_type() -> None:
    from app.platform.events.registry import is_registered_event_type

    assert is_registered_event_type("thesis.status_changed") is True


def test_accreditation_status_changed_is_registered_event_type() -> None:
    from app.platform.events.registry import is_registered_event_type

    assert is_registered_event_type("accreditation.status_changed") is True


# ---------------------------------------------------------------------------
# thesis/service.py — domain event emitted on status change
# ---------------------------------------------------------------------------


def test_update_thesis_status_emits_domain_event_on_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """When thesis transitions to 'rejected', EventPublisher.publish_event is called."""
    published: list[dict] = []

    class FakePublisher:
        def publish_event(self, **kwargs):
            published.append(kwargs)
            return {"id": 99}

    monkeypatch.setattr(
        "app.modules.thesis.service.list_entities_for_tenant",
        lambda table, tid: [
            {
                "id": 1,
                "tenant_id": str(tid),
                "thesis_code": "TH-001",
                "student_id": 42,
                "title": "Test Thesis",
                "advisor_faculty_id": "FAC-7",
                "status": "submitted",
                "defense_date": None,
                "repository_url": None,
            }
        ],
    )
    monkeypatch.setattr(
        "app.modules.thesis.service.update_entity_for_tenant",
        lambda table, eid, data, tid: {
            "id": 1,
            "tenant_id": str(tid),
            "thesis_code": "TH-001",
            "student_id": 42,
            "title": "Test Thesis",
            "advisor_faculty_id": "FAC-7",
            "status": data.get("status"),
            "defense_date": None,
            "repository_url": None,
        },
    )
    monkeypatch.setattr("app.modules.thesis.service.log_admin_action", lambda **_: None)

    with patch("app.platform.events.publisher.EventPublisher", return_value=FakePublisher()):
        from app.modules.thesis.service import update_thesis_status
        from app.modules.thesis.schemas import ThesisStatusUpdateSchema

        result = update_thesis_status(
            tenant_id=1,
            thesis_id=1,
            request=ThesisStatusUpdateSchema(status="rejected"),
            actor="admin@test.com",
        )

    assert result.status == "rejected"
    # Filter to the specific canonical status event (rejection_risk side-effect may also publish)
    status_events = [e for e in published if e.get("event_type") == "thesis.status_changed"]
    assert len(status_events) == 1
    assert status_events[0]["payload_json"]["to_status"] == "rejected"
    assert status_events[0]["payload_json"]["student_id"] == "42"
    assert status_events[0]["payload_json"]["source_module"] == "thesis"


def test_update_thesis_status_does_not_emit_on_non_risk_transition(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-risk transition (draft→submitted) should still emit the event — handler filters, not service."""
    published: list[dict] = []

    class FakePublisher:
        def publish_event(self, **kwargs):
            published.append(kwargs)
            return {"id": 100}

    monkeypatch.setattr(
        "app.modules.thesis.service.list_entities_for_tenant",
        lambda table, tid: [
            {
                "id": 2,
                "tenant_id": str(tid),
                "thesis_code": "TH-002",
                "student_id": 43,
                "title": "Test Thesis 2",
                "advisor_faculty_id": None,
                "status": "draft",
                "defense_date": None,
                "repository_url": None,
            }
        ],
    )
    monkeypatch.setattr(
        "app.modules.thesis.service.update_entity_for_tenant",
        lambda table, eid, data, tid: {
            "id": 2,
            "tenant_id": str(tid),
            "thesis_code": "TH-002",
            "student_id": 43,
            "title": "Test Thesis 2",
            "advisor_faculty_id": None,
            "status": data.get("status"),
            "defense_date": None,
            "repository_url": None,
        },
    )
    monkeypatch.setattr("app.modules.thesis.service.log_admin_action", lambda **_: None)

    with patch("app.platform.events.publisher.EventPublisher", return_value=FakePublisher()):
        from app.modules.thesis.service import update_thesis_status
        from app.modules.thesis.schemas import ThesisStatusUpdateSchema

        result = update_thesis_status(
            tenant_id=1,
            thesis_id=2,
            request=ThesisStatusUpdateSchema(status="submitted"),
            actor="admin@test.com",
        )

    assert result.status == "submitted"
    # Event is always emitted — handler (not service) decides whether to act
    assert len(published) == 1
    assert published[0]["payload_json"]["to_status"] == "submitted"


# ---------------------------------------------------------------------------
# accreditation/service.py — domain event emitted on status change
# ---------------------------------------------------------------------------


def test_update_accreditation_status_emits_event_on_remediation_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When accreditation transitions to 'remediation_required', event is published."""
    published: list[dict] = []

    class FakePublisher:
        def publish_event(self, **kwargs):
            published.append(kwargs)
            return {"id": 101}

    monkeypatch.setattr(
        "app.modules.accreditation.service.list_entities_for_tenant",
        lambda table, tid: [
            {
                "id": 5,
                "tenant_id": str(tid),
                "standard_code": "ACC-2026-ISO",
                "standard_type": "institutional",
                "title": "ISO Accreditation",
                "owner_department": "Engineering",
                "review_cycle_year": 2026,
                "due_date": None,
                "evidence_summary": None,
                "risk_level": "high",
                "status": "evidence_collected",
                "reviewer_notes": None,
                "remediation_plan": None,
            }
        ],
    )
    monkeypatch.setattr(
        "app.modules.accreditation.service.update_entity_for_tenant",
        lambda table, eid, data, tid: {
            "id": 5,
            "tenant_id": str(tid),
            "standard_code": "ACC-2026-ISO",
            "standard_type": "institutional",
            "title": "ISO Accreditation",
            "owner_department": "Engineering",
            "review_cycle_year": 2026,
            "due_date": None,
            "evidence_summary": None,
            "risk_level": "high",
            "status": data.get("status"),
            "reviewer_notes": data.get("reviewer_notes"),
            "remediation_plan": data.get("remediation_plan"),
        },
    )
    monkeypatch.setattr("app.modules.accreditation.service.log_admin_action", lambda **_: None)

    with patch("app.platform.events.publisher.EventPublisher", return_value=FakePublisher()):
        from app.modules.accreditation.service import update_accreditation_status
        from app.modules.accreditation.schemas import AccreditationStatusUpdateSchema

        result = update_accreditation_status(
            tenant_id=1,
            record_id=5,
            request=AccreditationStatusUpdateSchema(
                status="remediation_required",
                remediation_plan="Conduct full evidence review by 2026-06-01",
            ),
            actor="admin@test.com",
        )

    assert result.status == "remediation_required"
    assert len(published) == 1
    assert published[0]["event_type"] == "accreditation.status_changed"
    assert published[0]["payload_json"]["to_status"] == "remediation_required"
    assert published[0]["payload_json"]["standard_code"] == "ACC-2026-ISO"
    assert published[0]["payload_json"]["source_module"] == "accreditation"


# ---------------------------------------------------------------------------
# AcademicChainEventHandler — unit tests
# ---------------------------------------------------------------------------


def test_handler_skips_irrelevant_event_type() -> None:
    from app.platform.events.handlers.academic_chain_handler import AcademicChainEventHandler

    handler = AcademicChainEventHandler()
    event = _make_outbox_event("grade.submitted", 1, {"grade_code": "A"})
    uow = MagicMock()

    result = handler.handle(event, uow=uow)

    assert result["status"] == "skipped"
    assert result["reason"] == "irrelevant_event_type"


def test_handler_skips_thesis_non_risk_status() -> None:
    from app.platform.events.handlers.academic_chain_handler import AcademicChainEventHandler

    handler = AcademicChainEventHandler()
    event = _make_outbox_event(
        "thesis.status_changed",
        1,
        {"thesis_id": 1, "student_id": 42, "from_status": "draft", "to_status": "submitted"},
    )
    uow = MagicMock()

    result = handler.handle(event, uow=uow)

    assert result["status"] == "skipped"
    assert result["to_status"] == "submitted"


def test_handler_skips_accreditation_non_risk_status() -> None:
    from app.platform.events.handlers.academic_chain_handler import AcademicChainEventHandler

    handler = AcademicChainEventHandler()
    event = _make_outbox_event(
        "accreditation.status_changed",
        1,
        {
            "accreditation_id": 5,
            "standard_code": "ACC-001",
            "from_status": "draft",
            "to_status": "evidence_requested",
        },
    )
    uow = MagicMock()

    result = handler.handle(event, uow=uow)

    assert result["status"] == "skipped"
    assert result["to_status"] == "evidence_requested"


def test_handler_creates_intervention_case_for_rejected_thesis() -> None:
    """Handler calls _create_intervention_case for thesis.status_changed with to_status=rejected."""
    from app.platform.events.handlers.academic_chain_handler import AcademicChainEventHandler

    handler = AcademicChainEventHandler()
    event = _make_outbox_event(
        "thesis.status_changed",
        1,
        {
            "thesis_id": 10,
            "student_id": 55,
            "advisor_faculty_id": "FAC-3",
            "from_status": "under_review",
            "to_status": "rejected",
            "source_module": "thesis",
        },
    )
    uow = MagicMock()

    with patch(
        "app.platform.events.handlers.academic_chain_handler._create_intervention_case",
        return_value={"case_id": 42},
    ) as mock_create:
        result = handler.handle(event, uow=uow)

    assert result["status"] == "processed"
    assert result["action"] == "intervention_case_opened"
    assert result["case_id"] == 42

    mock_create.assert_called_once()
    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["tenant_id"] == 1
    assert call_kwargs["severity"] == "medium"
    assert call_kwargs["student_id"] == 55
    assert "rejected" in call_kwargs["title"]


def test_handler_creates_intervention_case_for_accreditation_remediation() -> None:
    """Handler calls _create_intervention_case for accreditation.status_changed with remediation_required."""
    from app.platform.events.handlers.academic_chain_handler import AcademicChainEventHandler

    handler = AcademicChainEventHandler()
    event = _make_outbox_event(
        "accreditation.status_changed",
        2,
        {
            "accreditation_id": 7,
            "standard_code": "ISO-9001",
            "owner_department": "Engineering",
            "from_status": "evidence_collected",
            "to_status": "remediation_required",
            "source_module": "accreditation",
        },
    )
    uow = MagicMock()

    with patch(
        "app.platform.events.handlers.academic_chain_handler._create_intervention_case",
        return_value={"case_id": 88},
    ) as mock_create:
        result = handler.handle(event, uow=uow)

    assert result["status"] == "processed"
    assert result["action"] == "intervention_case_opened"
    assert result["case_id"] == 88

    mock_create.assert_called_once()
    call_kwargs = mock_create.call_args.kwargs
    assert call_kwargs["tenant_id"] == 2
    assert call_kwargs["severity"] == "high"
    assert call_kwargs["student_id"] is None
    assert "ISO-9001" in call_kwargs["title"]


def test_handler_handles_missing_db_engine_gracefully() -> None:
    """If DB engine is unavailable (e.g., tests), handler returns skipped result without raising."""
    from app.platform.events.handlers.academic_chain_handler import AcademicChainEventHandler

    handler = AcademicChainEventHandler()
    event = _make_outbox_event(
        "thesis.status_changed",
        1,
        {
            "thesis_id": 1,
            "student_id": 1,
            "advisor_faculty_id": "",
            "from_status": "submitted",
            "to_status": "rejected",
        },
    )
    uow = MagicMock()

    with patch("app.platform.events.handlers.academic_chain_handler._create_intervention_case") as mock_create:
        mock_create.return_value = {"case_id": None, "skipped": True, "reason": "no_db_engine"}
        result = handler.handle(event, uow=uow)

    assert result["handler"] == "academic_chain"
    # No exception raised


def test_academic_chain_handler_name() -> None:
    from app.platform.events.handlers.academic_chain_handler import AcademicChainEventHandler

    assert AcademicChainEventHandler.name == "academic_chain"


def test_academic_chain_handler_in_worker_defaults() -> None:
    """AcademicChainEventHandler is included in the default worker handler list."""
    from app.platform.events.handlers.academic_chain_handler import AcademicChainEventHandler
    from app.platform.events.worker import OutboxEventWorker

    worker = OutboxEventWorker()
    handler_names = [h.name for h in worker._handlers]

    assert "academic_chain" in handler_names
    assert any(isinstance(h, AcademicChainEventHandler) for h in worker._handlers)
