"""Campus / Facilities / Housing / Transport Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CfhtSafetyFlags(BaseModel):
    live_iot_enabled: Literal[False] = False
    live_gps_tracking_enabled: Literal[False] = False
    building_automation_enabled: Literal[False] = False
    access_control_enforcement_enabled: Literal[False] = False
    safety_certification_claimed: Literal[False] = False
    maintenance_completion_guaranteed: Literal[False] = False
    automatic_housing_decision_enabled: Literal[False] = False
    automatic_eviction_enabled: Literal[False] = False
    automatic_student_staff_sanction_enabled: Literal[False] = False
    autonomous_dispatch_enabled: Literal[False] = False
    external_provider_sync_enabled: Literal[False] = False
    production_facilities_claimed: Literal[False] = False
    sales_ready_claimed: Literal[False] = False
    gcc_ready_claimed: Literal[False] = False
    l5_l6_claimed: Literal[False] = False
    human_review_required: Literal[True] = True
    incomplete_data: bool = True
    limitations: list[str] = Field(default_factory=list)


class CfhtRecord(BaseModel):
    id: int | None = None
    tenant_id: int
    status: str
    reference_key: str | None = None
    title: str | None = None
    source_module: str | None = None
    source_entity_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    incomplete_data: bool = True
    created_by: str | None = None
    updated_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CfhtResponseBase(CfhtSafetyFlags):
    tenant_id: int
    module: str = "campus_facilities_housing_transport"
    contract_version: str = "A-044.2.RUNTIME"
    runtime_mode: str = "METADATA_READINESS_EVIDENCE_CONTROL_VISIBILITY_HUMAN_REVIEW_ONLY"
    data_source: str = "computed_from_campus_facilities_housing_transport_records"


class CfhtCollectionResponse(CfhtResponseBase):
    records: list[CfhtRecord] = Field(default_factory=list)


class CfhtOverviewResponse(CfhtResponseBase):
    selected_vertical: str
    table_count: int
    route_count: int
    permission_count: int
    families: list[str] = Field(default_factory=list)


class CfhtDashboardResponse(CfhtResponseBase):
    summary: dict[str, Any] = Field(default_factory=dict)


class CfhtCampusResponse(CfhtCollectionResponse):
    pass


class CfhtFacilitiesResponse(CfhtCollectionResponse):
    pass


class CfhtBuildingsResponse(CfhtCollectionResponse):
    pass


class CfhtFloorsResponse(CfhtCollectionResponse):
    pass


class CfhtRoomsResponse(CfhtCollectionResponse):
    pass


class CfhtRoomTypesResponse(CfhtCollectionResponse):
    pass


class CfhtAvailabilityResponse(CfhtCollectionResponse):
    pass


class CfhtOccupancyResponse(CfhtCollectionResponse):
    pass


class CfhtDormitoriesResponse(CfhtCollectionResponse):
    pass


class CfhtHousingUnitsResponse(CfhtCollectionResponse):
    pass


class CfhtHousingRequestsResponse(CfhtCollectionResponse):
    pass


class CfhtMaintenanceResponse(CfhtCollectionResponse):
    pass


class CfhtServiceRequestsResponse(CfhtCollectionResponse):
    pass


class CfhtWorkOrdersResponse(CfhtCollectionResponse):
    pass


class CfhtTransportRoutesResponse(CfhtCollectionResponse):
    pass


class CfhtTransportVehiclesResponse(CfhtCollectionResponse):
    pass


class CfhtTransportSchedulesResponse(CfhtCollectionResponse):
    pass


class CfhtResponsibleUnitsResponse(CfhtCollectionResponse):
    pass


class CfhtSafetyReadinessResponse(CfhtCollectionResponse):
    pass


class CfhtBridgeResponse(CfhtCollectionResponse):
    pass


class CfhtAuditEvidenceResponse(CfhtCollectionResponse):
    pass


class CfhtLimitationsResponse(CfhtCollectionResponse):
    pass


class CfhtMetadataContractResponse(CfhtResponseBase):
    api_prefix: str
    db_prefix: str
    table_count: int
    route_count: int
    permission_count: int
    permission_namespace: str
    module_files: list[str] = Field(default_factory=list)


class CfhtHealthResponse(CfhtResponseBase):
    status: str
    expected_table_count: int
    expected_permission_count: int
    expected_route_count: int


class CfhtMutationResponse(CfhtResponseBase):
    record: CfhtRecord


class CfhtMetadataWriteRequest(BaseModel):
    reference_key: str = Field(min_length=1, max_length=128)
    title: str | None = Field(default=None, max_length=255)
    status: str = Field(default="draft", max_length=64)
    source_module: str | None = Field(default=None, max_length=128)
    source_entity_id: str | None = Field(default=None, max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    incomplete_data: bool = True


class CfhtEvidenceWriteRequest(CfhtMetadataWriteRequest):
    evidence_type: str = Field(default="metadata_only", max_length=128)
    reference_uri: str | None = Field(default=None, max_length=512)
