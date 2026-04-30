"""Phase X-X3: Delinquency & Collections service."""
from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.audit.service import log_admin_action
from app.modules.delinquency_collections.schemas import (
    DelinquencyEscalationUpdateSchema,
    DelinquencyRecordCreateSchema,
    DelinquencyRecordSchema,
    DelinquencyStatus,
    DelinquencyStatusUpdateSchema,
    EscalationStage,
)
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# W23: per-student escalation stage active-record caps
_ACTIVE_STATUSES_DC: frozenset[str] = frozenset({"open", "in_review", "escalated"})
_ESCALATION_STAGE_MAX_ACTIVE: dict[str, int] = {
    "stage_1": 5,
    "stage_2": 3,
    "stage_3": 1,
    "legal": 1,
}
# W67: legal escalation risk
_LEGAL_RISK_STAGES: frozenset[str] = frozenset({"legal"})

# W87: Legal escalation thresholds — legal action must only be taken on substantive debts.
# Escalating a trivial debt to legal causes attorney costs > debt and destroys student credit.
_LEGAL_ESCALATION_MIN_AMOUNT_DUE: float = 500.0   # minimum USD owed to justify legal action
_LEGAL_ESCALATION_MIN_DAYS_OVERDUE: int = 90       # minimum days overdue before legal escalation
# Escalation stages that require legal-threshold validation
_LEGAL_ESCALATION_STAGES: frozenset[str] = frozenset({"legal"})

# W115: Debt collection may only target students who are registered in the institution’s
# enrollment system. Without at least one enrollment record, the student has no financial
# relationship with the institution and no basis for a tuition/fee debt.
# Creating phantom debt against a non-enrolled person constitutes:
#   - Fraudulent debt record (may violate FCRA / FDCPA)
#   - Illegal debt collection against a non-debtor
#   - Phantom entry in financial reporting that distorts collection metrics
_DELINQUENCY_REQUIRES_ENROLLMENT_HISTORY: bool = True  # sentinel for tests


def _check_student_has_enrollment_history(
    *,
    tenant_id: int,
    student_id: str,
) -> None:
    """Cross-entity guard: delinquency_records × enrollments by student_id.

    A delinquency record may ONLY be created when the referenced student_id has
    at least one enrollment record in the institution’s enrollment system (any status).

    Tuition and fee debts can ONLY exist for students who actually registered
    for courses and received academic services. A student with zero enrollment
    records never incurred educational fees and therefore cannot legitimately
    owe tuition debt.

    Creating a delinquency record against a non-enrolled person:
    - Constitutes a fraudulent debt record (FCRA / FDCPA violation risk)
    - May trigger illegal automated collection actions against non-debtors
    - Distorts collection portfolio metrics with phantom accounts
    - Creates regulatory and legal liability for the institution

    FAIL-CLOSED: If enrollment lookup raises any exception, delinquency creation
    is BLOCKED. Cannot initiate debt collection without confirming enrollment history.
    """
    try:
        all_enrollments = list_entities_for_tenant("enrollments", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Delinquency record blocked for student_id='{student_id}': "
            f"enrollment lookup failed — {exc}. "
            f"Cannot initiate debt collection without confirming enrollment history."
        ) from exc

    normalized_sid = student_id.strip().lower()
    has_enrollment = any(
        str(row.get("student_id") or "").strip().lower() == normalized_sid
        for row in all_enrollments
    )

    if not has_enrollment:
        raise DomainValidationError(
            f"Delinquency record blocked: student_id='{student_id}' has no enrollment "
            f"history in this institution. Tuition debt can only be collected from "
            f"registered students who incurred fees for academic services. "
            f"Creating debt against a non-enrolled person constitutes a fraudulent "
            f"debt record and may violate FCRA/FDCPA regulations."
        )


def _ensure_collections_agent_record(
    tenant_id: int,
    record_id: int,
    record_data: dict,
) -> None:
    """Idempotent: create a collections_agent_records entry when escalation reaches stage_3/legal."""
    src = "collections_escalation"
    src_id = str(record_id)
    existing = list_entities_for_tenant("collections_agent_records", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == src
            and str(rec.get("source_entity_id")) == src_id
        ):
            return  # already created — idempotent
    create_entity_for_tenant(
        "collections_agent_records",
        {
            "record_id": record_id,
            "record_code": str(record_data.get("invoice_code") or ""),
            "student_id": str(record_data.get("student_id") or ""),
            "escalation_stage": str(record_data.get("escalation_stage") or ""),
            "amount_due": float(record_data.get("amount_due") or 0),
            "status": "assigned",
            "integration_source": src,
            "source_entity_id": src_id,
        },
        tenant_id,
    )


