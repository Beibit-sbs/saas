from __future__ import annotations

from app.core.module_helpers.audit_helpers import build_audit_action
from app.modules.audit.service import log_admin_action
from app.modules.operations.schemas import (
    CleaningCheckCreateSchema,
    CleaningCheckSchema,
    FacilityIssueCreateSchema,
    FacilityIssueSchema,
    MaintenanceAssetCreateSchema,
    MaintenanceAssetSchema,
    OperationsHealthSnapshotSchema,
    RoomReadinessCreateSchema,
    RoomReadinessSchema,
    UtilityReadingCreateSchema,
    UtilityReadingSchema,
    WorkOrderCreateSchema,
    WorkOrderSchema,
)
from app.modules.university_core.tenant_entity_service import create_entity_for_tenant, list_entities_for_tenant


_WORK_ORDER_STATUS_MAX_ACTIVE: dict[str, int] = {
    "open": 12,
    "assigned": 8,
    "in_progress": 8,
}
_ACTIVE_WORK_ORDER_STATUSES: frozenset[str] = frozenset({"open", "assigned", "in_progress"})

# ---------------------------------------------------------------------------
# W101: Room readiness safety guard
# A room cannot be marked 'ready' when there are open facility issues with
# critical or high severity for the same room_code.
# Marking a hazardous room as ready exposes students and staff to unsafe
# conditions and creates an accreditation/safety compliance violation.
# ---------------------------------------------------------------------------
_ROOM_READINESS_READY_STATUS: str = "ready"
_BLOCKING_FACILITY_ISSUE_SEVERITIES: frozenset[str] = frozenset({"critical", "high"})
_BLOCKING_FACILITY_ISSUE_STATUSES: frozenset[str] = frozenset({"open", "in_progress"})


def _check_no_blocking_facility_issues_for_room(
    tenant_id: int,
    room_code: str,
    target_status: str,
) -> None:
    """W101: Cross-entity guard — operations_room_readiness × operations_facility_issues.

    A room cannot be marked 'ready' when there are open or in-progress facility
    issues with severity 'critical' or 'high' for the same room_code.

    Real-world invariant: a room with unresolved high/critical safety issues is not
    ready for use. Marking it ready:
      - Allows classes and events in an unsafe space
      - Creates a safety compliance violation
      - Exposes the institution to liability and accreditation risk

    HARDENING: fail-closed — if the facility_issues query fails, the room
    readiness record is blocked. No silent fallback: an unknown safety state
    must default to NOT ready.
    """
    from app.core.module_helpers.service_validation import DomainValidationError

    if target_status != _ROOM_READINESS_READY_STATUS:
        return  # guard only applies to 'ready' target status

    normalised_room = str(room_code or "").strip().lower()

    try:
        all_issues = list_entities_for_tenant("operations_facility_issues", tenant_id)
    except Exception as exc:
        raise DomainValidationError(
            f"Cannot mark room '{room_code}' as ready: facility_issues query failed. "
            f"Cannot verify absence of blocking issues. Reason: {exc}"
        ) from exc

    for issue in all_issues:
        issue_room = str(issue.get("facility_code") or "").strip().lower()
        if issue_room != normalised_room:
            continue
        severity = str(issue.get("severity") or "").strip().lower()
        status = str(issue.get("status") or "").strip().lower()
        if severity in _BLOCKING_FACILITY_ISSUE_SEVERITIES and status in _BLOCKING_FACILITY_ISSUE_STATUSES:
            raise DomainValidationError(
                f"Cannot mark room '{room_code}' as ready: "
                f"open {severity}-severity facility issue exists "
                f"(issue_id={issue.get('id')}, status='{status}'). "
                f"Resolve all critical/high severity issues before marking the room ready."
            )


def _emit_audit(*, actor: str, action: str, path: str, metadata: dict, tenant_id: int) -> None:
    log_admin_action(
        actor=actor,
        action=action,
        path=path,
        client_ip="service",
        entity="operations",
        metadata=metadata,
        tenant_id=tenant_id,
    )


def list_facility_issues(tenant_id: int) -> list[FacilityIssueSchema]:
    rows = list_entities_for_tenant("operations_facility_issues", tenant_id)
    return [FacilityIssueSchema.model_validate(r) for r in rows]


