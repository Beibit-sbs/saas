"""Academic Integrity service layer with business logic and workflow enforcement."""

from typing import Optional
from datetime import datetime
import uuid
from app.modules.academic_integrity.schemas import (
    IntegrityCaseCreateSchema,
    IntegrityCaseStatusUpdateSchema,
    IntegrityCaseStatus,
)


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
        # Create case entity
        case_id = str(uuid.uuid4())
        now = datetime.utcnow()

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

        # Update case
        case["status"] = new_status.value
        case["resolution_notes"] = payload.resolution_notes
        case["recommended_action"] = payload.recommended_action
        case["updated_at"] = datetime.utcnow()

        # Persist update
        await self.tenant_entity_service.update_entity(
            tenant_id=tenant_id,
            entity_type="integrity_case",
            entity_id=case_id,
            entity_data=case,
        )

        if new_status == IntegrityCaseStatus.ESCALATED:
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
