"""Service layer for Campus / Facilities / Housing / Transport runtime."""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy.orm import Session

from app.modules.campus_facilities_housing_transport import models, permissions, repository, schemas


def _safety(*, incomplete_data: bool = True, limitations: list[str] | None = None) -> dict[str, Any]:
    return schemas.CfhtSafetyFlags(
        incomplete_data=incomplete_data,
        limitations=list(limitations or []),
    ).model_dump()


def _base(tenant_id: int, *, incomplete_data: bool = True, limitations: list[str] | None = None) -> dict[str, Any]:
    payload = {
        "tenant_id": tenant_id,
        **_safety(incomplete_data=incomplete_data, limitations=limitations),
    }
    return payload


def _collection_response(db: Session, tenant_id: int, family: str, response_model: type[schemas.CfhtCollectionResponse]):
    records = repository.list_family_records(db, tenant_id, family)
    incomplete_data = any(record.get("incomplete_data", True) for record in records) if records else True
    limitations = ["Metadata-only campus facilities visibility.", "Human review required before operational action."]
    return response_model(
        **_base(tenant_id, incomplete_data=incomplete_data, limitations=limitations),
        records=records,
    )


def get_overview(db: Session, tenant_id: int) -> schemas.CfhtOverviewResponse:
    del db
    families = [family for family in models.MODEL_BY_FAMILY if family != "dashboard"]
    return schemas.CfhtOverviewResponse(
        **_base(tenant_id, limitations=["Campus runtime is metadata-only.", "No automated housing, facilities, or transport actions are allowed."]),
        selected_vertical="Campus / Facilities / Housing / Transport Suite",
        table_count=models.EXPECTED_TABLE_COUNT,
        route_count=models.EXPECTED_ROUTE_COUNT,
        permission_count=models.EXPECTED_PERMISSION_COUNT,
        families=families,
    )


def get_dashboard(db: Session, tenant_id: int) -> schemas.CfhtDashboardResponse:
    summary = repository.get_dashboard_inputs(db, tenant_id)
    summary["tracked_families"] = len(summary)
    return schemas.CfhtDashboardResponse(
        **_base(tenant_id, limitations=["Dashboard values are derived from metadata, not live IoT or transport telemetry."]),
        summary=summary,
    )


def get_campus(db: Session, tenant_id: int) -> schemas.CfhtCampusResponse:
    return _collection_response(db, tenant_id, "campus", schemas.CfhtCampusResponse)


def get_facilities(db: Session, tenant_id: int) -> schemas.CfhtFacilitiesResponse:
    return _collection_response(db, tenant_id, "facilities", schemas.CfhtFacilitiesResponse)


def get_buildings(db: Session, tenant_id: int) -> schemas.CfhtBuildingsResponse:
    return _collection_response(db, tenant_id, "buildings", schemas.CfhtBuildingsResponse)


def get_floors(db: Session, tenant_id: int) -> schemas.CfhtFloorsResponse:
    return _collection_response(db, tenant_id, "floors", schemas.CfhtFloorsResponse)


def get_rooms(db: Session, tenant_id: int) -> schemas.CfhtRoomsResponse:
    return _collection_response(db, tenant_id, "rooms", schemas.CfhtRoomsResponse)


def get_room_types(db: Session, tenant_id: int) -> schemas.CfhtRoomTypesResponse:
    return _collection_response(db, tenant_id, "room_types", schemas.CfhtRoomTypesResponse)


def get_availability(db: Session, tenant_id: int) -> schemas.CfhtAvailabilityResponse:
    return _collection_response(db, tenant_id, "availability", schemas.CfhtAvailabilityResponse)


def get_occupancy(db: Session, tenant_id: int) -> schemas.CfhtOccupancyResponse:
    return _collection_response(db, tenant_id, "occupancy", schemas.CfhtOccupancyResponse)


def get_dormitories(db: Session, tenant_id: int) -> schemas.CfhtDormitoriesResponse:
    return _collection_response(db, tenant_id, "dormitories", schemas.CfhtDormitoriesResponse)


def get_housing_units(db: Session, tenant_id: int) -> schemas.CfhtHousingUnitsResponse:
    return _collection_response(db, tenant_id, "housing_units", schemas.CfhtHousingUnitsResponse)


def get_housing_requests(db: Session, tenant_id: int) -> schemas.CfhtHousingRequestsResponse:
    return _collection_response(db, tenant_id, "housing_requests", schemas.CfhtHousingRequestsResponse)


def get_maintenance(db: Session, tenant_id: int) -> schemas.CfhtMaintenanceResponse:
    return _collection_response(db, tenant_id, "maintenance", schemas.CfhtMaintenanceResponse)


def get_service_requests(db: Session, tenant_id: int) -> schemas.CfhtServiceRequestsResponse:
    return _collection_response(db, tenant_id, "service_requests", schemas.CfhtServiceRequestsResponse)


def get_work_orders(db: Session, tenant_id: int) -> schemas.CfhtWorkOrdersResponse:
    return _collection_response(db, tenant_id, "work_orders", schemas.CfhtWorkOrdersResponse)


def get_transport_routes(db: Session, tenant_id: int) -> schemas.CfhtTransportRoutesResponse:
    return _collection_response(db, tenant_id, "transport_routes", schemas.CfhtTransportRoutesResponse)


def get_transport_vehicles(db: Session, tenant_id: int) -> schemas.CfhtTransportVehiclesResponse:
    return _collection_response(db, tenant_id, "transport_vehicles", schemas.CfhtTransportVehiclesResponse)


def get_transport_schedules(db: Session, tenant_id: int) -> schemas.CfhtTransportSchedulesResponse:
    return _collection_response(db, tenant_id, "transport_schedules", schemas.CfhtTransportSchedulesResponse)


