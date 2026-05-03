"""
Teaching Quality service — W124 hardening + XXXIV.6 10-step loop.

Cross-entity guard: quality metric creation blocked when faculty has no active
employment contract (terminated/resigned ghost quality record prevention).
Fail-closed: any faculty_contracts lookup failure blocks the action.

XXXIV.6: fire-and-forget events for EVALUATION_SUBMITTED, SCORE_UPDATED,
LOW_SCORE_ALERT on create and update paths.
"""
from __future__ import annotations

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.faculty.service import (
    create_teaching_quality_record,
    list_teaching_quality,
)
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

_FACULTY_CONTRACT_ACTIVE_STATUSES: frozenset[str] = frozenset({"active"})
_LOW_SCORE_THRESHOLD: float = 60.0


# ---------------------------------------------------------------------------
# Cross-entity guard
# ---------------------------------------------------------------------------


def _check_faculty_has_active_contract_for_quality_metric(
    *,
    tenant_id: int,
    faculty_id: str,
) -> None:
    """Block quality metric creation when faculty has no active employment contract.

    Fail-closed: any lookup failure raises DomainValidationError (action blocked).
    """
    normalized_id = faculty_id.strip()

    try:
        contracts = list_entities_for_tenant("faculty_contracts", tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise DomainValidationError(
            f"faculty_contracts lookup failed for faculty '{normalized_id}': {exc}"
        ) from exc

    faculty_contracts = [
        c
        for c in contracts
        if str(c.get("faculty_id") or "").strip() == normalized_id
        or str(c.get("employee_id") or "").strip() == normalized_id
    ]

    if not faculty_contracts:
        raise DomainValidationError(
            f"Teaching quality metric blocked: no faculty contract records found "
            f"for faculty '{normalized_id}'"
        )

    active = [
        c
        for c in faculty_contracts
        if str(c.get("status") or "").strip().lower()
        in _FACULTY_CONTRACT_ACTIVE_STATUSES
        or str(c.get("contract_status") or "").strip().lower()
        in _FACULTY_CONTRACT_ACTIVE_STATUSES
    ]

    if not active:
        raise DomainValidationError(
            f"Teaching quality metric blocked: no active contract for faculty "
            f"'{normalized_id}' — terminated or resigned faculty cannot receive "
            f"quality metric records"
        )


def _fire_low_score_alert_if_needed(
    record: dict[str, object],
    tenant_id: int,
) -> None:
    """Fire teaching_quality.low_score.alert if score is below threshold (fire-and-forget)."""
    quality_score = float(record.get("quality_score") or 100.0)
    kpi_score = float(record.get("kpi_score") or 100.0)
    if quality_score < _LOW_SCORE_THRESHOLD or kpi_score < _LOW_SCORE_THRESHOLD:
        record_id = str(record.get("id") or "unknown")
        try:
            EventPublisher().publish_event(
                tenant_id=tenant_id,
                event_type="teaching_quality.low_score.alert",
                aggregate_type="teaching_quality_record",
                aggregate_id=record_id,
                payload_json={
                    "faculty_id": record.get("faculty_id"),
                    "course_id": record.get("course_id"),
                    "term_id": record.get("term_id"),
                    "quality_score": quality_score,
                    "kpi_score": kpi_score,
                    "tenant_id": tenant_id,
                },
            )
        except Exception:  # noqa: BLE001
            pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_quality_metric(
    payload: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    """Create a teaching quality metric with cross-entity faculty contract guard.

    Guard fires FIRST before any persistence. After persistence, fires
    teaching_quality.evaluation.submitted and optionally low_score.alert.
    """
    faculty_id = str(payload.get("faculty_id") or "").strip()
    if not faculty_id:
        raise DomainValidationError("faculty_id is required")

    _check_faculty_has_active_contract_for_quality_metric(
        tenant_id=tenant_id,
        faculty_id=faculty_id,
    )

    record = create_teaching_quality_record(payload, tenant_id)
    record_id = str(record.get("id") or "unknown")

    # Fire-and-forget: evaluation submitted event
    try:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="teaching_quality.evaluation.submitted",
            aggregate_type="teaching_quality_record",
            aggregate_id=record_id,
            payload_json={
                "faculty_id": record.get("faculty_id"),
                "course_id": record.get("course_id"),
                "term_id": record.get("term_id"),
                "quality_score": record.get("quality_score"),
                "kpi_score": record.get("kpi_score"),
                "tenant_id": tenant_id,
            },
        )
    except Exception:  # noqa: BLE001
        pass

    # Fire-and-forget: action log entity
    try:
        create_entity_for_tenant(
            "teaching_quality_action_logs",
            {
                "record_id": record_id,
                "action_type": "evaluation_submitted",
                "faculty_id": record.get("faculty_id"),
                "course_id": record.get("course_id"),
                "term_id": record.get("term_id"),
                "tenant_id": tenant_id,
            },
            tenant_id,
        )
    except Exception:  # noqa: BLE001
        pass

    # Conditional low-score alert
    _fire_low_score_alert_if_needed(record, tenant_id)

    return record


def update_quality_score(
    record_id: int,
    updates: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    """Update quality score fields and fire teaching_quality.score.updated event."""
    record = update_entity_for_tenant("teaching_quality_records", record_id, updates, tenant_id)
    rid = str(record.get("id") or record_id)

    # Fire-and-forget: score updated event
    try:
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="teaching_quality.score.updated",
            aggregate_type="teaching_quality_record",
            aggregate_id=rid,
            payload_json={
                "faculty_id": record.get("faculty_id"),
                "course_id": record.get("course_id"),
                "term_id": record.get("term_id"),
                "quality_score": record.get("quality_score"),
                "kpi_score": record.get("kpi_score"),
                "tenant_id": tenant_id,
            },
        )
    except Exception:  # noqa: BLE001
        pass

    # Conditional low-score alert
    _fire_low_score_alert_if_needed(record, tenant_id)

    return record


__all__ = [
    "_FACULTY_CONTRACT_ACTIVE_STATUSES",
    "_LOW_SCORE_THRESHOLD",
    "_check_faculty_has_active_contract_for_quality_metric",
    "create_quality_metric",
    "update_quality_score",
    "list_teaching_quality",
]
