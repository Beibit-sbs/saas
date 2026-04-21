from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.career_services.schemas import (
    CareerOpportunityCreateSchema,
    CareerOpportunitySchema,
    CareerOpportunityStatus,
    CareerOpportunityStatusUpdateSchema,
)
from app.modules.university_core.tenant_entity_service import (
    create_entity_for_tenant,
    list_entities_for_tenant,
    update_entity_for_tenant,
)


_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_review", "closed", "archived"},
    "in_review": {"closed", "archived", "open"},
    "closed": {"archived"},
    "archived": set(),
}


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="career_opportunity",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def list_career_opportunities(
    tenant_id: int,
    status: CareerOpportunityStatus | None = None,
    student_id: int | None = None,
) -> list[CareerOpportunitySchema]:
    rows = list_entities_for_tenant("career_opportunities", tenant_id)
    if status is not None:
        rows = [r for r in rows if str(r.get("status") or "") == status]
    if student_id is not None:
        rows = [r for r in rows if int(r.get("student_id") or 0) == student_id]
    return [CareerOpportunitySchema.model_validate(r) for r in rows]


def create_career_opportunity(
    tenant_id: int,
    request: CareerOpportunityCreateSchema,
    actor: str,
) -> CareerOpportunitySchema:
    created = create_entity_for_tenant(
        "career_opportunities",
        {
            "student_id": int(request.student_id),
            "title": request.title.strip(),
            "company": request.company.strip(),
            "opportunity_type": request.opportunity_type,
            "status": "open",
            "owner_id": (request.owner_id or "career-team").strip() or "career-team",
            "start_date": (request.start_date or "unscheduled").strip() or "unscheduled",
            "notes": (request.notes or "n/a").strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("career_services", "opportunity", "create"),
        path="/internal/career-services/opportunities",
        metadata={
            "resource_id": str(created.get("id")),
            "student_id": str(request.student_id),
            "company": request.company,
        },
        tenant_id=tenant_id,
    )
    return CareerOpportunitySchema.model_validate(created)


def update_career_opportunity_status(
    tenant_id: int,
    opportunity_id: int,
    request: CareerOpportunityStatusUpdateSchema,
    actor: str,
) -> CareerOpportunitySchema:
    rows = list_entities_for_tenant("career_opportunities", tenant_id)
    existing = next((r for r in rows if int(r.get("id") or 0) == opportunity_id), None)
    if existing is None:
        raise ValueError(f"opportunity {opportunity_id} not found")

    current_status = str(existing.get("status") or "open")
    if request.status not in _ALLOWED_TRANSITIONS.get(current_status, set()):
        raise ValueError(f"transition from '{current_status}' to '{request.status}' is not allowed")

    updated = update_entity_for_tenant(
        "career_opportunities",
        opportunity_id,
        {
            "student_id": int(existing.get("student_id") or 0),
            "title": str(existing.get("title") or "Untitled"),
            "company": str(existing.get("company") or "Unknown"),
            "opportunity_type": str(existing.get("opportunity_type") or "internship"),
            "status": request.status,
            "owner_id": str(existing.get("owner_id") or "career-team"),
            "start_date": str(existing.get("start_date") or "unscheduled"),
            "notes": (request.notes or str(existing.get("notes") or "n/a")).strip() or "n/a",
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("career_services", "opportunity", "status_update"),
        path=f"/internal/career-services/opportunities/{opportunity_id}/status",
        metadata={
            "resource_id": str(opportunity_id),
            "old_status": current_status,
            "new_status": request.status,
        },
        tenant_id=tenant_id,
    )
    return CareerOpportunitySchema.model_validate(updated)
