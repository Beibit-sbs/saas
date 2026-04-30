"""Phase X-X1: Faculty performance KPI service."""
from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.core.module_helpers.service_validation import DomainValidationError
from app.modules.audit.service import log_admin_action
from app.modules.faculty_performance_kpis.schemas import (
    FacultyKpiCreateSchema,
    FacultyKpiSchema,
    FacultyKpiStatus,
    FacultyKpiStatusUpdateSchema,
)
from app.modules.university_core.tenant_entity_api import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)
from app.platform.events.publisher import EventPublisher

# W38: cap on active KPIs per kpi_period
_KPI_PERIOD_MAX_ACTIVE: dict[str, int] = {
    "Q1": 50,
    "Q2": 50,
    "Q3": 50,
    "Q4": 50,
    "annual": 30,
    "semester": 40,
    "other": 60,
}

_ACTIVE_KPI_STATUSES: frozenset[str] = frozenset({"satisfactory", "needs_improvement", "on_probation"})

# W38: low overall score threshold requiring an alert record
_LOW_SCORE_THRESHOLD: float = 50.0

# W63: risk statuses for low performance alerts
_PERFORMANCE_RISK_STATUSES: frozenset[str] = frozenset({"needs_improvement", "on_probation"})

# ---------------------------------------------------------------------------
# W103: Faculty contract guard — KPI may only be created for faculty with
# an active employment contract. KPI records for non-employed faculty
# generate phantom Brain Core performance signals.
# ---------------------------------------------------------------------------
_KPI_ACTIVE_CONTRACT_STATUSES: frozenset[str] = frozenset({"active"})


def _check_faculty_has_active_contract_for_kpi(
    *,
    tenant_id: int,
    faculty_id: str,
    kpi_period: str,
) -> None:
    """W103: Cross-entity guard — faculty_performance_kpis × faculty_contracts.

    A KPI record may only be created for a faculty member who has an active
    employment contract. Creating a KPI for a non-contracted faculty member:
      - Generates Brain Core warning signals (faculty_performance.kpi.warning_detected)
        about a person not in active employment
      - May trigger automated HR decisions (probation, review) for non-employees
      - Corrupts faculty performance analytics and accreditation metrics
      - Creates a ghost record that inflates or deflates departmental KPI averages

    FAIL-CLOSED: if the faculty_contracts lookup fails (any exception), the KPI
    creation is BLOCKED. An unknown contract state must default to ineligible.
    """
    try:
        all_contracts = list_entities_for_tenant("faculty_contracts", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Faculty KPI creation blocked for faculty_id='{faculty_id}' "
            f"(kpi_period='{kpi_period}'): faculty_contracts lookup failed — {exc}. "
            "Cannot verify active employment status."
        ) from exc

    faculty_contracts = [
        row for row in all_contracts
        if str(row.get("faculty_id") or "").strip() == str(faculty_id).strip()
    ]

    if not faculty_contracts:
        raise DomainValidationError(
            f"Faculty KPI creation blocked for faculty_id='{faculty_id}' "
            f"(kpi_period='{kpi_period}'): no contract records found. "
            "An active employment contract is required to record faculty performance KPIs."
        )

    has_active = any(
        str(row.get("status") or "").strip().lower() in _KPI_ACTIVE_CONTRACT_STATUSES
        for row in faculty_contracts
    )
    if not has_active:
        found_statuses = list(
            {str(row.get("status") or "unknown") for row in faculty_contracts}
        )
        raise DomainValidationError(
            f"Faculty KPI creation blocked for faculty_id='{faculty_id}' "
            f"(kpi_period='{kpi_period}'): no active contract found. "
            f"Contract statuses found: {found_statuses}. "
            "KPI records require an active faculty employment contract."
        )



def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="faculty_performance_kpis",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def list_faculty_kpis(
    tenant_id: int,
    department_id: str | None = None,
    status: FacultyKpiStatus | None = None,
) -> list[FacultyKpiSchema]:
    rows = list_entities_for_tenant("faculty_performance_kpis", tenant_id)
    if department_id:
        dept = department_id.strip()
        rows = [r for r in rows if str(r.get("department_id") or "").strip() == dept]
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    return [FacultyKpiSchema.model_validate(r) for r in rows]


def get_faculty_kpi(tenant_id: int, kpi_id: int) -> FacultyKpiSchema | None:
    rows = list_entities_for_tenant("faculty_performance_kpis", tenant_id)
    row = next((r for r in rows if int(r.get("id") or 0) == kpi_id), None)
    if row is None:
        return None
    return FacultyKpiSchema.model_validate(row)


