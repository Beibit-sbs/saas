from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.faculty.schemas import (
    FacultyCapacityUpdatePayload,
    FacultyContractCreatePayload,
    FacultyContractItemResponse,
    FacultyContractListResponse,
    FacultyContractStatusUpdatePayload,
    FacultyConsistencyReportSchema,
    FacultyCreatePayload,
    FacultyDeleteResponse,
    FacultyItemResponse,
    FacultyListResponse,
    FacultyWorkloadItemResponse,
    FacultyWorkloadListResponse,
    FacultyUpdatePayload,
    TeachingQualityCreatePayload,
    TeachingQualityItemResponse,
    TeachingQualityListResponse,
    ProctoringCreatePayload,
    ProctoringItemResponse,
    ProctoringListResponse,
    OfficeHoursCreatePayload,
    OfficeHoursItemResponse,
    OfficeHoursListResponse,
)
from app.modules.faculty.service import (
    create_faculty_contract,
    create_faculty_member,
    create_teaching_quality_record,
    delete_faculty_member,
    get_department_workload_summary,
    get_faculty_brain_context,
    get_faculty_consistency_report,
    get_faculty_workload,
    list_faculty,
    list_faculty_contracts,
    list_teaching_quality,
    list_workload_alerts,
    update_faculty_contract_status,
    update_faculty_capacity,
    update_faculty_member,
    create_proctoring_record,
    get_proctoring_brain_context,
    list_proctoring_records,
    create_office_hours_record,
    get_office_hours_brain_context,
    list_office_hours,
)
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/org/faculty", tags=["org-faculty"])


