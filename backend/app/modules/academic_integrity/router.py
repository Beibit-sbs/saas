"""Academic Integrity FastAPI router."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.core.tenant import get_current_tenant
from app.modules.rbac.security import permission_dependency
from app.modules.academic_integrity.service import AcademicIntegrityService
from app.modules.academic_integrity.schemas import (
    IntegrityCaseCreateSchema,
    IntegrityCaseStatusUpdateSchema,
    IntegrityCaseListResponseSchema,
    IntegrityCaseDetailResponseSchema,
    IntegrityCaseRecordSchema,
)

router = APIRouter(prefix="/api/admin/academic-integrity", tags=["academic-integrity"])


def get_service(tenant_service) -> AcademicIntegrityService:
    """Dependency for service instance."""
    return AcademicIntegrityService(tenant_entity_service=tenant_service)


@router.get(
    "/cases",
    response_model=IntegrityCaseListResponseSchema,
    dependencies=[Depends(permission_dependency("admin.records.read"))],
)
async def list_integrity_cases(
    tenant=Depends(get_current_tenant),
    service: AcademicIntegrityService = Depends(get_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    student_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """
    List academic integrity cases.

    Requires ACADEMIC_RECORDS_READ permission.
    """
    result = await service.list_integrity_cases(
        tenant_id=tenant.id,
        page=page,
        page_size=page_size,
        student_id=student_id,
        status=status,
    )

    # Convert case dicts to schemas
    cases = [IntegrityCaseRecordSchema(**case) for case in result["cases"]]

    return IntegrityCaseListResponseSchema(
        cases=cases,
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.post(
    "/cases",
    response_model=IntegrityCaseDetailResponseSchema,
    dependencies=[Depends(permission_dependency("admin.records.write"))],
)
async def create_integrity_case(
    payload: IntegrityCaseCreateSchema,
    tenant=Depends(get_current_tenant),
    actor=Depends(lambda: "admin@example.com"),  # Will be replaced by auth in production
    service: AcademicIntegrityService = Depends(get_service),
):
    """
    Create a new academic integrity case.

    Requires ACADEMIC_RECORDS_WRITE permission.
    """
    case = await service.create_integrity_case(
        tenant_id=tenant.id,
        actor=actor,
        payload=payload,
    )

    case_record = IntegrityCaseRecordSchema(**case)
    return IntegrityCaseDetailResponseSchema(case=case_record)


@router.patch(
    "/cases/{case_id}/status",
    response_model=IntegrityCaseDetailResponseSchema,
    dependencies=[Depends(permission_dependency("admin.records.write"))],
)
async def update_integrity_case_status(
    case_id: str,
    payload: IntegrityCaseStatusUpdateSchema,
    tenant=Depends(get_current_tenant),
    actor=Depends(lambda: "admin@example.com"),  # Will be replaced by auth in production
    service: AcademicIntegrityService = Depends(get_service),
):
    """
    Update integrity case status with workflow enforcement.

    Requires ACADEMIC_RECORDS_WRITE permission.
    """
    case = await service.update_integrity_case_status(
        tenant_id=tenant.id,
        case_id=case_id,
        actor=actor,
        payload=payload,
    )

    case_record = IntegrityCaseRecordSchema(**case)
    return IntegrityCaseDetailResponseSchema(case=case_record)


@router.get(
    "/cases/{case_id}",
    response_model=IntegrityCaseDetailResponseSchema,
    dependencies=[Depends(permission_dependency("admin.records.read"))],
)
async def get_integrity_case(
    case_id: str,
    tenant=Depends(get_current_tenant),
    service: AcademicIntegrityService = Depends(get_service),
):
    """
    Get single academic integrity case details.

    Requires ACADEMIC_RECORDS_READ permission.
    """
    case = await service.get_integrity_case(
        tenant_id=tenant.id,
        case_id=case_id,
    )

    case_record = IntegrityCaseRecordSchema(**case)
    return IntegrityCaseDetailResponseSchema(case=case_record)
