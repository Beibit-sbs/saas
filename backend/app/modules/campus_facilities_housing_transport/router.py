"""FastAPI router for Campus / Facilities / Housing / Transport runtime."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.module_helpers.service_validation import DomainValidationError, TenantResourceNotFoundError
from app.modules.campus_facilities_housing_transport import permissions, schemas, service
from app.modules.campus_facilities_housing_transport.dependencies import get_campus_facilities_db, require_campus_facilities_tenant
from app.modules.rbac.security import get_actor, permission_dependency


router = APIRouter(prefix="/api/admin/campus-facilities", tags=["campus-facilities"])


class ErrorDetailResponse(BaseModel):
    detail: Any


def _parse_payload(schema_cls: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return schema_cls.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.errors()) from exc


def _handle(exc: Exception) -> None:
    if isinstance(exc, TenantResourceNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, (DomainValidationError, ValueError)):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


def _register_get(path: str, permission: str, handler: Callable[[Session, int], Any], response_model) -> None:
    def endpoint(
        actor: str = Depends(get_actor),
        permitted: None = Depends(permission_dependency(permission)),
        tenant: int = Depends(require_campus_facilities_tenant),
        db: Session = Depends(get_campus_facilities_db),
    ):
        try:
            del actor, permitted
            return handler(db, tenant)
        except Exception as exc:
            _handle(exc)

    endpoint.__name__ = f"get_{path.strip('/').replace('/', '_').replace('-', '_') or 'root'}"
    router.add_api_route(
        path,
        endpoint,
        methods=["GET"],
        response_model=response_model,
        responses={400: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
    )


def _register_post(path: str, permission: str, handler: Callable[[Session, int, str, Any], Any], request_model) -> None:
    def endpoint(
        payload: dict[str, Any] = Body(...),
        actor: str = Depends(get_actor),
        permitted: None = Depends(permission_dependency(permission)),
        tenant: int = Depends(require_campus_facilities_tenant),
        db: Session = Depends(get_campus_facilities_db),
    ):
        try:
            del permitted
            body = _parse_payload(request_model, payload)
            return handler(db, tenant, actor, body)
        except Exception as exc:
            _handle(exc)

    endpoint.__name__ = f"post_{path.strip('/').replace('/', '_').replace('-', '_')}"
    router.add_api_route(
        path,
        endpoint,
        methods=["POST"],
        response_model=schemas.CfhtMutationResponse,
        status_code=201,
        responses={400: {"model": ErrorDetailResponse}, 404: {"model": ErrorDetailResponse}},
    )


_register_get("/overview", permissions.OVERVIEW_READ, service.get_overview, schemas.CfhtOverviewResponse)
_register_get("/dashboard", permissions.DASHBOARD_READ, service.get_dashboard, schemas.CfhtDashboardResponse)
_register_get("/campus", permissions.CAMPUS_READ, service.get_campus, schemas.CfhtCampusResponse)
_register_get("/facilities", permissions.FACILITIES_READ, service.get_facilities, schemas.CfhtFacilitiesResponse)
_register_get("/buildings", permissions.BUILDINGS_READ, service.get_buildings, schemas.CfhtBuildingsResponse)
_register_get("/floors", permissions.FLOORS_READ, service.get_floors, schemas.CfhtFloorsResponse)
_register_get("/rooms", permissions.ROOMS_READ, service.get_rooms, schemas.CfhtRoomsResponse)
_register_get("/room-types", permissions.ROOM_TYPES_READ, service.get_room_types, schemas.CfhtRoomTypesResponse)
_register_get("/availability", permissions.AVAILABILITY_READ, service.get_availability, schemas.CfhtAvailabilityResponse)
_register_get("/occupancy", permissions.OCCUPANCY_READ, service.get_occupancy, schemas.CfhtOccupancyResponse)
_register_get("/dormitories", permissions.DORMITORIES_READ, service.get_dormitories, schemas.CfhtDormitoriesResponse)
_register_get("/housing-units", permissions.HOUSING_UNITS_READ, service.get_housing_units, schemas.CfhtHousingUnitsResponse)
_register_get("/housing-requests", permissions.HOUSING_REQUESTS_READ, service.get_housing_requests, schemas.CfhtHousingRequestsResponse)
_register_get("/maintenance", permissions.MAINTENANCE_READ, service.get_maintenance, schemas.CfhtMaintenanceResponse)
_register_get("/service-requests", permissions.SERVICE_REQUESTS_READ, service.get_service_requests, schemas.CfhtServiceRequestsResponse)
_register_get("/work-orders", permissions.WORK_ORDERS_READ, service.get_work_orders, schemas.CfhtWorkOrdersResponse)
_register_get("/transport-routes", permissions.TRANSPORT_ROUTES_READ, service.get_transport_routes, schemas.CfhtTransportRoutesResponse)
_register_get("/transport-vehicles", permissions.TRANSPORT_VEHICLES_READ, service.get_transport_vehicles, schemas.CfhtTransportVehiclesResponse)
_register_get("/transport-schedules", permissions.TRANSPORT_SCHEDULES_READ, service.get_transport_schedules, schemas.CfhtTransportSchedulesResponse)
_register_get("/responsible-units", permissions.RESPONSIBLE_UNITS_READ, service.get_responsible_units, schemas.CfhtResponsibleUnitsResponse)
_register_get("/safety-readiness", permissions.SAFETY_READINESS_READ, service.get_safety_readiness, schemas.CfhtSafetyReadinessResponse)
_register_get("/bridges/access-visitor", permissions.ACCESS_VISITOR_BRIDGE_READ, service.get_access_visitor_bridge, schemas.CfhtBridgeResponse)
_register_get("/bridges/student-services", permissions.STUDENT_SERVICES_BRIDGE_READ, service.get_student_services_bridge, schemas.CfhtBridgeResponse)
_register_get("/bridges/finance-assets", permissions.FINANCE_ASSET_BRIDGE_READ, service.get_finance_asset_bridge, schemas.CfhtBridgeResponse)
_register_get("/bridges/hr-staff", permissions.HR_STAFF_BRIDGE_READ, service.get_hr_staff_bridge, schemas.CfhtBridgeResponse)
_register_get("/audit-evidence", permissions.AUDIT_EVIDENCE_READ, service.get_audit_evidence, schemas.CfhtAuditEvidenceResponse)
_register_get("/limitations", permissions.LIMITATIONS_READ, service.get_limitations, schemas.CfhtLimitationsResponse)
_register_get("/metadata-contract", permissions.METADATA_CONTRACT_READ, service.get_metadata_contract, schemas.CfhtMetadataContractResponse)
_register_get("/health", permissions.METADATA_CONTRACT_READ, service.get_health, schemas.CfhtHealthResponse)
_register_get("/safety-boundaries", permissions.LIMITATIONS_READ, service.get_safety_boundaries, schemas.CfhtLimitationsResponse)

_register_post("/facilities/metadata", permissions.FACILITIES_METADATA, service.create_facility_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/campus/metadata", permissions.FACILITIES_METADATA, service.create_campus_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/buildings/metadata", permissions.BUILDINGS_METADATA, service.create_building_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/floors/metadata", permissions.BUILDINGS_METADATA, service.create_floor_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/rooms/metadata", permissions.ROOMS_METADATA, service.create_room_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/room-types/metadata", permissions.ROOMS_METADATA, service.create_room_type_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/availability/metadata", permissions.AVAILABILITY_METADATA, service.create_availability_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/occupancy/metadata", permissions.OCCUPANCY_METADATA, service.create_occupancy_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/dormitories/metadata", permissions.DORMITORIES_METADATA, service.create_dormitory_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/housing-units/metadata", permissions.HOUSING_REQUESTS_METADATA, service.create_housing_unit_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/housing-requests/metadata", permissions.HOUSING_REQUESTS_METADATA, service.create_housing_request_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/maintenance/metadata", permissions.MAINTENANCE_METADATA, service.create_maintenance_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/service-requests/metadata", permissions.SERVICE_REQUESTS_METADATA, service.create_service_request_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/work-orders/metadata", permissions.WORK_ORDERS_METADATA, service.create_work_order_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/transport/metadata", permissions.TRANSPORT_METADATA, service.create_transport_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/responsible-units/metadata", permissions.RESPONSIBLE_UNITS_METADATA, service.create_responsible_unit_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/safety-readiness/evidence", permissions.SAFETY_READINESS_EVIDENCE, service.create_safety_readiness_evidence, schemas.CfhtEvidenceWriteRequest)
_register_post("/bridges/access-visitor/metadata", permissions.ACCESS_VISITOR_BRIDGE_METADATA, service.create_access_visitor_bridge_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/bridges/student-services/metadata", permissions.STUDENT_SERVICES_BRIDGE_METADATA, service.create_student_services_bridge_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/bridges/finance-assets/metadata", permissions.FINANCE_ASSET_BRIDGE_METADATA, service.create_finance_asset_bridge_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/bridges/hr-staff/metadata", permissions.HR_STAFF_BRIDGE_METADATA, service.create_hr_staff_bridge_metadata, schemas.CfhtMetadataWriteRequest)
_register_post("/limitations/metadata", permissions.LIMITATIONS_METADATA, service.create_limitations_metadata, schemas.CfhtMetadataWriteRequest)

campus_facilities_housing_transport_router = router
