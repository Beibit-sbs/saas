from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.module_helpers.service_validation import DomainValidationError

from app.modules.academic_records.schemas import (
    AcademicRecordConsistencyReportSchema,
    RecordCreatePayload,
    RecordDeleteResponse,
    RecordItemResponse,
    RecordListResponse,
    RecordUpdatePayload,
)
from app.modules.academic_records.service import (
    create_record,
    delete_record,
    get_academic_records_brain_context,
    get_record_consistency_report,
    list_records,
    update_record,
)
from app.core.tenant import get_current_tenant
from app.modules.audit.service import log_admin_action
from app.modules.rbac.security import get_actor, permission_dependency

router = APIRouter(prefix="/api/admin/university/records", tags=["university-records"])


@router.get("", response_model=RecordListResponse)
def get_records(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.records.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> RecordListResponse:
    return {"records": list_records(int(tenant["id"]))}


@router.get("/consistency", response_model=AcademicRecordConsistencyReportSchema)
def get_record_consistency_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.records.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> AcademicRecordConsistencyReportSchema:
    return AcademicRecordConsistencyReportSchema.model_validate(
        get_record_consistency_report(int(tenant["id"]))
    )


@router.post("", response_model=RecordItemResponse)
def create_record_endpoint(
    payload: RecordCreatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.records.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> RecordItemResponse:
    try:
        record = create_record(payload.model_dump(), int(tenant["id"]), actor=actor)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.records.create",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_academic_records",
        result="success",
        metadata={"id": record["id"], "student_id": record["student_id"], "course_id": record["course_id"]},
    )
    return {"record": record}


@router.put("/{record_id}", response_model=RecordItemResponse)
def update_record_endpoint(
    record_id: int,
    payload: RecordUpdatePayload,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.records.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> RecordItemResponse:
    try:
        record = update_record(record_id, payload.model_dump(), int(tenant["id"]), actor=actor)
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.records.update",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_academic_records",
        result="success",
        metadata={"id": record["id"], "student_id": record["student_id"], "course_id": record["course_id"]},
    )
    return {"record": record}


@router.delete("/{record_id}", response_model=RecordDeleteResponse)
def delete_record_endpoint(
    record_id: int,
    request: Request,
    actor: Annotated[str, Depends(get_actor)],
    _: Annotated[None, Depends(permission_dependency("admin.records.write"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> RecordDeleteResponse:
    try:
        record = delete_record(record_id, int(tenant["id"]), actor=actor)
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    log_admin_action(
        actor=actor,
        tenant_id=int(tenant["id"]),
        action="university.records.delete",
        path=str(request.url.path),
        client_ip=request.client.host if request.client else "unknown",
        correlation_id=getattr(request.state, "request_id", None),
        entity="university_academic_records",
        result="success",
        metadata={"id": record["id"], "student_id": record["student_id"], "course_id": record["course_id"]},
    )
    return {"deleted": True, "record": record}


@router.get("/brain-context", response_model=dict, tags=["university-records", "brain-core"])
def get_academic_records_brain_context_endpoint(
    _: Annotated[str, Depends(get_actor)],
    __: Annotated[None, Depends(permission_dependency("admin.records.read"))],
    tenant: Annotated[dict, Depends(get_current_tenant)],
) -> dict:
    """Return aggregated brain-context snapshot for Brain Core context builder.

    Used by Brain Core to enrich decisions with academic records signals:
    total records, inconsistency count, records risk level.
    """
    return get_academic_records_brain_context(int(tenant["id"]))
