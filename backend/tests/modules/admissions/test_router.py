from unittest.mock import MagicMock

import pytest

from app.main import app
from app.modules.admissions.dependencies import get_admissions_db
from app.modules.admissions.router import _map_service_error
from app.modules.admissions.schemas import (
    ApplicantListResponseSchema,
    ApplicantReadSchema,
    ApplicationDecisionReadSchema,
    ApplicationListResponseSchema,
    ApplicationReadSchema,
    ApplicationStage,
    DocumentReadSchema,
    StageTransitionResponseSchema,
)
from app.modules.admissions import service as admissions_service
from tests.conftest import ADMIN_HEADERS, _auth_headers, client


@pytest.fixture
def override_admissions_db() -> MagicMock:
    session = MagicMock()
    app.dependency_overrides[get_admissions_db] = lambda: session
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_admissions_db, None)


def test_create_applicant_endpoint_dispatches_trusted_tenant(monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock) -> None:
    async def fake_create_applicant(self, tenant_id: int, request, created_by: str) -> ApplicantReadSchema:
        assert tenant_id == 1
        assert created_by == "owner@example.com"
        assert request.email == "router@applicant.edu"
        return ApplicantReadSchema(
            id=101,
            tenant_id=tenant_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            program_id=request.program_id,
            application_year=request.application_year,
            status=request.status,
            external_id=request.external_id,
            metadata_json=request.metadata_json,
            created_by=created_by,
            created_at="2026-03-22T12:00:00Z",
            updated_at="2026-03-22T12:00:00Z",
        )

    monkeypatch.setattr(admissions_service.ApplicantService, "create_applicant", fake_create_applicant)

    response = client.post(
        "/api/admin/admissions/applicants",
        headers=ADMIN_HEADERS,
        json={
            "email": "router@applicant.edu",
            "first_name": "Router",
            "last_name": "Applicant",
            "program_id": 501,
            "application_year": 2026,
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["tenant_id"] == 1


def test_list_applicants_endpoint_is_rbac_protected(monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock) -> None:
    async def fake_list_applicants(self, tenant_id: int, **kwargs) -> ApplicantListResponseSchema:
        return ApplicantListResponseSchema(total=0, page=1, page_size=20, items=[])

    monkeypatch.setattr(admissions_service.ApplicantService, "list_applicants", fake_list_applicants)

    auditor_headers = _auth_headers("auditor.example", ["auditor"])
    student_headers = _auth_headers("student.example", ["student"])

    allowed = client.get("/api/admin/admissions/applicants", headers=auditor_headers)
    denied = client.get("/api/admin/admissions/applicants", headers=student_headers)

    assert allowed.status_code == 200, allowed.text
    assert denied.status_code == 403, denied.text


def test_patch_applicant_maps_not_found_to_404(monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock) -> None:
    async def fake_update_applicant(self, tenant_id: int, applicant_id: int, request, updated_by: str):
        raise ValueError(f"Applicant {applicant_id} not found or does not belong to tenant {tenant_id}")

    monkeypatch.setattr(admissions_service.ApplicantService, "update_applicant", fake_update_applicant)

    response = client.patch(
        "/api/admin/admissions/applicants/999",
        headers=ADMIN_HEADERS,
        json={"first_name": "Missing"},
    )

    assert response.status_code == 404, response.text


def test_create_application_invalid_payload_maps_to_400(override_admissions_db: MagicMock) -> None:
    response = client.post(
        "/api/admin/admissions/applications",
        headers=ADMIN_HEADERS,
        json={"program_id": 501},
    )

    assert response.status_code == 400, response.text


def test_stage_transition_invalid_transition_maps_to_400(monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock) -> None:
    async def fake_transition_stage(self, tenant_id: int, application_id: int, request, actor_id: str) -> StageTransitionResponseSchema:
        raise ValueError("Invalid transition: new → concluded")

    monkeypatch.setattr(admissions_service.StageTransitionService, "transition_stage", fake_transition_stage)

    response = client.post(
        "/api/admin/admissions/applications/201/stage-transition",
        headers=ADMIN_HEADERS,
        json={"to_stage": ApplicationStage.CONCLUDED.value},
    )

    assert response.status_code == 400, response.text


def test_decision_version_conflict_maps_to_409(monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock) -> None:
    async def fake_make_decision(self, tenant_id: int, application_id: int, request) -> ApplicationDecisionReadSchema:
        raise ValueError("Version mismatch: expected 2, but application version is 3")

    monkeypatch.setattr(admissions_service.DecisionService, "make_decision", fake_make_decision)

    response = client.post(
        "/api/admin/admissions/applications/201/decision",
        headers=ADMIN_HEADERS,
        json={
            "decision_type": "accepted",
            "decided_by": "dean@example.com",
            "application_version": 2,
        },
    )

    assert response.status_code == 409, response.text


def test_document_attach_endpoint_uses_document_write_permission(monkeypatch: pytest.MonkeyPatch, override_admissions_db: MagicMock) -> None:
    async def fake_attach_document(self, tenant_id: int, application_id: int, request, created_by: str) -> DocumentReadSchema:
        return DocumentReadSchema(
            id=301,
            tenant_id=tenant_id,
            application_id=application_id,
            document_type=request.document_type,
            document_key=request.document_key,
            file_name=request.file_name,
            file_size_bytes=request.file_size_bytes,
            mime_type=request.mime_type,
            status="received",
            metadata_json=request.metadata_json,
            created_by=created_by,
            created_at="2026-03-22T12:00:00Z",
            verified_at=None,
            verified_by=None,
        )

    monkeypatch.setattr(admissions_service.DocumentService, "attach_document", fake_attach_document)

    response = client.post(
        "/api/admin/admissions/applications/201/documents",
        headers=ADMIN_HEADERS,
        json={
            "document_type": "transcript",
            "document_key": "s3://tenant-1/app-201/transcript.pdf",
            "file_name": "transcript.pdf",
        },
    )

    assert response.status_code == 201, response.text


def test_router_error_mapping_helper_behaves_consistently() -> None:
    assert _map_service_error(PermissionError("forbidden")).status_code == 403
    assert _map_service_error(ValueError("resource not found")).status_code == 404
    assert _map_service_error(ValueError("Version mismatch: expected 1, but application version is 2")).status_code == 409
    assert _map_service_error(ValueError("Invalid transition")).status_code == 400