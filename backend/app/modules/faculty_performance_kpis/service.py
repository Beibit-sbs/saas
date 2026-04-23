"""Phase X-X1: Faculty performance KPI service."""
from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
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

    return FacultyKpiSchema.model_validate(created)


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
