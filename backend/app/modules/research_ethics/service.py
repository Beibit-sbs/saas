"""Phase VII-VII1: Research ethics service."""
from __future__ import annotations

from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.research_ethics.schemas import (
    EthicsReviewStatusUpdateSchema,
    RE_ALLOWED_TRANSITIONS,
)
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher


_REVIEW_TYPE_MAX_ACTIVE_REVIEWS: dict[str, int] = {
    "irb": 30,
    "biosafety": 15,
    "clinical": 20,
    "data_privacy": 25,
}

_ACTIVE_REVIEW_STATUSES: frozenset[str] = frozenset({
    "pending",
    "under_review",
    "revision_requested",
})

_HIGH_RISK_LEVELS: frozenset[str] = frozenset({"high", "critical"})

# W90: approval transition requires PI eligibility across faculty + contracts.
_APPROVAL_TRANSITION_STATUSES: frozenset[str] = frozenset({"approved"})
_REQUIRED_PI_FACULTY_STATUSES: frozenset[str] = frozenset({"active"})
_REQUIRED_PI_CONTRACT_STATUSES: frozenset[str] = frozenset({"active"})

# W126: PI must have an active contract to submit an ethics review
_PI_CONTRACT_ACTIVE_STATUSES: frozenset[str] = frozenset({"active"})


def _check_pi_has_active_contract_for_ethics_review(
    *,
    tenant_id: int,
    pi_id: str,
) -> None:
    """W126: Cross-entity guard — ethics_reviews × faculty_contracts.

    An ethics review cannot be created when the PI has no active faculty contract.
    A terminated or resigned faculty member submitting an IRB/ethics review creates
    a ghost protocol tied to an ineligible researcher, corrupting ethics audit trail
    and potentially enabling regulatory fraud (IRB/biosafety violations).

    Fail-closed: any lookup failure raises DomainValidationError.
    """
    normalized_pi = pi_id.strip()

    try:
        contracts = list_entities_for_tenant("faculty_contracts", tenant_id)
    except Exception as exc:  # noqa: BLE001
        raise DomainValidationError(
            f"faculty_contracts lookup failed for PI '{normalized_pi}': {exc}"
        ) from exc

    pi_contracts = [
        c for c in contracts
        if str(c.get("faculty_id") or "").strip() == normalized_pi
        or str(c.get("employee_id") or "").strip() == normalized_pi
    ]

    if not pi_contracts:
        raise DomainValidationError(
            f"Ethics review blocked: no faculty contract records found for PI '{normalized_pi}'"
        )

    active = [
        c for c in pi_contracts
        if str(c.get("status") or "").strip().lower() in _PI_CONTRACT_ACTIVE_STATUSES
        or str(c.get("contract_status") or "").strip().lower() in _PI_CONTRACT_ACTIVE_STATUSES
    ]

    if not active:
        raise DomainValidationError(
            f"Ethics review blocked: PI '{normalized_pi}' has no active faculty contract "
            f"— terminated or resigned PI cannot submit ethics reviews"
        )


def list_ethics_reviews(
    tenant_id: int,
    status: str | None = None,
    risk_level: str | None = None,
) -> list[dict[str, object]]:
    rows = list_entities_for_tenant("ethics_reviews", tenant_id)
    status_filter = str(status or "").strip().lower()
    risk_filter = str(risk_level or "").strip().lower()

    result: list[dict[str, object]] = []
    for row in rows:
        if status_filter and str(row.get("status") or "").strip().lower() != status_filter:
            continue
        if risk_filter and str(row.get("risk_level") or "").strip().lower() != risk_filter:
            continue
        result.append(row)
    return result


