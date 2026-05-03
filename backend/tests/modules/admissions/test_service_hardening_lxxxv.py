"""LXXXV - Admissions Service Hardening (10-step contract).

Tests:
1. submit_application emits event after persist and records metric
2. transition_stage emits event after persist and records metric
3. transition_stage invalid transition is fail-closed
4. make_decision emits event after persist and records metric
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.modules.admissions.schemas import (
    ApplicationConclusionType,
    ApplicationStage,
    DecisionMakeRequestSchema,
    StageTransitionRequestSchema,
)
from app.modules.admissions.service import (
    ApplicationService,
    DecisionService,
    StageTransitionService,
)
from tests.modules.admissions.conftest import ExecuteResult


@pytest.mark.asyncio
async def test_submit_application_emits_event_after_persist_and_records_metric(
    db_session,
    application_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    committed = {"done": False}
    events: list[str] = []
    metrics: list[str] = []

    def _commit() -> None:
        committed["done"] = True

    def _publish(self_pub, *, event_type: str, **kwargs) -> None:  # noqa: ANN001
        assert committed["done"] is True, "event must be emitted after commit/persist"
        events.append(event_type)

    def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
        assert committed["done"] is True, "metric must be recorded after commit/persist"
        metrics.append(metric)

    db_session.commit.side_effect = _commit
    application = application_factory(
        stage=ApplicationStage.NEW.value,
        version=3,
        metadata_json={},
    )
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=application)

    service = ApplicationService(db_session)
    monkeypatch.setattr(service, "_start_admissions_workflow", AsyncMock(return_value={"id": 789}))
    monkeypatch.setattr("app.modules.admissions.service.log_admin_action", lambda **kw: None)
    monkeypatch.setattr("app.platform.events.publisher.EventPublisher.publish_event", _publish)
    monkeypatch.setattr("app.modules.usage.service.record_usage_event", _metric)

    result = await service.submit_application(
        tenant_id=1,
        application_id=application.id,
        actor="applicant@example.com",
        expected_version=3,
    )

    assert result.stage == ApplicationStage.RECEIVED
    assert "admissions.application.submitted" in events
    assert "admissions_applications_submitted" in metrics


@pytest.mark.asyncio
async def test_transition_stage_emits_event_after_persist_and_records_metric(
    db_session,
    application_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    committed = {"done": False}
    events: list[str] = []
    metrics: list[str] = []

    def _commit() -> None:
        committed["done"] = True

    def _publish(self_pub, *, event_type: str, **kwargs) -> None:  # noqa: ANN001
        assert committed["done"] is True, "event must be emitted after commit/persist"
        events.append(event_type)

    def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
        assert committed["done"] is True, "metric must be recorded after commit/persist"
        metrics.append(metric)

    db_session.commit.side_effect = _commit
    application = application_factory(stage=ApplicationStage.RECEIVED.value)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=application)

    service = StageTransitionService(db_session)
    monkeypatch.setattr("app.modules.admissions.service.log_admin_action", lambda **kw: None)
    monkeypatch.setattr("app.platform.events.publisher.EventPublisher.publish_event", _publish)
    monkeypatch.setattr("app.modules.usage.service.record_usage_event", _metric)

    request = StageTransitionRequestSchema(
        to_stage=ApplicationStage.UNDER_REVIEW,
        reason="manual review started",
    )

    result = await service.transition_stage(
        tenant_id=1,
        application_id=application.id,
        request=request,
        actor_id="reviewer@example.com",
    )

    assert result.to_stage == ApplicationStage.UNDER_REVIEW
    assert "admissions.application.stage_changed" in events
    assert "admissions_stage_transitions" in metrics


@pytest.mark.asyncio
async def test_transition_stage_invalid_transition_is_fail_closed(
    db_session,
    application_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    def _publish(self_pub, *, event_type: str, **kwargs) -> None:  # noqa: ANN001
        events.append(event_type)

    application = application_factory(stage=ApplicationStage.NEW.value)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=application)

    service = StageTransitionService(db_session)
    monkeypatch.setattr("app.platform.events.publisher.EventPublisher.publish_event", _publish)

    with pytest.raises(ValueError, match="Invalid transition"):
        await service.transition_stage(
            tenant_id=1,
            application_id=application.id,
            request=StageTransitionRequestSchema(to_stage=ApplicationStage.CONCLUDED),
            actor_id="reviewer@example.com",
        )

    db_session.commit.assert_not_called()
    assert not events


@pytest.mark.asyncio
async def test_make_decision_emits_event_after_persist_and_records_metric(
    db_session,
    application_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    committed = {"done": False}
    events: list[str] = []
    metrics: list[str] = []
    brain_signals: list[str] = []

    def _commit() -> None:
        committed["done"] = True

    def _publish(self_pub, *, event_type: str, **kwargs) -> None:  # noqa: ANN001
        assert committed["done"] is True, "event must be emitted after commit/persist"
        events.append(event_type)

    def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
        assert committed["done"] is True, "metric must be recorded after commit/persist"
        metrics.append(metric)

    def _brain_signal(signal: dict) -> dict:
        assert committed["done"] is True, "brain signal must be emitted after commit/persist"
        brain_signals.append(signal["event_type"])
        return {"status": "processed"}

    db_session.commit.side_effect = _commit
    application = application_factory(
        stage=ApplicationStage.DECISION_PENDING.value,
        version=1,
    )
    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=application),
        ExecuteResult(scalar_one_or_none=None),
    ]

    service = DecisionService(db_session)
    monkeypatch.setattr("app.modules.admissions.service.log_admin_action", lambda **kw: None)
    monkeypatch.setattr("app.platform.events.publisher.EventPublisher.publish_event", _publish)
    monkeypatch.setattr("app.modules.usage.service.record_usage_event", _metric)
    monkeypatch.setattr("app.modules.brain_core.service.brain_core_service.process_signal", _brain_signal)

    request = DecisionMakeRequestSchema(
        decision_type=ApplicationConclusionType.ACCEPTED,
        decision_rationale="Ready for admission",
        decided_by="dean@example.com",
        conditions_json={},
        application_version=1,
    )

    result = await service.make_decision(
        tenant_id=1,
        application_id=application.id,
        request=request,
    )

    assert result.application_id == application.id
    assert "admissions.application.decision_made" in events
    assert "admissions_decisions_made" in metrics
    assert "admissions.decision.made" in brain_signals
