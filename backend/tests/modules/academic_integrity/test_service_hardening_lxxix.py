from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.academic_integrity.schemas import (
    IntegrityCaseCreateSchema,
    IntegrityCaseStatus,
    IntegrityCaseStatusUpdateSchema,
    IntegrityCaseType,
)
from app.modules.academic_integrity.service import AcademicIntegrityService


class _FakeEntityAdapter:
    def __init__(self) -> None:
        self.cases: dict[str, dict] = {}

    async def list_entities(self, *, entity_type: str, tenant_id: str, **kwargs):  # type: ignore[no-untyped-def]
        items = [v for v in self.cases.values() if str(v.get("tenant_id")) == str(tenant_id)]
        return items, len(items)

    async def create_entity(self, *, entity_type: str, entity_data: dict, tenant_id: str, **kwargs):  # type: ignore[no-untyped-def]
        self.cases[str(entity_data["id"])] = dict(entity_data)
        return dict(entity_data)

    async def get_entity(self, *, entity_type: str, entity_id: str, tenant_id: str, **kwargs):  # type: ignore[no-untyped-def]
        item = self.cases.get(str(entity_id))
        if not item:
            return None
        return dict(item)

    async def update_entity(self, *, entity_type: str, entity_id: str, entity_data: dict, tenant_id: str, **kwargs):  # type: ignore[no-untyped-def]
        self.cases[str(entity_id)] = dict(entity_data)
        return dict(entity_data)


@pytest.mark.asyncio
async def test_create_case_emits_event_after_persist(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = _FakeEntityAdapter()
    service = AcademicIntegrityService(tenant_entity_service=adapter)

    emitted: list[str] = []
    metrics: list[str] = []

    def _publish_event_stub(self, *, event_type: str, aggregate_id: str, **kwargs):  # type: ignore[no-untyped-def]
        # event-after-persist contract: case must already exist by the time event fires
        assert str(aggregate_id) in adapter.cases
        emitted.append(str(event_type))
        return {"status": "queued"}

    monkeypatch.setattr("app.platform.events.publisher.EventPublisher.publish_event", _publish_event_stub)
    monkeypatch.setattr(
        "app.modules.academic_integrity.service.record_usage_event",
        lambda tenant_id, metric, value=1: metrics.append(str(metric)),
    )
    monkeypatch.setattr("app.modules.academic_integrity.service.log_admin_action", lambda **kwargs: None)

    created = await service.create_integrity_case(
        tenant_id="1",
        actor="admin@example.com",
        payload=IntegrityCaseCreateSchema(
            student_id="student-1",
            course_id="course-1",
            assignment_id="assignment-1",
            case_type=IntegrityCaseType.PLAGIARISM,
            description="Plagiarism risk detected in assignment draft.",
            evidence_url="https://example.test/report",
            priority="high",
        ),
    )

    assert created["status"] == IntegrityCaseStatus.FLAGGED.value
    assert "academic_integrity.case.created" in emitted
    assert "academic_integrity_cases_created" in metrics


@pytest.mark.asyncio
async def test_invalid_transition_raises_domain_validation_error() -> None:
    adapter = _FakeEntityAdapter()
    service = AcademicIntegrityService(tenant_entity_service=adapter)

    created = await service.create_integrity_case(
        tenant_id="1",
        actor="admin@example.com",
        payload=IntegrityCaseCreateSchema(
            student_id="student-2",
            course_id="course-2",
            assignment_id=None,
            case_type=IntegrityCaseType.CHEATING,
            description="Proctoring evidence indicates prohibited material usage.",
            evidence_url=None,
            priority="normal",
        ),
    )

    with pytest.raises(DomainValidationError):
        await service.update_integrity_case_status(
            tenant_id="1",
            case_id=str(created["id"]),
            actor="admin@example.com",
            payload=IntegrityCaseStatusUpdateSchema(
                status=IntegrityCaseStatus.RESOLVED,
                resolution_notes="Resolved directly without review",
                recommended_action=None,
            ),
        )


@pytest.mark.asyncio
async def test_resolved_status_records_outcome_and_outcome_event(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = _FakeEntityAdapter()
    service = AcademicIntegrityService(tenant_entity_service=adapter)

    emitted: list[str] = []
    metrics: list[str] = []
    outcomes: list[dict] = []

    monkeypatch.setattr(
        "app.platform.events.publisher.EventPublisher.publish_event",
        lambda self, *, event_type, **kwargs: emitted.append(str(event_type)) or {"status": "queued"},
    )
    monkeypatch.setattr(
        "app.modules.academic_integrity.service.record_usage_event",
        lambda tenant_id, metric, value=1: metrics.append(str(metric)),
    )
    monkeypatch.setattr("app.modules.academic_integrity.service.log_admin_action", lambda **kwargs: None)

    from app.modules.brain_core import service as brain_service_module

    original_brain_core = brain_service_module.brain_core_service
    brain_service_module.brain_core_service = SimpleNamespace(
        record_dispatch_outcome=lambda case_id, payload, actor="system": outcomes.append(
            {"case_id": case_id, "payload": payload, "actor": actor}
        )
        or {"status": "recorded"}
    )

    try:
        created = await service.create_integrity_case(
            tenant_id="1",
            actor="admin@example.com",
            payload=IntegrityCaseCreateSchema(
                student_id="student-3",
                course_id="course-3",
                assignment_id=None,
                case_type=IntegrityCaseType.FABRICATION,
                description="Evidence indicates fabricated data in submission.",
                evidence_url=None,
                priority="high",
            ),
        )

        await service.update_integrity_case_status(
            tenant_id="1",
            case_id=str(created["id"]),
            actor="admin@example.com",
            payload=IntegrityCaseStatusUpdateSchema(
                status=IntegrityCaseStatus.UNDER_REVIEW,
                resolution_notes="Investigation started",
                recommended_action=None,
            ),
        )
        await service.update_integrity_case_status(
            tenant_id="1",
            case_id=str(created["id"]),
            actor="admin@example.com",
            payload=IntegrityCaseStatusUpdateSchema(
                status=IntegrityCaseStatus.RESOLVED,
                resolution_notes="Violation confirmed and sanctions applied.",
                recommended_action="grade_penalty",
            ),
        )
    finally:
        brain_service_module.brain_core_service = original_brain_core

    assert any(evt == "academic_integrity.case.outcome_recorded" for evt in emitted)
    assert outcomes and outcomes[0]["payload"]["outcome_type"] == "resolved"
    assert "academic_integrity_case_outcomes_recorded" in metrics
