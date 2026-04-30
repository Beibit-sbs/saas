from __future__ import annotations

import logging

from app.core.module_helpers.service_validation import DomainValidationError
from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.accreditation.schemas import (
    AccreditationCreateSchema,
    AccreditationRecordSchema,
    AccreditationStandardType,
    AccreditationStatus,
    AccreditationStatusUpdateSchema,
)
from app.modules.audit.service import log_admin_action
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"evidence_requested", "under_review"},
    "evidence_requested": {"evidence_collected", "remediation_required"},
    "evidence_collected": {"under_review", "remediation_required"},
    "under_review": {"compliant", "remediation_required", "evidence_requested"},
    "remediation_required": {"evidence_collected", "under_review"},
    "compliant": set(),
}

# W42: cap on active accreditation records per standard_type per tenant
_ACCREDITATION_TYPE_MAX_ACTIVE: dict[str, int] = {
    "institutional": 50,
    "programmatic": 100,
    "curriculum": 150,
    "faculty_qualifications": 80,
    "learning_outcomes": 120,
}

_ACTIVE_ACCREDITATION_STATUSES: frozenset[str] = frozenset({
    "draft", "evidence_requested", "evidence_collected",
    "under_review", "remediation_required",
})

# W42: risk levels that trigger a risk-alert side-effect record
_HIGH_RISK_LEVELS: frozenset[str] = frozenset({"high"})

# W98: guard — accreditation report can only be marked compliant with minimum active faculty
_ACCREDITATION_COMPLIANT_TARGET_STATUS: str = "compliant"
_ACTIVE_FACULTY_CONTRACT_STATUSES: frozenset[str] = frozenset({"active"})
_MIN_ACTIVE_FACULTY_FOR_COMPLIANT: int = 3


def _check_minimum_active_faculty_for_accreditation_compliant(
    *,
    tenant_id: int,
    record_id: int,
    target_status: str,
) -> None:
    """Guard: marking an accreditation record compliant requires >= 3 faculty with active contracts."""
    if target_status != _ACCREDITATION_COMPLIANT_TARGET_STATUS:
        return

    try:
        contracts = list_entities_for_tenant("faculty_contracts", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Accreditation record {record_id} compliant transition blocked: "
            f"faculty_contracts lookup failed — {exc}"
        ) from exc

    active_count = sum(
        1 for c in contracts
        if str(c.get("status") or "").strip().lower() in _ACTIVE_FACULTY_CONTRACT_STATUSES
    )

    if active_count < _MIN_ACTIVE_FACULTY_FOR_COMPLIANT:
        raise DomainValidationError(
            f"Accreditation record {record_id} compliant transition blocked: "
            f"found {active_count} active faculty contract(s), minimum required is "
            f"{_MIN_ACTIVE_FACULTY_FOR_COMPLIANT} — accreditation compliance requires sufficient active faculty"
        )


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="accreditation_record",
        metadata=metadata,
        tenant_id=tenant_id,
    )


_logger = logging.getLogger("app.modules.accreditation")


def _emit_domain_event(
    *,
    tenant_id: int,
    record_id: int,
    standard_code: str,
    owner_department: str,
    from_status: str,
    to_status: str,
) -> None:
    """Fire-and-forget: publish accreditation.status_changed to the outbox for B/C-domain consumers."""
    try:
        from app.platform.events.publisher import EventPublisher

        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="accreditation.status_changed",
            aggregate_type="accreditation_record",
            aggregate_id=record_id,
            payload_json={
                "accreditation_id": record_id,
                "standard_code": standard_code,
                "owner_department": owner_department,
                "from_status": from_status,
                "to_status": to_status,
                "source_module": "accreditation",
            },
        )
    except Exception:  # noqa: BLE001
        _logger.exception(
            "accreditation.status_changed event failed silently for tenant_id=%s record_id=%s",
            tenant_id,
            record_id,
        )


def list_accreditation_records(
    tenant_id: int,
    status: AccreditationStatus | None = None,
    standard_type: AccreditationStandardType | None = None,
) -> list[AccreditationRecordSchema]:
    rows = list_entities_for_tenant("accreditation_records", tenant_id)
    if status is not None:
        rows = [row for row in rows if str(row.get("status") or "") == status]
    if standard_type is not None:
        rows = [row for row in rows if str(row.get("standard_type") or "") == standard_type]
    return [AccreditationRecordSchema.model_validate(row) for row in rows]


def get_accreditation_record(tenant_id: int, record_id: int) -> AccreditationRecordSchema:
    rows = list_entities_for_tenant("accreditation_records", tenant_id)
    current = next((row for row in rows if int(row.get("id") or 0) == record_id), None)
    if current is None:
        raise ValueError("accreditation record not found")
    return AccreditationRecordSchema.model_validate(current)


