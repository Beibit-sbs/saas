"""FastAPI router for Document / Decree / Correspondence runtime."""

from __future__ import annotations

from typing import Annotated, Any, Callable

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.modules.document_decree_correspondence import permissions, schemas, service
from app.modules.document_decree_correspondence.dependencies import get_document_decree_correspondence_db, require_document_decree_correspondence_tenant
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/document-decree-correspondence", tags=["document-decree-correspondence"])

_Tenant = Annotated[int, Depends(require_document_decree_correspondence_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_document_decree_correspondence_db)]


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _handle(exc: Exception) -> None:
    if isinstance(exc, TenantResourceNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, (DomainValidationError, ValueError)):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


def _register_get(path: str, permission: str, handler: Callable[[Session, int], Any], response_model) -> None:
    def endpoint(
        actor: str = Depends(get_actor),
        permitted: None = Depends(permission_dependency(permission)),
        tenant: int = Depends(require_document_decree_correspondence_tenant),
        db: Session = Depends(get_document_decree_correspondence_db),
    ):
        try:
            del actor, permitted
            return handler(db, tenant)
        except Exception as exc:
            _handle(exc)

    endpoint.__name__ = f"get_{path.strip('/').replace('/', '_').replace('-', '_') or 'root'}"
    router.add_api_route(path, endpoint, methods=["GET"], response_model=response_model, responses={400: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}})


def _register_post(path: str, permission: str, handler: Callable[[Session, int, str, Any], Any], request_model) -> None:
    def endpoint(
        payload: dict[str, Any] = Body(...),
        actor: str = Depends(get_actor),
        permitted: None = Depends(permission_dependency(permission)),
        tenant: int = Depends(require_document_decree_correspondence_tenant),
        db: Session = Depends(get_document_decree_correspondence_db),
    ):
        try:
            del permitted
            body = _parse_payload(request_model, payload)
            return handler(db, tenant, actor, body)
        except Exception as exc:
            _handle(exc)

    endpoint.__name__ = f"post_{path.strip('/').replace('/', '_').replace('-', '_')}"
    router.add_api_route(path, endpoint, methods=["POST"], response_model=dict[str, Any], status_code=201, responses={400: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}})


_register_get("/overview", permissions.OVERVIEW_READ, service.get_overview, schemas.DdcOverviewResponse)
_register_get("/readiness", permissions.READINESS_READ, service.get_readiness, schemas.DdcReadinessResponse)
_register_get("/limitations", permissions.LIMITATIONS_READ, service.get_limitations, schemas.DdcLimitationsResponse)
_register_get("/safety-boundaries", permissions.LIMITATIONS_READ, service.get_safety_boundaries, schemas.DdcLimitationsResponse)
_register_get("/dashboard", permissions.DASHBOARD_READ, service.get_dashboard, schemas.DdcDashboardResponse)
_register_get("/documents", permissions.DOCUMENTS_READ, service.get_documents, schemas.DdcDocumentRegistrationResponse)
_register_get("/document-intake", permissions.DOCUMENT_INTAKE_READ, service.get_document_intake, schemas.DdcDocumentIntakeResponse)
_register_get("/document-routing", permissions.DOCUMENT_ROUTING_READ, service.get_document_routing, schemas.DdcDocumentRoutingResponse)
_register_get("/rector-resolutions", permissions.RECTOR_RESOLUTIONS_READ, service.get_rector_resolutions, schemas.DdcRectorResolutionResponse)
_register_get("/decrees", permissions.DECREES_READ, service.get_decrees, schemas.DdcDecreeRegistryResponse)
_register_get("/decree-drafts", permissions.DECREE_DRAFTS_READ, service.get_decree_drafts, schemas.DdcDecreeDraftResponse)
_register_get("/incoming-correspondence", permissions.INCOMING_CORRESPONDENCE_READ, service.get_incoming_correspondence, schemas.DdcIncomingCorrespondenceResponse)
_register_get("/outgoing-correspondence", permissions.OUTGOING_CORRESPONDENCE_READ, service.get_outgoing_correspondence, schemas.DdcOutgoingCorrespondenceResponse)
_register_get("/templates", permissions.TEMPLATES_READ, service.get_templates, schemas.DdcTemplateMetadataResponse)
_register_get("/committee-decisions", permissions.COMMITTEE_DECISIONS_READ, service.get_committee_decisions, schemas.DdcCommitteeDecisionBridgeResponse)
_register_get("/assignments", permissions.ASSIGNMENTS_READ, service.get_assignments, schemas.DdcAssignmentBridgeResponse)
_register_get("/execution-control", permissions.EXECUTION_CONTROL_READ, service.get_execution_control, schemas.DdcExecutionControlResponse)
_register_get("/sla-deadlines", permissions.SLA_DEADLINES_READ, service.get_sla_deadlines, schemas.DdcSlaDeadlineResponse)
_register_get("/evidence", permissions.EVIDENCE_READ, service.get_evidence, schemas.DdcEvidenceItemResponse)
_register_get("/attachments", permissions.ATTACHMENTS_READ, service.get_attachments, schemas.DdcAttachmentMetadataResponse)
_register_get("/audit-events", permissions.AUDIT_READ, service.get_audit_events, schemas.DdcAuditEventResponse)
_register_get("/archive", permissions.ARCHIVE_READ, service.get_archive, schemas.DdcArchiveReadinessResponse)
_register_get("/signature-readiness", permissions.SIGNATURE_READINESS_READ, service.get_signature_readiness, schemas.DdcSignatureReadinessResponse)
_register_get("/delivery-readiness", permissions.DELIVERY_READINESS_READ, service.get_delivery_readiness, schemas.DdcDeliveryReadinessResponse)
_register_get("/bridges/executive", permissions.BRIDGES_EXECUTIVE_READ, service.get_bridge_executive, schemas.DdcBridgeResponse)
_register_get("/bridges/assignments", permissions.BRIDGES_ASSIGNMENTS_READ, service.get_bridge_assignments, schemas.DdcBridgeResponse)
_register_get("/health", permissions.OVERVIEW_READ, service.get_health, dict[str, Any])
_register_get("/roles", permissions.ROLES_READ, service.get_roles, dict[str, Any])
_register_get("/permissions", permissions.METADATA_READ, service.get_permissions, dict[str, Any])
_register_get("/metadata-contract", permissions.METADATA_READ, service.get_metadata_contract, schemas.DdcMetadataContractResponse)

