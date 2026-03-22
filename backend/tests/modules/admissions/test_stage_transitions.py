import pytest

from app.modules.admissions.schemas import ApplicationStage, StageTransitionRequestSchema
from app.modules.admissions.service import StageTransitionService

from tests.modules.admissions.conftest import ExecuteResult


def test_invalid_stage_transition_is_rejected(db_session, application_factory, run_async) -> None:
    application = application_factory(stage=ApplicationStage.NEW.value)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=application)
    service = StageTransitionService(db_session)

    with pytest.raises(ValueError, match="Invalid transition"):
        run_async(
            service.transition_stage(
                tenant_id=1,
                application_id=application.id,
                request=StageTransitionRequestSchema(to_stage=ApplicationStage.CONCLUDED),
                actor_id="reviewer@example.com",
            )
        )

    db_session.add.assert_not_called()


def test_transition_stage_creates_append_only_history_and_updates_application(
    db_session,
    application_factory,
    audit_calls,
    run_async,
) -> None:
    application = application_factory(stage=ApplicationStage.NEW.value)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=application)
    service = StageTransitionService(db_session)

    result = run_async(
        service.transition_stage(
            tenant_id=1,
            application_id=application.id,
            request=StageTransitionRequestSchema(
                to_stage=ApplicationStage.RECEIVED,
                reason="application submitted",
            ),
            actor_id="reviewer@example.com",
        )
    )

    history_record = db_session.add.call_args.args[0]
    assert history_record.from_stage == ApplicationStage.NEW.value
    assert history_record.to_stage == ApplicationStage.RECEIVED.value
    assert application.stage == ApplicationStage.RECEIVED.value
    db_session.delete.assert_not_called()
    assert audit_calls[0]["action"] == "admissions.application.update"
    assert result.to_stage == ApplicationStage.RECEIVED


def test_transition_to_concluded_requires_existing_decision(db_session, application_factory, run_async) -> None:
    application = application_factory(stage=ApplicationStage.DECISION_PENDING.value)
    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=application),
        ExecuteResult(scalar_one_or_none=None),
    ]
    service = StageTransitionService(db_session)

    with pytest.raises(ValueError, match="without a decision"):
        run_async(
            service.transition_stage(
                tenant_id=1,
                application_id=application.id,
                request=StageTransitionRequestSchema(to_stage=ApplicationStage.CONCLUDED),
                actor_id="reviewer@example.com",
            )
        )