import pytest

from app.modules.admissions.schemas import (
    ApplicationConclusionType,
    ApplicationStage,
    DecisionMakeRequestSchema,
)
from app.modules.admissions.service import DecisionService

from tests.modules.admissions.conftest import ExecuteResult


def test_make_decision_requires_decision_pending_stage(db_session, application_factory, run_async) -> None:
    application = application_factory(stage=ApplicationStage.UNDER_REVIEW.value, version=3)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=application)
    service = DecisionService(db_session)

    with pytest.raises(ValueError, match="decision_pending"):
        run_async(
            service.make_decision(
                tenant_id=1,
                application_id=application.id,
                request=DecisionMakeRequestSchema(
                    decision_type=ApplicationConclusionType.ACCEPTED,
                    decided_by="dean@example.com",
                    application_version=3,
                ),
            )
        )


def test_make_decision_enforces_single_decision(db_session, application_factory, decision_factory, run_async) -> None:
    application = application_factory(stage=ApplicationStage.DECISION_PENDING.value, version=1)
    decision = decision_factory(application_id=application.id)
    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=application),
        ExecuteResult(scalar_one_or_none=decision),
    ]
    service = DecisionService(db_session)

    with pytest.raises(ValueError, match="Decision already exists"):
        run_async(
            service.make_decision(
                tenant_id=1,
                application_id=application.id,
                request=DecisionMakeRequestSchema(
                    decision_type=ApplicationConclusionType.ACCEPTED,
                    decided_by="dean@example.com",
                    application_version=1,
                ),
            )
        )


def test_make_decision_updates_application_and_audits(
    db_session,
    application_factory,
    audit_calls,
    run_async,
) -> None:
    application = application_factory(stage=ApplicationStage.DECISION_PENDING.value, version=2)
    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=application),
        ExecuteResult(scalar_one_or_none=None),
    ]
    service = DecisionService(db_session)

    result = run_async(
        service.make_decision(
            tenant_id=1,
            application_id=application.id,
            request=DecisionMakeRequestSchema(
                decision_type=ApplicationConclusionType.WAITLIST,
                decision_rationale="Capacity constraints",
                decided_by="dean@example.com",
                application_version=2,
            ),
        )
    )

    assert application.version == 3
    assert application.conclusion_type == ApplicationConclusionType.WAITLIST.value
    assert result.application_id == application.id
    assert audit_calls[0]["action"] == "admissions.decision.create"