def create_ethics_review(payload: dict[str, object], tenant_id: int) -> dict[str, object]:
    # W126: cross-entity guard — PI must have active faculty contract
    pi_id = str(payload.get("principal_investigator_id") or "").strip()
    if not pi_id:
        raise DomainValidationError("principal_investigator_id is required")
    _check_pi_has_active_contract_for_ethics_review(
        tenant_id=tenant_id,
        pi_id=pi_id,
    )

    review_type = str(payload.get("review_type") or "irb").strip().lower()
    status = str(payload.get("status") or "pending").strip().lower()
    cap = _REVIEW_TYPE_MAX_ACTIVE_REVIEWS.get(review_type, 20)

    if status in _ACTIVE_REVIEW_STATUSES:
        rows = list_entities_for_tenant("ethics_reviews", tenant_id)
        active_count = sum(
            1
            for row in rows
            if str(row.get("review_type") or "").strip().lower() == review_type
            and str(row.get("status") or "").strip().lower() in _ACTIVE_REVIEW_STATUSES
        )
        if active_count >= cap:
            raise ValueError(
                f"Active ethics review cap ({cap}) reached for review_type '{review_type}'."
            )

    created = create_entity_for_tenant("ethics_reviews", payload, tenant_id)

    # XXXIV.7: fire submission event (fire-and-forget)
    try:
        EventPublisher().publish_event(
            "research_ethics.submission.created",
            {"tenant_id": tenant_id, "review_id": str(created.get("id", "")),
             "review_type": review_type, "pi_id": pi_id},
        )
    except Exception:  # noqa: BLE001
        pass

    # XXXIV.7: persist action log (fire-and-forget)
    try:
        create_entity_for_tenant(
            "research_ethics_action_logs",
            {
                "review_id": str(created.get("id", "")),
                "action_type": "submission_created",
                "pi_id": pi_id,
                "review_type": review_type,
                "tenant_id": tenant_id,
            },
            tenant_id,
        )
    except Exception:  # noqa: BLE001
        pass

    risk_level = str(payload.get("risk_level") or "").strip().lower()
    if risk_level in _HIGH_RISK_LEVELS:
        _ensure_ethics_alert_record(created, tenant_id)
        # XXXIV.7: high-risk alert event (fire-and-forget)
        try:
            EventPublisher().publish_event(
                "research_ethics.review.high_risk_flagged",
                {"tenant_id": tenant_id, "review_id": str(created.get("id", "")),
                 "risk_level": risk_level},
            )
        except Exception:  # noqa: BLE001
            pass

    return created


def _ensure_ethics_alert_record(review: dict[str, object], tenant_id: int) -> None:
    review_id = str(review.get("id") or review.get("review_code") or "unknown")
    existing = list_entities_for_tenant("ethics_alert_records", tenant_id)
    for row in existing:
        if str(row.get("source_entity_id") or "") == review_id and str(
            row.get("integration_source") or ""
        ) == "research_ethics_high_risk":
            return

    create_entity_for_tenant(
        "ethics_alert_records",
        {
            "review_id": review_id,
            "review_code": review.get("review_code"),
            "risk_level": review.get("risk_level"),
            "integration_source": "research_ethics_high_risk",
            "source_entity_id": review_id,
            "tenant_id": tenant_id,
        },
        tenant_id,
    )


def _check_pi_eligibility_for_approval(
    *,
    tenant_id: int,
    review_id: int,
    review_data: dict[str, object],
    target_status: str,
) -> None:
    """Block approval when PI is not active in faculty + contracts.

    This guard is fail-closed: query failures raise DomainValidationError.
    """
    normalized_status = str(target_status or "").strip().lower()
    if normalized_status not in _APPROVAL_TRANSITION_STATUSES:
        return

    pi_id = str(review_data.get("principal_investigator_id") or "").strip()
    if not pi_id:
        raise DomainValidationError(
            f"Cannot approve ethics review {review_id}: principal_investigator_id is missing"
        )

    try:
        faculty_rows = list_entities_for_tenant("faculty", tenant_id)
    except Exception as exc:  # pragma: no cover - exercised by monkeypatch tests
        raise DomainValidationError(
            "Cannot approve ethics review: faculty lookup failed. "
            "PI eligibility must be verified before approval"
        ) from exc

    pi_faculty = next(
        (r for r in faculty_rows if str(r.get("faculty_id") or "").strip() == pi_id),
        None,
    )
    if pi_faculty is None:
        raise DomainValidationError(
            f"Cannot approve ethics review {review_id}: PI '{pi_id}' is not found in faculty registry"
        )

    pi_faculty_status = str(pi_faculty.get("status") or "").strip().lower()
    if pi_faculty_status not in _REQUIRED_PI_FACULTY_STATUSES:
        raise DomainValidationError(
            f"Cannot approve ethics review {review_id}: PI '{pi_id}' has faculty status "
            f"'{pi_faculty_status}', required={sorted(_REQUIRED_PI_FACULTY_STATUSES)}"
        )

    try:
        contract_rows = list_entities_for_tenant("faculty_contracts", tenant_id)
    except Exception as exc:  # pragma: no cover - exercised by monkeypatch tests
        raise DomainValidationError(
            "Cannot approve ethics review: faculty_contracts lookup failed. "
            "PI contract eligibility must be verified before approval"
        ) from exc

    pi_contract_statuses = {
        str(c.get("status") or "").strip().lower()
        for c in contract_rows
        if str(c.get("faculty_id") or "").strip() == pi_id
    }
    if not pi_contract_statuses:
        raise DomainValidationError(
            f"Cannot approve ethics review {review_id}: PI '{pi_id}' has no faculty_contracts records"
        )

    if not (pi_contract_statuses & _REQUIRED_PI_CONTRACT_STATUSES):
        raise DomainValidationError(
            f"Cannot approve ethics review {review_id}: PI '{pi_id}' contract statuses "
            f"{sorted(pi_contract_statuses)} do not satisfy required "
            f"{sorted(_REQUIRED_PI_CONTRACT_STATUSES)}"
        )