def create_faculty_kpi(
    tenant_id: int,
    request: FacultyKpiCreateSchema,
    actor: str,
) -> FacultyKpiSchema:
    period = str(request.kpi_period or "other").strip()
    cap = _KPI_PERIOD_MAX_ACTIVE.get(period, _KPI_PERIOD_MAX_ACTIVE["other"])
    existing = list_entities_for_tenant("faculty_performance_kpis", tenant_id)
    active_count = sum(
        1
        for k in existing
        if str(k.get("kpi_period") or "").strip() == period
        and str(k.get("status") or "") in _ACTIVE_KPI_STATUSES
    )
    if active_count >= cap:
        raise ValueError(
            f"Active KPI cap ({cap}) reached for kpi_period '{period}'"
        )

    # W103: Active contract guard — KPI may only be created for actively employed faculty
    _check_faculty_has_active_contract_for_kpi(
        tenant_id=tenant_id,
        faculty_id=request.faculty_id.strip(),
        kpi_period=period,
    )

    created = create_entity_for_tenant(
        "faculty_performance_kpis",
        {
            "faculty_id": request.faculty_id.strip(),
            "name": request.name.strip(),
            "department_id": request.department_id.strip(),
            "kpi_period": request.kpi_period.strip(),
            "teaching_score": float(request.teaching_score),
            "research_score": float(request.research_score),
            "service_score": float(request.service_score),
            "overall_score": float(request.overall_score),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("faculty_performance_kpis", "kpi", "create"),
        path="/internal/faculty-performance-kpis",
        metadata={"resource_id": str(created.get("id")), "faculty_id": request.faculty_id},
        tenant_id=tenant_id,
    )

    # Brain signal: warn when overall_score is below threshold
    try:
        score = float(created.get("overall_score") or 0)
    except (TypeError, ValueError):
        score = 0.0

    if score < 60.0:
        record_id = str(created.get("id") or "unknown")
        EventPublisher().publish_event(
            tenant_id=tenant_id,
            event_type="faculty_performance.kpi.warning_detected",
            aggregate_type="faculty_performance_kpis",
            aggregate_id=record_id,
            payload_json={
                "faculty_id": request.faculty_id,
                "overall_score": score,
                "kpi_period": request.kpi_period,
            },
        )

    # W38: side-effect alert for critically low overall scores
    if score < _LOW_SCORE_THRESHOLD:
        _ensure_low_performance_alert_record(
            tenant_id=tenant_id,
            kpi_id=int(created.get("id") or 0),
            kpi_data={
                "faculty_id": request.faculty_id,
                "kpi_period": request.kpi_period,
                "overall_score": score,
            },
        )

    return FacultyKpiSchema.model_validate(created)


def _ensure_low_performance_alert_record(
    tenant_id: int,
    kpi_id: int,
    kpi_data: dict,
) -> None:
    """Idempotent: create a faculty_kpi_low_performance_alerts entry for critically low scores."""
    existing = list_entities_for_tenant("faculty_kpi_low_performance_alerts", tenant_id)
    for rec in existing:
        if (
            str(rec.get("integration_source")) == "faculty_kpi_alert"
            and str(rec.get("source_entity_id")) == str(kpi_id)
        ):
            return  # already exists
    create_entity_for_tenant(
        "faculty_kpi_low_performance_alerts",
        {
            "kpi_id": kpi_id,
            "faculty_id": str(kpi_data.get("faculty_id") or ""),
            "kpi_period": str(kpi_data.get("kpi_period") or ""),
            "overall_score": float(kpi_data.get("overall_score") or 0.0),
            "alert_status": "open",
            "integration_source": "faculty_kpi_alert",
            "source_entity_id": str(kpi_id),
            "tenant_id": tenant_id,
        },
        tenant_id,
    )
    EventPublisher().publish_event(
        tenant_id=tenant_id,
        event_type="campus.faculty_performance.low_score_alert_detected",
        aggregate_type="faculty_performance_kpis",
        aggregate_id=str(kpi_id),
        payload_json={
            "kpi_id": kpi_id,
            "faculty_id": str(kpi_data.get("faculty_id") or ""),
            "kpi_period": str(kpi_data.get("kpi_period") or ""),
            "overall_score": float(kpi_data.get("overall_score") or 0.0),
            "source_module": "faculty_performance_kpis",
            "source_entity_type": "faculty_performance_kpis",
            "source_entity_id": str(kpi_id),
        },
    )


def update_faculty_kpi_status(
    tenant_id: int,
    kpi_id: int,
    request: FacultyKpiStatusUpdateSchema,
    actor: str,
) -> FacultyKpiSchema | None:
    rows = list_entities_for_tenant("faculty_performance_kpis", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == kpi_id), None)
    if existing is None:
        return None

    updated = update_entity_for_tenant(
        "faculty_performance_kpis",
        kpi_id,
        {**existing, "status": request.status},
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("faculty_performance_kpis", "kpi", "status_update"),
        path=f"/internal/faculty-performance-kpis/{kpi_id}/status",
        metadata={"resource_id": str(kpi_id), "new_status": request.status},
        tenant_id=tenant_id,
    )

    return FacultyKpiSchema.model_validate(updated)
