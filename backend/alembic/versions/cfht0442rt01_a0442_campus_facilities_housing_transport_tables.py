"""A-044.2 runtime tables for Campus / Facilities / Housing / Transport."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "cfht0442rt01"
down_revision = "sac0432rt01"
branch_labels = None
depends_on = None


CREATE_TABLES = [
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


def _jsonb_default_empty_object():
    return sa.text("'{}'::jsonb")


def _jsonb_default_empty_list():
    return sa.text("'[]'::jsonb")


def _common_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False, server_default=sa.text("'active'")),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("live_iot_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("live_gps_tracking_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("building_automation_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("access_control_enforcement_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("safety_certification_claimed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("maintenance_completion_guaranteed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_housing_decision_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_eviction_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("automatic_student_staff_sanction_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("autonomous_dispatch_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("external_provider_sync_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("production_facilities_claimed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sales_ready_claimed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("gcc_ready_claimed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("l5_l6_claimed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("incomplete_data", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("source_module", sa.String(length=128), nullable=True),
        sa.Column("source_entity_id", sa.String(length=128), nullable=True),
        sa.Column("reference_key", sa.String(length=128), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object()),
        sa.Column("limitations_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_list()),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("updated_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _create_standard_indexes(table_name: str) -> None:
    op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"], unique=False)
    op.create_index(f"ix_{table_name}_tenant_status", table_name, ["tenant_id", "status"], unique=False)


def upgrade() -> None:
    op.create_table("cfht_campus_profiles", *(_common_columns() + [sa.Column("campus_code", sa.String(length=128), nullable=True)]))
    _create_standard_indexes("cfht_campus_profiles")
    op.create_table("cfht_facility_registry_records", *_common_columns())
    _create_standard_indexes("cfht_facility_registry_records")
    op.create_table("cfht_building_records", *_common_columns())
    _create_standard_indexes("cfht_building_records")
    op.create_table("cfht_floor_records", *_common_columns())
    _create_standard_indexes("cfht_floor_records")
    op.create_table("cfht_room_records", *_common_columns())
    _create_standard_indexes("cfht_room_records")
    op.create_table("cfht_room_type_records", *_common_columns())
    _create_standard_indexes("cfht_room_type_records")
    op.create_table("cfht_room_availability_snapshots", *_common_columns())
    _create_standard_indexes("cfht_room_availability_snapshots")
    op.create_table("cfht_occupancy_visibility_records", *_common_columns())
    _create_standard_indexes("cfht_occupancy_visibility_records")
    op.create_table("cfht_dormitory_records", *_common_columns())
    _create_standard_indexes("cfht_dormitory_records")
    op.create_table("cfht_housing_unit_records", *_common_columns())
    _create_standard_indexes("cfht_housing_unit_records")
    op.create_table("cfht_housing_request_metadata", *_common_columns())
    _create_standard_indexes("cfht_housing_request_metadata")
    op.create_table("cfht_maintenance_request_records", *_common_columns())
    _create_standard_indexes("cfht_maintenance_request_records")
    op.create_table("cfht_service_request_records", *_common_columns())
    _create_standard_indexes("cfht_service_request_records")
    op.create_table("cfht_work_order_metadata", *_common_columns())
    _create_standard_indexes("cfht_work_order_metadata")
    op.create_table("cfht_transport_route_records", *_common_columns())
    _create_standard_indexes("cfht_transport_route_records")
    op.create_table("cfht_transport_vehicle_metadata", *_common_columns())
    _create_standard_indexes("cfht_transport_vehicle_metadata")
    op.create_table("cfht_transport_schedule_metadata", *_common_columns())
    _create_standard_indexes("cfht_transport_schedule_metadata")
    op.create_table("cfht_facility_responsible_unit_records", *_common_columns())
    _create_standard_indexes("cfht_facility_responsible_unit_records")
    op.create_table("cfht_campus_safety_readiness_records", *_common_columns())
    _create_standard_indexes("cfht_campus_safety_readiness_records")
    op.create_table("cfht_access_visitor_bridge_records", *(_common_columns() + [sa.Column("bridge_key", sa.String(length=128), nullable=True)]))
    _create_standard_indexes("cfht_access_visitor_bridge_records")
    op.create_table("cfht_student_services_bridge_records", *(_common_columns() + [sa.Column("bridge_key", sa.String(length=128), nullable=True)]))
    _create_standard_indexes("cfht_student_services_bridge_records")
    op.create_table("cfht_finance_asset_bridge_records", *(_common_columns() + [sa.Column("bridge_key", sa.String(length=128), nullable=True)]))
    _create_standard_indexes("cfht_finance_asset_bridge_records")
    op.create_table("cfht_hr_staff_assignment_bridge_records", *(_common_columns() + [sa.Column("bridge_key", sa.String(length=128), nullable=True)]))
    _create_standard_indexes("cfht_hr_staff_assignment_bridge_records")
    op.create_table("cfht_rectorate_dashboard_snapshots", *(_common_columns() + [sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=_jsonb_default_empty_object())]))
    _create_standard_indexes("cfht_rectorate_dashboard_snapshots")
    op.create_table("cfht_audit_evidence_records", *(_common_columns() + [sa.Column("evidence_type", sa.String(length=128), nullable=True), sa.Column("reference_uri", sa.Text(), nullable=True)]))
    _create_standard_indexes("cfht_audit_evidence_records")
    op.create_table("cfht_limitations", *(_common_columns() + [sa.Column("limitation_text", sa.Text(), nullable=False, server_default=sa.text("''"))]))
    _create_standard_indexes("cfht_limitations")


def downgrade() -> None:
    op.drop_index("ix_cfht_limitations_tenant_status", table_name="cfht_limitations")
    op.drop_index("ix_cfht_limitations_tenant_id", table_name="cfht_limitations")
    op.drop_table("cfht_limitations")
    op.drop_index("ix_cfht_audit_evidence_records_tenant_status", table_name="cfht_audit_evidence_records")
    op.drop_index("ix_cfht_audit_evidence_records_tenant_id", table_name="cfht_audit_evidence_records")
    op.drop_table("cfht_audit_evidence_records")
    op.drop_index("ix_cfht_rectorate_dashboard_snapshots_tenant_status", table_name="cfht_rectorate_dashboard_snapshots")
    op.drop_index("ix_cfht_rectorate_dashboard_snapshots_tenant_id", table_name="cfht_rectorate_dashboard_snapshots")
    op.drop_table("cfht_rectorate_dashboard_snapshots")
    op.drop_index("ix_cfht_hr_staff_assignment_bridge_records_tenant_status", table_name="cfht_hr_staff_assignment_bridge_records")
    op.drop_index("ix_cfht_hr_staff_assignment_bridge_records_tenant_id", table_name="cfht_hr_staff_assignment_bridge_records")
    op.drop_table("cfht_hr_staff_assignment_bridge_records")
    op.drop_index("ix_cfht_finance_asset_bridge_records_tenant_status", table_name="cfht_finance_asset_bridge_records")
    op.drop_index("ix_cfht_finance_asset_bridge_records_tenant_id", table_name="cfht_finance_asset_bridge_records")
    op.drop_table("cfht_finance_asset_bridge_records")
    op.drop_index("ix_cfht_student_services_bridge_records_tenant_status", table_name="cfht_student_services_bridge_records")
    op.drop_index("ix_cfht_student_services_bridge_records_tenant_id", table_name="cfht_student_services_bridge_records")
    op.drop_table("cfht_student_services_bridge_records")
    op.drop_index("ix_cfht_access_visitor_bridge_records_tenant_status", table_name="cfht_access_visitor_bridge_records")
    op.drop_index("ix_cfht_access_visitor_bridge_records_tenant_id", table_name="cfht_access_visitor_bridge_records")
    op.drop_table("cfht_access_visitor_bridge_records")
    op.drop_index("ix_cfht_campus_safety_readiness_records_tenant_status", table_name="cfht_campus_safety_readiness_records")
    op.drop_index("ix_cfht_campus_safety_readiness_records_tenant_id", table_name="cfht_campus_safety_readiness_records")
    op.drop_table("cfht_campus_safety_readiness_records")
    op.drop_index("ix_cfht_facility_responsible_unit_records_tenant_status", table_name="cfht_facility_responsible_unit_records")
    op.drop_index("ix_cfht_facility_responsible_unit_records_tenant_id", table_name="cfht_facility_responsible_unit_records")
    op.drop_table("cfht_facility_responsible_unit_records")
    op.drop_index("ix_cfht_transport_schedule_metadata_tenant_status", table_name="cfht_transport_schedule_metadata")
    op.drop_index("ix_cfht_transport_schedule_metadata_tenant_id", table_name="cfht_transport_schedule_metadata")
    op.drop_table("cfht_transport_schedule_metadata")
    op.drop_index("ix_cfht_transport_vehicle_metadata_tenant_status", table_name="cfht_transport_vehicle_metadata")
    op.drop_index("ix_cfht_transport_vehicle_metadata_tenant_id", table_name="cfht_transport_vehicle_metadata")
    op.drop_table("cfht_transport_vehicle_metadata")
    op.drop_index("ix_cfht_transport_route_records_tenant_status", table_name="cfht_transport_route_records")
    op.drop_index("ix_cfht_transport_route_records_tenant_id", table_name="cfht_transport_route_records")
    op.drop_table("cfht_transport_route_records")
    op.drop_index("ix_cfht_work_order_metadata_tenant_status", table_name="cfht_work_order_metadata")
    op.drop_index("ix_cfht_work_order_metadata_tenant_id", table_name="cfht_work_order_metadata")
    op.drop_table("cfht_work_order_metadata")
    op.drop_index("ix_cfht_service_request_records_tenant_status", table_name="cfht_service_request_records")
    op.drop_index("ix_cfht_service_request_records_tenant_id", table_name="cfht_service_request_records")
    op.drop_table("cfht_service_request_records")
    op.drop_index("ix_cfht_maintenance_request_records_tenant_status", table_name="cfht_maintenance_request_records")
    op.drop_index("ix_cfht_maintenance_request_records_tenant_id", table_name="cfht_maintenance_request_records")
    op.drop_table("cfht_maintenance_request_records")
    op.drop_index("ix_cfht_housing_request_metadata_tenant_status", table_name="cfht_housing_request_metadata")
    op.drop_index("ix_cfht_housing_request_metadata_tenant_id", table_name="cfht_housing_request_metadata")
    op.drop_table("cfht_housing_request_metadata")
    op.drop_index("ix_cfht_housing_unit_records_tenant_status", table_name="cfht_housing_unit_records")
    op.drop_index("ix_cfht_housing_unit_records_tenant_id", table_name="cfht_housing_unit_records")
    op.drop_table("cfht_housing_unit_records")
    op.drop_index("ix_cfht_dormitory_records_tenant_status", table_name="cfht_dormitory_records")
    op.drop_index("ix_cfht_dormitory_records_tenant_id", table_name="cfht_dormitory_records")
    op.drop_table("cfht_dormitory_records")
    op.drop_index("ix_cfht_occupancy_visibility_records_tenant_status", table_name="cfht_occupancy_visibility_records")
    op.drop_index("ix_cfht_occupancy_visibility_records_tenant_id", table_name="cfht_occupancy_visibility_records")
    op.drop_table("cfht_occupancy_visibility_records")
    op.drop_index("ix_cfht_room_availability_snapshots_tenant_status", table_name="cfht_room_availability_snapshots")
    op.drop_index("ix_cfht_room_availability_snapshots_tenant_id", table_name="cfht_room_availability_snapshots")
    op.drop_table("cfht_room_availability_snapshots")
    op.drop_index("ix_cfht_room_type_records_tenant_status", table_name="cfht_room_type_records")
    op.drop_index("ix_cfht_room_type_records_tenant_id", table_name="cfht_room_type_records")
    op.drop_table("cfht_room_type_records")
    op.drop_index("ix_cfht_room_records_tenant_status", table_name="cfht_room_records")
    op.drop_index("ix_cfht_room_records_tenant_id", table_name="cfht_room_records")
    op.drop_table("cfht_room_records")
    op.drop_index("ix_cfht_floor_records_tenant_status", table_name="cfht_floor_records")
    op.drop_index("ix_cfht_floor_records_tenant_id", table_name="cfht_floor_records")
    op.drop_table("cfht_floor_records")
    op.drop_index("ix_cfht_building_records_tenant_status", table_name="cfht_building_records")
    op.drop_index("ix_cfht_building_records_tenant_id", table_name="cfht_building_records")
    op.drop_table("cfht_building_records")
    op.drop_index("ix_cfht_facility_registry_records_tenant_status", table_name="cfht_facility_registry_records")
    op.drop_index("ix_cfht_facility_registry_records_tenant_id", table_name="cfht_facility_registry_records")
    op.drop_table("cfht_facility_registry_records")
    op.drop_index("ix_cfht_campus_profiles_tenant_status", table_name="cfht_campus_profiles")
    op.drop_index("ix_cfht_campus_profiles_tenant_id", table_name="cfht_campus_profiles")
    op.drop_table("cfht_campus_profiles")
