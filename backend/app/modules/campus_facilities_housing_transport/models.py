"""Campus / Facilities / Housing / Transport SQLAlchemy models."""

from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, DateTime, Index, String, Text, text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from app.core.db import Base


MODULE_NAME = "campus_facilities_housing_transport"
API_PREFIX = "/api/admin/campus-facilities"
DB_PREFIX = "cfht_"
TABLE_PREFIX = DB_PREFIX
PERMISSION_NAMESPACE = "campus_facilities.*"
RUNTIME_MODE = "METADATA_READINESS_EVIDENCE_CONTROL_VISIBILITY_HUMAN_REVIEW_ONLY"
EXPECTED_TABLE_COUNT = 26
EXPECTED_PERMISSION_COUNT = 46
EXPECTED_ROUTE_COUNT = 52
CONTRACT_VERSION = "A-044.2.RUNTIME"
DATA_SOURCE = "computed_from_campus_facilities_housing_transport_records"

LIVE_IOT_ENABLED = False
LIVE_GPS_TRACKING_ENABLED = False
BUILDING_AUTOMATION_ENABLED = False
ACCESS_CONTROL_ENFORCEMENT_ENABLED = False
SAFETY_CERTIFICATION_CLAIMED = False
MAINTENANCE_COMPLETION_GUARANTEED = False
AUTOMATIC_HOUSING_DECISION_ENABLED = False
AUTOMATIC_EVICTION_ENABLED = False
AUTOMATIC_STUDENT_STAFF_SANCTION_ENABLED = False
AUTONOMOUS_DISPATCH_ENABLED = False
EXTERNAL_PROVIDER_SYNC_ENABLED = False
PRODUCTION_FACILITIES_CLAIMED = False
SALES_READY_CLAIMED = False
GCC_READY_CLAIMED = False
L5_L6_CLAIMED = False
HUMAN_REVIEW_REQUIRED = True

TABLE_NAMES = [
    "cfht_campus_profiles",
    "cfht_facility_registry_records",
    "cfht_building_records",
    "cfht_floor_records",
    "cfht_room_records",
    "cfht_room_type_records",
    "cfht_room_availability_snapshots",
    "cfht_occupancy_visibility_records",
    "cfht_dormitory_records",
    "cfht_housing_unit_records",
    "cfht_housing_request_metadata",
    "cfht_maintenance_request_records",
    "cfht_service_request_records",
    "cfht_work_order_metadata",
    "cfht_transport_route_records",
    "cfht_transport_vehicle_metadata",
    "cfht_transport_schedule_metadata",
    "cfht_facility_responsible_unit_records",
    "cfht_campus_safety_readiness_records",
    "cfht_access_visitor_bridge_records",
    "cfht_student_services_bridge_records",
    "cfht_finance_asset_bridge_records",
    "cfht_hr_staff_assignment_bridge_records",
    "cfht_rectorate_dashboard_snapshots",
    "cfht_audit_evidence_records",
    "cfht_limitations",
]


def _table_args(table_name: str):
    return (
        Index(f"ix_{table_name}_tenant_id", "tenant_id"),
        Index(f"ix_{table_name}_tenant_status", "tenant_id", "status"),
    )


@declarative_mixin
class CfhtCommonMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False, server_default=sa_text("'active'"))
    human_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    live_iot_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    live_gps_tracking_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    building_automation_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    access_control_enforcement_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    safety_certification_claimed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    maintenance_completion_guaranteed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_housing_decision_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_eviction_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    automatic_student_staff_sanction_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    autonomous_dispatch_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    external_provider_sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    production_facilities_claimed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    sales_ready_claimed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    gcc_ready_claimed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    l5_l6_claimed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("false"))
    incomplete_data: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=sa_text("true"))
    source_module: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reference_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))
    limitations_json: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=sa_text("'[]'::jsonb"))
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, server_default=sa_text("NOW()"))
    archived_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CfhtCampusProfile(CfhtCommonMixin, Base):
    __tablename__ = "cfht_campus_profiles"
    __table_args__ = _table_args(__tablename__)
    campus_code: Mapped[str | None] = mapped_column(String(128), nullable=True)


class CfhtFacilityRegistryRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_facility_registry_records"
    __table_args__ = _table_args(__tablename__)


class CfhtBuildingRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_building_records"
    __table_args__ = _table_args(__tablename__)


class CfhtFloorRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_floor_records"
    __table_args__ = _table_args(__tablename__)


class CfhtRoomRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_room_records"
    __table_args__ = _table_args(__tablename__)


class CfhtRoomTypeRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_room_type_records"
    __table_args__ = _table_args(__tablename__)


class CfhtRoomAvailabilitySnapshot(CfhtCommonMixin, Base):
    __tablename__ = "cfht_room_availability_snapshots"
    __table_args__ = _table_args(__tablename__)


class CfhtOccupancyVisibilityRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_occupancy_visibility_records"
    __table_args__ = _table_args(__tablename__)


class CfhtDormitoryRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_dormitory_records"
    __table_args__ = _table_args(__tablename__)


class CfhtHousingUnitRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_housing_unit_records"
    __table_args__ = _table_args(__tablename__)


class CfhtHousingRequestMetadata(CfhtCommonMixin, Base):
    __tablename__ = "cfht_housing_request_metadata"
    __table_args__ = _table_args(__tablename__)


class CfhtMaintenanceRequestRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_maintenance_request_records"
    __table_args__ = _table_args(__tablename__)


class CfhtServiceRequestRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_service_request_records"
    __table_args__ = _table_args(__tablename__)


class CfhtWorkOrderMetadata(CfhtCommonMixin, Base):
    __tablename__ = "cfht_work_order_metadata"
    __table_args__ = _table_args(__tablename__)


class CfhtTransportRouteRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_transport_route_records"
    __table_args__ = _table_args(__tablename__)


class CfhtTransportVehicleMetadata(CfhtCommonMixin, Base):
    __tablename__ = "cfht_transport_vehicle_metadata"
    __table_args__ = _table_args(__tablename__)


class CfhtTransportScheduleMetadata(CfhtCommonMixin, Base):
    __tablename__ = "cfht_transport_schedule_metadata"
    __table_args__ = _table_args(__tablename__)


class CfhtFacilityResponsibleUnitRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_facility_responsible_unit_records"
    __table_args__ = _table_args(__tablename__)


class CfhtCampusSafetyReadinessRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_campus_safety_readiness_records"
    __table_args__ = _table_args(__tablename__)


class CfhtAccessVisitorBridgeRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_access_visitor_bridge_records"
    __table_args__ = _table_args(__tablename__)
    bridge_key: Mapped[str | None] = mapped_column(String(128), nullable=True)


class CfhtStudentServicesBridgeRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_student_services_bridge_records"
    __table_args__ = _table_args(__tablename__)
    bridge_key: Mapped[str | None] = mapped_column(String(128), nullable=True)


class CfhtFinanceAssetBridgeRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_finance_asset_bridge_records"
    __table_args__ = _table_args(__tablename__)
    bridge_key: Mapped[str | None] = mapped_column(String(128), nullable=True)


class CfhtHrStaffAssignmentBridgeRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_hr_staff_assignment_bridge_records"
    __table_args__ = _table_args(__tablename__)
    bridge_key: Mapped[str | None] = mapped_column(String(128), nullable=True)


class CfhtRectorateDashboardSnapshot(CfhtCommonMixin, Base):
    __tablename__ = "cfht_rectorate_dashboard_snapshots"
    __table_args__ = _table_args(__tablename__)
    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=sa_text("'{}'::jsonb"))


class CfhtAuditEvidenceRecord(CfhtCommonMixin, Base):
    __tablename__ = "cfht_audit_evidence_records"
    __table_args__ = _table_args(__tablename__)
    evidence_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reference_uri: Mapped[str | None] = mapped_column(Text, nullable=True)


class CfhtLimitation(CfhtCommonMixin, Base):
    __tablename__ = "cfht_limitations"
    __table_args__ = _table_args(__tablename__)
    limitation_text: Mapped[str] = mapped_column(Text, nullable=False, server_default=sa_text("''"))


MODEL_BY_FAMILY = {
    "campus": CfhtCampusProfile,
    "facilities": CfhtFacilityRegistryRecord,
    "buildings": CfhtBuildingRecord,
    "floors": CfhtFloorRecord,
    "rooms": CfhtRoomRecord,
    "room_types": CfhtRoomTypeRecord,
    "availability": CfhtRoomAvailabilitySnapshot,
    "occupancy": CfhtOccupancyVisibilityRecord,
    "dormitories": CfhtDormitoryRecord,
    "housing_units": CfhtHousingUnitRecord,
    "housing_requests": CfhtHousingRequestMetadata,
    "maintenance": CfhtMaintenanceRequestRecord,
    "service_requests": CfhtServiceRequestRecord,
    "work_orders": CfhtWorkOrderMetadata,
    "transport_routes": CfhtTransportRouteRecord,
    "transport_vehicles": CfhtTransportVehicleMetadata,
    "transport_schedules": CfhtTransportScheduleMetadata,
    "responsible_units": CfhtFacilityResponsibleUnitRecord,
    "safety_readiness": CfhtCampusSafetyReadinessRecord,
    "access_visitor_bridge": CfhtAccessVisitorBridgeRecord,
    "student_services_bridge": CfhtStudentServicesBridgeRecord,
    "finance_asset_bridge": CfhtFinanceAssetBridgeRecord,
    "hr_staff_bridge": CfhtHrStaffAssignmentBridgeRecord,
    "dashboard": CfhtRectorateDashboardSnapshot,
    "audit_evidence": CfhtAuditEvidenceRecord,
    "limitations": CfhtLimitation,
}
