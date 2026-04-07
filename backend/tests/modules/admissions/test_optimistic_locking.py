import pytest

from app.modules.admissions.schemas import (
    ApplicationConclusionType,
    ApplicationStage,
    DecisionMakeRequestSchema,
)
from app.modules.admissions.service import DecisionService

from tests.modules.admissions.conftest import ExecuteResult


def test_make_decision_rejects_stale_application_version(db_session, application_factory, audit_calls, run_async) -> None:
    application = application_factory(stage=ApplicationStage.DECISION_PENDING.value, version=3)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=application)
    service = DecisionService(db_session)

    with pytest.raises(ValueError, match="Version mismatch"):
        run_async(
            service.make_decision(
                tenant_id=1,
                application_id=application.id,
                request=DecisionMakeRequestSchema(
                    decision_type=ApplicationConclusionType.ACCEPTED,
                    decided_by="dean@example.com",
                    application_version=2,
                ),
            )
        )

    assert audit_calls == []
    db_session.commit.assert_not_called()