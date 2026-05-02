"""Academic Integrity service layer with business logic and workflow enforcement."""

from typing import Optional
from datetime import datetime, timezone
import uuid
from app.modules.academic_integrity.schemas import (
    IntegrityCaseCreateSchema,
    IntegrityCaseStatusUpdateSchema,
    IntegrityCaseStatus,
)


_INTEGRITY_CASE_STATUS_MAX_ACTIVE: dict[str, int] = {
    "flagged": 400,
    "under_review": 250,
    "escalated": 120,
    "resolved": 2000,
    "dismissed": 1500,
}
_ACTIVE_INTEGRITY_CASE_STATUSES = frozenset({"flagged", "under_review", "escalated"})
_INTEGRITY_ESCALATION_RISK_STATUSES = frozenset({"escalated"})


class _InMemoryEntityAdapter:
    """Minimal adapter that proxies AcademicIntegrityService to in-memory tenant store."""

    async def list_entities(self, *, entity_type: str, tenant_id: str, **kwargs):  # type: ignore[no-untyped-def]
        from app.modules.university_core.tenant_entity_api import list_entities_for_tenant
        try:
            tenant_id_int = int(tenant_id)
        except (TypeError, ValueError):
            tenant_id_int = 1
        try:
            items = list_entities_for_tenant(entity_type, tenant_id_int)
        except (ValueError, KeyError):
            items = []
        return items, len(items)

    async def create_entity(self, *, entity_type: str, entity_data: dict, tenant_id: str, **kwargs):  # type: ignore[no-untyped-def]
        from app.modules.university_core.tenant_entity_api import create_entity_for_tenant
        try:
            tenant_id_int = int(tenant_id)
        except (TypeError, ValueError):
            tenant_id_int = 1
        return create_entity_for_tenant(entity_type, entity_data, tenant_id_int)

    async def get_entity(self, *, entity_type: str, entity_id: str, tenant_id: str, **kwargs):  # type: ignore[no-untyped-def]
        from app.modules.university_core.tenant_entity_api import list_entities_for_tenant
        try:
            tenant_id_int = int(tenant_id)
        except (TypeError, ValueError):
            tenant_id_int = 1
        for item in list_entities_for_tenant(entity_type, tenant_id_int):
            if str(item.get("id")) == str(entity_id):
                return item
        return None

    async def update_entity(self, *, entity_type: str, entity_id: str, entity_data: dict, tenant_id: str, **kwargs):  # type: ignore[no-untyped-def]
        return entity_data


def get_default_entity_service() -> "_InMemoryEntityAdapter":
    """Return default in-memory entity adapter for dependency injection."""
    return _InMemoryEntityAdapter()


# State machine: allowed transitions between statuses
_ALLOWED_TRANSITIONS = {
    IntegrityCaseStatus.FLAGGED: [
        IntegrityCaseStatus.UNDER_REVIEW,
        IntegrityCaseStatus.DISMISSED,
    ],
    IntegrityCaseStatus.UNDER_REVIEW: [
        IntegrityCaseStatus.RESOLVED,
        IntegrityCaseStatus.ESCALATED,
        IntegrityCaseStatus.DISMISSED,
    ],
    IntegrityCaseStatus.ESCALATED: [
        IntegrityCaseStatus.RESOLVED,
        IntegrityCaseStatus.DISMISSED,
    ],
    IntegrityCaseStatus.RESOLVED: [],  # Terminal state
    IntegrityCaseStatus.DISMISSED: [],  # Terminal state
}

# Statuses that require resolution_notes before transition is permitted
_CLOSURE_REQUIRES_NOTES = frozenset({
    IntegrityCaseStatus.RESOLVED,
    IntegrityCaseStatus.DISMISSED,
})

# Statuses that require recommended_action before transition is permitted
_ESCALATION_REQUIRES_ACTION = frozenset({
    IntegrityCaseStatus.ESCALATED,
})


