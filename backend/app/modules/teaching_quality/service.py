"""
Teaching Quality service — W124 hardening.

Cross-entity guard: quality metric creation blocked when faculty has no active
employment contract (terminated/resigned ghost quality record prevention).
Fail-closed: any faculty_contracts lookup failure blocks the action.
"""
from __future__ import annotations

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.faculty.service import (
    create_teaching_quality_record,
    list_teaching_quality,
)
from app.modules.university_core.tenant_entity_service import list_entities_for_tenant

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

_FACULTY_CONTRACT_ACTIVE_STATUSES: frozenset[str] = frozenset({"active"})


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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_quality_metric(
    payload: dict[str, object],
    tenant_id: int,
) -> dict[str, object]:
    """Create a teaching quality metric with cross-entity faculty contract guard.

    Guard fires FIRST before any persistence.
    """
    faculty_id = str(payload.get("faculty_id") or "").strip()
    if not faculty_id:
        raise DomainValidationError("faculty_id is required")

    _check_faculty_has_active_contract_for_quality_metric(
        tenant_id=tenant_id,
        faculty_id=faculty_id,
    )

    return create_teaching_quality_record(payload, tenant_id)


__all__ = [
    "_FACULTY_CONTRACT_ACTIVE_STATUSES",
    "_check_faculty_has_active_contract_for_quality_metric",
    "create_quality_metric",
    "list_teaching_quality",
]
