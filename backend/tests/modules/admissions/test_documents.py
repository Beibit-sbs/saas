import pytest

from app.modules.admissions.schemas import (
    ApplicationStage,
    DocumentAttachRequestSchema,
    DocumentStatus,
    DocumentVerifyRequestSchema,
)
from app.modules.admissions.service import DocumentService

from tests.modules.admissions.conftest import ExecuteResult


def test_attach_document_rejects_unsafe_document_key(db_session, application_factory, run_async) -> None:
    application = application_factory(stage=ApplicationStage.NEW.value)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=application)
    service = DocumentService(db_session)

    with pytest.raises(ValueError, match="safe reference"):
        run_async(
            service.attach_document(
                tenant_id=1,
                application_id=application.id,
                request=DocumentAttachRequestSchema(
                    document_type="transcript",
                    document_key="/srv/private/transcript.pdf",
                    file_name="transcript.pdf",
                ),
                created_by="owner@example.com",
            )
        )


def test_attach_document_rejects_upload_after_conclusion(db_session, application_factory, run_async) -> None:
    application = application_factory(stage=ApplicationStage.CONCLUDED.value)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=application)
    service = DocumentService(db_session)

    with pytest.raises(ValueError, match="Cannot upload documents"):
        run_async(
            service.attach_document(
                tenant_id=1,
                application_id=application.id,
                request=DocumentAttachRequestSchema(
                    document_type="transcript",
                    document_key="s3://tenant-1/app-1/transcript.pdf",
                    file_name="transcript.pdf",
                ),
                created_by="owner@example.com",
            )
        )


def test_verify_document_rejected_status_is_audited(
    db_session,
    document_factory,
    audit_calls,
    run_async,
) -> None:
    document = document_factory(status=DocumentStatus.RECEIVED.value)
    db_session.execute.return_value = ExecuteResult(scalar_one_or_none=document)
    service = DocumentService(db_session)

    result = run_async(
        service.verify_document(
            tenant_id=1,
            document_id=document.id,
            request=DocumentVerifyRequestSchema(
                status=DocumentStatus.REJECTED,
                verified_by="reviewer@example.com",
                metadata_json={"reason": "invalid scan"},
            ),
        )
    )

    assert result.status == DocumentStatus.REJECTED
    assert audit_calls[0]["action"] == "admissions.document.verify"