def get_responsible_units(db: Session, tenant_id: int) -> schemas.CfhtResponsibleUnitsResponse:
    return _collection_response(db, tenant_id, "responsible_units", schemas.CfhtResponsibleUnitsResponse)


def get_safety_readiness(db: Session, tenant_id: int) -> schemas.CfhtSafetyReadinessResponse:
    return _collection_response(db, tenant_id, "safety_readiness", schemas.CfhtSafetyReadinessResponse)


def get_access_visitor_bridge(db: Session, tenant_id: int) -> schemas.CfhtBridgeResponse:
    return _collection_response(db, tenant_id, "access_visitor_bridge", schemas.CfhtBridgeResponse)


def get_student_services_bridge(db: Session, tenant_id: int) -> schemas.CfhtBridgeResponse:
    return _collection_response(db, tenant_id, "student_services_bridge", schemas.CfhtBridgeResponse)


def get_finance_asset_bridge(db: Session, tenant_id: int) -> schemas.CfhtBridgeResponse:
    return _collection_response(db, tenant_id, "finance_asset_bridge", schemas.CfhtBridgeResponse)


def get_hr_staff_bridge(db: Session, tenant_id: int) -> schemas.CfhtBridgeResponse:
    return _collection_response(db, tenant_id, "hr_staff_bridge", schemas.CfhtBridgeResponse)


def get_audit_evidence(db: Session, tenant_id: int) -> schemas.CfhtAuditEvidenceResponse:
    return _collection_response(db, tenant_id, "audit_evidence", schemas.CfhtAuditEvidenceResponse)


def get_limitations(db: Session, tenant_id: int) -> schemas.CfhtLimitationsResponse:
    return _collection_response(db, tenant_id, "limitations", schemas.CfhtLimitationsResponse)


def get_safety_boundaries(db: Session, tenant_id: int) -> schemas.CfhtLimitationsResponse:
    del db
    records = [
        {
            "tenant_id": tenant_id,
            "status": "active",
            "reference_key": "metadata_only",
            "title": "Metadata-only runtime",
            "metadata": {"boundary": "No live IoT, GPS, building automation, or transport dispatch integrations."},
            "limitations": ["Human review required."],
            "incomplete_data": True,
        },
        {
            "tenant_id": tenant_id,
            "status": "active",
            "reference_key": "no_autonomy",
            "title": "No autonomous decisions",
            "metadata": {"boundary": "No automatic housing allocation, eviction, sanctions, or maintenance closure."},
            "limitations": ["Human review required."],
            "incomplete_data": True,
        },
    ]
    return schemas.CfhtLimitationsResponse(
        **_base(tenant_id, limitations=["Operational actions stay outside this runtime slice."]),
        records=records,
    )


def get_metadata_contract(db: Session, tenant_id: int) -> schemas.CfhtMetadataContractResponse:
    del db
    return schemas.CfhtMetadataContractResponse(
        **_base(tenant_id, limitations=["Contract describes metadata visibility and evidence capture only."]),
        api_prefix=models.API_PREFIX,
        db_prefix=models.DB_PREFIX,
        table_count=models.EXPECTED_TABLE_COUNT,
        route_count=models.EXPECTED_ROUTE_COUNT,
        permission_count=models.EXPECTED_PERMISSION_COUNT,
        permission_namespace=models.PERMISSION_NAMESPACE,
        module_files=[
            "__init__.py",
            "dependencies.py",
            "models.py",
            "permissions.py",
            "repository.py",
            "router.py",
            "schemas.py",
            "service.py",
        ],
    )


def get_health(db: Session, tenant_id: int) -> schemas.CfhtHealthResponse:
    del db
    return schemas.CfhtHealthResponse(
        **_base(tenant_id, limitations=["Health reflects module metadata readiness, not operational campus state."]),
        status="healthy_metadata_only",
        expected_table_count=models.EXPECTED_TABLE_COUNT,
        expected_permission_count=models.EXPECTED_PERMISSION_COUNT,
        expected_route_count=models.EXPECTED_ROUTE_COUNT,
    )


def _create(db: Session, tenant_id: int, actor: str, family: str, payload: Any) -> schemas.CfhtMutationResponse:
    record = repository.create_family_record(db, tenant_id, family, actor, payload)
    return schemas.CfhtMutationResponse(
        **_base(tenant_id, limitations=["Writes store metadata or evidence only."]),
        record=record,
    )


def create_facility_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "facilities", payload)


def create_campus_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "campus", payload)


def create_building_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "buildings", payload)


def create_floor_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "floors", payload)


def create_room_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "rooms", payload)


def create_room_type_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "room_types", payload)


def create_availability_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "availability", payload)


def create_occupancy_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "occupancy", payload)


def create_dormitory_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "dormitories", payload)


def create_housing_unit_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "housing_units", payload)


def create_housing_request_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "housing_requests", payload)


def create_maintenance_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "maintenance", payload)


def create_service_request_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "service_requests", payload)


def create_work_order_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "work_orders", payload)


def create_transport_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "transport_vehicles", payload)


def create_responsible_unit_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "responsible_units", payload)


def create_safety_readiness_evidence(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "safety_readiness", payload)


def create_access_visitor_bridge_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "access_visitor_bridge", payload)


def create_student_services_bridge_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "student_services_bridge", payload)


def create_finance_asset_bridge_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "finance_asset_bridge", payload)


def create_hr_staff_bridge_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "hr_staff_bridge", payload)


def create_limitations_metadata(db: Session, tenant_id: int, actor: str, payload: Any) -> schemas.CfhtMutationResponse:
    return _create(db, tenant_id, actor, "limitations", payload)
