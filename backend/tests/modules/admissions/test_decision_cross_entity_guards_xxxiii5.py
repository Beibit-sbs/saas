from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.modules.admissions.schemas import ApplicationStage
from app.modules.admissions.service import DecisionService

from tests.modules.admissions.conftest import ExecuteResult


def _open_period() -> dict[str, str]:
    now = datetime.now(UTC)
    return {
        "start_at": (now - timedelta(days=1)).isoformat(),
        "end_at": (now + timedelta(days=1)).isoformat(),
    }


def _base_metadata() -> dict[str, object]:
    return {
        "admission_period": _open_period(),
        "program_quota_limit": 5,
        "required_documents": ["transcript", "identification"],
        "workflow_instance_id": 991,
    }


def _program(status: str = "active") -> MagicMock:
    program = MagicMock()
    program.id = 501
    program.status = status
    return program


def _doc(document_type: str) -> MagicMock:
    item = MagicMock()
    item.document_type = document_type
    return item


def test_finalize_blocks_when_admission_period_missing(
    db_session,
    application_factory,
    run_async,
) -> None:
    application = application_factory(
        stage=ApplicationStage.DECISION_PENDING.value,
        metadata_json={"workflow_instance_id": 991, "program_quota_limit": 5},
        program_id=501,
    )
    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=application),
        ExecuteResult(scalar_one_or_none=None),
    ]
    service = DecisionService(db_session)

    with pytest.raises(ValueError, match="admission period"):
        run_async(
            service.finalize_workflow_decision(
                tenant_id=1,
                application_id=application.id,
                workflow_instance_id=991,
                approval_action="approve",
                actor="dean@example.com",
            )
        )

    db_session.add.assert_not_called()
    db_session.commit.assert_not_called()


def test_cross_entity_guard_blocks_program_mismatch(
    db_session,
    application_factory,
    applicant_factory,
) -> None:
    application = application_factory(
        stage=ApplicationStage.DECISION_PENDING.value,
        metadata_json=_base_metadata(),
        program_id=501,
    )
    applicant = applicant_factory(program_id=777)

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=applicant),
    ]

    service = DecisionService(db_session)
    with pytest.raises(ValueError, match="applicant/program mismatch"):
        service._validate_final_decision_cross_entity_guards(
            tenant_id=1,
            application=application,
        )


def test_cross_entity_guard_blocks_quota_exhausted(
    db_session,
    application_factory,
    applicant_factory,
) -> None:
    application = application_factory(
        stage=ApplicationStage.DECISION_PENDING.value,
        metadata_json=_base_metadata(),
        program_id=501,
    )
    applicant = applicant_factory(program_id=501, application_year=2026)

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=applicant),
        ExecuteResult(scalar_one_or_none=_program()),
        ExecuteResult(scalar=5),
    ]

    service = DecisionService(db_session)
    with pytest.raises(ValueError, match="quota is exhausted"):
        service._validate_final_decision_cross_entity_guards(
            tenant_id=1,
            application=application,
        )


def test_cross_entity_guard_blocks_missing_verified_documents(
    db_session,
    application_factory,
    applicant_factory,
) -> None:
    application = application_factory(
        stage=ApplicationStage.DECISION_PENDING.value,
        metadata_json=_base_metadata(),
        program_id=501,
    )
    applicant = applicant_factory(program_id=501)

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=applicant),
        ExecuteResult(scalar_one_or_none=_program()),
        ExecuteResult(scalar=1),
        ExecuteResult(scalars=[_doc("transcript")]),
    ]

    service = DecisionService(db_session)
    with pytest.raises(ValueError, match="required verified documents are missing"):
        service._validate_final_decision_cross_entity_guards(
            tenant_id=1,
            application=application,
        )


def test_cross_entity_guard_blocks_duplicate_student_identity(
    db_session,
    application_factory,
    applicant_factory,
) -> None:
    application = application_factory(
        stage=ApplicationStage.DECISION_PENDING.value,
        metadata_json=_base_metadata(),
        program_id=501,
    )
    applicant = applicant_factory(program_id=501, email="duplicate@example.com")
    person = MagicMock()
    person.id = 44

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=applicant),
        ExecuteResult(scalar_one_or_none=_program()),
        ExecuteResult(scalar=0),
        ExecuteResult(scalars=[_doc("transcript"), _doc("identification")]),
        ExecuteResult(scalar_one_or_none=person),
        ExecuteResult(scalar=1),
    ]

    service = DecisionService(db_session)
    with pytest.raises(ValueError, match="duplicate student identity"):
        service._validate_final_decision_cross_entity_guards(
            tenant_id=1,
            application=application,
        )


def test_cross_entity_guard_allows_valid_acceptance(
    db_session,
    application_factory,
    applicant_factory,
) -> None:
    application = application_factory(
        stage=ApplicationStage.DECISION_PENDING.value,
        metadata_json=_base_metadata(),
        program_id=501,
    )
    applicant = applicant_factory(program_id=501, email="new@example.com")

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=applicant),
        ExecuteResult(scalar_one_or_none=_program("active")),
        ExecuteResult(scalar=2),
        ExecuteResult(scalars=[_doc("transcript"), _doc("identification")]),
        ExecuteResult(scalar_one_or_none=None),
    ]

    service = DecisionService(db_session)
    service._validate_final_decision_cross_entity_guards(
        tenant_id=1,
        application=application,
    )
