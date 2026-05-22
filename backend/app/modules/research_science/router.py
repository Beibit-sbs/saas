"""FastAPI router for Research / Science backend foundation."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.router_errors import integrity_error_to_http, permission_error_to_http, tenant_not_found_to_http, validation_error_to_http
from app.core.module_helpers.service_validation import DomainValidationError, OptimisticLockConflictError, TenantResourceNotFoundError
from app.modules.rbac.security import get_actor, permission_dependency
from app.modules.research_science import permissions, service
from app.modules.research_science.dependencies import get_research_science_db, require_research_science_tenant
from app.modules.research_science.schemas import (
    ConferenceParticipationCreateRequest,
    ConferenceParticipationListResponse,
    ConferenceParticipationResponse,
    ConferenceParticipationUpdateRequest,
    GrantApplicationCreateRequest,
    GrantApplicationListResponse,
    GrantApplicationResponse,
    GrantApplicationUpdateRequest,
    GrantDeliverableCreateRequest,
    GrantDeliverableListResponse,
    GrantDeliverableResponse,
    GrantDeliverableUpdateRequest,
    PublicationMetadataCreateRequest,
    PublicationMetadataListResponse,
    PublicationMetadataResponse,
    PublicationMetadataUpdateRequest,
    ResearchAuditEventListResponse,
    ResearchAuditEventResponse,
    ResearchBridgeCreateRequest,
    ResearchBridgeListResponse,
    ResearchBridgeResponse,
    ResearchBridgeSummaryResponse,
    ResearchEthicsAmendmentCreateRequest,
    ResearchEthicsAmendmentListResponse,
    ResearchEthicsAmendmentResponse,
    ResearchEthicsRequestCreateRequest,
    ResearchEthicsRequestListResponse,
    ResearchEthicsRequestResponse,
    ResearchEthicsRequestUpdateRequest,
    ResearchEvidenceCreateRequest,
    ResearchEvidenceListResponse,
    ResearchEvidenceResponse,
    ResearchProjectCreateRequest,
    ResearchProjectListResponse,
    ResearchProjectResponse,
    ResearchProjectUpdateRequest,
    ResearchScienceDashboardResponse,
    ResearchScienceHealthResponse,
    ResearchScienceLimitationsResponse,
    ResearchScienceMatrixSummaryResponse,
    ScientificSupervisionCreateRequest,
    ScientificSupervisionListResponse,
    ScientificSupervisionResponse,
    ScientificSupervisionUpdateRequest,
    StudentResearchWorkCreateRequest,
    StudentResearchWorkListResponse,
    StudentResearchWorkResponse,
    StudentResearchWorkUpdateRequest,
)


router = APIRouter(prefix="/api/admin/research-science", tags=["research-science"])

_Tenant = Annotated[int, Depends(require_research_science_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_research_science_db)]


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _handle(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        raise tenant_not_found_to_http(exc)
    if isinstance(exc, (DomainValidationError, ValueError)):
        raise validation_error_to_http(exc)
    if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
        raise integrity_error_to_http(exc)
    raise exc


def _resp(obj: Any, schema_cls):
    if isinstance(obj, dict):
        data = dict(obj)
    else:
        data = obj.__dict__.copy()
    if "limitations_json" in data:
        data["limitations"] = list(data.pop("limitations_json") or [])
    if "metadata_json" in data:
        data["metadata"] = dict(data.pop("metadata_json") or {})
    if "summary_json" in data:
        data["summary"] = dict(data.pop("summary_json") or {})
    if "payload_json" in data:
        data["payload"] = dict(data.pop("payload_json") or {})
    data.setdefault("official_external_verification", data.get("official_verification_enabled", False))
    return schema_cls.model_validate(data)


@router.get("/health", response_model=ResearchScienceHealthResponse)
def get_health(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.HEALTH_READ))], tenant: _Tenant, db: _DB) -> ResearchScienceHealthResponse:
    try:
        return service.get_research_health_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/dashboard", response_model=ResearchScienceDashboardResponse)
def get_dashboard(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))], tenant: _Tenant, db: _DB) -> ResearchScienceDashboardResponse:
    try:
        return service.get_research_dashboard_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/matrix-summary", response_model=ResearchScienceMatrixSummaryResponse)
def get_matrix_summary(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.MATRIX_READ))], tenant: _Tenant, db: _DB) -> ResearchScienceMatrixSummaryResponse:
    try:
        return service.get_research_matrix_summary_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/limitations", response_model=ResearchScienceLimitationsResponse)
def get_limitations(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.LIMITATIONS_READ))], tenant: _Tenant, db: _DB) -> ResearchScienceLimitationsResponse:
    try:
        return service.list_research_limitations_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/projects", response_model=ResearchProjectListResponse)
def list_projects(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PROJECTS_READ))], tenant: _Tenant, db: _DB) -> ResearchProjectListResponse:
    try:
        return ResearchProjectListResponse(items=[_resp(item, ResearchProjectResponse) for item in service.list_research_projects_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/projects", response_model=ResearchProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.PROJECTS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ResearchProjectResponse:
    try:
        body = _parse_payload(ResearchProjectCreateRequest, payload)
        return _resp(service.create_research_project_service(db, tenant, actor, body), ResearchProjectResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/projects/{project_id}", response_model=ResearchProjectResponse)
def get_project(project_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PROJECTS_READ))], tenant: _Tenant, db: _DB) -> ResearchProjectResponse:
    try:
        return _resp(service.get_research_project_service(db, tenant, project_id), ResearchProjectResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/projects/{project_id}", response_model=ResearchProjectResponse)
def update_project(project_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.PROJECTS_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ResearchProjectResponse:
    try:
        body = _parse_payload(ResearchProjectUpdateRequest, payload)
        return _resp(service.update_research_project_service(db, tenant, actor, project_id, body), ResearchProjectResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/student-research", response_model=StudentResearchWorkListResponse)
def list_student_research(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.STUDENT_RESEARCH_READ))], tenant: _Tenant, db: _DB) -> StudentResearchWorkListResponse:
    try:
        return StudentResearchWorkListResponse(items=[_resp(item, StudentResearchWorkResponse) for item in service.list_student_research_work_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/student-research", response_model=StudentResearchWorkResponse, status_code=status.HTTP_201_CREATED)
def create_student_research(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.STUDENT_RESEARCH_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentResearchWorkResponse:
    try:
        body = _parse_payload(StudentResearchWorkCreateRequest, payload)
        return _resp(service.create_student_research_work_service(db, tenant, actor, body), StudentResearchWorkResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/student-research/{student_research_id}", response_model=StudentResearchWorkResponse)
def get_student_research(student_research_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.STUDENT_RESEARCH_READ))], tenant: _Tenant, db: _DB) -> StudentResearchWorkResponse:
    try:
        return _resp(service.get_student_research_work_service(db, tenant, student_research_id), StudentResearchWorkResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/student-research/{student_research_id}", response_model=StudentResearchWorkResponse)
def update_student_research(student_research_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.STUDENT_RESEARCH_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> StudentResearchWorkResponse:
    try:
        body = _parse_payload(StudentResearchWorkUpdateRequest, payload)
        return _resp(service.update_student_research_work_service(db, tenant, actor, student_research_id, body), StudentResearchWorkResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/supervision", response_model=ScientificSupervisionListResponse)
def list_supervision(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.SUPERVISION_READ))], tenant: _Tenant, db: _DB) -> ScientificSupervisionListResponse:
    try:
        return ScientificSupervisionListResponse(items=[_resp(item, ScientificSupervisionResponse) for item in service.list_scientific_supervisions_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/supervision", response_model=ScientificSupervisionResponse, status_code=status.HTTP_201_CREATED)
def create_supervision(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.SUPERVISION_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ScientificSupervisionResponse:
    try:
        body = _parse_payload(ScientificSupervisionCreateRequest, payload)
        return _resp(service.create_scientific_supervision_service(db, tenant, actor, body), ScientificSupervisionResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/supervision/{supervision_id}", response_model=ScientificSupervisionResponse)
def get_supervision(supervision_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.SUPERVISION_READ))], tenant: _Tenant, db: _DB) -> ScientificSupervisionResponse:
    try:
        return _resp(service.get_scientific_supervision_service(db, tenant, supervision_id), ScientificSupervisionResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/supervision/{supervision_id}", response_model=ScientificSupervisionResponse)
def update_supervision(supervision_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.SUPERVISION_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ScientificSupervisionResponse:
    try:
        body = _parse_payload(ScientificSupervisionUpdateRequest, payload)
        return _resp(service.update_scientific_supervision_service(db, tenant, actor, supervision_id, body), ScientificSupervisionResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/publications", response_model=PublicationMetadataListResponse)
def list_publications(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PUBLICATIONS_READ))], tenant: _Tenant, db: _DB) -> PublicationMetadataListResponse:
    try:
        return PublicationMetadataListResponse(items=[_resp(item, PublicationMetadataResponse) for item in service.list_publication_metadata_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/publications", response_model=PublicationMetadataResponse, status_code=status.HTTP_201_CREATED)
def create_publication(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.PUBLICATIONS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> PublicationMetadataResponse:
    try:
        body = _parse_payload(PublicationMetadataCreateRequest, payload)
        return _resp(service.create_publication_metadata_service(db, tenant, actor, body), PublicationMetadataResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/publications/{publication_id}", response_model=PublicationMetadataResponse)
def get_publication(publication_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.PUBLICATIONS_READ))], tenant: _Tenant, db: _DB) -> PublicationMetadataResponse:
    try:
        return _resp(service.get_publication_metadata_service(db, tenant, publication_id), PublicationMetadataResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/publications/{publication_id}", response_model=PublicationMetadataResponse)
def update_publication(publication_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.PUBLICATIONS_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> PublicationMetadataResponse:
    try:
        body = _parse_payload(PublicationMetadataUpdateRequest, payload)
        return _resp(service.update_publication_metadata_service(db, tenant, actor, publication_id, body), PublicationMetadataResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/conferences", response_model=ConferenceParticipationListResponse)
def list_conferences(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.CONFERENCES_READ))], tenant: _Tenant, db: _DB) -> ConferenceParticipationListResponse:
    try:
        return ConferenceParticipationListResponse(items=[_resp(item, ConferenceParticipationResponse) for item in service.list_conference_participation_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/conferences", response_model=ConferenceParticipationResponse, status_code=status.HTTP_201_CREATED)
def create_conference(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.CONFERENCES_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ConferenceParticipationResponse:
    try:
        body = _parse_payload(ConferenceParticipationCreateRequest, payload)
        return _resp(service.create_conference_participation_service(db, tenant, actor, body), ConferenceParticipationResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/conferences/{conference_id}", response_model=ConferenceParticipationResponse)
def get_conference(conference_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.CONFERENCES_READ))], tenant: _Tenant, db: _DB) -> ConferenceParticipationResponse:
    try:
        return _resp(service.get_conference_participation_service(db, tenant, conference_id), ConferenceParticipationResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/conferences/{conference_id}", response_model=ConferenceParticipationResponse)
def update_conference(conference_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.CONFERENCES_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ConferenceParticipationResponse:
    try:
        body = _parse_payload(ConferenceParticipationUpdateRequest, payload)
        return _resp(service.update_conference_participation_service(db, tenant, actor, conference_id, body), ConferenceParticipationResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/grants", response_model=GrantApplicationListResponse)
def list_grants(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.GRANTS_READ))], tenant: _Tenant, db: _DB) -> GrantApplicationListResponse:
    try:
        return GrantApplicationListResponse(items=[_resp(item, GrantApplicationResponse) for item in service.list_grant_applications_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/grants", response_model=GrantApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_grant(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.GRANTS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> GrantApplicationResponse:
    try:
        body = _parse_payload(GrantApplicationCreateRequest, payload)
        return _resp(service.create_grant_application_service(db, tenant, actor, body), GrantApplicationResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/grants/{grant_id}", response_model=GrantApplicationResponse)
def get_grant(grant_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.GRANTS_READ))], tenant: _Tenant, db: _DB) -> GrantApplicationResponse:
    try:
        return _resp(service.get_grant_application_service(db, tenant, grant_id), GrantApplicationResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/grants/{grant_id}", response_model=GrantApplicationResponse)
def update_grant(grant_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.GRANTS_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> GrantApplicationResponse:
    try:
        body = _parse_payload(GrantApplicationUpdateRequest, payload)
        return _resp(service.update_grant_application_service(db, tenant, actor, grant_id, body), GrantApplicationResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/grant-deliverables", response_model=GrantDeliverableListResponse)
def list_grant_deliverables(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.GRANT_DELIVERABLES_READ))], tenant: _Tenant, db: _DB) -> GrantDeliverableListResponse:
    try:
        return GrantDeliverableListResponse(items=[_resp(item, GrantDeliverableResponse) for item in service.list_grant_deliverables_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/grant-deliverables", response_model=GrantDeliverableResponse, status_code=status.HTTP_201_CREATED)
def create_grant_deliverable(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.GRANT_DELIVERABLES_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> GrantDeliverableResponse:
    try:
        body = _parse_payload(GrantDeliverableCreateRequest, payload)
        return _resp(service.create_grant_deliverable_service(db, tenant, actor, body), GrantDeliverableResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/grant-deliverables/{deliverable_id}", response_model=GrantDeliverableResponse)
def update_grant_deliverable(deliverable_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.GRANT_DELIVERABLES_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> GrantDeliverableResponse:
    try:
        body = _parse_payload(GrantDeliverableUpdateRequest, payload)
        return _resp(service.update_grant_deliverable_service(db, tenant, actor, deliverable_id, body), GrantDeliverableResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/ethics", response_model=ResearchEthicsRequestListResponse)
def list_ethics(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.ETHICS_READ))], tenant: _Tenant, db: _DB) -> ResearchEthicsRequestListResponse:
    try:
        return ResearchEthicsRequestListResponse(items=[_resp(item, ResearchEthicsRequestResponse) for item in service.list_ethics_requests_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/ethics", response_model=ResearchEthicsRequestResponse, status_code=status.HTTP_201_CREATED)
def create_ethics(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.ETHICS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ResearchEthicsRequestResponse:
    try:
        body = _parse_payload(ResearchEthicsRequestCreateRequest, payload)
        return _resp(service.create_ethics_request_service(db, tenant, actor, body), ResearchEthicsRequestResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/ethics/{ethics_id}", response_model=ResearchEthicsRequestResponse)
def get_ethics(ethics_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.ETHICS_READ))], tenant: _Tenant, db: _DB) -> ResearchEthicsRequestResponse:
    try:
        return _resp(service.get_ethics_request_service(db, tenant, ethics_id), ResearchEthicsRequestResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/ethics/{ethics_id}", response_model=ResearchEthicsRequestResponse)
def update_ethics(ethics_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.ETHICS_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ResearchEthicsRequestResponse:
    try:
        body = _parse_payload(ResearchEthicsRequestUpdateRequest, payload)
        return _resp(service.update_ethics_request_service(db, tenant, actor, ethics_id, body), ResearchEthicsRequestResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/ethics-amendments", response_model=ResearchEthicsAmendmentListResponse)
def list_ethics_amendments(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.ETHICS_AMENDMENTS_READ))], tenant: _Tenant, db: _DB) -> ResearchEthicsAmendmentListResponse:
    try:
        return ResearchEthicsAmendmentListResponse(items=[_resp(item, ResearchEthicsAmendmentResponse) for item in service.list_ethics_amendments_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/ethics-amendments", response_model=ResearchEthicsAmendmentResponse, status_code=status.HTTP_201_CREATED)
def create_ethics_amendment(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.ETHICS_AMENDMENTS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ResearchEthicsAmendmentResponse:
    try:
        body = _parse_payload(ResearchEthicsAmendmentCreateRequest, payload)
        return _resp(service.create_ethics_amendment_service(db, tenant, actor, body), ResearchEthicsAmendmentResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/evidence", response_model=ResearchEvidenceListResponse)
def list_evidence(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_READ))], tenant: _Tenant, db: _DB) -> ResearchEvidenceListResponse:
    try:
        return ResearchEvidenceListResponse(items=[_resp(item, ResearchEvidenceResponse) for item in service.list_research_evidence_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/evidence", response_model=ResearchEvidenceResponse, status_code=status.HTTP_201_CREATED)
def create_evidence(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_ATTACH))] = None, tenant: _Tenant = None, db: _DB = None) -> ResearchEvidenceResponse:
    try:
        body = _parse_payload(ResearchEvidenceCreateRequest, payload)
        return _resp(service.attach_research_evidence_service(db, tenant, actor, body), ResearchEvidenceResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/audit", response_model=ResearchAuditEventListResponse)
def list_audit(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_READ))], tenant: _Tenant, db: _DB) -> ResearchAuditEventListResponse:
    try:
        return ResearchAuditEventListResponse(items=[_resp(item, ResearchAuditEventResponse) for item in service.list_research_audit_events_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.get("/bridges", response_model=ResearchBridgeListResponse)
def list_bridges(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.BRIDGES_READ))], tenant: _Tenant, db: _DB) -> ResearchBridgeListResponse:
    try:
        return ResearchBridgeListResponse(items=[_resp(item, ResearchBridgeResponse) for item in service.list_research_bridge_metadata_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/bridges", response_model=ResearchBridgeResponse, status_code=status.HTTP_201_CREATED)
def create_bridge(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.BRIDGES_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> ResearchBridgeResponse:
    try:
        body = _parse_payload(ResearchBridgeCreateRequest, payload)
        return _resp(service.create_research_bridge_metadata_service(db, tenant, actor, body), ResearchBridgeResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/bridges/summary", response_model=ResearchBridgeSummaryResponse)
def get_bridge_summary(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.BRIDGES_READ))], tenant: _Tenant, db: _DB) -> ResearchBridgeSummaryResponse:
    try:
        return ResearchBridgeSummaryResponse(
            tenant_id=tenant,
            bridge_counts=service.repository.get_research_bridge_summary(db, tenant),
            read_only_first=True,
            mutation_allowed=False,
            provider_sync_enabled=False,
            external_submission_enabled=False,
        )
    except Exception as exc:
        _handle(exc)