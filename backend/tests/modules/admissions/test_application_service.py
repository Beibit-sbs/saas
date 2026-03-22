import pytest

from app.modules.admissions.schemas import ApplicationCreateSchema, ApplicationStage
from app.modules.admissions.service import ApplicationService

from tests.modules.admissions.conftest import ExecuteResult


def test_create_application_requires_tenant_scoped_applicant(db_session, audit_calls, run_async) -> None:
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=None)
    service = ApplicationService(db_session)

    with pytest.raises(ValueError, match="Applicant .* not found"):
        run_async(
            service.create_application(
                tenant_id=1,
                request=ApplicationCreateSchema(applicant_id=999, program_id=501),
                created_by="owner@example.com",
            )
        )

    assert audit_calls == []


def test_create_application_creates_new_stage_application(
    db_session,
    applicant_factory,
    audit_calls,
    run_async,
) -> None:
    applicant = applicant_factory()
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=applicant)

    service = ApplicationService(db_session)
    result = run_async(
        service.create_application(
            tenant_id=1,
            request=ApplicationCreateSchema(applicant_id=applicant.id, program_id=applicant.program_id),
            created_by="owner@example.com",
        )
    )

    assert result.stage == ApplicationStage.NEW
    assert audit_calls[0]["action"] == "admissions.application.create"
    db_session.commit.assert_called_once()


def test_list_applications_returns_tenant_scoped_page(db_session, application_factory, run_async) -> None:
    applications = [
        application_factory(id=201, tenant_id=1),
        application_factory(id=202, tenant_id=1, stage=ApplicationStage.UNDER_REVIEW.value),
    ]
    db_session.execute.side_effect = [
        ExecuteResult(scalar=2),
        ExecuteResult(scalars=applications),
    ]

    service = ApplicationService(db_session)
    result = run_async(service.list_applications(tenant_id=1, page=1, page_size=20))

    assert result.total == 2
    assert [item.id for item in result.items] == [201, 202]