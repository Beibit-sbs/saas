from datetime import datetime

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
    # First execute: find applicant → returns applicant.
    # Second execute: check for existing active application → returns None (no duplicate).
    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=applicant),
        ExecuteResult(scalar_one_or_none=None),
    ]

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


def test_get_tenant_consistency_report_detects_orphaned_links(
    db_session,
    applicant_factory,
    application_factory,
    document_factory,
    stage_history_factory,
    decision_factory,
    run_async,
) -> None:
    applicants = [
        applicant_factory(id=101, program_id=501),
    ]
    applications = [
        application_factory(
            id=201,
            applicant_id=101,
            program_id=999,
            stage=ApplicationStage.CONCLUDED.value,
            decision_at=datetime(2026, 3, 22, 12, 0, 0),
        ),
        application_factory(id=202, applicant_id=404, program_id=501, stage=ApplicationStage.DECISION_PENDING.value),
    ]
    documents = [
        document_factory(id=301, application_id=777),
    ]
    stage_histories = [
        stage_history_factory(id=351, application_id=777, to_stage=ApplicationStage.RECEIVED.value),
        stage_history_factory(id=352, application_id=201, to_stage=ApplicationStage.RECEIVED.value),
    ]
    decisions = [
        decision_factory(id=401, application_id=888),
        decision_factory(id=402, application_id=202),
    ]

    db_session.execute.side_effect = [
        ExecuteResult(scalars=applicants),
        ExecuteResult(scalars=applications),
        ExecuteResult(scalars=documents),
        ExecuteResult(scalars=stage_histories),
        ExecuteResult(scalars=decisions),
    ]

    service = ApplicationService(db_session)
    report = run_async(service.get_tenant_consistency_report(tenant_id=1))

    assert report.applicant_count == 1
    assert report.application_count == 2
    assert report.document_count == 1
    assert report.decision_count == 2
    assert report.issue_count >= 10

    issue_types = {issue.issue_type for issue in report.issues}
    assert "application_program_mismatch" in issue_types
    assert "application_missing_applicant" in issue_types
    assert "document_missing_application" in issue_types
    assert "decision_missing_application" in issue_types
    assert "stage_history_missing_application" in issue_types
    assert "concluded_application_missing_decision" in issue_types
    assert "decision_application_stage_mismatch" in issue_types
    assert "application_stage_missing_history_entry" in issue_types
    assert "application_decision_timestamp_without_decision" in issue_types


def test_get_tenant_consistency_report_detects_applicant_and_application_field_drift(
    db_session,
    applicant_factory,
    application_factory,
    document_factory,
    stage_history_factory,
    decision_factory,
    run_async,
) -> None:
    applicants = [
        applicant_factory(id=501, program_id=801, email="valid@example.com", status="active"),
        applicant_factory(id=502, program_id=802, email=None, status="inactive"),
        applicant_factory(id=503, program_id=803, email="bad-email", status="BOGUS_STATUS"),
    ]
    applications = [
        application_factory(id=601, applicant_id=501, program_id=801, stage="valid_stage"),
        application_factory(id=602, applicant_id=502, program_id=802, stage="INVALID_STAGE"),
    ]
    documents = []
    stage_histories = []
    decisions = []

    db_session.execute.side_effect = [
        ExecuteResult(scalars=applicants),
        ExecuteResult(scalars=applications),
        ExecuteResult(scalars=documents),
        ExecuteResult(scalars=stage_histories),
        ExecuteResult(scalars=decisions),
    ]

    service = ApplicationService(db_session)
    report = run_async(service.get_tenant_consistency_report(tenant_id=1))

    issue_types = [issue.issue_type for issue in report.issues]
    assert "applicant_missing_email" in issue_types
    assert "applicant_invalid_email_format" in issue_types
    assert "applicant_invalid_status" in issue_types
    assert "application_invalid_status" in issue_types


def test_get_tenant_consistency_report_detects_duplicate_applications(
    db_session,
    applicant_factory,
    application_factory,
    document_factory,
    stage_history_factory,
    decision_factory,
    run_async,
) -> None:
    applicants = [
        applicant_factory(id=701, program_id=901, email="app@example.com", status="active", application_year="2026"),
    ]
    applications = [
        application_factory(id=801, applicant_id=701, program_id=901, stage="new"),
        application_factory(id=802, applicant_id=701, program_id=901, stage="new"),
    ]
    documents = []
    stage_histories = []
    decisions = []

    db_session.execute.side_effect = [
        ExecuteResult(scalars=applicants),
        ExecuteResult(scalars=applications),
        ExecuteResult(scalars=documents),
        ExecuteResult(scalars=stage_histories),
        ExecuteResult(scalars=decisions),
    ]

    service = ApplicationService(db_session)
    report = run_async(service.get_tenant_consistency_report(tenant_id=1))

    issue_types = [issue.issue_type for issue in report.issues]
    assert issue_types.count("duplicate_application_per_applicant") == 2


def test_get_tenant_consistency_report_detects_duplicate_decisions_per_application(
    db_session,
    applicant_factory,
    application_factory,
    document_factory,
    stage_history_factory,
    decision_factory,
    run_async,
) -> None:
    applicants = [
        applicant_factory(id=901, program_id=1001, email="dupdec@example.com", status="active"),
    ]
    applications = [
        application_factory(id=1001, applicant_id=901, program_id=1001, stage=ApplicationStage.CONCLUDED.value),
    ]
    documents = []
    stage_histories = [
        stage_history_factory(id=1201, application_id=1001, to_stage=ApplicationStage.CONCLUDED.value),
    ]
    decisions = [
        decision_factory(id=1301, application_id=1001),
        decision_factory(id=1302, application_id=1001),
    ]

    db_session.execute.side_effect = [
        ExecuteResult(scalars=applicants),
        ExecuteResult(scalars=applications),
        ExecuteResult(scalars=documents),
        ExecuteResult(scalars=stage_histories),
        ExecuteResult(scalars=decisions),
    ]

    service = ApplicationService(db_session)
    report = run_async(service.get_tenant_consistency_report(tenant_id=1))

    issue_types = [issue.issue_type for issue in report.issues]
    assert issue_types.count("duplicate_decisions_for_application") == 2