@router.get("", response_model=FacultyListResponse)
def get_faculty(
    request: Request,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyListResponse:
    _ = request
    return {"faculty": list_faculty(int(tenant["id"]))}


@router.get("/consistency", response_model=FacultyConsistencyReportSchema)
def get_faculty_consistency_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyConsistencyReportSchema:
    return FacultyConsistencyReportSchema.model_validate(
        get_faculty_consistency_report(int(tenant["id"]))
    )


@router.post("", response_model=FacultyItemResponse)
def create_faculty_endpoint(
    payload: FacultyCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyItemResponse:
    try:
        faculty_entry = create_faculty_member(payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.faculty.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_faculty",
        result="success",
        metadata={"id": faculty_entry["id"], "faculty_id": faculty_entry["faculty_id"]},
    )
    return {"faculty": faculty_entry}


@router.put("/{faculty_row_id}", response_model=FacultyItemResponse)
def update_faculty_endpoint(
    faculty_row_id: int,
    payload: FacultyUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyItemResponse:
    try:
        faculty_entry = update_faculty_member(faculty_row_id, payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.faculty.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_faculty",
        result="success",
        metadata={"id": faculty_entry["id"], "faculty_id": faculty_entry["faculty_id"]},
    )
    return {"faculty": faculty_entry}


@router.delete("/{faculty_row_id}", response_model=FacultyDeleteResponse)
def delete_faculty_endpoint(
    faculty_row_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyDeleteResponse:
    try:
        faculty_entry = delete_faculty_member(faculty_row_id, int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.faculty.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_faculty",
        result="success",
        metadata={"id": faculty_entry["id"], "faculty_id": faculty_entry["faculty_id"]},
    )
    return {"deleted": True, "faculty": faculty_entry}


@router.get("/contracts", response_model=FacultyContractListResponse)
def get_faculty_contracts_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    faculty_id: str | None = None,
    status: str | None = None,
) -> FacultyContractListResponse:
    contracts = list_faculty_contracts(int(tenant["id"]), faculty_id=faculty_id, status=status)
    return {"contracts": contracts}


@router.post("/contracts", response_model=FacultyContractItemResponse)
def create_faculty_contract_endpoint(
    payload: FacultyContractCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyContractItemResponse:
    try:
        contract = create_faculty_contract(payload.model_dump(), int(tenant["id"]))
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.faculty_contract.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_faculty_contracts",
        result="success",
        metadata={"id": contract["id"], "faculty_id": contract["faculty_id"]},
    )
    return {"contract": contract}


@router.patch("/contracts/{contract_id}/status", response_model=FacultyContractItemResponse)
def update_faculty_contract_status_endpoint(
    contract_id: int,
    payload: FacultyContractStatusUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyContractItemResponse:
    try:
        contract = update_faculty_contract_status(
            contract_id=contract_id,
            status=payload.status,
            tenant_id=int(tenant["id"]),
            notes=payload.notes,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.faculty_contract.update_status",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_faculty_contracts",
        result="success",
        metadata={"id": contract_id, "status": payload.status},
    )
    return {"contract": contract}


@router.get("/{faculty_id}/workload", response_model=FacultyWorkloadItemResponse)
def get_faculty_workload_endpoint(
    faculty_id: str,
    term_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyWorkloadItemResponse:
    try:
        workload = get_faculty_workload(int(tenant["id"]), faculty_id, term_id)
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc
    return {"workload": workload}


@router.get("/workload/department/{department}", response_model=FacultyWorkloadListResponse)
def get_department_workload_summary_endpoint(
    department: str,
    term_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyWorkloadListResponse:
    workloads = get_department_workload_summary(int(tenant["id"]), department, term_id)
    return {"workloads": workloads}


@router.get("/workload/alerts", response_model=FacultyWorkloadListResponse)
def get_workload_alerts_endpoint(
    term_id: int,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyWorkloadListResponse:
    workloads = list_workload_alerts(int(tenant["id"]), term_id)
    return {"workloads": workloads}


@router.get("/teaching-quality", response_model=TeachingQualityListResponse)
def list_teaching_quality_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    faculty_id: str | None = None,
) -> TeachingQualityListResponse:
    records = list_teaching_quality(int(tenant["id"]), faculty_id=faculty_id)
    return {"records": records}


@router.post("/teaching-quality", response_model=TeachingQualityItemResponse)
def create_teaching_quality_endpoint(
    payload: TeachingQualityCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> TeachingQualityItemResponse:
    record = create_teaching_quality_record(payload.model_dump(), int(tenant["id"]))
    return {"record": record}


@router.get("/brain-context")
def get_faculty_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    return get_faculty_brain_context(int(tenant["id"]))


@router.put("/{faculty_id}/capacity", response_model=FacultyItemResponse)
def update_faculty_capacity_endpoint(
    faculty_id: str,
    payload: FacultyCapacityUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> FacultyItemResponse:
    try:
        faculty_entry = update_faculty_capacity(
            int(tenant["id"]),
            faculty_id,
            payload.max_credit_hours,
            payload.fte_ratio,
        )
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.faculty.update_capacity",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_faculty",
        result="success",
        metadata={"faculty_id": faculty_id},
    )
    return {"faculty": faculty_entry}


# ---------------------------------------------------------------------------
# Proctoring endpoints (Phase IV-IV2)
# ---------------------------------------------------------------------------


@router.get("/proctoring", response_model=ProctoringListResponse)
def list_proctoring_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    faculty_id: str | None = None,
    exam_id: str | None = None,
) -> ProctoringListResponse:
    records = list_proctoring_records(int(tenant["id"]), faculty_id=faculty_id, exam_id=exam_id)
    return {"records": records}


@router.post("/proctoring", response_model=ProctoringItemResponse)
def create_proctoring_endpoint(
    payload: ProctoringCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> ProctoringItemResponse:
    record = create_proctoring_record(payload.model_dump(), int(tenant["id"]))
    return {"record": record}


@router.get("/proctoring/brain-context")
def get_proctoring_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    return get_proctoring_brain_context(int(tenant["id"]))


# ---------------------------------------------------------------------------
# Office hours endpoints (Phase IV-IV3)
# ---------------------------------------------------------------------------


@router.get("/office-hours", response_model=OfficeHoursListResponse)
def list_office_hours_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
    faculty_id: str | None = None,
) -> OfficeHoursListResponse:
    records = list_office_hours(int(tenant["id"]), faculty_id=faculty_id)
    return {"records": records}


@router.post("/office-hours", response_model=OfficeHoursItemResponse)
def create_office_hours_endpoint(
    payload: OfficeHoursCreatePayload,
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> OfficeHoursItemResponse:
    record = create_office_hours_record(payload.model_dump(), int(tenant["id"]))
    return {"record": record}


@router.get("/office-hours/brain-context")
def get_office_hours_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.faculty.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    return get_office_hours_brain_context(int(tenant["id"]))