def _check_legal_escalation_threshold(
    *,
    record_id: int,
    student_id: str,
    amount_due: float,
    days_overdue: int,
    target_stage: str,
) -> None:
    """W87: Transition Guard — legal escalation requires substantive debt.

    Legal action may only be initiated when BOTH conditions are met:
      1. amount_due >= _LEGAL_ESCALATION_MIN_AMOUNT_DUE  (debt is material)
      2. days_overdue >= _LEGAL_ESCALATION_MIN_DAYS_OVERDUE  (debt is genuinely overdue)

    Escalating a student to legal stage with a trivial or recent debt causes:
    - University attorney costs that exceed the recovered amount
    - Irreversible damage to the student's credit record
    - Regulatory / Title IV compliance exposure

    HARDENING: both conditions must be met; failing either → DomainValidationError.
    This guard fires BEFORE persist — no state change occurs on failure.
    """
    if target_stage not in _LEGAL_ESCALATION_STAGES:
        return  # guard only applies to legal stage

    violations: list[str] = []
    if amount_due < _LEGAL_ESCALATION_MIN_AMOUNT_DUE:
        violations.append(
            f"amount_due={amount_due:.2f} is below the legal-action minimum "
            f"of {_LEGAL_ESCALATION_MIN_AMOUNT_DUE:.2f}"
        )
    if days_overdue < _LEGAL_ESCALATION_MIN_DAYS_OVERDUE:
        violations.append(
            f"days_overdue={days_overdue} is below the required minimum "
            f"of {_LEGAL_ESCALATION_MIN_DAYS_OVERDUE} days"
        )

    if violations:
        raise DomainValidationError(
            f"Cannot escalate record_id={record_id} (student_id={student_id!r}) to legal stage: "
            f"{'; '.join(violations)}. "
            f"Legal action requires amount_due >= {_LEGAL_ESCALATION_MIN_AMOUNT_DUE:.0f} AND "
            f"days_overdue >= {_LEGAL_ESCALATION_MIN_DAYS_OVERDUE}. "
            f"Escalating a trivial or recent debt to legal causes attorney costs > debt recovered "
            f"and permanently damages the student's credit record."
        )


def _ensure_legal_escalation_risk_alert(
    tenant_id: int,
    record_id: int,
    record_data: dict,
) -> None:
    """Idempotent: create a delinquency_legal_escalation_alerts record when stage=legal."""
    src = "delinquency_legal_queue"
    src_id = str(record_id)
    existing = list_entities_for_tenant("delinquency_legal_escalation_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == src
            and str(rec.get("source_entity_id")) == src_id
        ):
            return  # already created — idempotent
    create_entity_for_tenant(
        "delinquency_legal_escalation_alerts",
        {
            "record_id": record_id,
            "student_id": str(record_data.get("student_id") or ""),
            "escalation_stage": str(record_data.get("escalation_stage") or "legal"),
            "amount_due": float(record_data.get("amount_due") or 0),
            "alert_status": "open",
            "integration_source": src,
            "source_entity_id": src_id,
        },
        tenant_id,
    )
    try:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="campus.delinquency_collections.legal_escalation_risk_detected",
            aggregate_type="delinquency_records",
            aggregate_id=src_id,
            payload_json={
                "record_id": record_id,
                "student_id": str(record_data.get("student_id") or ""),
                "escalation_stage": "legal",
                "amount_due": float(record_data.get("amount_due") or 0),
            },
        )
    except Exception:  # noqa: BLE001
        pass


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="delinquency_collections",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def list_delinquency_records(
    tenant_id: int,
    status: DelinquencyStatus | None = None,
    escalation_stage: EscalationStage | None = None,
) -> list[DelinquencyRecordSchema]:
    rows = list_entities_for_tenant("delinquency_records", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if escalation_stage is not None:
        rows = [r for r in rows if str(r.get("escalation_stage") or "") == escalation_stage]
    return [DelinquencyRecordSchema.model_validate(r) for r in rows]


def get_delinquency_record(tenant_id: int, record_id: int) -> DelinquencyRecordSchema | None:
    rows = list_entities_for_tenant("delinquency_records", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == record_id), None)
    if row is None:
        return None
    return DelinquencyRecordSchema.model_validate(row)


