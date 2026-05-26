"""Document / Decree / Correspondence service layer."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.document_decree_correspondence import models, permissions, repository, schemas


EXPECTED_ROUTE_COUNT = models.EXPECTED_ROUTE_COUNT
EXPECTED_TABLE_COUNT = models.EXPECTED_TABLE_COUNT
EXPECTED_PERMISSION_COUNT = models.EXPECTED_PERMISSION_COUNT

CANONICAL_MODULES = [
    "document_workflow",
    "document_workflow_os",
    "order_decree_registry",
    "incoming_outgoing_correspondence",
    "document_template_library",
    "rector_resolution_tracking_workflow",
    "committee_decision_registry",
    "rector_assignment_workflow",
    "audit",
    "archive_retention_management",
]

ROLE_NAMES = [
    "RECTOR_OVERSIGHT",
    "VICE_RECTOR_REVIEW",
    "CHANCELLERY_CONTROLLER",
    "EXECUTIVE_ASSISTANT",
    "LEGAL_REVIEWER",
    "DEPARTMENT_REVIEWER",
    "EXECUTION_COORDINATOR",
    "AUDIT_REVIEWER",
    "ARCHIVE_REVIEWER",
    "SIGNATURE_READINESS_REVIEWER",
    "DELIVERY_READINESS_REVIEWER",
    "COMMITTEE_SECRETARY",
    "READ_ONLY_VIEWER",
]

REQUIRED_LIMITATIONS = [
    "metadata_only_runtime",
    "evidence_metadata_only",
    "archive_readiness_only",
    "signature_readiness_only",
    "delivery_readiness_only",
    "human_review_required",
    "no_fake_documents",
    "no_fake_decrees",
    "no_fake_signatures",
    "no_fake_delivery_confirmations",
    "no_fake_archive_legal_record",
    "no_automatic_rector_decision",
    "no_automatic_decree_approval",
    "no_automatic_document_signing",
    "no_external_submission",
    "no_external_delivery_execution",
    "no_official_legal_effect",
    "no_hidden_score",
]

ROUTE_PATHS = [
    "/overview",
    "/readiness",
    "/limitations",
    "/safety-boundaries",
    "/dashboard",
    "/documents",
    "/document-intake",
    "/document-routing",
    "/rector-resolutions",
    "/decrees",
    "/decree-drafts",
    "/incoming-correspondence",
    "/outgoing-correspondence",
    "/templates",
    "/committee-decisions",
    "/assignments",
    "/execution-control",
    "/sla-deadlines",
    "/evidence",
    "/attachments",
    "/audit-events",
    "/archive",
    "/signature-readiness",
    "/delivery-readiness",
    "/bridges/executive",
    "/bridges/assignments",
    "/health",
    "/roles",
    "/permissions",
    "/metadata-contract",
    "/document-intake",
    "/document-registration",
    "/document-routing",
    "/rector-resolutions/metadata",
    "/decrees/metadata",
    "/decree-drafts",
    "/incoming-correspondence",
    "/outgoing-correspondence",
    "/templates/metadata",
    "/committee-decisions/bridge",
    "/assignments/bridge",
    "/execution-control/metadata",
    "/sla-deadlines",
    "/evidence",
    "/attachments/metadata",
    "/audit-events",
    "/archive/readiness",
    "/retention/metadata",
    "/signature-readiness/evidence",
    "/delivery-readiness/evidence",
    "/bridges/executive",
    "/bridges/assignments",
    "/limitations",
]


def _now() -> datetime:
    return datetime.now(UTC)


def _validate_tenant(tenant_id: int) -> int:
    return repository.verify_tenant_scope(tenant_id)


def _validate_actor(actor_user_id: str | int | None) -> str:
    actor = str(actor_user_id or "").strip()
    if not actor:
        raise DomainValidationError("actor_user_id is required")
    return actor


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _merge_limitations(values: list[str] | None) -> list[str]:
    merged = list(values or [])
    for limitation in REQUIRED_LIMITATIONS:
        if limitation not in merged:
            merged.append(limitation)
    return merged


def _base_response_kwargs(tenant_id: int, limitations: list[str] | None = None) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "module": models.MODULE_NAME,
        "contract_version": models.CONTRACT_VERSION,
        "runtime_mode": models.RUNTIME_MODE,
        "data_source": models.DATA_SOURCE,
        "fake_documents": False,
        "fake_decrees": False,
        "fake_signatures": False,
        "fake_delivery_confirmations": False,
        "fake_archive_legal_record": False,
        "official_legal_effect": False,
        "external_submission_enabled": False,
        "automatic_rector_decision_enabled": False,
        "automatic_decree_approval_enabled": False,
        "automatic_document_signing_enabled": False,
        "hidden_score_present": False,
        "human_review_required": True,
        "incomplete_data": True,
        "limitations": _merge_limitations(limitations),
    }


def _metadata_kwargs(request: schemas.DdcMetadataCreateRequest, actor: str, *, status_default: str = "DRAFT", extra: dict[str, Any] | None = None) -> dict[str, Any]:
    data = request.model_dump(exclude_none=True)
    data["metadata_json"] = data.pop("metadata", {})
    data["limitations_json"] = _merge_limitations(data.pop("limitations", None))
    data.setdefault("status", status_default)
    data["human_review_required"] = True
    data["fake_documents"] = False
    data["fake_decrees"] = False
    data["fake_signatures"] = False
    data["fake_delivery_confirmations"] = False
    data["fake_archive_legal_record"] = False
    data["official_legal_effect"] = False
    data["external_submission_enabled"] = False
    data["automatic_rector_decision_enabled"] = False
    data["automatic_decree_approval_enabled"] = False
    data["automatic_document_signing_enabled"] = False
    data["hidden_score_present"] = False
    data["incomplete_data"] = True
    data["created_by"] = actor
    data["updated_by"] = actor
    return data | (extra or {})


def _evidence_kwargs(request: schemas.DdcEvidenceItemCreateRequest, actor: str) -> dict[str, Any]:
    return {
        "status": "RECORDED",
        "evidence_type": request.evidence_type,
        "title": request.title,
        "reference_uri": request.reference_uri,
        "source_module": request.source_module,
        "source_record_id": request.source_record_id,
        "metadata_json": dict(request.metadata),
        "limitations_json": _merge_limitations(request.limitations),
        "human_review_required": True,
        "fake_documents": False,
        "fake_decrees": False,
        "fake_signatures": False,
        "fake_delivery_confirmations": False,
        "fake_archive_legal_record": False,
        "official_legal_effect": False,
        "external_submission_enabled": False,
        "automatic_rector_decision_enabled": False,
        "automatic_decree_approval_enabled": False,
        "automatic_document_signing_enabled": False,
        "hidden_score_present": False,
        "incomplete_data": True,
        "created_by": actor,
    }


def _audit_kwargs(request: schemas.DdcAuditEventCreateRequest, actor: str) -> dict[str, Any]:
    return {
        "status": "RECORDED",
        "entity_type": request.entity_type,
        "entity_id": request.entity_id,
        "action": request.action,
        "actor_user_id": actor,
        "before_json": dict(request.before),
        "after_json": dict(request.after),
        "metadata_json": dict(request.metadata),
        "human_review_required": True,
        "hidden_score_present": False,
    }


def _record_from_model(item) -> schemas.DdcMetadataRecord:
    return schemas.DdcMetadataRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "status": getattr(item, "status", "ACTIVE"),
            "reference_key": getattr(item, "reference_key", None),
            "title": getattr(item, "title", None),
            "source_module": getattr(item, "source_module", None),
            "source_record_id": getattr(item, "source_record_id", None),
            "metadata": dict(getattr(item, "metadata_json", {}) or {}),
            "limitations": list(getattr(item, "limitations_json", []) or []),
            "created_at": getattr(item, "created_at", None),
            "updated_at": getattr(item, "updated_at", None),
        }
    )


def _audit_record_from_model(item) -> schemas.DdcAuditEventRecord:
    return schemas.DdcAuditEventRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "status": item.status,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "action": item.action,
            "actor_user_id": item.actor_user_id,
            "before": dict(item.before_json or {}),
            "after": dict(item.after_json or {}),
            "metadata": dict(item.metadata_json or {}),
            "created_at": item.created_at,
        }
    )


def _evidence_record_from_model(item) -> schemas.DdcEvidenceItemRecord:
    return schemas.DdcEvidenceItemRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "status": item.status,
            "evidence_type": item.evidence_type,
            "title": item.title,
            "reference_uri": item.reference_uri,
            "source_module": item.source_module,
            "source_record_id": item.source_record_id,
            "metadata": dict(item.metadata_json or {}),
            "limitations": list(item.limitations_json or []),
            "created_at": item.created_at,
        }
    )


def _collection_response(schema_cls, tenant_id: int, items):
    return schema_cls.model_validate(_base_response_kwargs(tenant_id) | {"records": [_record_from_model(item) for item in items]})


def _audit_response(tenant_id: int, items) -> schemas.DdcAuditEventResponse:
    return schemas.DdcAuditEventResponse.model_validate(_base_response_kwargs(tenant_id) | {"records": [_audit_record_from_model(item) for item in items]})


def _evidence_response(tenant_id: int, items) -> schemas.DdcEvidenceItemResponse:
    return schemas.DdcEvidenceItemResponse.model_validate(_base_response_kwargs(tenant_id) | {"records": [_evidence_record_from_model(item) for item in items]})


def get_overview(db: Session, tenant_id: int) -> schemas.DdcOverviewResponse:
    del db
    tenant_id = _validate_tenant(tenant_id)
    return schemas.DdcOverviewResponse.model_validate(
        _base_response_kwargs(tenant_id)
        | {
            "target_level": models.TARGET_LEVEL,
            "foundation_status": models.FOUNDATION_STATUS,
            "selected_vertical": models.PRODUCT_VERTICAL,
            "canonical_modules": CANONICAL_MODULES,
            "table_count": models.EXPECTED_TABLE_COUNT,
            "route_count": models.EXPECTED_ROUTE_COUNT,
            "permission_count": models.EXPECTED_PERMISSION_COUNT,
        }
    )


def get_readiness(db: Session, tenant_id: int) -> schemas.DdcReadinessResponse:
    tenant_id = _validate_tenant(tenant_id)
    inputs = repository.get_dashboard_inputs(db, tenant_id)
    present = [key for key, value in inputs.items() if value > 0]
    required = ["documents", "decrees", "correspondence", "assignments"]
    missing = [key for key in required if key not in present]
    score = max(0, 100 - (len(missing) * 25))
    status = "READY_FOR_REVIEW" if not missing else "INCOMPLETE_DATA"
    return schemas.DdcReadinessResponse.model_validate(
        _base_response_kwargs(tenant_id)
        | {
            "readiness_status": status,
            "readiness_score": score,
            "required_evidence": required,
            "present_evidence": present,
            "missing_evidence": missing,
        }
    )


def get_limitations(db: Session, tenant_id: int) -> schemas.DdcLimitationsResponse:
    return _collection_response(schemas.DdcLimitationsResponse, _validate_tenant(tenant_id), repository.list_records(db, "limitations", tenant_id))


def get_safety_boundaries(db: Session, tenant_id: int) -> schemas.DdcLimitationsResponse:
    return get_limitations(db, tenant_id)


def get_dashboard(db: Session, tenant_id: int) -> schemas.DdcDashboardResponse:
    tenant_id = _validate_tenant(tenant_id)
    return schemas.DdcDashboardResponse.model_validate(_base_response_kwargs(tenant_id) | {"summary": repository.get_dashboard_inputs(db, tenant_id)})


def get_documents(db: Session, tenant_id: int) -> schemas.DdcDocumentRegistrationResponse:
    items = repository.list_records(db, "document_workflow", _validate_tenant(tenant_id))
    return _collection_response(schemas.DdcDocumentRegistrationResponse, tenant_id, items)


def get_document_intake(db: Session, tenant_id: int) -> schemas.DdcDocumentIntakeResponse:
    return _collection_response(schemas.DdcDocumentIntakeResponse, _validate_tenant(tenant_id), repository.list_records(db, "document_intake", tenant_id))


def get_document_routing(db: Session, tenant_id: int) -> schemas.DdcDocumentRoutingResponse:
    return _collection_response(schemas.DdcDocumentRoutingResponse, _validate_tenant(tenant_id), repository.list_records(db, "document_routing", tenant_id))


def get_rector_resolutions(db: Session, tenant_id: int) -> schemas.DdcRectorResolutionResponse:
    return _collection_response(schemas.DdcRectorResolutionResponse, _validate_tenant(tenant_id), repository.list_records(db, "rector_resolutions", tenant_id))


def get_decrees(db: Session, tenant_id: int) -> schemas.DdcDecreeRegistryResponse:
    return _collection_response(schemas.DdcDecreeRegistryResponse, _validate_tenant(tenant_id), repository.list_records(db, "decrees", tenant_id))


def get_decree_drafts(db: Session, tenant_id: int) -> schemas.DdcDecreeDraftResponse:
    return _collection_response(schemas.DdcDecreeDraftResponse, _validate_tenant(tenant_id), repository.list_records(db, "decree_drafts", tenant_id))


def get_incoming_correspondence(db: Session, tenant_id: int) -> schemas.DdcIncomingCorrespondenceResponse:
    return _collection_response(schemas.DdcIncomingCorrespondenceResponse, _validate_tenant(tenant_id), repository.list_records(db, "incoming_correspondence", tenant_id))


def get_outgoing_correspondence(db: Session, tenant_id: int) -> schemas.DdcOutgoingCorrespondenceResponse:
    return _collection_response(schemas.DdcOutgoingCorrespondenceResponse, _validate_tenant(tenant_id), repository.list_records(db, "outgoing_correspondence", tenant_id))


def get_templates(db: Session, tenant_id: int) -> schemas.DdcTemplateMetadataResponse:
    return _collection_response(schemas.DdcTemplateMetadataResponse, _validate_tenant(tenant_id), repository.list_records(db, "templates", tenant_id))


def get_committee_decisions(db: Session, tenant_id: int) -> schemas.DdcCommitteeDecisionBridgeResponse:
    return _collection_response(schemas.DdcCommitteeDecisionBridgeResponse, _validate_tenant(tenant_id), repository.list_records(db, "committee_decisions", tenant_id))


def get_assignments(db: Session, tenant_id: int) -> schemas.DdcAssignmentBridgeResponse:
    return _collection_response(schemas.DdcAssignmentBridgeResponse, _validate_tenant(tenant_id), repository.list_records(db, "assignments", tenant_id))


def get_execution_control(db: Session, tenant_id: int) -> schemas.DdcExecutionControlResponse:
    return _collection_response(schemas.DdcExecutionControlResponse, _validate_tenant(tenant_id), repository.list_records(db, "execution_control", tenant_id))


def get_sla_deadlines(db: Session, tenant_id: int) -> schemas.DdcSlaDeadlineResponse:
    return _collection_response(schemas.DdcSlaDeadlineResponse, _validate_tenant(tenant_id), repository.list_records(db, "sla_deadlines", tenant_id))


def get_evidence(db: Session, tenant_id: int) -> schemas.DdcEvidenceItemResponse:
    return _evidence_response(_validate_tenant(tenant_id), repository.list_evidence_items(db, tenant_id))


def get_attachments(db: Session, tenant_id: int) -> schemas.DdcAttachmentMetadataResponse:
    return _collection_response(schemas.DdcAttachmentMetadataResponse, _validate_tenant(tenant_id), repository.list_records(db, "attachments", tenant_id))


def get_audit_events(db: Session, tenant_id: int) -> schemas.DdcAuditEventResponse:
    return _audit_response(_validate_tenant(tenant_id), repository.list_audit_events(db, tenant_id))


def get_archive(db: Session, tenant_id: int) -> schemas.DdcArchiveReadinessResponse:
    return _collection_response(schemas.DdcArchiveReadinessResponse, _validate_tenant(tenant_id), repository.list_records(db, "archive", tenant_id))


def get_signature_readiness(db: Session, tenant_id: int) -> schemas.DdcSignatureReadinessResponse:
    return _collection_response(schemas.DdcSignatureReadinessResponse, _validate_tenant(tenant_id), repository.list_records(db, "signature_readiness", tenant_id))


def get_delivery_readiness(db: Session, tenant_id: int) -> schemas.DdcDeliveryReadinessResponse:
    return _collection_response(schemas.DdcDeliveryReadinessResponse, _validate_tenant(tenant_id), repository.list_records(db, "delivery_readiness", tenant_id))


def get_bridge_executive(db: Session, tenant_id: int) -> schemas.DdcBridgeResponse:
    return _collection_response(schemas.DdcBridgeResponse, _validate_tenant(tenant_id), repository.get_bridge_inputs(db, tenant_id))


def get_bridge_assignments(db: Session, tenant_id: int) -> schemas.DdcBridgeResponse:
    return _collection_response(schemas.DdcBridgeResponse, _validate_tenant(tenant_id), repository.list_records(db, "bridges", tenant_id))


def get_health(db: Session, tenant_id: int) -> dict[str, Any]:
    tenant_id = _validate_tenant(tenant_id)
    return _base_response_kwargs(tenant_id) | {
        "status": "OK",
        "table_count": EXPECTED_TABLE_COUNT,
        "route_count": EXPECTED_ROUTE_COUNT,
        "permission_count": EXPECTED_PERMISSION_COUNT,
        "generated_at": _now().isoformat(),
    }


def get_roles(db: Session, tenant_id: int) -> dict[str, Any]:
    del db
    return _base_response_kwargs(_validate_tenant(tenant_id)) | {"roles": ROLE_NAMES}


def get_permissions(db: Session, tenant_id: int) -> dict[str, Any]:
    del db
    return _base_response_kwargs(_validate_tenant(tenant_id)) | {"permissions": permissions.DOCUMENT_DECREE_CORRESPONDENCE_PERMISSIONS}


def get_metadata_contract(db: Session, tenant_id: int) -> schemas.DdcMetadataContractResponse:
    del db
    tenant_id = _validate_tenant(tenant_id)
    return schemas.DdcMetadataContractResponse.model_validate(
        _base_response_kwargs(tenant_id)
        | {
            "route_count": EXPECTED_ROUTE_COUNT,
            "table_count": EXPECTED_TABLE_COUNT,
            "permission_count": EXPECTED_PERMISSION_COUNT,
            "route_paths": ROUTE_PATHS,
            "permissions": permissions.DOCUMENT_DECREE_CORRESPONDENCE_PERMISSIONS,
            "canonical_modules": CANONICAL_MODULES,
        }
    )


def _create_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest, model_key: str, *, status_default: str = "DRAFT", extra: dict[str, Any] | None = None) -> dict[str, Any]:
    tenant_id = _validate_tenant(tenant_id)
    actor = _validate_actor(actor)
    item = repository.create_record(db, model_key, tenant_id, **_metadata_kwargs(request, actor, status_default=status_default, extra=extra))
    _commit(db)
    return _base_response_kwargs(tenant_id) | {"record": _record_from_model(item).model_dump()}


def create_document_intake_record(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "document_intake")


def create_document_registration_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "document_registration")


def create_document_routing_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "document_routing")


def create_rector_resolution_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "rector_resolutions")


def create_decree_registry_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "decrees")


def create_decree_draft_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "decree_drafts")


def create_incoming_correspondence_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "incoming_correspondence")


def create_outgoing_correspondence_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "outgoing_correspondence")


def create_template_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "templates")


def create_committee_decision_bridge_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "committee_decisions", extra={"metadata_json": dict(request.metadata) | {"bridge_mode": "metadata_only"}})


def create_assignment_bridge_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "assignments", extra={"metadata_json": dict(request.metadata) | {"bridge_mode": "metadata_only"}})


def create_execution_control_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "execution_control")


def create_sla_deadline_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "sla_deadlines")


def create_evidence_item(db: Session, tenant_id: int, actor: str, request: schemas.DdcEvidenceItemCreateRequest) -> dict[str, Any]:
    tenant_id = _validate_tenant(tenant_id)
    actor = _validate_actor(actor)
    item = repository.create_evidence_item(db, tenant_id, **_evidence_kwargs(request, actor))
    _commit(db)
    return _base_response_kwargs(tenant_id) | {"record": _evidence_record_from_model(item).model_dump()}


def create_attachment_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "attachments")


def create_audit_event(db: Session, tenant_id: int, actor: str, request: schemas.DdcAuditEventCreateRequest) -> dict[str, Any]:
    tenant_id = _validate_tenant(tenant_id)
    actor = _validate_actor(actor)
    item = repository.create_audit_event(db, tenant_id, **_audit_kwargs(request, actor))
    _commit(db)
    return _base_response_kwargs(tenant_id) | {"record": _audit_record_from_model(item).model_dump()}


def create_archive_readiness_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "archive")


def create_retention_metadata(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "retention")


def create_signature_readiness_evidence(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "signature_readiness")


def create_delivery_readiness_evidence(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "delivery_readiness")


def create_bridge_record(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "bridges", extra={"metadata_json": dict(request.metadata) | {"read_only_first": True, "mutation_allowed": False}})


def create_limitation_record(db: Session, tenant_id: int, actor: str, request: schemas.DdcMetadataCreateRequest) -> dict[str, Any]:
    return _create_metadata(db, tenant_id, actor, request, "limitations", status_default="ACTIVE")
