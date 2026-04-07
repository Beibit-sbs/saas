from app.modules.admissions.schemas import (
    ApplicantCreateSchema,
    ApplicationCreateSchema,
    ApplicationConclusionType,
    ApplicationStage,
    DecisionMakeRequestSchema,
    DocumentAttachRequestSchema,
    StageTransitionRequestSchema,
)
from app.modules.admissions.service import (
    ApplicantService,
    ApplicationService,
    DecisionService,
    DocumentService,
    StageTransitionService,
)

from tests.modules.admissions.conftest import ExecuteResult


def test_all_mutating_services_emit_explicit_tenant_audit_context(
    db_session,
    applicant_factory,
    application_factory,
    audit_calls,
    run_async,
) -> None:
    applicant = applicant_factory()
    application_for_document = application_factory(id=201, stage=ApplicationStage.NEW.value, version=1)
    application_for_transition = application_factory(id=201, stage=ApplicationStage.RECEIVED.value, version=1)
    application_for_decision = application_factory(id=201, stage=ApplicationStage.DECISION_PENDING.value, version=1)

    db_session.execute.side_effect = [
        ExecuteResult(scalar_one_or_none=applicant),
        ExecuteResult(scalar_one_or_none=application_for_document),
        ExecuteResult(scalar_one_or_none=application_for_transition),
        ExecuteResult(scalar_one_or_none=application_for_decision),
        ExecuteResult(scalar_one_or_none=None),
    ]

    run_async(
        ApplicationService(db_session).create_application(
            tenant_id=77,
            request=ApplicationCreateSchema(applicant_id=applicant.id, program_id=applicant.program_id),
            created_by="owner@example.com",
        )
    )
    run_async(
        DocumentService(db_session).attach_document(
            tenant_id=77,
            application_id=application_for_document.id,
            request=DocumentAttachRequestSchema(
                document_type="transcript",
                document_key="s3://tenant-77/app-201/transcript.pdf",
                file_name="transcript.pdf",
            ),
            created_by="owner@example.com",
        )
    )
    run_async(
        StageTransitionService(db_session).transition_stage(
            tenant_id=77,
            application_id=application_for_transition.id,
            request=StageTransitionRequestSchema(to_stage=ApplicationStage.UNDER_REVIEW),
            actor_id="reviewer@example.com",
        )
    )
    run_async(
        DecisionService(db_session).make_decision(
            tenant_id=77,
            application_id=application_for_decision.id,
            request=DecisionMakeRequestSchema(
                decision_type=ApplicationConclusionType.ACCEPTED,
                decided_by="dean@example.com",
                application_version=1,
            ),
        )
    )

    assert len(audit_calls) == 4
    assert {call["tenant_id"] for call in audit_calls} == {77}
    assert all(call["path"].startswith("/internal/admissions/") for call in audit_calls)


def test_applicant_create_audit_payload_contains_resource_context(db_session, audit_calls, run_async) -> None:
    run_async(
        ApplicantService(db_session).create_applicant(
            tenant_id=5,
            request=ApplicantCreateSchema(
                email="audit@applicant.edu",
                first_name="Audit",
                last_name="Target",
                program_id=12,
                application_year=2026,
            ),
            created_by="owner@example.com",
        )
    )

    payload = audit_calls[0]
    assert payload["tenant_id"] == 5
    assert payload["entity"] == "applicant"
    assert payload["metadata"]["program_id"] == 12