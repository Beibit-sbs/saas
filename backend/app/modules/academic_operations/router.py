"""FastAPI router for Academic Operations backend foundation."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.module_helpers.router_errors import integrity_error_to_http, permission_error_to_http, tenant_not_found_to_http, validation_error_to_http
from app.core.module_helpers.service_validation import DomainValidationError, OptimisticLockConflictError, TenantResourceNotFoundError
from app.core.tenant import get_current_tenant
from app.modules.academic_operations import permissions, service
from app.modules.academic_operations.dependencies import get_academic_operations_db, require_academic_operations_tenant
from app.modules.academic_operations.schemas import (
    AcademicGroupCreateRequest,
    AcademicGroupListResponse,
    AcademicGroupResponse,
    AcademicGroupUpdateRequest,
    AcademicOperationsAuditEventResponse,
    AcademicOperationsDashboardResponse,
    AcademicOperationsEvidenceCreateRequest,
    AcademicOperationsEvidenceListResponse,
    AcademicOperationsEvidenceResponse,
    AcademicOperationsHealthResponse,
    AcademicOperationsMatrixSummaryResponse,
    AdvisorTutorAssignmentCreateRequest,
    AdvisorTutorAssignmentListResponse,
    AdvisorTutorAssignmentResponse,
    AdvisorTutorAssignmentUpdateRequest,
    CanonicalModuleBridgeCreateRequest,
    CanonicalModuleBridgeListResponse,
    CanonicalModuleBridgeResponse,
    CohortCreateRequest,
    CohortListResponse,
    CohortResponse,
    CohortUpdateRequest,
    CourseRegistrationMetadataCreateRequest,
    CourseRegistrationMetadataListResponse,
    CourseRegistrationMetadataResponse,
    DocumentWorkflowBridgeResponse,
    ExecutiveGovernanceBridgeResponse,
    GradebookMetadataCreateRequest,
    GradebookMetadataListResponse,
    GradebookMetadataResponse,
    GradebookMetadataUpdateRequest,
    QualityAccreditationBridgeResponse,
    RetakePlanCreateRequest,
    RetakePlanListResponse,
    RetakePlanResponse,
    RetakePlanUpdateRequest,
    StudentLifecycleBridgeResponse,
    SummerSemesterTermCreateRequest,
    SummerSemesterTermListResponse,
    SummerSemesterTermResponse,
    SummerSemesterTermUpdateRequest,
)
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/academic-operations", tags=["academic-operations"])

_Tenant = Annotated[int, Depends(require_academic_operations_tenant)]
_Actor = Annotated[str, Depends(get_actor)]
_DB = Annotated[Session, Depends(get_academic_operations_db)]


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _handle(exc: Exception) -> None:
    if isinstance(exc, PermissionError):
        raise permission_error_to_http(exc)
    if isinstance(exc, TenantResourceNotFoundError):
        raise tenant_not_found_to_http(exc)
    if isinstance(exc, (DomainValidationError, ValueError)):
        raise validation_error_to_http(exc)
    if isinstance(exc, (IntegrityError, OptimisticLockConflictError)):
        raise integrity_error_to_http(exc)
    raise exc


def _resp(obj: Any, schema_cls):
    data = obj.__dict__.copy()
    if "limitations_json" in data:
        data["limitations"] = list(data.pop("limitations_json") or [])
    if "metadata_json" in data:
        data["metadata"] = dict(data.pop("metadata_json") or {})
    if "summary_json" in data:
        data["summary"] = dict(data.pop("summary_json") or {})
    if "payload_json" in data:
        data["payload"] = dict(data.pop("payload_json") or {})
    return schema_cls.model_validate(data)


@router.get("/health", response_model=AcademicOperationsHealthResponse)
def get_health(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.HEALTH_READ))], tenant: _Tenant, db: _DB) -> AcademicOperationsHealthResponse:
    try:
        return service.get_academic_operations_health_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/dashboard", response_model=AcademicOperationsDashboardResponse)
def get_dashboard(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.DASHBOARD_READ))], tenant: _Tenant, db: _DB) -> AcademicOperationsDashboardResponse:
    try:
        return service.get_academic_operations_dashboard_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/matrix-summary", response_model=AcademicOperationsMatrixSummaryResponse)
def get_matrix_summary(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.OVERVIEW_READ))], tenant: _Tenant, db: _DB) -> AcademicOperationsMatrixSummaryResponse:
    try:
        return service.get_academic_operations_matrix_summary_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/canonical-reuse-summary", response_model=dict)
def get_canonical_reuse_summary(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.CANONICAL_BRIDGE_READ))], tenant: _Tenant, db: _DB) -> dict[str, Any]:
    try:
        return service.get_canonical_reuse_summary_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/academic-groups", response_model=AcademicGroupListResponse)
def list_academic_groups(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.ACADEMIC_GROUPS_READ))], tenant: _Tenant, db: _DB) -> AcademicGroupListResponse:
    try:
        return AcademicGroupListResponse(items=[_resp(item, AcademicGroupResponse) for item in service.list_academic_groups_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/academic-groups", response_model=AcademicGroupResponse, status_code=status.HTTP_201_CREATED)
def create_academic_group(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.ACADEMIC_GROUPS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> AcademicGroupResponse:
    try:
        body = _parse_payload(AcademicGroupCreateRequest, payload)
        return _resp(service.create_academic_group_service(db, tenant, actor, body), AcademicGroupResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/academic-groups/{group_id}", response_model=AcademicGroupResponse)
def get_academic_group(group_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.ACADEMIC_GROUPS_READ))], tenant: _Tenant, db: _DB) -> AcademicGroupResponse:
    try:
        return _resp(service.get_academic_group_service(db, tenant, group_id), AcademicGroupResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/academic-groups/{group_id}", response_model=AcademicGroupResponse)
def update_academic_group(group_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.ACADEMIC_GROUPS_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> AcademicGroupResponse:
    try:
        body = _parse_payload(AcademicGroupUpdateRequest, payload)
        return _resp(service.update_academic_group_service(db, tenant, actor, group_id, body), AcademicGroupResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/cohorts", response_model=CohortListResponse)
def list_cohorts(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.COHORTS_READ))], tenant: _Tenant, db: _DB) -> CohortListResponse:
    try:
        return CohortListResponse(items=[_resp(item, CohortResponse) for item in service.list_cohorts_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/cohorts", response_model=CohortResponse, status_code=status.HTTP_201_CREATED)
def create_cohort(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.COHORTS_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> CohortResponse:
    try:
        body = _parse_payload(CohortCreateRequest, payload)
        return _resp(service.create_cohort_service(db, tenant, actor, body), CohortResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/cohorts/{cohort_id}", response_model=CohortResponse)
def get_cohort(cohort_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.COHORTS_READ))], tenant: _Tenant, db: _DB) -> CohortResponse:
    try:
        return _resp(service.get_cohort_service(db, tenant, cohort_id), CohortResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/cohorts/{cohort_id}", response_model=CohortResponse)
def update_cohort(cohort_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.COHORTS_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> CohortResponse:
    try:
        body = _parse_payload(CohortUpdateRequest, payload)
        return _resp(service.update_cohort_service(db, tenant, actor, cohort_id, body), CohortResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/course-registration", response_model=CourseRegistrationMetadataListResponse)
def list_course_registration(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.CANONICAL_BRIDGE_READ))], tenant: _Tenant, db: _DB) -> CourseRegistrationMetadataListResponse:
    try:
        return CourseRegistrationMetadataListResponse(items=[_resp(item, CourseRegistrationMetadataResponse) for item in service.list_course_registration_metadata_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/course-registration", response_model=CourseRegistrationMetadataResponse, status_code=status.HTTP_201_CREATED)
def create_course_registration(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.CANONICAL_BRIDGE_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> CourseRegistrationMetadataResponse:
    try:
        body = _parse_payload(CourseRegistrationMetadataCreateRequest, payload)
        return _resp(service.create_course_registration_metadata_service(db, tenant, actor, body), CourseRegistrationMetadataResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/gradebook-metadata", response_model=GradebookMetadataListResponse)
def list_gradebook_metadata(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.GRADEBOOK_METADATA_READ))], tenant: _Tenant, db: _DB) -> GradebookMetadataListResponse:
    try:
        return GradebookMetadataListResponse(items=[_resp(item, GradebookMetadataResponse) for item in service.list_gradebook_metadata_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/gradebook-metadata", response_model=GradebookMetadataResponse, status_code=status.HTTP_201_CREATED)
def create_gradebook_metadata(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.GRADEBOOK_METADATA_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> GradebookMetadataResponse:
    try:
        body = _parse_payload(GradebookMetadataCreateRequest, payload)
        return _resp(service.create_gradebook_metadata_service(db, tenant, actor, body), GradebookMetadataResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/gradebook-metadata/{gradebook_id}", response_model=GradebookMetadataResponse)
def get_gradebook_metadata(gradebook_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.GRADEBOOK_METADATA_READ))], tenant: _Tenant, db: _DB) -> GradebookMetadataResponse:
    try:
        return _resp(service.get_gradebook_metadata_service(db, tenant, gradebook_id), GradebookMetadataResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/gradebook-metadata/{gradebook_id}", response_model=GradebookMetadataResponse)
def update_gradebook_metadata(gradebook_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.GRADEBOOK_METADATA_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> GradebookMetadataResponse:
    try:
        body = _parse_payload(GradebookMetadataUpdateRequest, payload)
        return _resp(service.update_gradebook_metadata_service(db, tenant, actor, gradebook_id, body), GradebookMetadataResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/retakes", response_model=RetakePlanListResponse)
def list_retakes(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.RETAKE_MANAGEMENT_READ))], tenant: _Tenant, db: _DB) -> RetakePlanListResponse:
    try:
        return RetakePlanListResponse(items=[_resp(item, RetakePlanResponse) for item in service.list_retake_plans_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/retakes", response_model=RetakePlanResponse, status_code=status.HTTP_201_CREATED)
def create_retake(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.RETAKE_MANAGEMENT_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> RetakePlanResponse:
    try:
        body = _parse_payload(RetakePlanCreateRequest, payload)
        return _resp(service.create_retake_plan_service(db, tenant, actor, body), RetakePlanResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/retakes/{retake_id}", response_model=RetakePlanResponse)
def get_retake(retake_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.RETAKE_MANAGEMENT_READ))], tenant: _Tenant, db: _DB) -> RetakePlanResponse:
    try:
        return _resp(service.get_retake_plan_service(db, tenant, retake_id), RetakePlanResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/retakes/{retake_id}", response_model=RetakePlanResponse)
def update_retake(retake_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.RETAKE_MANAGEMENT_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> RetakePlanResponse:
    try:
        body = _parse_payload(RetakePlanUpdateRequest, payload)
        return _resp(service.update_retake_plan_service(db, tenant, actor, retake_id, body), RetakePlanResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/summer-semesters", response_model=SummerSemesterTermListResponse)
def list_summer_semesters(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.SUMMER_SEMESTER_READ))], tenant: _Tenant, db: _DB) -> SummerSemesterTermListResponse:
    try:
        return SummerSemesterTermListResponse(items=[_resp(item, SummerSemesterTermResponse) for item in service.list_summer_semester_terms_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/summer-semesters", response_model=SummerSemesterTermResponse, status_code=status.HTTP_201_CREATED)
def create_summer_semester(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.SUMMER_SEMESTER_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> SummerSemesterTermResponse:
    try:
        body = _parse_payload(SummerSemesterTermCreateRequest, payload)
        return _resp(service.create_summer_semester_term_service(db, tenant, actor, body), SummerSemesterTermResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/summer-semesters/{term_id}", response_model=SummerSemesterTermResponse)
def get_summer_semester(term_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.SUMMER_SEMESTER_READ))], tenant: _Tenant, db: _DB) -> SummerSemesterTermResponse:
    try:
        return _resp(service.get_summer_semester_term_service(db, tenant, term_id), SummerSemesterTermResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/summer-semesters/{term_id}", response_model=SummerSemesterTermResponse)
def update_summer_semester(term_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.SUMMER_SEMESTER_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> SummerSemesterTermResponse:
    try:
        body = _parse_payload(SummerSemesterTermUpdateRequest, payload)
        return _resp(service.update_summer_semester_term_service(db, tenant, actor, term_id, body), SummerSemesterTermResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/advisor-tutor", response_model=AdvisorTutorAssignmentListResponse)
def list_advisor_tutor(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.ADVISOR_TUTOR_READ))], tenant: _Tenant, db: _DB) -> AdvisorTutorAssignmentListResponse:
    try:
        return AdvisorTutorAssignmentListResponse(items=[_resp(item, AdvisorTutorAssignmentResponse) for item in service.list_advisor_tutor_assignments_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/advisor-tutor", response_model=AdvisorTutorAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_advisor_tutor(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.ADVISOR_TUTOR_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> AdvisorTutorAssignmentResponse:
    try:
        body = _parse_payload(AdvisorTutorAssignmentCreateRequest, payload)
        return _resp(service.create_advisor_tutor_assignment_service(db, tenant, actor, body), AdvisorTutorAssignmentResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/advisor-tutor/{assignment_id}", response_model=AdvisorTutorAssignmentResponse)
def get_advisor_tutor(assignment_id: int, actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.ADVISOR_TUTOR_READ))], tenant: _Tenant, db: _DB) -> AdvisorTutorAssignmentResponse:
    try:
        return _resp(service.get_advisor_tutor_assignment_service(db, tenant, assignment_id), AdvisorTutorAssignmentResponse)
    except Exception as exc:
        _handle(exc)


@router.patch("/advisor-tutor/{assignment_id}", response_model=AdvisorTutorAssignmentResponse)
def update_advisor_tutor(assignment_id: int, payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.ADVISOR_TUTOR_UPDATE))] = None, tenant: _Tenant = None, db: _DB = None) -> AdvisorTutorAssignmentResponse:
    try:
        body = _parse_payload(AdvisorTutorAssignmentUpdateRequest, payload)
        return _resp(service.update_advisor_tutor_assignment_service(db, tenant, actor, assignment_id, body), AdvisorTutorAssignmentResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/bridges", response_model=CanonicalModuleBridgeListResponse)
def list_bridges(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.CANONICAL_BRIDGE_READ))], tenant: _Tenant, db: _DB) -> CanonicalModuleBridgeListResponse:
    try:
        return CanonicalModuleBridgeListResponse(items=[_resp(item, CanonicalModuleBridgeResponse) for item in service.list_canonical_module_bridges_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/bridges", response_model=CanonicalModuleBridgeResponse, status_code=status.HTTP_201_CREATED)
def create_bridge(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.CANONICAL_BRIDGE_CREATE))] = None, tenant: _Tenant = None, db: _DB = None) -> CanonicalModuleBridgeResponse:
    try:
        body = _parse_payload(CanonicalModuleBridgeCreateRequest, payload)
        return _resp(service.create_canonical_module_bridge_service(db, tenant, actor, body), CanonicalModuleBridgeResponse)
    except Exception as exc:
        _handle(exc)


@router.get("/bridges/canonical", response_model=dict)
def get_bridge_canonical(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.CANONICAL_BRIDGE_READ))], tenant: _Tenant, db: _DB) -> dict[str, Any]:
    try:
        return service.get_canonical_reuse_summary_service(db, tenant)
    except Exception as exc:
        _handle(exc)


@router.get("/bridges/student-lifecycle", response_model=list[StudentLifecycleBridgeResponse])
def get_bridge_student_lifecycle(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.STUDENT_LIFECYCLE_BRIDGE_READ))], tenant: _Tenant, db: _DB) -> list[StudentLifecycleBridgeResponse]:
    try:
        return [_resp(item, StudentLifecycleBridgeResponse) for item in service.repository.get_student_lifecycle_bridge_summary(db, tenant)]
    except Exception as exc:
        _handle(exc)


@router.get("/bridges/document-workflow", response_model=list[DocumentWorkflowBridgeResponse])
def get_bridge_document_workflow(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.DOCUMENT_WORKFLOW_BRIDGE_READ))], tenant: _Tenant, db: _DB) -> list[DocumentWorkflowBridgeResponse]:
    try:
        return [_resp(item, DocumentWorkflowBridgeResponse) for item in service.repository.get_document_workflow_bridge_summary(db, tenant)]
    except Exception as exc:
        _handle(exc)


@router.get("/bridges/executive-governance", response_model=list[ExecutiveGovernanceBridgeResponse])
def get_bridge_executive_governance(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.EXECUTIVE_GOVERNANCE_BRIDGE_READ))], tenant: _Tenant, db: _DB) -> list[ExecutiveGovernanceBridgeResponse]:
    try:
        return [_resp(item, ExecutiveGovernanceBridgeResponse) for item in service.repository.get_executive_governance_bridge_summary(db, tenant)]
    except Exception as exc:
        _handle(exc)


@router.get("/bridges/quality-accreditation", response_model=list[QualityAccreditationBridgeResponse])
def get_bridge_quality_accreditation(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.QUALITY_ACCREDITATION_BRIDGE_READ))], tenant: _Tenant, db: _DB) -> list[QualityAccreditationBridgeResponse]:
    try:
        return [_resp(item, QualityAccreditationBridgeResponse) for item in service.repository.get_quality_accreditation_bridge_summary(db, tenant)]
    except Exception as exc:
        _handle(exc)


@router.get("/audit", response_model=list[AcademicOperationsAuditEventResponse])
def list_audit(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.AUDIT_READ))], tenant: _Tenant, db: _DB) -> list[AcademicOperationsAuditEventResponse]:
    try:
        return [_resp(item, AcademicOperationsAuditEventResponse) for item in service.list_audit_events_service(db, tenant)]
    except Exception as exc:
        _handle(exc)


@router.get("/evidence", response_model=AcademicOperationsEvidenceListResponse)
def list_evidence(actor: _Actor, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_READ))], tenant: _Tenant, db: _DB) -> AcademicOperationsEvidenceListResponse:
    try:
        return AcademicOperationsEvidenceListResponse(items=[_resp(item, AcademicOperationsEvidenceResponse) for item in service.list_evidence_metadata_service(db, tenant)])
    except Exception as exc:
        _handle(exc)


@router.post("/evidence", response_model=AcademicOperationsEvidenceResponse, status_code=status.HTTP_201_CREATED)
def create_evidence(payload: dict[str, Any] = Body(...), actor: _Actor = None, _: Annotated[None, Depends(permission_dependency(permissions.EVIDENCE_ATTACH))] = None, tenant: _Tenant = None, db: _DB = None) -> AcademicOperationsEvidenceResponse:
    try:
        body = _parse_payload(AcademicOperationsEvidenceCreateRequest, payload)
        return _resp(service.attach_evidence_metadata_service(db, tenant, actor, body), AcademicOperationsEvidenceResponse)
    except Exception as exc:
        _handle(exc)