def update_ethics_review_status(
    tenant_id: int,
    review_id: int,
    request: EthicsReviewStatusUpdateSchema,
) -> dict[str, object]:
    rows = list_entities_for_tenant("ethics_reviews", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == review_id), None)
    if existing is None:
        raise ValueError(f"Ethics review {review_id} not found for tenant {tenant_id}")
    current_status = str(existing.get("status") or "pending")
    allowed = RE_ALLOWED_TRANSITIONS.get(current_status, [])
    if request.status not in allowed:
        raise ValueError(
            f"Transition from '{current_status}' to '{request.status}' is not allowed. "
            f"Allowed: {allowed}"
        )

    _check_pi_eligibility_for_approval(
        tenant_id=tenant_id,
        review_id=review_id,
        review_data=existing,
        target_status=request.status,
    )

    updated = update_entity_for_tenant(
        "ethics_reviews",
        review_id,
        {**existing, "status": request.status, **({
            "notes": request.notes
        } if request.notes is not None else {})},
        tenant_id,
    )

    # XXXIV.7: fire approved/rejected lifecycle events (fire-and-forget)
    _fire_review_lifecycle_event(updated, request.status, tenant_id)

    return updated


def _fire_review_lifecycle_event(
    review: dict[str, object],
    new_status: str,
    tenant_id: int,
) -> None:
    """XXXIV.7: fire approved/rejected event fire-and-forget."""
    status = str(new_status or "").strip().lower()
    if status == "approved":
        event_type = "research_ethics.review.approved"
    elif status in {"rejected", "denied"}:
        event_type = "research_ethics.review.rejected"
    else:
        return
    try:
        EventPublisher().publish_event(
            event_type,
            {"tenant_id": tenant_id, "review_id": str(review.get("id", "")),
             "status": status},
        )
    except Exception:  # noqa: BLE001
        pass


def get_research_ethics_brain_context(tenant_id: int) -> dict[str, object]:
    rows = list_entities_for_tenant("ethics_reviews", tenant_id)

    total = len(rows)
    pending = 0
    approved = 0
    rejected = 0
    high_risk = 0

    for row in rows:
        st = str(row.get("status") or "").strip().lower()
        if st == "pending":
            pending += 1
        elif st == "approved":
            approved += 1
        elif st in {"rejected", "denied"}:
            rejected += 1
        rl = str(row.get("risk_level") or "").strip().lower()
        if rl in {"high", "critical"}:
            high_risk += 1

    if high_risk > 0 or rejected > 0:
        compliance_status = "at_risk"
    elif pending > 0:
        compliance_status = "under_review"
    else:
        compliance_status = "compliant"

    return {
        "module": "research_ethics",
        "tenant_id": tenant_id,
        "total_reviews": total,
        "pending_reviews": pending,
        "approved_reviews": approved,
        "rejected_reviews": rejected,
        "high_risk_reviews": high_risk,
        "compliance_status": compliance_status,
    }
