import { describe, expect, it } from 'vitest';
import {
  CAMPUS_FACILITIES_BACKEND_ENDPOINT_COUNT,
  CAMPUS_FACILITIES_BACKEND_ROUTE_COUNT,
  CAMPUS_FACILITIES_PERMISSION_COUNT,
  CAMPUS_FACILITIES_PLANNED_ROUTE_COUNT,
  CAMPUS_FACILITIES_TABLE_COUNT,
  RUNTIME_MODE,
} from '@/modules/campus-facilities/constants';
import type {
  AccessVisitorBridge,
  AuditEvidence,
  AvailabilitySnapshot,
  BuildingRecord,
  CampusFacilitiesApiResult,
  CampusFacilitiesDashboard,
  CampusFacilitiesOverview,
  CampusFacilitiesRouteDefinition,
  CampusFacilitiesRouteKey,
  CampusFacilitiesSafetyFlags,
  CampusProfile,
  DormitoryRecord,
  FacilityRecord,
  FinanceAssetBridge,
  FloorRecord,
  HealthResponse,
  HousingRequestMetadata,
  HousingUnit,
  HrStaffBridge,
  Limitations,
  MaintenanceRequest,
  MetadataContract,
  OccupancyVisibility,
  ResponsibleUnit,
  RoomRecord,
  RoomTypeRecord,
  SafetyReadiness,
  ServiceRequest,
  StudentServicesBridge,
  TransportRoute,
  TransportScheduleMetadata,
  TransportVehicleMetadata,
  WorkOrderMetadata,
} from '@/modules/campus-facilities/types';

describe('Campus Facilities types', () => {
  const safetyFlags: CampusFacilitiesSafetyFlags = {
    liveIotEnabled: false,
    liveGpsTrackingEnabled: false,
    buildingAutomationEnabled: false,
    accessControlEnforcementEnabled: false,
    safetyCertificationClaimed: false,
    maintenanceCompletionGuaranteed: false,
    automaticHousingDecisionEnabled: false,
    automaticEvictionEnabled: false,
    automaticStudentStaffSanctionEnabled: false,
    autonomousDispatchEnabled: false,
    externalProviderSyncEnabled: false,
    productionFacilitiesClaimed: false,
    salesReadyClaimed: false,
    gccReadyClaimed: false,
    l5L6Claimed: false,
    humanReviewRequired: true,
    incompleteData: true,
  };

  it('keeps fixed platform metrics', () => {
    expect(CAMPUS_FACILITIES_PLANNED_ROUTE_COUNT).toBe(24);
    expect(CAMPUS_FACILITIES_BACKEND_ROUTE_COUNT).toBe(52);
    expect(CAMPUS_FACILITIES_TABLE_COUNT).toBe(26);
    expect(CAMPUS_FACILITIES_PERMISSION_COUNT).toBe(46);
    expect(CAMPUS_FACILITIES_BACKEND_ENDPOINT_COUNT).toBe(52);
  });

  it('keeps runtime mode contract fixed', () => {
    expect(RUNTIME_MODE).toBe('METADATA_READINESS_EVIDENCE_CONTROL_VISIBILITY_HUMAN_REVIEW_ONLY');
  });

  it('supports safety flags contract', () => {
    expect(safetyFlags.liveIotEnabled).toBe(false);
    expect(safetyFlags.l5L6Claimed).toBe(false);
    expect(safetyFlags.humanReviewRequired).toBe(true);
  });

  it('supports overview and dashboard contracts', () => {
    const overview: CampusFacilitiesOverview = {
      module: 'campus-facilities',
      contractVersion: 'A-044.3',
      runtimeMode: RUNTIME_MODE,
      tenantId: 1,
      safetyFlags,
      title: 'Overview',
      summary: 'metadata only',
      routeCount: 24,
      backendRouteCount: 52,
      tableCount: 26,
      permissionCount: 46,
      bridgeCount: 4,
    };

    const dashboard: CampusFacilitiesDashboard = {
      module: 'campus-facilities',
      contractVersion: 'A-044.3',
      runtimeMode: RUNTIME_MODE,
      tenantId: 1,
      safetyFlags,
      title: 'Dashboard',
      summary: 'readiness',
      widgets: [],
      incompleteData: true,
    };

    expect(overview.backendRouteCount).toBe(52);
    expect(dashboard.incompleteData).toBe(true);
  });

  it('supports route definition contract', () => {
    const route: CampusFacilitiesRouteDefinition = {
      routeKey: 'overview' as CampusFacilitiesRouteKey,
      path: '/console/campus-facilities',
      title: 'Overview',
      description: 'desc',
      requiredPermission: 'campus_facilities.overview.read',
      endpointGroup: 'overview',
      backendEndpoints: ['GET /api/admin/campus-facilities/overview'],
      dashboardLike: true,
      bridgeRoute: false,
      sensitive: false,
      humanReviewRequired: true,
      incompleteDataSupported: true,
      forbiddenClaims: ['No live IoT integration'],
      boundaryLabels: ['Human review required'],
    };
    expect(route.path).toContain('/console/campus-facilities');
  });

  it('supports all domain response shapes', () => {
    const responses: Array<
      CampusProfile | FacilityRecord | BuildingRecord | FloorRecord | RoomRecord | RoomTypeRecord |
      AvailabilitySnapshot | OccupancyVisibility | DormitoryRecord | HousingUnit | HousingRequestMetadata |
      MaintenanceRequest | ServiceRequest | WorkOrderMetadata | TransportRoute | TransportVehicleMetadata |
      TransportScheduleMetadata | ResponsibleUnit | SafetyReadiness | AccessVisitorBridge |
      StudentServicesBridge | FinanceAssetBridge | HrStaffBridge | AuditEvidence | Limitations |
      MetadataContract | HealthResponse
    > = [
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Campus', campusCount: 1, notes: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Facilities', items: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Buildings', items: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Floors', items: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Rooms', items: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Room Types', items: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Availability', availabilityWindows: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Occupancy', occupancyWindows: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Dorms', dormitories: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Units', units: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Requests', requests: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Maint', requests: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Service', requests: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'WO', workOrders: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'TR', routes: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'TV', vehicles: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'TS', schedules: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'RU', units: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'SR', readiness: 'pending', evidence: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'B1', bridgeFamily: 'access-visitor', endpoints: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'B2', bridgeFamily: 'student-services', endpoints: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'B3', bridgeFamily: 'finance-asset', endpoints: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'B4', bridgeFamily: 'hr-staff', endpoints: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Audit', evidenceItems: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Lim', limitations: [] },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Meta', expectedRouteCount: 52, expectedTableCount: 26, expectedPermissionCount: 46, permissionNamespace: 'campus_facilities.*' },
      { module: 'campus-facilities', contractVersion: 'A-044.3', runtimeMode: RUNTIME_MODE, tenantId: 1, safetyFlags, title: 'Health', status: 'ok' },
    ];

    expect(responses).toHaveLength(27);
  });

  it('supports generic api result wrapper', () => {
    const wrapped: CampusFacilitiesApiResult<{ item: { ok: boolean } }> = {
      module: 'campus-facilities',
      contractVersion: 'A-044.3',
      runtimeMode: RUNTIME_MODE,
      tenantId: 1,
      safetyFlags,
      item: { ok: true },
    };
    expect(wrapped.item.ok).toBe(true);
  });
});