def create_delinquency_record(
    tenant_id: int,
    request: DelinquencyRecordCreateSchema,
    actor: str,
) -> DelinquencyRecordSchema:
    # W115: Cross-entity guard — student must have enrollment history before debt collection
    _check_student_has_enrollment_history(
        tenant_id=tenant_id,
        student_id=request.student_id,
    )

    # W23: cap guard — per student_id + escalation_stage active records
    _active_statuses = _ACTIVE_STATUSES_DC
    max_for_stage = _ESCALATION_STAGE_MAX_ACTIVE.get(request.escalation_stage, 999)
    existing_all = list_entities_for_tenant("delinquency_records", tenant_id)
    active_count = sum(
        1 for r in existing_all
        if str(r.get("student_id") or "") == request.student_id
        and str(r.get("escalation_stage") or "") == request.escalation_stage
        and str(r.get("status") or "") in _active_statuses
    )
    if active_count >= max_for_stage:
        raise ValueError(
            f"student_id={request.student_id!r} already has {active_count} active "
            f"'{request.escalation_stage}' records; max={max_for_stage}"
        )
    created = create_entity_for_tenant(
        "delinquency_records",
        {
            "student_id": request.student_id.strip(),
            "invoice_code": request.invoice_code.strip(),
            "amount_due": float(request.amount_due),
            "days_overdue": int(request.days_overdue),
            "escalation_stage": request.escalation_stage,
            "status": request.status,
        },
        tenant_id,
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("delinquency_collections", "record", "create"),
        path="/internal/delinquency-collections",
        metadata={"resource_id": str(created.get("id")), "student_id": request.student_id},
        tenant_id=tenant_id,
    )
    # Brain signal for high overdue
    try:
        days = int(created.get("days_overdue") or 0)
    except (TypeError, ValueError):
        days = 0

    if days >= 90:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="collections.delinquency.critical_overdue",
            aggregate_type="delinquency_records",
            aggregate_id=str(created.get("id") or "unknown"),
            payload_json={
                "student_id": request.student_id,
                "days_overdue": days,
                "amount_due": float(request.amount_due),
            },
        )
    # W23: wire escalation agent record side-effect
    if request.escalation_stage in {"stage_3", "legal"}:
        _ensure_collections_agent_record(tenant_id, int(created.get("id") or 0), created)
    return DelinquencyRecordSchema.model_validate(created)


def update_delinquency_status(
    tenant_id: int,
    record_id: int,
    request: DelinquencyStatusUpdateSchema,
    actor: str,
) -> DelinquencyRecordSchema | None:
    rows = list_entities_for_tenant("delinquency_records", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == record_id), None)
    if existing is None:
        return None
    updated = update_entity_for_tenant(
        "delinquency_records", record_id, {**existing, "status": request.status}, tenant_id
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("delinquency_collections", "record", "status_update"),
        path=f"/internal/delinquency-collections/{record_id}/status",
        metadata={"resource_id": str(record_id), "new_status": request.status},
        tenant_id=tenant_id,
    )
    return DelinquencyRecordSchema.model_validate(updated)


def update_delinquency_escalation(
    tenant_id: int,
    record_id: int,
    request: DelinquencyEscalationUpdateSchema,
    actor: str,
) -> DelinquencyRecordSchema | None:
    rows = list_entities_for_tenant("delinquency_records", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == record_id), None)
    if existing is None:
        return None

    # W87: Transition Guard — legal escalation requires minimum debt amount and overdue days
    if request.escalation_stage in _LEGAL_ESCALATION_STAGES:
        try:
            amount_due = float(existing.get("amount_due") or 0.0)
        except (TypeError, ValueError):
            amount_due = 0.0
        try:
            days_overdue = int(existing.get("days_overdue") or 0)
        except (TypeError, ValueError):
            days_overdue = 0
        _check_legal_escalation_threshold(
            record_id=record_id,
            student_id=str(existing.get("student_id") or ""),
            amount_due=amount_due,
            days_overdue=days_overdue,
            target_stage=request.escalation_stage,
        )

    updated = update_entity_for_tenant(
        "delinquency_records", record_id, {**existing, "escalation_stage": request.escalation_stage}, tenant_id
    )
    _emit_audit(
        actor=actor,
        action=build_audit_action("delinquency_collections", "record", "escalation_update"),
        path=f"/internal/delinquency-collections/{record_id}/escalation",
        metadata={"resource_id": str(record_id), "new_stage": request.escalation_stage},
        tenant_id=tenant_id,
    )
    # W67: legal escalation risk alert side-effect
    if request.escalation_stage in _LEGAL_RISK_STAGES:
        _ensure_legal_escalation_risk_alert(tenant_id, record_id, updated)
    return DelinquencyRecordSchema.model_validate(updated)
