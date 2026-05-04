from __future__ import annotations

import logging
from datetime import UTC, date, datetime

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.audit.service import log_admin_action
from app.modules.thesis.schemas import ThesisCreateSchema, ThesisRecordSchema, ThesisStatus, ThesisStatusUpdateSchema
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)

logger = logging.getLogger("app.modules.thesis")


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"submitted"},
    "submitted": {"under_review", "rejected"},
    "under_review": {"approved", "rejected"},
    "approved": {"defended"},
    "rejected": {"submitted"},
    "defended": set(),
}

# W41: cap on active (draft/submitted/under_review) theses per tenant
_THESIS_STATUS_MAX_ACTIVE: dict[str, int] = {
    "draft": 200,
    "submitted": 100,
    "under_review": 80,
}

_ACTIVE_THESIS_STATUSES: frozenset[str] = frozenset({"draft", "submitted", "under_review"})

# W41: statuses requiring an overdue-review alert
_HIGH_RISK_THESIS_STATUSES: frozenset[str] = frozenset({"under_review"})

# W69: statuses that trigger a rejection risk alert
_REJECTION_RISK_STATUSES: frozenset[str] = frozenset({"rejected"})

# W92: defending thesis requires no open academic integrity cases for the student.
_DEFENSE_TRANSITION_STATUSES: frozenset[str] = frozenset({"defended"})
_BLOCKING_INTEGRITY_CASE_STATUSES: frozenset[str] = frozenset({"flagged", "under_review", "escalated"})


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    try:
        log_admin_action(
            actor=actor,
            action=action,
            path=path,
            client_ip="service",
            entity="thesis_record",
            metadata=metadata,
            tenant_id=tenant_id,
        )
    except Exception:  # noqa: BLE001
        logger.exception("thesis audit failed action=%s path=%s", action, path)


def _record_outcome(*, thesis_id: int, outcome_type: str, actor: str) -> None:
    try:
        from app.modules.brain_core.service import brain_core_service

        brain_core_service.record_dispatch_outcome(
            str(thesis_id),
            payload={
                "outcome_type": outcome_type,
                "source_module": "thesis",
                "thesis_id": str(thesis_id),
            },
            actor=actor,
        )
    except Exception:  # noqa: BLE001
        logger.exception("thesis outcome failed thesis_id=%s outcome=%s", thesis_id, outcome_type)


def _metric(tenant_id: int, metric: str, value: int = 1) -> None:
    try:
        from app.modules.usage.service import record_usage_event

        record_usage_event(tenant_id=tenant_id, metric=metric, value=value)
    except Exception:  # noqa: BLE001
        logger.exception("thesis metric failed tenant_id=%s metric=%s", tenant_id, metric)


def _emit_domain_event(
    *,
    tenant_id: int,
    thesis_id: int,
    student_id: int,
    advisor_faculty_id: str,
    from_status: str,
    to_status: str,
    days_since_last_milestone: int = 0,
) -> None:
    """Fire-and-forget: publish thesis.status_changed to the outbox for B-domain consumers.

    Payload conforms to the canonical Brain Core signal format so that the event can
    be processed directly by BrainCoreService.process_signal without adaptation.
    """
    try:
        from app.platform.events.publisher import EventPublisher

        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="thesis.status_changed",
            aggregate_type="thesis_record",
            aggregate_id=thesis_id,
            payload_json={
                # Canonical brain signal fields
                "thesis_id": str(thesis_id),
                "student_id": str(student_id),
                "advisor_id": advisor_faculty_id,
                "faculty_id": advisor_faculty_id,
                "days_since_last_milestone": days_since_last_milestone,
                "source_entity_type": "thesis",
                "source_entity_id": str(thesis_id),
                # Status transition context (for academic_chain_handler)
                "from_status": from_status,
                "to_status": to_status,
                "source_module": "thesis",
            },
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "thesis.status_changed event failed silently for tenant_id=%s thesis_id=%s",
            tenant_id,
            thesis_id,
        )


def list_thesis_records(tenant_id: int, status: ThesisStatus | None = None) -> list[ThesisRecordSchema]:
    rows = list_entities_for_tenant("thesis_records", tenant_id)
    if status is not None:
        rows = [row for row in rows if str(row.get("status") or "") == status]
    return [ThesisRecordSchema.model_validate(row) for row in rows]


