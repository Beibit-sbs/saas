from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.advising.schemas import AdvisingSessionStatusUpdateSchema
from app.modules.advising.service import update_advising_session_status


@pytest.mark.parametrize("status", ["completed", "cancelled", "no_show"])
def test_update_status_emits_event_after_persist_and_records_outcome(
    monkeypatch: pytest.MonkeyPatch,
    status: str,
) -> None:
    session_store: dict[int, dict] = {
        101: {
            "id": 101,
            "student_id": 3001,
            "advisor_id": "FAC-101",
            "session_type": "academic",
            "status": "scheduled",
            "scheduled_at": "2026-06-01T11:00",
            "notes": "Initial advising",
            "outcome": "pending",
            "tenant_id": "1",
        }
    }

    events: list[str] = []
    metrics: list[str] = []
    outcomes: list[dict] = []

    def _list_entities(entity_type: str, tenant_id: int):
        if entity_type == "advising_sessions":
            return [dict(session_store[101])]
        if entity_type == "advising_no_show_risk_alerts":
            return []
        return []

    def _update_entity(entity_type: str, entity_id: int, entity_data: dict, tenant_id: int):
        updated = {"id": entity_id, "tenant_id": str(tenant_id), **entity_data}
        session_store[entity_id] = dict(updated)
        return dict(updated)

    def _publish_event_stub(self, *, event_type: str, aggregate_id: str, **kwargs):  # type: ignore[no-untyped-def]
        if event_type == "advising.session.status_changed":
            # event-after-persist contract: status event is emitted only after update is persisted
            assert session_store[int(aggregate_id)]["status"] == status
        events.append(str(event_type))
        return {"status": "queued"}

    monkeypatch.setattr("app.modules.advising.service.list_entities_for_tenant", _list_entities)
    monkeypatch.setattr("app.modules.advising.service.update_entity_for_tenant", _update_entity)
    monkeypatch.setattr("app.modules.advising.service.log_admin_action", lambda **kwargs: None)
    monkeypatch.setattr(
        "app.modules.advising.service.record_usage_event",
        lambda tenant_id, metric, value=1: metrics.append(str(metric)),
    )
    monkeypatch.setattr("app.platform.events.publisher.EventPublisher.publish_event", _publish_event_stub)

    from app.modules.brain_core import service as brain_service_module

    original_brain_core = brain_service_module.brain_core_service
    brain_service_module.brain_core_service = SimpleNamespace(
        record_dispatch_outcome=lambda case_id, payload, actor="system": outcomes.append(
            {"case_id": case_id, "payload": payload, "actor": actor}
        )
        or {"status": "recorded"}
    )

    try:
        result = update_advising_session_status(
            tenant_id=1,
            session_id=101,
            request=AdvisingSessionStatusUpdateSchema(status=status, outcome="Session closed with plan"),
            actor="advisor@example.com",
        )
    finally:
        brain_service_module.brain_core_service = original_brain_core

    assert result.status == status
    assert "advising.session.status_changed" in events
    assert "advising_sessions_status_updated" in metrics
    assert "advising_session_outcomes_recorded" in metrics
    assert outcomes and outcomes[0]["payload"]["outcome_type"] == status


def test_invalid_transition_raises_domain_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _list_entities(entity_type: str, tenant_id: int):
        if entity_type == "advising_sessions":
            return [
                {
                    "id": 202,
                    "student_id": 3002,
                    "advisor_id": "FAC-202",
                    "session_type": "academic",
                    "status": "completed",
                    "scheduled_at": "2026-06-10T09:00",
                    "notes": "Done",
                    "outcome": "completed",
                }
            ]
        return []

    monkeypatch.setattr("app.modules.advising.service.list_entities_for_tenant", _list_entities)

    with pytest.raises(DomainValidationError, match="not allowed"):
        update_advising_session_status(
            tenant_id=1,
            session_id=202,
            request=AdvisingSessionStatusUpdateSchema(status="scheduled", outcome="retry"),
            actor="advisor@example.com",
        )


def test_missing_session_raises_domain_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.advising.service.list_entities_for_tenant", lambda entity_type, tenant_id: [])

    with pytest.raises(DomainValidationError, match="not found"):
        update_advising_session_status(
            tenant_id=1,
            session_id=9999,
            request=AdvisingSessionStatusUpdateSchema(status="completed", outcome="none"),
            actor="advisor@example.com",
        )
