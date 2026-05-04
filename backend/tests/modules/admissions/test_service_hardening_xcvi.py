"""XCVI - Admissions Service Hardening (canonical 10-step hooks).

Verifies:
1. submit_application uses canonical EventPublisher constructor and records metric.
2. transition_stage uses canonical EventPublisher constructor and records metric.
3. make_decision survives outcome hook failure and still records metric.
4. finalize_workflow_decision uses canonical EventPublisher constructor and records metric.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

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

MODULE = "app.modules.admissions.service"


@pytest.mark.asyncio
async def test_submit_application_uses_canonical_event_publisher_and_metric(
    db_session,
    application_factory,
) -> None:
    application = application_factory(stage=ApplicationStage.NEW.value, version=3, metadata_json={})
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=application)

    metrics: list[tuple[int, str, int]] = []

    def _metric(*, tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    with (
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.usage.service.record_usage_event", side_effect=_metric),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        service = ApplicationService(db_session)
        with patch.object(service, "_start_admissions_workflow", AsyncMock(return_value={"id": 789})):
            result = await service.submit_application(
                tenant_id=1,
                application_id=application.id,
                actor="applicant@test.com",
                expected_version=3,
            )

    assert result.stage == ApplicationStage.RECEIVED
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "admissions_applications_submitted", 1) in metrics


@pytest.mark.asyncio
async def test_transition_stage_uses_canonical_event_publisher_and_metric(
    db_session,
    application_factory,
) -> None:
    application = application_factory(stage=ApplicationStage.RECEIVED.value)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=application)

    metrics: list[tuple[int, str, int]] = []

    def _metric(*, tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    with (
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.usage.service.record_usage_event", side_effect=_metric),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch("app.modules.brain_core.service.brain_core_service"),
    ):
        service = StageTransitionService(db_session)
        result = await service.transition_stage(
            tenant_id=1,
            application_id=application.id,
            request=StageTransitionRequestSchema(
                to_stage=ApplicationStage.UNDER_REVIEW,
                reason="manual review started",
            ),
            actor_id="reviewer@test.com",
        )

    assert result.to_stage == ApplicationStage.UNDER_REVIEW
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "admissions_stage_transitions", 1) in metrics


@pytest.mark.asyncio
async def test_make_decision_survives_outcome_failure_and_records_metric(
    db_session,
    application_factory,
) -> None:
    application = application_factory(stage=ApplicationStage.DECISION_PENDING.value, version=1)
    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=application),
        ExecuteResult(scalar_one_or_none=None),
    ]

    metrics: list[tuple[int, str, int]] = []

    def _metric(*, tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    with (
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.usage.service.record_usage_event", side_effect=_metric),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
    ):
        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        service = DecisionService(db_session)
        result = await service.make_decision(
            tenant_id=1,
            application_id=application.id,
            request=DecisionMakeRequestSchema(
                decision_type=ApplicationConclusionType.REJECTED,
                decision_rationale="insufficient score",
                decided_by="dean@test.com",
                conditions_json={},
                application_version=1,
            ),
        )

    assert result.application_id == application.id
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "admissions_decisions_made", 1) in metrics


@pytest.mark.asyncio
async def test_finalize_workflow_decision_uses_canonical_publisher_and_metric(
    db_session,
    application_factory,
) -> None:
    application = application_factory(
        stage=ApplicationStage.DECISION_PENDING.value,
        metadata_json={"workflow_instance_id": 999},
    )
    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=application),
        ExecuteResult(scalar_one_or_none=None),
    ]

    metrics: list[tuple[int, str, int]] = []

    def _metric(*, tenant_id: int, metric: str, value: int = 1) -> None:
        metrics.append((tenant_id, metric, value))

    with (
        patch(f"{MODULE}.log_admin_action"),
        patch("app.modules.usage.service.record_usage_event", side_effect=_metric),
        patch(f"{MODULE}.EventPublisher") as mock_ep,
        patch("app.modules.brain_core.service.brain_core_service") as mock_brain,
    ):
        mock_brain.record_dispatch_outcome.side_effect = RuntimeError("brain down")
        service = DecisionService(db_session)
        with patch.object(service, "_provision_student_identity_on_accept", AsyncMock(return_value=None)):
            result = await service.finalize_workflow_decision(
                tenant_id=1,
                application_id=application.id,
                workflow_instance_id=999,
                approval_action="reject",
                actor="workflow@test.com",
            )

    assert result.application_id == application.id
    mock_ep.assert_called_once_with()
    mock_ep.return_value.publish_event.assert_called_once()
    assert (1, "admissions_workflow_decisions_finalized", 1) in metrics