def create_accreditation_record(
    tenant_id: int,
    request: AccreditationCreateSchema,
    actor: str,
) -> AccreditationRecordSchema:
    existing = list_entities_for_tenant("accreditation_records", tenant_id)
    standard_code = request.standard_code.strip()
    if any(
        str(row.get("standard_code") or "").strip().lower() == standard_code.lower()
        and int(row.get("review_cycle_year") or 0) == int(request.review_cycle_year)
        for row in existing
    ):
        raise ValueError("standard_code already exists for review cycle")

    # W42: count-cap guard on active records by standard_type
    standard_type = request.standard_type
    cap = _ACCREDITATION_TYPE_MAX_ACTIVE.get(standard_type, 100)
    active_count = sum(
        1 for r in existing
        if str(r.get("standard_type") or "") == standard_type
        and str(r.get("status") or "") in _ACTIVE_ACCREDITATION_STATUSES
    )
    if active_count >= cap:
        raise ValueError(
            f"Active accreditation cap ({cap}) reached for standard_type '{standard_type}'"
        )

    created = create_entity_for_tenant(
        "accreditation_records",
        {
            "standard_code": standard_code,
            "standard_type": request.standard_type,
            "title": request.title.strip(),
            "owner_department": request.owner_department.strip(),
            "review_cycle_year": int(request.review_cycle_year),
            "due_date": request.due_date.isoformat() if request.due_date else None,
            "evidence_summary": _normalize_optional(request.evidence_summary),
            "risk_level": request.risk_level,
            "external_auditor_id": _normalize_optional(request.external_auditor_id),
            "status": "draft",
            "reviewer_notes": None,
            "remediation_plan": None,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("accreditation", "record", "create"),
        path="/internal/accreditation/records",
        metadata={
            "resource_id": str(created.get("id")),
            "standard_code": standard_code,
            "review_cycle_year": request.review_cycle_year,
        },
        tenant_id=tenant_id,
    )

    # W42: side-effect alert for high-risk records
    if str(request.risk_level) in _HIGH_RISK_LEVELS:
        _ensure_high_risk_alert_record(
            tenant_id=tenant_id,
            record_id=int(created.get("id") or 0),
            record_data={
                "standard_code": standard_code,
                "standard_type": standard_type,
                "owner_department": request.owner_department.strip(),
                "risk_level": request.risk_level,
            },
        )

    return AccreditationRecordSchema.model_validate(created)


def _ensure_high_risk_alert_record(
    tenant_id: int,
    record_id: int,
    record_data: dict,
) -> None:
    """Idempotent: create an accreditation_risk_alerts entry for high-risk records."""
    existing = list_entities_for_tenant("accreditation_risk_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "accreditation_risk_queue"
            and str(rec.get("source_entity_id")) == str(record_id)
        ):
            return  # already exists
    create_entity_for_tenant(
        "accreditation_risk_alerts",
        {
            "accreditation_id": record_id,
            "standard_code": str(record_data.get("standard_code") or ""),
            "standard_type": str(record_data.get("standard_type") or ""),
            "owner_department": str(record_data.get("owner_department") or ""),
            "risk_level": str(record_data.get("risk_level") or ""),
            "alert_status": "open",
            "integration_source": "accreditation_risk_queue",
            "source_entity_id": str(record_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def update_accreditation_status(
    tenant_id: int,
    record_id: int,
    request: AccreditationStatusUpdateSchema,
    actor: str,
) -> AccreditationRecordSchema:
    rows = list_entities_for_tenant("accreditation_records", tenant_id)
    current = next((row for row in rows if int(row.get("id") or 0) == record_id), None)
    if current is None:
        raise ValueError("accreditation record not found")

    current_status = str(current.get("status") or "draft")
    next_status = request.status
    if next_status != current_status and next_status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"invalid status transition: {current_status} -> {next_status}")

    # W98 guard: compliant transition requires minimum active faculty
    _check_minimum_active_faculty_for_accreditation_compliant(
        tenant_id=tenant_id,
        record_id=record_id,
        target_status=next_status,
    )

    if next_status == "remediation_required" and not _normalize_optional(request.remediation_plan):
        raise ValueError("remediation_plan is required when status is remediation_required")

    updated = update_entity_for_tenant(
        "accreditation_records",
        record_id,
        {
            "status": next_status,
            "reviewer_notes": _normalize_optional(request.reviewer_notes),
            "remediation_plan": _normalize_optional(request.remediation_plan),
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("accreditation", "record", "status_update"),
        path=f"/internal/accreditation/records/{record_id}/status",
        metadata={"resource_id": str(record_id), "from": current_status, "to": next_status},
        tenant_id=tenant_id,
    )

    # Cross-domain event: notify B (Student Success) + C (Faculty) on remediation_required
    _emit_domain_event(
        tenant_id=tenant_id,
        record_id=record_id,
        standard_code=str(current.get("standard_code") or ""),
        owner_department=str(current.get("owner_department") or ""),
        from_status=current_status,
        to_status=next_status,
    )

    return AccreditationRecordSchema.model_validate(updated)