def create_facility_issue(tenant_id: int, request: FacilityIssueCreateSchema, actor: str) -> FacilityIssueSchema:
    created = create_entity_for_tenant(
        "operations_facility_issues",
        {
            "facility_code": request.facility_code.strip(),
            "issue_type": request.issue_type.strip(),
            "severity": request.severity.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("operations", "facility_issue", "create"),
        path="/internal/operations/facility-issues",
        metadata={"resource_id": str(created.get("id")), "facility_code": request.facility_code},
        tenant_id=tenant_id,
    )
    return FacilityIssueSchema.model_validate(created)


def list_work_orders(tenant_id: int) -> list[WorkOrderSchema]:
    rows = list_entities_for_tenant("operations_work_orders", tenant_id)
    return [WorkOrderSchema.model_validate(r) for r in rows]


def _ensure_dispatch_record(work_order: dict[str, object], tenant_id: int, assigned_team: str) -> None:
    existing = list_entities_for_tenant("operations_dispatch_records", tenant_id)
    source_entity_id = str(work_order.get("id") or "")
    already_exists = any(
        str(row.get("integration_source") or "") == "operations_work_order"
        and str(row.get("source_entity_id") or "") == source_entity_id
        for row in existing
    )
    if already_exists:
        return
    create_entity_for_tenant(
        "operations_dispatch_records",
        {
            "work_order_id": source_entity_id,
            "work_order_code": str(work_order.get("work_order_code") or ""),
            "facility_code": str(work_order.get("facility_code") or ""),
            "assigned_team": assigned_team.strip(),
            "status": str(work_order.get("status") or "open"),
            "integration_source": "operations_work_order",
            "source_entity_id": source_entity_id,
        },
        tenant_id,
    )


def create_work_order(tenant_id: int, request: WorkOrderCreateSchema, actor: str) -> WorkOrderSchema:
    requested_status = str(request.status)
    if requested_status in _ACTIVE_WORK_ORDER_STATUSES:
        existing = list_entities_for_tenant("operations_work_orders", tenant_id)
        active_count = sum(
            1
            for row in existing
            if str(row.get("status") or "") == requested_status
            and str(row.get("status") or "") in _ACTIVE_WORK_ORDER_STATUSES
        )
        cap = _WORK_ORDER_STATUS_MAX_ACTIVE.get(requested_status, 12)
        if active_count >= cap:
            raise ValueError(
                f"Active work order cap exceeded for status '{requested_status}': limit={cap}, current={active_count}"
            )

    created = create_entity_for_tenant(
        "operations_work_orders",
        {
            "work_order_code": request.work_order_code.strip(),
            "facility_code": request.facility_code.strip(),
            "summary": request.summary.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("operations", "work_order", "create"),
        path="/internal/operations/work-orders",
        metadata={"resource_id": str(created.get("id")), "work_order_code": request.work_order_code},
        tenant_id=tenant_id,
    )
    if request.assigned_team:
        _ensure_dispatch_record(created, tenant_id, request.assigned_team)
    return WorkOrderSchema.model_validate(created)


def list_cleaning_checks(tenant_id: int) -> list[CleaningCheckSchema]:
    rows = list_entities_for_tenant("operations_cleaning_checks", tenant_id)
    return [CleaningCheckSchema.model_validate(r) for r in rows]


def create_cleaning_check(tenant_id: int, request: CleaningCheckCreateSchema, actor: str) -> CleaningCheckSchema:
    created = create_entity_for_tenant(
        "operations_cleaning_checks",
        {
            "room_code": request.room_code.strip(),
            "scheduled_slot": request.scheduled_slot.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("operations", "cleaning_check", "create"),
        path="/internal/operations/cleaning-checks",
        metadata={"resource_id": str(created.get("id")), "room_code": request.room_code},
        tenant_id=tenant_id,
    )
    return CleaningCheckSchema.model_validate(created)


def list_room_readiness(tenant_id: int) -> list[RoomReadinessSchema]:
    rows = list_entities_for_tenant("operations_room_readiness", tenant_id)
    return [RoomReadinessSchema.model_validate(r) for r in rows]


def list_maintenance_assets(tenant_id: int) -> list[MaintenanceAssetSchema]:
    rows = list_entities_for_tenant("operations_maintenance_assets", tenant_id)
    return [MaintenanceAssetSchema.model_validate(r) for r in rows]


def create_maintenance_asset(
    tenant_id: int,
    request: MaintenanceAssetCreateSchema,
    actor: str,
) -> MaintenanceAssetSchema:
    created = create_entity_for_tenant(
        "operations_maintenance_assets",
        {
            "asset_code": request.asset_code.strip(),
            "facility_code": request.facility_code.strip(),
            "asset_type": request.asset_type.strip(),
            "health_score": request.health_score,
            "days_since_maintenance": request.days_since_maintenance,
            "expected_service_interval_days": request.expected_service_interval_days,
            "status": request.status.strip(),
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("operations", "maintenance_asset", "create"),
        path="/internal/operations/maintenance-assets",
        metadata={"resource_id": str(created.get("id")), "asset_code": request.asset_code},
        tenant_id=tenant_id,
    )
    return MaintenanceAssetSchema.model_validate(created)


def list_utility_readings(tenant_id: int) -> list[UtilityReadingSchema]:
    rows = list_entities_for_tenant("operations_utility_readings", tenant_id)
    return [UtilityReadingSchema.model_validate(r) for r in rows]


def create_utility_reading(
    tenant_id: int,
    request: UtilityReadingCreateSchema,
    actor: str,
) -> UtilityReadingSchema:
    created = create_entity_for_tenant(
        "operations_utility_readings",
        {
            "meter_code": request.meter_code.strip(),
            "building_code": request.building_code.strip(),
            "utility_type": request.utility_type.strip(),
            "usage_value": request.usage_value,
            "baseline_value": request.baseline_value,
            "status": request.status.strip(),
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("operations", "utility_reading", "create"),
        path="/internal/operations/utility-readings",
        metadata={"resource_id": str(created.get("id")), "meter_code": request.meter_code},
        tenant_id=tenant_id,
    )
    return UtilityReadingSchema.model_validate(created)


def create_room_readiness(tenant_id: int, request: RoomReadinessCreateSchema, actor: str) -> RoomReadinessSchema:
    # W101: Block 'ready' status when unresolved critical/high facility issues exist
    _check_no_blocking_facility_issues_for_room(
        tenant_id=tenant_id,
        room_code=request.room_code,
        target_status=str(request.status),
    )
    created = create_entity_for_tenant(
        "operations_room_readiness",
        {
            "room_code": request.room_code.strip(),
            "building_code": request.building_code.strip(),
            "status": request.status,
        },
        tenant_id,
    )

    _emit_audit(
        actor=actor,
        action=build_audit_action("operations", "room_readiness", "create"),
        path="/internal/operations/room-readiness",
        metadata={"resource_id": str(created.get("id")), "room_code": request.room_code},
        tenant_id=tenant_id,
    )
    return RoomReadinessSchema.model_validate(created)


def _to_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return default


def _to_int(value: object, default: int = 0) -> int:
    if isinstance(value, int):
        return value
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def get_operations_health_snapshot(tenant_id: int) -> OperationsHealthSnapshotSchema:
    facility_rows = list_entities_for_tenant("operations_facility_issues", tenant_id)
    work_order_rows = list_entities_for_tenant("operations_work_orders", tenant_id)
    cleaning_rows = list_entities_for_tenant("operations_cleaning_checks", tenant_id)
    readiness_rows = list_entities_for_tenant("operations_room_readiness", tenant_id)
    maintenance_rows = list_entities_for_tenant("operations_maintenance_assets", tenant_id)
    utility_rows = list_entities_for_tenant("operations_utility_readings", tenant_id)

    open_facility_issues = 0
    for row in facility_rows:
        if str(row.get("status") or "") in {"reported", "in_progress", "blocked"}:
            open_facility_issues += 1

    missed_cleaning_checks = 0
    for row in cleaning_rows:
        if str(row.get("status") or "") == "missed":
            missed_cleaning_checks += 1

    rooms_not_ready = 0
    for row in readiness_rows:
        if str(row.get("status") or "") != "ready":
            rooms_not_ready += 1

    predictive_maintenance_due = 0
    for row in maintenance_rows:
        days_since = _to_int(row.get("days_since_maintenance"))
        service_interval = max(1, _to_int(row.get("expected_service_interval_days"), 1))
        health_score = _to_float(row.get("health_score"), 100.0)
        if days_since >= service_interval or health_score <= 40:
            predictive_maintenance_due += 1

    utility_anomaly_readings = 0
    for row in utility_rows:
        usage_value = _to_float(row.get("usage_value"))
        baseline_value = _to_float(row.get("baseline_value"))
        if baseline_value > 0 and usage_value >= baseline_value * 1.2:
            utility_anomaly_readings += 1

    return OperationsHealthSnapshotSchema(
        tenant_id=tenant_id,
        facilities_total=len(facility_rows),
        open_facility_issues=open_facility_issues,
        work_orders_total=len(work_order_rows),
        missed_cleaning_checks=missed_cleaning_checks,
        rooms_total=len(readiness_rows),
        rooms_not_ready=rooms_not_ready,
        maintenance_assets_total=len(maintenance_rows),
        predictive_maintenance_due=predictive_maintenance_due,
        utility_readings_total=len(utility_rows),
        utility_anomaly_readings=utility_anomaly_readings,
    )