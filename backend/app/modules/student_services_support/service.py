"""Service layer for Student Services / Welfare / Support."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, validate_tenant_id_provided
from app.modules.student_services_support import models, repository, schemas


_REQUEST_ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"submitted", "archived"}),
    "submitted": frozenset({"triaged", "archived"}),
    "triaged": frozenset({"assigned", "archived"}),
    "assigned": frozenset({"in_progress", "waiting_student_response", "escalated", "archived"}),
    "in_progress": frozenset({"waiting_student_response", "escalated", "resolved", "archived"}),
    "waiting_student_response": frozenset({"in_progress", "resolved", "archived"}),
    "escalated": frozenset({"in_progress", "resolved", "archived"}),
    "resolved": frozenset({"closed", "archived"}),
    "closed": frozenset({"archived"}),
    "archived": frozenset(),
}

_CASE_OPEN_STATUSES = frozenset({"open", "under_review", "action_plan_draft", "action_plan_review", "follow_up", "escalated"})
_REQUEST_OPEN_STATUSES = frozenset({"draft", "submitted", "triaged", "assigned", "in_progress", "waiting_student_response", "escalated"})
_FINANCE_HARDSHIP_SOURCE_FLOW = "student_finance_receivables_handoff"
_MISSING_EVIDENCE_READINESS_STATUSES = frozenset({"blocked_missing_required_evidence", "insufficient_evidence"})


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


def _validate_transition(current_status: str, new_status: str) -> None:
    if new_status == current_status:
        raise DomainValidationError("status transition must change current status")
    allowed = _REQUEST_ALLOWED_TRANSITIONS.get(current_status)
    if allowed is None or new_status not in allowed:
        raise DomainValidationError(f"invalid_request_status_transition: {current_status} -> {new_status}")


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


def _request_record(item: models.StudentServiceRequest) -> schemas.ServiceRequestRecord:
    return schemas.ServiceRequestRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "request_type": item.request_type,
            "status": item.status,
            "support_priority": item.support_priority,
            "student_id": item.student_id,
            "assigned_to_user_id": item.assigned_to_user_id,
            "subject": item.subject,
            "description": item.description,
            "metadata": dict(item.metadata_json or {}),
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
    )


def _case_record(item: models.StudentSupportCase) -> schemas.SupportCaseRecord:
    return schemas.SupportCaseRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "case_type": item.case_type,
            "status": item.status,
            "request_id": item.request_id,
            "assigned_to_user_id": item.assigned_to_user_id,
            "title": item.title,
            "metadata": dict(item.metadata_json or {}),
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
    )


def _readiness_from_model(item, *, status_value: str) -> schemas.ReadinessRecord:
    return schemas.ReadinessRecord.model_validate(
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "request_id": item.request_id,
            "status": item.status,
            "readiness_status": status_value,
            "missing_evidence": list(item.missing_evidence_json or []),
            "recommended_next_step": item.recommended_next_step,
        }
    )


def _evaluate_readiness(evidence_refs: list[str]) -> tuple[str, list[str], str]:
    unique_evidence = [ref for ref in {str(v).strip() for v in evidence_refs if str(v).strip()}]
    if len(unique_evidence) >= 2:
        return "ready_for_human_review", [], "queue_human_review"
    if len(unique_evidence) == 1:
        return "needs_follow_up", ["supporting_document"], "collect_supporting_document"
    return "blocked_missing_required_evidence", ["student_statement", "supporting_document"], "collect_minimum_evidence"


def _emit_request_event(db: Session, tenant_id: int, request_id: int, event_type: str, actor: str, payload: dict[str, Any]) -> None:
    repository.create_service_request_event(
        db,
        tenant_id,
        request_id=request_id,
        event_type=event_type,
        actor_user_id=actor,
        payload_json=payload,
    )


def _emit_case_event(db: Session, tenant_id: int, case_id: int, event_type: str, actor: str, payload: dict[str, Any]) -> None:
    repository.create_support_case_event(
        db,
        tenant_id,
        case_id=case_id,
        event_type=event_type,
        actor_user_id=actor,
        payload_json=payload,
    )


def create_service_request(db: Session, tenant_id: int, actor_user_id: str, request: schemas.ServiceRequestCreateRequest) -> schemas.ServiceRequestItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    item = repository.create_service_request(
        db,
        tenant_id,
        request_type=request.request_type,
        status="submitted",
        support_priority=request.support_priority,
        student_id=request.student_id,
        subject=request.subject,
        description=request.description,
        metadata_json=request.metadata,
        limitations_json=[],
        human_review_required=True,
        fake_metrics=False,
        provider_live_enabled=False,
        autonomous_decision_enabled=False,
        hidden_score_present=False,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )
    _emit_request_event(
        db,
        tenant_id,
        item.id,
        "student_service.request.created",
        actor,
        {"request_type": request.request_type, "student_id": request.student_id},
    )
    _commit(db)
    return schemas.ServiceRequestItemResponse.model_validate({"tenant_id": tenant_id, "item": _request_record(item)} | _base_response())


def list_service_requests(db: Session, tenant_id: int) -> schemas.ServiceRequestListResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    items = [_request_record(item) for item in repository.list_service_requests(db, tenant_id)]
    return schemas.ServiceRequestListResponse.model_validate({"tenant_id": tenant_id, "items": items} | _base_response())


def get_service_request(db: Session, tenant_id: int, request_id: int) -> schemas.ServiceRequestItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    item = repository.get_service_request(db, tenant_id, request_id)
    if item is None:
        raise DomainValidationError(f"service_request {request_id} not found in tenant scope")
    return schemas.ServiceRequestItemResponse.model_validate({"tenant_id": tenant_id, "item": _request_record(item)} | _base_response())


def assign_service_request(db: Session, tenant_id: int, request_id: int, actor_user_id: str, request: schemas.ServiceRequestAssignRequest) -> schemas.ServiceRequestItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = repository.get_service_request(db, tenant_id, request_id)
    if current is None:
        raise DomainValidationError(f"service_request {request_id} not found in tenant scope")
    if current.status not in {"triaged", "assigned", "in_progress", "waiting_student_response", "escalated"}:
        raise DomainValidationError("request must be triaged before assignment")
    updated = repository.update_service_request(
        db,
        tenant_id,
        request_id,
        assigned_to_user_id=request.assigned_to_user_id,
        status="assigned",
        updated_by_user_id=actor,
    )
    _emit_request_event(
        db,
        tenant_id,
        request_id,
        "student_service.request.assigned",
        actor,
        {"assigned_to_user_id": request.assigned_to_user_id},
    )
    _commit(db)
    return schemas.ServiceRequestItemResponse.model_validate({"tenant_id": tenant_id, "item": _request_record(updated)} | _base_response())


def update_service_request_status(db: Session, tenant_id: int, request_id: int, actor_user_id: str, request: schemas.ServiceRequestStatusUpdateRequest) -> schemas.ServiceRequestItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    current = repository.get_service_request(db, tenant_id, request_id)
    if current is None:
        raise DomainValidationError(f"service_request {request_id} not found in tenant scope")
    _validate_transition(current.status, request.status)
    updated = repository.update_service_request(db, tenant_id, request_id, status=request.status, updated_by_user_id=actor)
    _emit_request_event(
        db,
        tenant_id,
        request_id,
        "student_service.request.status_changed",
        actor,
        {"previous_status": current.status, "new_status": request.status, "reason": request.reason},
    )
    _commit(db)
    return schemas.ServiceRequestItemResponse.model_validate({"tenant_id": tenant_id, "item": _request_record(updated)} | _base_response())


def create_support_case(db: Session, tenant_id: int, actor_user_id: str, request: schemas.SupportCaseCreateRequest) -> schemas.SupportCaseItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    if request.request_id is not None and repository.get_service_request(db, tenant_id, request.request_id) is None:
        raise DomainValidationError(f"service_request {request.request_id} not found in tenant scope")
    item = repository.create_support_case(
        db,
        tenant_id,
        case_type=request.case_type,
        request_id=request.request_id,
        title=request.title,
        assigned_to_user_id=request.assigned_to_user_id,
        status="open",
        metadata_json=request.metadata,
        limitations_json=[],
        human_review_required=True,
        fake_metrics=False,
        provider_live_enabled=False,
        autonomous_decision_enabled=False,
        hidden_score_present=False,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )
    _emit_case_event(db, tenant_id, item.id, "student_support.case.created", actor, {"case_type": request.case_type})
    _commit(db)
    return schemas.SupportCaseItemResponse.model_validate({"tenant_id": tenant_id, "item": _case_record(item)} | _base_response())


def list_support_cases(db: Session, tenant_id: int) -> schemas.SupportCaseListResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    items = [_case_record(item) for item in repository.list_support_cases(db, tenant_id)]
    return schemas.SupportCaseListResponse.model_validate({"tenant_id": tenant_id, "items": items} | _base_response())


def get_support_case(db: Session, tenant_id: int, case_id: int) -> schemas.SupportCaseItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    item = repository.get_support_case(db, tenant_id, case_id)
    if item is None:
        raise DomainValidationError(f"support_case {case_id} not found in tenant scope")
    return schemas.SupportCaseItemResponse.model_validate({"tenant_id": tenant_id, "item": _case_record(item)} | _base_response())


def add_support_case_note(db: Session, tenant_id: int, case_id: int, actor_user_id: str, request: schemas.SupportCaseNoteCreateRequest) -> schemas.SupportCaseNoteItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    case = repository.get_support_case(db, tenant_id, case_id)
    if case is None:
        raise DomainValidationError(f"support_case {case_id} not found in tenant scope")
    note = repository.create_support_case_note(
        db,
        tenant_id,
        case_id=case_id,
        note=request.note,
        actor_user_id=actor,
        metadata_json=request.metadata,
    )
    _emit_case_event(db, tenant_id, case_id, "student_support.case.note_added", actor, {"note_id": note.id})
    _commit(db)
    item = schemas.SupportCaseNoteRecord.model_validate(
        {
            "id": note.id,
            "tenant_id": note.tenant_id,
            "case_id": note.case_id,
            "note": note.note,
            "metadata": dict(note.metadata_json or {}),
            "created_at": note.created_at,
        }
    )
    return schemas.SupportCaseNoteItemResponse.model_validate({"tenant_id": tenant_id, "item": item} | _base_response())


def attach_support_evidence_metadata(db: Session, tenant_id: int, case_id: int, actor_user_id: str, request: schemas.SupportEvidenceCreateRequest) -> schemas.SupportEvidenceItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    case = repository.get_support_case(db, tenant_id, case_id)
    if case is None:
        raise DomainValidationError(f"support_case {case_id} not found in tenant scope")
    evidence = repository.create_support_evidence(
        db,
        tenant_id,
        case_id=case_id,
        evidence_type=request.evidence_type,
        evidence_ref=request.evidence_ref,
        source_available=request.source_available,
        limitations=request.limitations,
        metadata_json=request.metadata,
        created_by_user_id=actor,
    )
    _emit_case_event(db, tenant_id, case_id, "student_support.evidence.attached", actor, {"evidence_id": evidence.id})
    _commit(db)
    item = schemas.SupportEvidenceRecord.model_validate(
        {
            "id": evidence.id,
            "tenant_id": evidence.tenant_id,
            "case_id": evidence.case_id,
            "evidence_type": evidence.evidence_type,
            "evidence_ref": evidence.evidence_ref,
            "source_available": evidence.source_available,
            "limitations": evidence.limitations,
            "metadata": dict(evidence.metadata_json or {}),
            "created_at": evidence.created_at,
        }
    )
    return schemas.SupportEvidenceItemResponse.model_validate({"tenant_id": tenant_id, "item": item} | _base_response())


def create_hardship_support_request(db: Session, tenant_id: int, actor_user_id: str, request: schemas.HardshipSupportCreateRequest) -> schemas.HardshipReadinessItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    readiness_status, missing_evidence, next_step = _evaluate_readiness(request.evidence_refs)
    item = repository.create_hardship_request(
        db,
        tenant_id,
        request_id=request.request_id,
        status="readiness_evaluated",
        readiness_status=readiness_status,
        missing_evidence_json=missing_evidence,
        recommended_next_step=next_step,
        metadata_json=request.metadata,
        limitations_json=[],
        human_review_required=True,
        fake_metrics=False,
        provider_live_enabled=False,
        autonomous_decision_enabled=False,
        hidden_score_present=False,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )
    if request.request_id is not None:
        _emit_request_event(
            db,
            tenant_id,
            request.request_id,
            "hardship.readiness_evaluated",
            actor,
            {"readiness_status": readiness_status, "missing_evidence": missing_evidence},
        )
    _commit(db)
    record = _readiness_from_model(item, status_value=readiness_status)
    return schemas.HardshipReadinessItemResponse.model_validate({"tenant_id": tenant_id, "item": record} | _base_response())


def create_hardship_support_request_from_finance_handoff(
    db: Session,
    tenant_id: int,
    actor_user_id: str,
    request: schemas.FinanceHardshipHandoffCreateRequest,
) -> schemas.HardshipReadinessItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    metadata = {
        **dict(request.metadata),
        "source_module": "finance_procurement_asset",
        "source_flow": "student_finance_receivables_handoff",
        "receivables_metadata_id": request.receivables_metadata_id,
        "no_automatic_aid_decision": True,
        "no_billing_balance_mutation": True,
    }
    service_request = repository.create_service_request(
        db,
        tenant_id,
        request_type="hardship",
        status="submitted",
        support_priority=request.support_priority,
        student_id=request.student_id,
        subject="Financial hardship review from student finance handoff",
        description="Metadata-only hardship intake from student finance receivables handoff.",
        metadata_json=metadata,
        limitations_json=["no_automatic_hardship_approval", "no_billing_balance_mutation"],
        human_review_required=True,
        fake_metrics=False,
        provider_live_enabled=False,
        autonomous_decision_enabled=False,
        hidden_score_present=False,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )
    readiness_status, missing_evidence, next_step = _evaluate_readiness(request.evidence_refs)
    hardship = repository.create_hardship_request(
        db,
        tenant_id,
        request_id=service_request.id,
        status="readiness_evaluated",
        readiness_status=readiness_status,
        missing_evidence_json=missing_evidence,
        recommended_next_step=next_step,
        metadata_json=metadata,
        limitations_json=["no_automatic_hardship_approval", "no_aid_decision", "no_billing_balance_mutation"],
        human_review_required=True,
        fake_metrics=False,
        provider_live_enabled=False,
        autonomous_decision_enabled=False,
        hidden_score_present=False,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )
    _emit_request_event(
        db,
        tenant_id,
        service_request.id,
        "hardship.finance_handoff_received",
        actor,
        {
            "readiness_status": readiness_status,
            "missing_evidence": missing_evidence,
            "receivables_metadata_id": request.receivables_metadata_id,
        },
    )
    _commit(db)
    record = _readiness_from_model(hardship, status_value=readiness_status)
    return schemas.HardshipReadinessItemResponse.model_validate({"tenant_id": tenant_id, "item": record} | _base_response())


def evaluate_hardship_readiness(db: Session, tenant_id: int, evidence_refs: list[str]) -> dict[str, Any]:
    del db
    tenant_id = validate_tenant_id_provided(tenant_id)
    readiness_status, missing_evidence, next_step = _evaluate_readiness(evidence_refs)
    return {
        "tenant_id": tenant_id,
        "readiness_status": readiness_status,
        "missing_evidence": missing_evidence,
        "recommended_next_step": next_step,
        "human_review_required": True,
    }


def create_disability_accommodation_request(db: Session, tenant_id: int, actor_user_id: str, request: schemas.DisabilityAccommodationCreateRequest) -> schemas.AccommodationReadinessItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    readiness_status, missing_evidence, next_step = _evaluate_readiness(request.evidence_refs)
    item = repository.create_accommodation_request(
        db,
        tenant_id,
        request_id=request.request_id,
        status="readiness_evaluated",
        readiness_status=readiness_status,
        missing_evidence_json=missing_evidence,
        recommended_next_step=next_step,
        metadata_json=request.metadata,
        limitations_json=[],
        human_review_required=True,
        fake_metrics=False,
        provider_live_enabled=False,
        autonomous_decision_enabled=False,
        hidden_score_present=False,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )
    if request.request_id is not None:
        _emit_request_event(
            db,
            tenant_id,
            request.request_id,
            "accommodation.readiness_evaluated",
            actor,
            {"readiness_status": readiness_status, "missing_evidence": missing_evidence},
        )
    _commit(db)
    record = _readiness_from_model(item, status_value=readiness_status)
    return schemas.AccommodationReadinessItemResponse.model_validate({"tenant_id": tenant_id, "item": record} | _base_response())


def evaluate_accommodation_readiness(db: Session, tenant_id: int, evidence_refs: list[str]) -> dict[str, Any]:
    del db
    tenant_id = validate_tenant_id_provided(tenant_id)
    readiness_status, missing_evidence, next_step = _evaluate_readiness(evidence_refs)
    return {
        "tenant_id": tenant_id,
        "readiness_status": readiness_status,
        "missing_evidence": missing_evidence,
        "recommended_next_step": next_step,
        "human_review_required": True,
    }


def create_student_complaint(db: Session, tenant_id: int, actor_user_id: str, request: schemas.StudentComplaintCreateRequest) -> schemas.ComplaintItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    item = repository.create_complaint(
        db,
        tenant_id,
        request_id=request.request_id,
        status="triaged",
        routed_to=request.route_to,
        complaint_summary=request.complaint_summary,
        metadata_json=request.metadata,
        limitations_json=[],
        human_review_required=True,
        fake_metrics=False,
        provider_live_enabled=False,
        autonomous_decision_enabled=False,
        hidden_score_present=False,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )
    if request.request_id is not None:
        _emit_request_event(db, tenant_id, request.request_id, "complaint.created", actor, {"complaint_id": item.id})
    _commit(db)
    return route_student_complaint(db, tenant_id, item.id, actor, request.route_to)


def route_student_complaint(db: Session, tenant_id: int, complaint_id: int, actor_user_id: str, route_to: str | None) -> schemas.ComplaintItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    routed = repository.update_complaint(db, tenant_id, complaint_id, status="routed", routed_to=route_to, updated_by_user_id=actor)
    if routed.request_id is not None:
        _emit_request_event(db, tenant_id, routed.request_id, "complaint.routed", actor, {"routed_to": route_to})
    _commit(db)
    item = schemas.ComplaintRecord.model_validate(
        {
            "id": routed.id,
            "tenant_id": routed.tenant_id,
            "status": routed.status,
            "request_id": routed.request_id,
            "routed_to": routed.routed_to,
            "complaint_summary": routed.complaint_summary,
            "metadata": dict(routed.metadata_json or {}),
        }
    )
    return schemas.ComplaintItemResponse.model_validate({"tenant_id": tenant_id, "item": item} | _base_response())


def escalate_support_case(db: Session, tenant_id: int, actor_user_id: str, request: schemas.SupportEscalationCreateRequest) -> schemas.EscalationItemResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    case = repository.get_support_case(db, tenant_id, request.case_id)
    if case is None:
        raise DomainValidationError(f"support_case {request.case_id} not found in tenant scope")
    updated_case = repository.update_support_case(db, tenant_id, request.case_id, status="escalated", updated_by_user_id=actor)
    escalation = repository.create_escalation(
        db,
        tenant_id,
        case_id=request.case_id,
        status="pending",
        escalation_status="pending",
        reason=request.reason,
        metadata_json=request.metadata,
        limitations_json=[],
        human_review_required=True,
        fake_metrics=False,
        provider_live_enabled=False,
        autonomous_decision_enabled=False,
        hidden_score_present=False,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )
    _emit_case_event(db, tenant_id, request.case_id, "support_case.escalated", actor, {"reason": request.reason, "case_status": updated_case.status})
    _commit(db)
    item = schemas.EscalationRecord.model_validate(
        {
            "id": escalation.id,
            "tenant_id": escalation.tenant_id,
            "case_id": escalation.case_id,
            "escalation_status": escalation.escalation_status,
            "reason": escalation.reason,
            "metadata": dict(escalation.metadata_json or {}),
        }
    )
    return schemas.EscalationItemResponse.model_validate({"tenant_id": tenant_id, "item": item} | _base_response())


def _build_finance_hardship_handoff_visibility(readiness_counts: dict[str, int]) -> dict[str, Any]:
    return {
        "source_module": "finance_procurement_asset",
        "source_flow": _FINANCE_HARDSHIP_SOURCE_FLOW,
        "total": sum(readiness_counts.values()),
        "review_queue_count": int(readiness_counts.get("ready_for_human_review", 0)),
        "missing_evidence_count": sum(
            count for status, count in readiness_counts.items() if status in _MISSING_EVIDENCE_READINESS_STATUSES
        ),
        "readiness_counts": readiness_counts,
        "no_automatic_aid_decision": True,
        "no_billing_balance_mutation": True,
        "human_review_required": True,
    }


def list_finance_hardship_reviewer_queue(
    db: Session,
    tenant_id: int,
    actor_user_id: str,
) -> schemas.FinanceHardshipReviewerQueueResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    _validate_actor(actor_user_id)
    rows = repository.list_hardship_reviewer_queue_by_source_flow(db, tenant_id, _FINANCE_HARDSHIP_SOURCE_FLOW)
    items = []
    for hardship, service_request in rows:
        metadata = dict(hardship.metadata_json or {})
        items.append(
            schemas.FinanceHardshipReviewerQueueItem.model_validate(
                {
                    "hardship_id": hardship.id,
                    "request_id": hardship.request_id,
                    "student_id": getattr(service_request, "student_id", None),
                    "support_priority": getattr(service_request, "support_priority", None),
                    "hardship_status": hardship.status,
                    "service_request_status": getattr(service_request, "status", None),
                    "readiness_status": hardship.readiness_status,
                    "missing_evidence": list(hardship.missing_evidence_json or []),
                    "recommended_next_step": hardship.recommended_next_step,
                    "receivables_metadata_id": metadata.get("receivables_metadata_id"),
                    "source_module": metadata.get("source_module", "finance_procurement_asset"),
                    "source_flow": metadata.get("source_flow", _FINANCE_HARDSHIP_SOURCE_FLOW),
                    "no_automatic_aid_decision": True,
                    "no_billing_balance_mutation": True,
                    "human_review_required": True,
                    "created_at": hardship.created_at,
                    "updated_at": hardship.updated_at,
                }
            )
        )
    return schemas.FinanceHardshipReviewerQueueResponse.model_validate(
        {
            "tenant_id": tenant_id,
            "data_source": models.DATA_SOURCE,
            "incomplete_data": False,
            "items": items,
        }
        | _base_response()
    )


def intake_finance_hardship_evidence_gap(
    db: Session,
    tenant_id: int,
    actor_user_id: str,
    hardship_id: int,
    request: schemas.FinanceHardshipEvidenceGapIntakeRequest,
) -> schemas.FinanceHardshipEvidenceGapIntakeResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    hardship = repository.get_hardship_request(db, tenant_id, hardship_id)
    if hardship is None:
        raise DomainValidationError(f"hardship_request {hardship_id} not found in tenant scope")
    metadata = dict(hardship.metadata_json or {})
    if metadata.get("source_flow") != _FINANCE_HARDSHIP_SOURCE_FLOW:
        raise DomainValidationError("hardship_request is not a finance handoff record")

    satisfied_gap = request.satisfies_gap.strip()
    current_missing = [str(value) for value in list(hardship.missing_evidence_json or [])]
    remaining_missing = [value for value in current_missing if value != satisfied_gap]
    readiness_status = "ready_for_human_review" if not remaining_missing else "needs_follow_up"
    next_step = "queue_human_review" if not remaining_missing else "collect_remaining_evidence"
    evidence_metadata = {
        "evidence_type": request.evidence_type,
        "evidence_ref": request.evidence_ref,
        "satisfies_gap": satisfied_gap,
        "source_available": request.source_available,
        "limitations": request.limitations,
        "metadata": dict(request.metadata),
        "captured_by_user_id": actor,
        "no_automatic_aid_decision": True,
        "no_billing_balance_mutation": True,
        "human_review_required": True,
    }
    existing_gap_intake = metadata.get("evidence_gap_intake")
    evidence_gap_intake = [*existing_gap_intake, evidence_metadata] if isinstance(existing_gap_intake, list) else [evidence_metadata]
    updated_metadata = {
        **metadata,
        "evidence_gap_intake": evidence_gap_intake,
        "last_evidence_gap_intake": evidence_metadata,
        "no_automatic_aid_decision": True,
        "no_billing_balance_mutation": True,
    }
    updated = repository.update_hardship_request(
        db,
        tenant_id,
        hardship_id,
        readiness_status=readiness_status,
        missing_evidence_json=remaining_missing,
        recommended_next_step=next_step,
        metadata_json=updated_metadata,
        updated_by_user_id=actor,
    )
    if updated.request_id is not None:
        _emit_request_event(
            db,
            tenant_id,
            updated.request_id,
            "hardship.finance_handoff_evidence_gap_intake",
            actor,
            {
                "hardship_id": hardship_id,
                "satisfied_gap": satisfied_gap,
                "remaining_missing_evidence": remaining_missing,
                "readiness_status": readiness_status,
            },
        )
    _commit(db)
    record = _readiness_from_model(updated, status_value=readiness_status)
    return schemas.FinanceHardshipEvidenceGapIntakeResponse.model_validate(
        {
            "tenant_id": tenant_id,
            "item": record,
            "evidence_metadata": evidence_metadata,
            "satisfied_gap": satisfied_gap,
            "remaining_missing_evidence": remaining_missing,
            "no_automatic_aid_decision": True,
            "no_billing_balance_mutation": True,
        }
        | _base_response()
    )


def record_finance_hardship_human_review_outcome_note(
    db: Session,
    tenant_id: int,
    actor_user_id: str,
    hardship_id: int,
    request: schemas.FinanceHardshipHumanReviewOutcomeNoteRequest,
) -> schemas.FinanceHardshipHumanReviewOutcomeNoteResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    hardship = repository.get_hardship_request(db, tenant_id, hardship_id)
    if hardship is None:
        raise DomainValidationError(f"hardship_request {hardship_id} not found in tenant scope")
    metadata = dict(hardship.metadata_json or {})
    if metadata.get("source_flow") != _FINANCE_HARDSHIP_SOURCE_FLOW:
        raise DomainValidationError("hardship_request is not a finance handoff record")

    outcome_note_metadata = {
        "outcome_label": request.outcome_label,
        "reviewer_recommendation": request.reviewer_recommendation,
        "note": request.note,
        "metadata": dict(request.metadata),
        "recorded_by_user_id": actor,
        "no_automatic_aid_decision": True,
        "no_billing_balance_mutation": True,
        "human_review_required": True,
    }
    existing_notes = metadata.get("human_review_outcome_notes")
    human_review_outcome_notes = [*existing_notes, outcome_note_metadata] if isinstance(existing_notes, list) else [outcome_note_metadata]
    updated_metadata = {
        **metadata,
        "human_review_outcome_notes": human_review_outcome_notes,
        "last_human_review_outcome_note": outcome_note_metadata,
        "no_automatic_aid_decision": True,
        "no_billing_balance_mutation": True,
    }
    updated = repository.update_hardship_request(
        db,
        tenant_id,
        hardship_id,
        status="human_review_outcome_recorded",
        metadata_json=updated_metadata,
        updated_by_user_id=actor,
    )
    if updated.request_id is not None:
        _emit_request_event(
            db,
            tenant_id,
            updated.request_id,
            "hardship.finance_handoff_human_review_outcome_note_recorded",
            actor,
            {
                "hardship_id": hardship_id,
                "outcome_label": request.outcome_label,
                "reviewer_recommendation": request.reviewer_recommendation,
                "no_automatic_aid_decision": True,
                "no_billing_balance_mutation": True,
            },
        )
    _commit(db)
    record = _readiness_from_model(updated, status_value=updated.readiness_status)
    return schemas.FinanceHardshipHumanReviewOutcomeNoteResponse.model_validate(
        {
            "tenant_id": tenant_id,
            "item": record,
            "outcome_note_metadata": outcome_note_metadata,
            "outcome_label": request.outcome_label,
            "reviewer_recommendation": request.reviewer_recommendation,
            "no_automatic_aid_decision": True,
            "no_billing_balance_mutation": True,
        }
        | _base_response()
    )


def create_finance_hardship_finance_office_referral(
    db: Session,
    tenant_id: int,
    actor_user_id: str,
    hardship_id: int,
    request: schemas.FinanceHardshipFinanceOfficeReferralRequest,
) -> schemas.FinanceHardshipFinanceOfficeReferralResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)
    hardship = repository.get_hardship_request(db, tenant_id, hardship_id)
    if hardship is None:
        raise DomainValidationError(f"hardship_request {hardship_id} not found in tenant scope")
    metadata = dict(hardship.metadata_json or {})
    if metadata.get("source_flow") != _FINANCE_HARDSHIP_SOURCE_FLOW:
        raise DomainValidationError("hardship_request is not a finance handoff record")

    referral_metadata = {
        "referral_target": request.referral_target,
        "referral_reason": request.referral_reason,
        "referral_priority": request.referral_priority,
        "note": request.note,
        "metadata": dict(request.metadata),
        "referred_by_user_id": actor,
        "source_module": "student_services_support",
        "target_module": "finance_procurement_asset",
        "no_automatic_aid_decision": True,
        "no_billing_balance_mutation": True,
        "no_payment_execution": True,
        "human_review_required": True,
    }
    existing_referrals = metadata.get("finance_office_referrals")
    finance_office_referrals = [*existing_referrals, referral_metadata] if isinstance(existing_referrals, list) else [referral_metadata]
    updated_metadata = {
        **metadata,
        "finance_office_referrals": finance_office_referrals,
        "last_finance_office_referral": referral_metadata,
        "no_automatic_aid_decision": True,
        "no_billing_balance_mutation": True,
        "no_payment_execution": True,
    }
    updated = repository.update_hardship_request(
        db,
        tenant_id,
        hardship_id,
        status="finance_office_referral_recorded",
        metadata_json=updated_metadata,
        updated_by_user_id=actor,
    )
    if updated.request_id is not None:
        _emit_request_event(
            db,
            tenant_id,
            updated.request_id,
            "hardship.finance_office_referral_recorded",
            actor,
            {
                "hardship_id": hardship_id,
                "referral_target": request.referral_target,
                "referral_priority": request.referral_priority,
                "no_automatic_aid_decision": True,
                "no_billing_balance_mutation": True,
                "no_payment_execution": True,
            },
        )
    _commit(db)
    record = _readiness_from_model(updated, status_value=updated.readiness_status)
    return schemas.FinanceHardshipFinanceOfficeReferralResponse.model_validate(
        {
            "tenant_id": tenant_id,
            "item": record,
            "referral_metadata": referral_metadata,
            "referral_target": request.referral_target,
            "referral_priority": request.referral_priority,
            "no_automatic_aid_decision": True,
            "no_billing_balance_mutation": True,
            "no_payment_execution": True,
        }
        | _base_response()
    )


def list_finance_hardship_finance_office_referral_queue(
    db: Session,
    tenant_id: int,
    actor_user_id: str,
) -> schemas.FinanceHardshipFinanceOfficeReferralQueueResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    _validate_actor(actor_user_id)
    rows = repository.list_hardship_reviewer_queue_by_source_flow(db, tenant_id, _FINANCE_HARDSHIP_SOURCE_FLOW)
    items = []
    for hardship, service_request in rows:
        metadata = dict(hardship.metadata_json or {})
        referral = metadata.get("last_finance_office_referral")
        if not isinstance(referral, dict):
            continue
        items.append(
            schemas.FinanceHardshipFinanceOfficeReferralQueueItem.model_validate(
                {
                    "hardship_id": hardship.id,
                    "request_id": hardship.request_id,
                    "student_id": getattr(service_request, "student_id", None),
                    "support_priority": getattr(service_request, "support_priority", None),
                    "hardship_status": hardship.status,
                    "readiness_status": hardship.readiness_status,
                    "receivables_metadata_id": metadata.get("receivables_metadata_id"),
                    "referral_target": referral.get("referral_target"),
                    "referral_reason": referral.get("referral_reason"),
                    "referral_priority": referral.get("referral_priority"),
                    "note": referral.get("note"),
                    "referred_by_user_id": referral.get("referred_by_user_id"),
                    "source_module": referral.get("source_module", "student_services_support"),
                    "target_module": referral.get("target_module", "finance_procurement_asset"),
                    "no_automatic_aid_decision": True,
                    "no_billing_balance_mutation": True,
                    "no_payment_execution": True,
                    "human_review_required": True,
                    "created_at": hardship.created_at,
                    "updated_at": hardship.updated_at,
                }
            )
        )
    return schemas.FinanceHardshipFinanceOfficeReferralQueueResponse.model_validate(
        {
            "tenant_id": tenant_id,
            "data_source": models.DATA_SOURCE,
            "incomplete_data": False,
            "items": items,
        }
        | _base_response()
    )


def compute_student_support_dashboard_summary(db: Session, tenant_id: int, actor_user_id: str) -> schemas.DashboardSummaryResponse:
    tenant_id = validate_tenant_id_provided(tenant_id)
    actor = _validate_actor(actor_user_id)

    request_counts = repository.count_by_status(db, models.StudentServiceRequest, tenant_id)
    case_counts = repository.count_by_status(db, models.StudentSupportCase, tenant_id)
    hardship_counts = repository.count_by_status(db, models.HardshipSupportRequest, tenant_id)
    finance_hardship_counts = repository.count_hardship_readiness_by_source_flow(db, tenant_id, _FINANCE_HARDSHIP_SOURCE_FLOW)
    finance_hardship_visibility = _build_finance_hardship_handoff_visibility(finance_hardship_counts)
    accommodation_counts = repository.count_by_status(db, models.DisabilityAccommodationRequest, tenant_id)
    complaint_counts = repository.count_by_status(db, models.StudentComplaint, tenant_id)

    open_requests = sum(v for status, v in request_counts.items() if status in _REQUEST_OPEN_STATUSES)
    open_support_cases = sum(v for status, v in case_counts.items() if status in _CASE_OPEN_STATUSES)
    escalated_cases = int(case_counts.get("escalated", 0))

    summary_payload = {
        "open_requests": open_requests,
        "open_support_cases": open_support_cases,
        "escalated_cases": escalated_cases,
        "hardship_readiness_counts": hardship_counts,
        "finance_hardship_handoff_visibility": finance_hardship_visibility,
        "accommodation_readiness_counts": accommodation_counts,
        "complaint_counts": complaint_counts,
    }
    repository.create_dashboard_snapshot(
        db,
        tenant_id,
        status="active",
        data_source=models.DATA_SOURCE,
        summary_json=summary_payload,
        metadata_json={"computed_by": actor},
        limitations_json=[],
        human_review_required=True,
        fake_metrics=False,
        provider_live_enabled=False,
        autonomous_decision_enabled=False,
        hidden_score_present=False,
        created_by_user_id=actor,
        updated_by_user_id=actor,
    )

    _commit(db)
    return schemas.DashboardSummaryResponse.model_validate(
        {
            "tenant_id": tenant_id,
            "data_source": models.DATA_SOURCE,
            "incomplete_data": False,
            "open_requests": open_requests,
            "open_support_cases": open_support_cases,
            "escalated_cases": escalated_cases,
            "hardship_readiness_counts": hardship_counts,
            "finance_hardship_handoff_visibility": finance_hardship_visibility,
            "accommodation_readiness_counts": accommodation_counts,
            "complaint_counts": complaint_counts,
        }
        | _base_response()
    )
