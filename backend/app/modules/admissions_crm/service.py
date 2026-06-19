"""Service layer for Admissions CRM Batch 1."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, validate_tenant_id_provided
from app.modules.admissions_crm import models, repository, schemas


_LEAD_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "lead_created": frozenset({"lead_qualified", "archived"}),
    "lead_qualified": frozenset({"applicant_created", "archived"}),
    "applicant_created": frozenset({"archived"}),
    "archived": frozenset(),
}
_APPLICATION_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "application_started": frozenset({"application_submitted", "archived"}),
    "application_submitted": frozenset({"archived"}),
    "archived": frozenset(),
}


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _validate_actor(actor_user_id: str | int | None) -> str:
    actor = str(actor_user_id or "").strip()
    if not actor:
        raise DomainValidationError("actor_user_id is required")
    return actor


def _validate_transition(current_status: str, new_status: str, transitions: dict[str, frozenset[str]]) -> None:
    if new_status == current_status:
        raise DomainValidationError("status transition must change current status")
    allowed = transitions.get(current_status)
    if allowed is None or new_status not in allowed:
        raise DomainValidationError(f"invalid_status_transition: {current_status} -> {new_status}")


def _base_response() -> dict[str, Any]:
    return {
        "module": models.MODULE_NAME,
        "contract_version": models.CONTRACT_VERSION,
        "runtime_mode": models.RUNTIME_MODE,
        "fake_metrics": False,
        "provider_live_enabled": False,
        "autonomous_decision_enabled": False,
        "hidden_score_present": False,
        "human_review_required": True,
    }


def _lead_record(item: models.Lead) -> schemas.LeadRecord:
    return schemas.LeadRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "lead_ref": item.lead_ref,
            "status": item.status,
            "full_name": item.full_name,
            "email": item.email,
            "phone": item.phone,
            "source_channel": item.source_channel,
            "metadata": dict(item.metadata_json or {}),
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
    )


def _applicant_record(item: models.Applicant) -> schemas.ApplicantRecord:
    return schemas.ApplicantRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "lead_id": item.lead_id,
            "applicant_ref": item.applicant_ref,
            "status": item.status,
            "full_name": item.full_name,
            "email": item.email,
            "metadata": dict(item.metadata_json or {}),
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
    )


def _application_record(item: models.Application) -> schemas.ApplicationRecord:
    return schemas.ApplicationRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "applicant_id": item.applicant_id,
            "application_ref": item.application_ref,
            "status": item.status,
            "program_code": item.program_code,
            "intake_term": item.intake_term,
            "metadata": dict(item.metadata_json or {}),
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
    )


def _emit_events(
    db: Session,
    tenant_id: int,
    actor: str,
    *,
    entity_type: str,
    entity_id: int,
    event_type: str,
    from_status: str | None,
    to_status: str | None,
    payload: dict[str, Any],
) -> None:
    repository.create_workflow_event(
        db,
        tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        actor_user_id=actor,
        payload_json=payload,
    )
    repository.create_audit_event(
        db,
        tenant_id,
        action=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor,
        metadata_json=payload,
    )


def create_lead(db: Session, tenant_id: int, actor_user_id: str, request: schemas.LeadCreateRequest) -> schemas.LeadItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    item = repository.create_lead(
        db,
        tenant_id,
        lead_ref=request.lead_ref,
        full_name=request.full_name,
        email=request.email,
        phone=request.phone,
        source_channel=request.source_channel,
        status="lead_created",
        metadata_json=request.metadata,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )
    repository.create_lead_status_history(
        db,
        tenant_id,
        lead_id=item.id,
        from_status=None,
        to_status="lead_created",
        changed_by_user_id=actor,
        note="lead created",
    )
    _emit_events(
        db,
        tenant_id,
        actor,
        entity_type="lead",
        entity_id=item.id,
        event_type="lead_created",
        from_status=None,
        to_status="lead_created",
        payload={"lead_ref": request.lead_ref},
    )
    _commit(db)
    return schemas.LeadItemResponse.model_validate({"tenant_id": tenant_id, "item": _lead_record(item)} | _base_response())


def list_leads(db: Session, tenant_id: int) -> schemas.LeadListResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    items = [_lead_record(item) for item in repository.list_leads(db, tenant_id)]
    return schemas.LeadListResponse.model_validate({"tenant_id": tenant_id, "items": items} | _base_response())


def get_lead(db: Session, tenant_id: int, lead_id: int) -> schemas.LeadItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    item = repository.get_lead(db, tenant_id, lead_id)
    if item is None:
        raise DomainValidationError(f"lead {lead_id} not found in tenant scope")
    return schemas.LeadItemResponse.model_validate({"tenant_id": tenant_id, "item": _lead_record(item)} | _base_response())


def qualify_lead(db: Session, tenant_id: int, lead_id: int, actor_user_id: str, request: schemas.LeadQualifyRequest) -> schemas.LeadItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = repository.get_lead(db, tenant_id, lead_id)
    if current is None:
        raise DomainValidationError(f"lead {lead_id} not found in tenant scope")
    _validate_transition(current.status, "lead_qualified", _LEAD_ALLOWED_TRANSITIONS)
    updated = repository.update_lead(db, tenant_id, lead_id, status="lead_qualified", updated_by_user_id=actor)
    repository.create_lead_status_history(
        db,
        tenant_id,
        lead_id=lead_id,
        from_status=current.status,
        to_status="lead_qualified",
        changed_by_user_id=actor,
        note=request.reason,
    )
    _emit_events(
        db,
        tenant_id,
        actor,
        entity_type="lead",
        entity_id=lead_id,
        event_type="lead_qualified",
        from_status=current.status,
        to_status="lead_qualified",
        payload={"reason": request.reason},
    )
    _commit(db)
    return schemas.LeadItemResponse.model_validate({"tenant_id": tenant_id, "item": _lead_record(updated)} | _base_response())


def create_applicant(db: Session, tenant_id: int, actor_user_id: str, request: schemas.ApplicantCreateRequest) -> schemas.ApplicantItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    lead = repository.get_lead(db, tenant_id, request.lead_id)
    if lead is None:
        raise DomainValidationError(f"lead {request.lead_id} not found in tenant scope")
    _validate_transition(lead.status, "applicant_created", _LEAD_ALLOWED_TRANSITIONS)
    repository.update_lead(db, tenant_id, lead.id, status="applicant_created", updated_by_user_id=actor)
    repository.create_lead_status_history(
        db,
        tenant_id,
        lead_id=lead.id,
        from_status=lead.status,
        to_status="applicant_created",
        changed_by_user_id=actor,
        note="converted to applicant",
    )
    item = repository.create_applicant(
        db,
        tenant_id,
        lead_id=request.lead_id,
        applicant_ref=request.applicant_ref,
        full_name=request.full_name,
        email=request.email,
        status="applicant_created",
        metadata_json=request.metadata,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )
    _emit_events(
        db,
        tenant_id,
        actor,
        entity_type="applicant",
        entity_id=item.id,
        event_type="applicant_created",
        from_status="lead_qualified",
        to_status="applicant_created",
        payload={"lead_id": request.lead_id, "applicant_ref": request.applicant_ref},
    )
    _commit(db)
    return schemas.ApplicantItemResponse.model_validate({"tenant_id": tenant_id, "item": _applicant_record(item)} | _base_response())


def list_applicants(db: Session, tenant_id: int) -> schemas.ApplicantListResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    items = [_applicant_record(item) for item in repository.list_applicants(db, tenant_id)]
    return schemas.ApplicantListResponse.model_validate({"tenant_id": tenant_id, "items": items} | _base_response())


def get_applicant(db: Session, tenant_id: int, applicant_id: int) -> schemas.ApplicantItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    item = repository.get_applicant(db, tenant_id, applicant_id)
    if item is None:
        raise DomainValidationError(f"applicant {applicant_id} not found in tenant scope")
    return schemas.ApplicantItemResponse.model_validate({"tenant_id": tenant_id, "item": _applicant_record(item)} | _base_response())


def create_application(db: Session, tenant_id: int, actor_user_id: str, request: schemas.ApplicationCreateRequest) -> schemas.ApplicationItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    if repository.get_applicant(db, tenant_id, request.applicant_id) is None:
        raise DomainValidationError(f"applicant {request.applicant_id} not found in tenant scope")
    item = repository.create_application(
        db,
        tenant_id,
        applicant_id=request.applicant_id,
        application_ref=request.application_ref,
        program_code=request.program_code,
        intake_term=request.intake_term,
        status="application_started",
        metadata_json=request.metadata,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )
    repository.create_application_status_history(
        db,
        tenant_id,
        application_id=item.id,
        from_status=None,
        to_status="application_started",
        changed_by_user_id=actor,
        note="application started",
    )
    _emit_events(
        db,
        tenant_id,
        actor,
        entity_type="application",
        entity_id=item.id,
        event_type="application_started",
        from_status=None,
        to_status="application_started",
        payload={"application_ref": request.application_ref},
    )
    _commit(db)
    return schemas.ApplicationItemResponse.model_validate({"tenant_id": tenant_id, "item": _application_record(item)} | _base_response())


def list_applications(db: Session, tenant_id: int) -> schemas.ApplicationListResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    items = [_application_record(item) for item in repository.list_applications(db, tenant_id)]
    return schemas.ApplicationListResponse.model_validate({"tenant_id": tenant_id, "items": items} | _base_response())


def get_application(db: Session, tenant_id: int, application_id: int) -> schemas.ApplicationItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    item = repository.get_application(db, tenant_id, application_id)
    if item is None:
        raise DomainValidationError(f"application {application_id} not found in tenant scope")
    return schemas.ApplicationItemResponse.model_validate({"tenant_id": tenant_id, "item": _application_record(item)} | _base_response())


def submit_application(
    db: Session,
    tenant_id: int,
    application_id: int,
    actor_user_id: str,
    request: schemas.ApplicationSubmitRequest,
) -> schemas.ApplicationItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = repository.get_application(db, tenant_id, application_id)
    if current is None:
        raise DomainValidationError(f"application {application_id} not found in tenant scope")
    _validate_transition(current.status, "application_submitted", _APPLICATION_ALLOWED_TRANSITIONS)
    updated = repository.update_application(db, tenant_id, application_id, status="application_submitted", updated_by_user_id=actor)
    repository.create_application_status_history(
        db,
        tenant_id,
        application_id=application_id,
        from_status=current.status,
        to_status="application_submitted",
        changed_by_user_id=actor,
        note=request.note,
    )
    _emit_events(
        db,
        tenant_id,
        actor,
        entity_type="application",
        entity_id=application_id,
        event_type="application_submitted",
        from_status=current.status,
        to_status="application_submitted",
        payload={"note": request.note},
    )
    _commit(db)
    return schemas.ApplicationItemResponse.model_validate({"tenant_id": tenant_id, "item": _application_record(updated)} | _base_response())