def create_thesis_record(
    tenant_id: int,
    request: ThesisCreateSchema,
    actor: str,
) -> ThesisRecordSchema:
    existing = list_entities_for_tenant("thesis_records", tenant_id)
    thesis_code = request.thesis_code.strip()
    if any(str(row.get("thesis_code") or "").strip().lower() == thesis_code.lower() for row in existing):
        raise ValueError("thesis_code already exists")

    # W41: count-cap guard on active theses
    initial_status = "draft"
    cap = _THESIS_STATUS_MAX_ACTIVE.get(initial_status, 200)
    active_count = sum(
        1 for r in existing
        if str(r.get("status") or "") in _ACTIVE_THESIS_STATUSES
    )
    if active_count >= cap:
        raise ValueError(
            f"Active thesis cap ({cap}) reached; cannot create new draft thesis"
        )

    created = create_entity_for_tenant(
        "thesis_records",
        {
            "thesis_code": thesis_code,
            "student_id": int(request.student_id),
            "title": request.title.strip(),
            "advisor_faculty_id": _normalize_optional(request.advisor_faculty_id),
            "status": "draft",
            "defense_date": None,
            "repository_url": _normalize_optional(request.repository_url),
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("thesis", "record", "create"),
        path="/internal/thesis/records",
        metadata={"resource_id": str(created.get("id")), "thesis_code": thesis_code},
        tenant_id=tenant_id,
    )

    created_id = int(created.get("id") or 0)
    _emit_domain_event(
        tenant_id=tenant_id,
        thesis_id=created_id,
        student_id=int(created.get("student_id") or 0),
        advisor_faculty_id=str(created.get("advisor_faculty_id") or ""),
        from_status="",
        to_status="draft",
    )
    _record_outcome(thesis_id=created_id, outcome_type="thesis_created", actor=actor)
    _metric(tenant_id, "thesis_records_created", 1)

    return ThesisRecordSchema.model_validate(created)


def update_thesis_status(
    tenant_id: int,
    thesis_id: int,
    request: ThesisStatusUpdateSchema,
    actor: str,
) -> ThesisRecordSchema:
    all_rows = list_entities_for_tenant("thesis_records", tenant_id)
    current = next((row for row in all_rows if int(row.get("id") or 0) == thesis_id), None)
    if current is None:
        raise ValueError("thesis record not found")

    current_status = str(current.get("status") or "draft")
    next_status = request.status
    if next_status != current_status and next_status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"invalid status transition: {current_status} -> {next_status}")

    defense_date_value: date | None = request.defense_date
    if next_status == "defended" and defense_date_value is None:
        raise ValueError("defense_date is required when status is defended")

    _check_no_open_integrity_cases_for_defense(
        tenant_id=tenant_id,
        thesis_id=thesis_id,
        thesis_data=current,
        target_status=next_status,
    )

    updated = update_entity_for_tenant(
        "thesis_records",
        thesis_id,
        {
            "status": next_status,
            "defense_date": defense_date_value.isoformat() if defense_date_value else None,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("thesis", "record", "status_update"),
        path=f"/internal/thesis/records/{thesis_id}/status",
        metadata={"resource_id": str(thesis_id), "from": current_status, "to": next_status},
        tenant_id=tenant_id,
    )

    # Cross-domain event: notify B (Student Success) on risk statuses
    # Compute days_since_last_milestone from last_milestone_at if recorded, else 0.
    last_milestone_at_str = str(current.get("last_milestone_at") or "")
    days_since_last_milestone = 0
    if last_milestone_at_str:
        try:
            last_dt = datetime.fromisoformat(last_milestone_at_str)
            days_since_last_milestone = (datetime.now(UTC) - last_dt.replace(tzinfo=UTC)).days
        except ValueError:
            pass

    _emit_domain_event(
        tenant_id=tenant_id,
        thesis_id=thesis_id,
        student_id=int(current.get("student_id") or 0),
        advisor_faculty_id=str(current.get("advisor_faculty_id") or ""),
        from_status=current_status,
        to_status=next_status,
        days_since_last_milestone=days_since_last_milestone,
    )
    _record_outcome(thesis_id=thesis_id, outcome_type=f"thesis_status_{next_status}", actor=actor)
    _metric(tenant_id, "thesis_status_updates", 1)

    # W41: side-effect overdue alert for high-risk statuses
    if next_status in _HIGH_RISK_THESIS_STATUSES:
        _ensure_overdue_alert_record(
            tenant_id=tenant_id,
            thesis_id=thesis_id,
            thesis_data={
                "thesis_code": current.get("thesis_code"),
                "student_id": current.get("student_id"),
                "current_status": next_status,
            },
        )

    # W69: side-effect rejection risk alert
    if next_status in _REJECTION_RISK_STATUSES:
        _ensure_rejection_risk_alert(
            tenant_id=tenant_id,
            thesis_id=thesis_id,
            thesis_data={
                "thesis_code": current.get("thesis_code"),
                "student_id": current.get("student_id"),
                "current_status": next_status,
            },
        )

    return ThesisRecordSchema.model_validate(updated)


def _check_no_open_integrity_cases_for_defense(
    *,
    tenant_id: int,
    thesis_id: int,
    thesis_data: dict,
    target_status: str,
) -> None:
    """Fail-closed invariant: defended transition requires integrity clearance.

    A thesis defense cannot be finalized while the student has active academic
    integrity cases (flagged/under_review/escalated).
    """
    if target_status not in _DEFENSE_TRANSITION_STATUSES:
        return

    student_id_raw = thesis_data.get("student_id")
    try:
        student_id = int(student_id_raw)
    except (TypeError, ValueError) as exc:
        raise DomainValidationError(
            f"Cannot mark thesis {thesis_id} as defended: missing or invalid student_id"
        ) from exc

    try:
        integrity_cases = list_entities_for_tenant("integrity_case", tenant_id)
    except Exception as exc:  # pragma: no cover - exercised via monkeypatch tests
        raise DomainValidationError(
            "Cannot mark thesis as defended: academic_integrity lookup failed. "
            "Integrity clearance must be verified before defense finalization"
        ) from exc

    blocking_cases = [
        row
        for row in integrity_cases
        if int(row.get("student_id") or 0) == student_id
        and str(row.get("status") or "").strip().lower() in _BLOCKING_INTEGRITY_CASE_STATUSES
    ]
    if blocking_cases:
        blocking_case_ids = [str(row.get("id") or "unknown") for row in blocking_cases]
        raise DomainValidationError(
            f"Cannot mark thesis {thesis_id} as defended for student_id={student_id}: "
            "open academic integrity cases exist "
            f"(statuses={sorted(_BLOCKING_INTEGRITY_CASE_STATUSES)}, case_ids={blocking_case_ids})"
        )


def _ensure_overdue_alert_record(
    tenant_id: int,
    thesis_id: int,
    thesis_data: dict,
) -> None:
    """Idempotent: create a thesis_overdue_alerts entry when thesis enters under_review."""
    existing = list_entities_for_tenant("thesis_overdue_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "thesis_review_queue"
            and str(rec.get("source_entity_id")) == str(thesis_id)
        ):
            return  # already exists
    create_entity_for_tenant(
        "thesis_overdue_alerts",
        {
            "thesis_id": thesis_id,
            "thesis_code": str(thesis_data.get("thesis_code") or ""),
            "student_id": int(thesis_data.get("student_id") or 0),
            "current_status": str(thesis_data.get("current_status") or ""),
            "alert_status": "open",
            "integration_source": "thesis_review_queue",
            "source_entity_id": str(thesis_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def _ensure_rejection_risk_alert(
    tenant_id: int,
    thesis_id: int,
    thesis_data: dict,
) -> None:
    """Idempotent: create a thesis_rejection_risk_alerts entry when thesis transitions to rejected."""
    existing = list_entities_for_tenant("thesis_rejection_risk_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "thesis_rejection_queue"
            and str(rec.get("source_entity_id")) == str(thesis_id)
        ):
            return  # already recorded
    create_entity_for_tenant(
        "thesis_rejection_risk_alerts",
        {
            "thesis_id": thesis_id,
            "thesis_code": str(thesis_data.get("thesis_code") or ""),
            "student_id": int(thesis_data.get("student_id") or 0),
            "current_status": str(thesis_data.get("current_status") or ""),
            "alert_status": "open",
            "integration_source": "thesis_rejection_queue",
            "source_entity_id": str(thesis_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    try:
        from app.platform.events.publisher import EventPublisher
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="campus.thesis.rejection_risk_detected",
            aggregate_type="thesis_record",
            aggregate_id=str(thesis_id),
            payload_json={
                "thesis_id": thesis_id,
                "thesis_code": str(thesis_data.get("thesis_code") or ""),
                "student_id": str(thesis_data.get("student_id") or ""),
                "source_entity_type": "thesis_record",
                "source_entity_id": str(thesis_id),
            },
        )
    except Exception:  # noqa: BLE001
        pass
