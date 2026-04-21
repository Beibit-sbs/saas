"""Academic Integrity service layer with business logic and workflow enforcement."""

from typing import Optional
from datetime import datetime
import uuid
from app.modules.academic_integrity.schemas import (
    IntegrityCaseCreateSchema,
    IntegrityCaseStatusUpdateSchema,
    IntegrityCaseStatus,
)


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
