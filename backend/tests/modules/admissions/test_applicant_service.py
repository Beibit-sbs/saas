import pytest

from app.modules.admissions.schemas import ApplicantCreateSchema, ApplicantUpdateSchema
from app.modules.admissions.service import ApplicantService

from tests.modules.admissions.conftest import ExecuteResult


def test_create_applicant_requires_explicit_tenant_id(db_session, audit_calls, run_async) -> None:
    service = ApplicantService(db_session)

    with pytest.raises(ValueError, match="tenant_id"):
        run_async(
            service.create_applicant(
                tenant_id=None,
                request=ApplicantCreateSchema(
                    email="new@applicant.edu",
                    first_name="Grace",
                    last_name="Hopper",
                    program_id=900,
                    application_year=2026,
                ),
                created_by="owner@example.com",
            )
        )

    assert audit_calls == []
    db_session.commit.assert_not_called()


def test_create_applicant_persists_and_audits(db_session, audit_calls, run_async) -> None:
    service = ApplicantService(db_session)

    result = run_async(
        service.create_applicant(
            tenant_id=7,
            request=ApplicantCreateSchema(
                email="new@applicant.edu",
                first_name="Grace",
                last_name="Hopper",
                program_id=900,
                application_year=2026,
            ),
            created_by="owner@example.com",
        )
    )

    db_session.add.assert_called_once()
    db_session.flush.assert_called_once()
    db_session.commit.assert_called_once()
    assert result.tenant_id == 7
    assert len(audit_calls) == 1
    assert audit_calls[0]["tenant_id"] == 7
    assert audit_calls[0]["action"] == "admissions.applicant.create"


def test_get_applicant_scopes_lookup_by_tenant(db_session, applicant_factory, run_async) -> None:
    applicant = applicant_factory(tenant_id=9)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=applicant)

    service = ApplicantService(db_session)
    result = run_async(service.get_applicant(tenant_id=9, applicant_id=applicant.id))

    assert result.id == applicant.id
    assert result.tenant_id == 9


def test_update_applicant_updates_model_and_audits(db_session, applicant_factory, audit_calls, run_async) -> None:
    applicant = applicant_factory(first_name="Ada")
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=applicant)

    service = ApplicantService(db_session)
    result = run_async(
        service.update_applicant(
            tenant_id=1,
            applicant_id=applicant.id,
            request=ApplicantUpdateSchema(first_name="Updated", metadata_json={"gpa": 4.0}),
            updated_by="reviewer@example.com",
        )
    )

    assert applicant.first_name == "Updated"
    assert result.first_name == "Updated"
    assert audit_calls[0]["action"] == "admissions.applicant.update"
    db_session.commit.assert_called_once()