_register_post("/document-intake", permissions.DOCUMENT_INTAKE_MANAGE, service.create_document_intake_record, schemas.DdcMetadataCreateRequest)
_register_post("/document-registration", permissions.DOCUMENT_REGISTRATION_MANAGE, service.create_document_registration_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/document-routing", permissions.DOCUMENT_ROUTING_MANAGE, service.create_document_routing_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/rector-resolutions/metadata", permissions.RECTOR_RESOLUTIONS_METADATA, service.create_rector_resolution_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/decrees/metadata", permissions.DECREES_METADATA, service.create_decree_registry_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/decree-drafts", permissions.DECREE_DRAFTS_MANAGE, service.create_decree_draft_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/incoming-correspondence", permissions.INCOMING_CORRESPONDENCE_MANAGE, service.create_incoming_correspondence_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/outgoing-correspondence", permissions.OUTGOING_CORRESPONDENCE_MANAGE, service.create_outgoing_correspondence_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/templates/metadata", permissions.TEMPLATES_METADATA, service.create_template_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/committee-decisions/bridge", permissions.COMMITTEE_DECISIONS_BRIDGE, service.create_committee_decision_bridge_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/assignments/bridge", permissions.ASSIGNMENTS_BRIDGE, service.create_assignment_bridge_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/execution-control/metadata", permissions.EXECUTION_CONTROL_METADATA, service.create_execution_control_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/sla-deadlines", permissions.SLA_DEADLINES_METADATA, service.create_sla_deadline_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/evidence", permissions.EVIDENCE_WRITE, service.create_evidence_item, schemas.DdcEvidenceItemCreateRequest)
_register_post("/attachments/metadata", permissions.ATTACHMENTS_METADATA, service.create_attachment_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/audit-events", permissions.AUDIT_WRITE, service.create_audit_event, schemas.DdcAuditEventCreateRequest)
_register_post("/archive/readiness", permissions.ARCHIVE_READINESS, service.create_archive_readiness_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/retention/metadata", permissions.RETENTION_METADATA, service.create_retention_metadata, schemas.DdcMetadataCreateRequest)
_register_post("/signature-readiness/evidence", permissions.SIGNATURE_READINESS_EVIDENCE, service.create_signature_readiness_evidence, schemas.DdcMetadataCreateRequest)
_register_post("/delivery-readiness/evidence", permissions.DELIVERY_READINESS_EVIDENCE, service.create_delivery_readiness_evidence, schemas.DdcMetadataCreateRequest)
_register_post("/bridges/executive", permissions.BRIDGES_EXECUTIVE_WRITE, service.create_bridge_record, schemas.DdcMetadataCreateRequest)
_register_post("/bridges/assignments", permissions.BRIDGES_ASSIGNMENTS_WRITE, service.create_bridge_record, schemas.DdcMetadataCreateRequest)
_register_post("/limitations", permissions.LIMITATIONS_READ, service.create_limitation_record, schemas.DdcMetadataCreateRequest)