class AcademicIntegrityService:
    """Service for managing academic integrity cases."""

    def __init__(self, tenant_entity_service):
        """Initialize service with tenant entity service."""
        self.tenant_entity_service = tenant_entity_service

    async def list_integrity_cases(
        self,
        tenant_id: str,
        page: int = 1,
        page_size: int = 20,
        student_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """
        List integrity cases with optional filters.

        Args:
            tenant_id: Tenant UUID
            page: Page number (1-indexed)
            page_size: Results per page
            student_id: Filter by student
            status: Filter by case status

        Returns:
            Dict with cases list, total count, pagination info
        """
        # Build filters
        filters = {"tenant_id": tenant_id}
        if student_id:
            filters["student_id"] = student_id
        if status:
            filters["status"] = status

        # Get cases from persistence layer
        cases, total = await self.tenant_entity_service.list_entities(
            tenant_id=tenant_id,
            entity_type="integrity_case",
            filters=filters,
            page=page,
            page_size=page_size,
        )

        return {
            "cases": cases,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def create_integrity_case(
        self, tenant_id: str, actor: str, payload: IntegrityCaseCreateSchema
    ) -> dict:
        """
        Create a new integrity case.

        Args:
            tenant_id: Tenant UUID
            actor: User UUID creating the case
            payload: Case creation data

        Returns:
            Created case record
        """
        existing_cases, _ = await self.tenant_entity_service.list_entities(
            tenant_id=tenant_id,
            entity_type="integrity_case",
            filters={"tenant_id": tenant_id},
            page=1,
            page_size=2000,
        )
        active_case_count = sum(
            1
            for c in existing_cases
            if str(c.get("status") or "").strip().lower() in _ACTIVE_INTEGRITY_CASE_STATUSES
        )
        requested_status = IntegrityCaseStatus.FLAGGED.value
        case_cap = _INTEGRITY_CASE_STATUS_MAX_ACTIVE.get(requested_status, 400)
        if active_case_count >= case_cap:
            raise ValueError("academic_integrity_case active cap reached")

        # Create case entity
        case_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        case = {
            "id": case_id,
            "student_id": payload.student_id,
            "course_id": payload.course_id,
            "assignment_id": payload.assignment_id,
            "case_type": payload.case_type.value,
            "description": payload.description,
            "evidence_url": payload.evidence_url,
            "priority": payload.priority,
            "status": IntegrityCaseStatus.FLAGGED.value,
            "resolution_notes": None,
            "recommended_action": None,
            "created_at": now,
            "updated_at": now,
            "created_by": actor,
            "tenant_id": tenant_id,
        }

        # Persist case
        await self.tenant_entity_service.create_entity(
            tenant_id=tenant_id,
            entity_type="integrity_case",
            entity_data=case,
        )

        return case

    async def update_integrity_case_status(
        self,
        tenant_id: str,
        case_id: str,
        actor: str,
        payload: IntegrityCaseStatusUpdateSchema,
    ) -> dict:
        """
        Update integrity case status with workflow validation.

        Args:
            tenant_id: Tenant UUID
            case_id: Case UUID
            actor: User UUID performing update
            payload: Status update data

        Returns:
            Updated case record

        Raises:
            ValueError: If transition not allowed
        """
        # Get current case
        case = await self.tenant_entity_service.get_entity(
            tenant_id=tenant_id,
            entity_type="integrity_case",
            entity_id=case_id,
        )

        if not case:
            raise ValueError(f"Case {case_id} not found")

        # Validate transition
        current_status = IntegrityCaseStatus(case["status"])
        new_status = payload.status

        allowed = _ALLOWED_TRANSITIONS.get(current_status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from {current_status.value} to {new_status.value}"
            )

        # Enforce documentation requirements before state transition
        if new_status in _CLOSURE_REQUIRES_NOTES:
            if not (payload.resolution_notes and payload.resolution_notes.strip()):
                raise ValueError(
                    f"Cannot transition integrity case to '{new_status.value}' without "
                    f"resolution_notes: all case closures require documented rationale "
                    f"for institutional accountability and accreditation compliance."
                )
        if new_status in _ESCALATION_REQUIRES_ACTION:
            if not (payload.recommended_action and payload.recommended_action.strip()):
                raise ValueError(
                    "Cannot escalate integrity case without recommended_action: "
                    "escalation requires a documented action recommendation."
                )

        # Update case
        case["status"] = new_status.value
        case["resolution_notes"] = payload.resolution_notes
        case["recommended_action"] = payload.recommended_action
        case["updated_at"] = datetime.now(timezone.utc)

        # Persist update
        await self.tenant_entity_service.update_entity(
            tenant_id=tenant_id,
            entity_type="integrity_case",
            entity_id=case_id,
            entity_data=case,
        )

        if new_status.value in _INTEGRITY_ESCALATION_RISK_STATUSES:
            await self._ensure_integrity_escalation_alert_record(tenant_id=tenant_id, case=case)
            from app.platform.events.publisher import EventPublisher
            EventPublisher().publish_event(
                tenant_id=tenant_id,
                event_type="academic_integrity.case.escalated",
                aggregate_type="integrity_case",
                aggregate_id=case_id,
                payload_json={
                    "case_id": case_id,
                    "case_type": case.get("case_type"),
                    "student_id": case.get("student_id"),
                    "source_module": "academic_integrity",
                },
            )

        return case

    async def _ensure_integrity_escalation_alert_record(self, tenant_id: str, case: dict) -> None:
        from app.modules.university_core.tenant_entity_service import list_entities_for_tenant, create_entity_for_tenant
        try:
            tid = int(tenant_id)
        except (ValueError, TypeError):
            tid = 0
        existing_alerts = list_entities_for_tenant("integrity_escalation_alerts", tid)
        case_id = str(case.get("id") or "")
        already_exists = any(
            str(r.get("integration_source") or "") == "academic_integrity_escalation_queue"
            and str(r.get("source_entity_id") or "") == case_id
            for r in existing_alerts
        )
        if already_exists:
            return
        create_entity_for_tenant(
            "integrity_escalation_alerts",
            {
                "case_id": case_id,
                "alert_status": "open",
                "integration_source": "academic_integrity_escalation_queue",
                "source_entity_id": case_id,
                "tenant_id": str(tenant_id),
            },
            tid,
        )

    async def get_integrity_case(self, tenant_id: str, case_id: str) -> dict:
        """Get single integrity case by ID."""
        case = await self.tenant_entity_service.get_entity(
            tenant_id=tenant_id,
            entity_type="integrity_case",
            entity_id=case_id,
        )

        if not case:
            raise ValueError(f"Case {case_id} not found")

        return case

    async def get_brain_context(self, tenant_id: str) -> dict:
        """Return aggregated brain-context snapshot for Brain Core context builder."""
        result = await self.list_integrity_cases(tenant_id=tenant_id, page=1, page_size=200)
        cases = result.get("cases", [])
        total = result.get("total", 0)
        escalated = sum(1 for c in cases if c.get("status") == "escalated")
        under_review = sum(1 for c in cases if c.get("status") == "under_review")
        return {
            "snapshot_type": "brain_context",
            "module": "academic_integrity",
            "tenant_id": tenant_id,
            "total_cases": total,
            "escalated_cases": escalated,
            "under_review_cases": under_review,
            "open_cases": under_review,
            "integrity_risk_level": "high" if escalated > 0 else ("medium" if under_review > 2 else "low"),
        }
