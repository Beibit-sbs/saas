import { CAMPUS_FACILITIES_NO_OVERCLAIM_COPY, getCampusFacilitiesBoundaryLabels } from './boundaryLabels';
import type { CampusFacilitiesDashboardCard, CampusFacilitiesRouteDefinition, CampusFacilitiesRouteKey, CampusFacilitiesSafetyFlags } from './types';

export const CAMPUS_FACILITIES_MODULE_NAME = 'campus-facilities';
export const CAMPUS_FACILITIES_ROUTE_FAMILY = '/console/campus-facilities';
export const CAMPUS_FACILITIES_API_BASE = '/api/admin/campus-facilities';
export const CAMPUS_FACILITIES_BACKEND_ROUTE_COUNT = 52;
export const CAMPUS_FACILITIES_TABLE_COUNT = 26;
export const CAMPUS_FACILITIES_PERMISSION_COUNT = 46;
export const CAMPUS_FACILITIES_PLANNED_ROUTE_COUNT = 24;
export const RUNTIME_MODE = 'METADATA_READINESS_EVIDENCE_CONTROL_VISIBILITY_HUMAN_REVIEW_ONLY';

export const LIVE_IOT_ENABLED = false;
export const LIVE_GPS_TRACKING_ENABLED = false;
export const BUILDING_AUTOMATION_ENABLED = false;
export const ACCESS_CONTROL_ENFORCEMENT_ENABLED = false;
export const SAFETY_CERTIFICATION_CLAIMED = false;
export const MAINTENANCE_COMPLETION_GUARANTEED = false;
export const AUTOMATIC_HOUSING_DECISION_ENABLED = false;
export const AUTOMATIC_EVICTION_ENABLED = false;
export const AUTOMATIC_STUDENT_STAFF_SANCTION_ENABLED = false;
export const AUTONOMOUS_DISPATCH_ENABLED = false;
export const EXTERNAL_PROVIDER_SYNC_ENABLED = false;
export const PRODUCTION_FACILITIES_CLAIMED = false;
export const SALES_READY_CLAIMED = false;
export const GCC_READY_CLAIMED = false;
export const L5_L6_CLAIMED = false;
export const HUMAN_REVIEW_REQUIRED = true;

export const CAMPUS_FACILITIES_SAFETY_FLAGS: CampusFacilitiesSafetyFlags = {
  liveIotEnabled: LIVE_IOT_ENABLED,
  liveGpsTrackingEnabled: LIVE_GPS_TRACKING_ENABLED,
  buildingAutomationEnabled: BUILDING_AUTOMATION_ENABLED,
  accessControlEnforcementEnabled: ACCESS_CONTROL_ENFORCEMENT_ENABLED,
  safetyCertificationClaimed: SAFETY_CERTIFICATION_CLAIMED,
  maintenanceCompletionGuaranteed: MAINTENANCE_COMPLETION_GUARANTEED,
  automaticHousingDecisionEnabled: AUTOMATIC_HOUSING_DECISION_ENABLED,
  automaticEvictionEnabled: AUTOMATIC_EVICTION_ENABLED,
  automaticStudentStaffSanctionEnabled: AUTOMATIC_STUDENT_STAFF_SANCTION_ENABLED,
  autonomousDispatchEnabled: AUTONOMOUS_DISPATCH_ENABLED,
  externalProviderSyncEnabled: EXTERNAL_PROVIDER_SYNC_ENABLED,
  productionFacilitiesClaimed: PRODUCTION_FACILITIES_CLAIMED,
  salesReadyClaimed: SALES_READY_CLAIMED,
  gccReadyClaimed: GCC_READY_CLAIMED,
  l5L6Claimed: L5_L6_CLAIMED,
  humanReviewRequired: HUMAN_REVIEW_REQUIRED,
  incompleteData: true,
};

export const CAMPUS_FACILITIES_ROUTE_GROUPS = [
  'overview',
  'dashboard',
  'campus',
  'registry',
  'spaces',
  'housing',
  'requests',
  'transport',
  'responsibility',
  'readiness',
  'bridges',
  'audit',
  'limitations',
] as const;

function endpoint(method: 'GET' | 'POST', path: string) {
  return `${method} ${CAMPUS_FACILITIES_API_BASE}${path}`;
}

export const CAMPUS_FACILITIES_BACKEND_ENDPOINTS = [
  endpoint('GET', '/overview'),
  endpoint('GET', '/dashboard'),
  endpoint('GET', '/campus'),
  endpoint('GET', '/facilities'),
  endpoint('GET', '/buildings'),
  endpoint('GET', '/floors'),
  endpoint('GET', '/rooms'),
  endpoint('GET', '/room-types'),
  endpoint('GET', '/availability'),
  endpoint('GET', '/occupancy'),
  endpoint('GET', '/dormitories'),
  endpoint('GET', '/housing-units'),
  endpoint('GET', '/housing-requests'),
  endpoint('GET', '/maintenance'),
  endpoint('GET', '/service-requests'),
  endpoint('GET', '/work-orders'),
  endpoint('GET', '/transport/routes'),
  endpoint('GET', '/transport/vehicles'),
  endpoint('GET', '/transport/schedules'),
  endpoint('GET', '/responsible-units'),
  endpoint('GET', '/safety-readiness'),
  endpoint('GET', '/bridges/access-visitor'),
  endpoint('GET', '/bridges/student-services'),
  endpoint('GET', '/bridges/finance-asset'),
  endpoint('GET', '/bridges/hr-staff'),
  endpoint('GET', '/audit-evidence'),
  endpoint('GET', '/limitations'),
  endpoint('GET', '/metadata-contract'),
  endpoint('GET', '/safety-boundaries'),
  endpoint('GET', '/health'),
  endpoint('POST', '/facilities/metadata'),
  endpoint('POST', '/buildings/metadata'),
  endpoint('POST', '/floors/metadata'),
  endpoint('POST', '/rooms/metadata'),
  endpoint('POST', '/availability/metadata'),
  endpoint('POST', '/occupancy/metadata'),
  endpoint('POST', '/dormitories/metadata'),
  endpoint('POST', '/housing-units/metadata'),
  endpoint('POST', '/housing-requests/metadata'),
  endpoint('POST', '/maintenance/metadata'),
  endpoint('POST', '/service-requests/metadata'),
  endpoint('POST', '/work-orders/metadata'),
  endpoint('POST', '/transport/routes/metadata'),
  endpoint('POST', '/transport/vehicles/metadata'),
  endpoint('POST', '/transport/schedules/metadata'),
  endpoint('POST', '/responsible-units/metadata'),
  endpoint('POST', '/safety-readiness/evidence'),
  endpoint('POST', '/bridges/access-visitor/metadata'),
  endpoint('POST', '/bridges/student-services/metadata'),
  endpoint('POST', '/bridges/finance-asset/metadata'),
  endpoint('POST', '/bridges/hr-staff/metadata'),
  endpoint('POST', '/limitations/metadata'),
] as const;

export const CAMPUS_FACILITIES_BACKEND_ENDPOINT_COUNT = CAMPUS_FACILITIES_BACKEND_ENDPOINTS.length;

function routeDefinition(
  routeKey: CampusFacilitiesRouteKey,
  path: string,
  title: string,
  description: string,
  requiredPermission: string,
  endpointGroup: string,
  backendEndpoints: string[],
  options?: { dashboardLike?: boolean; bridgeRoute?: boolean; sensitive?: boolean },
): CampusFacilitiesRouteDefinition {
  return {
    routeKey,
    path,
    title,
    description,
    requiredPermission,
    endpointGroup,
    backendEndpoints,
    dashboardLike: options?.dashboardLike ?? false,
    bridgeRoute: options?.bridgeRoute ?? false,
    sensitive: options?.sensitive ?? false,
    humanReviewRequired: true,
    incompleteDataSupported: true,
    forbiddenClaims: [...CAMPUS_FACILITIES_NO_OVERCLAIM_COPY],
    boundaryLabels: getCampusFacilitiesBoundaryLabels(routeKey),
  };
}

export const CAMPUS_FACILITIES_ROUTE_DEFINITIONS = [
  routeDefinition('overview', CAMPUS_FACILITIES_ROUTE_FAMILY, 'Campus / Facilities / Housing / Transport', 'Suite overview and governance summary.', 'campus_facilities.overview.read', 'overview', [endpoint('GET', '/overview'), endpoint('GET', '/metadata-contract')], { dashboardLike: true }),
  routeDefinition('dashboard', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/dashboard`, 'Campus Facilities Dashboard', 'Readiness dashboard with metadata-only cards.', 'campus_facilities.dashboard.read', 'dashboard', [endpoint('GET', '/dashboard'), endpoint('GET', '/metadata-contract')], { dashboardLike: true }),
  routeDefinition('campus', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/campus`, 'Campus Registry', 'Campus-level catalog and profile metadata.', 'campus_facilities.campus.read', 'campus', [endpoint('GET', '/campus')]),
  routeDefinition('facilities', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/facilities`, 'Facilities Registry', 'Facilities metadata and evidence panel.', 'campus_facilities.facilities.read', 'registry', [endpoint('GET', '/facilities'), endpoint('POST', '/facilities/metadata')]),
  routeDefinition('buildings', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/buildings`, 'Buildings', 'Building registry visibility.', 'campus_facilities.buildings.read', 'registry', [endpoint('GET', '/buildings'), endpoint('POST', '/buildings/metadata')]),
  routeDefinition('floors', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/floors`, 'Floors', 'Floor metadata inventory.', 'campus_facilities.floors.read', 'spaces', [endpoint('GET', '/floors'), endpoint('POST', '/floors/metadata')]),
  routeDefinition('rooms', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/rooms`, 'Rooms', 'Room and room-type metadata.', 'campus_facilities.rooms.read', 'spaces', [endpoint('GET', '/rooms'), endpoint('GET', '/room-types'), endpoint('POST', '/rooms/metadata')]),
  routeDefinition('availability', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/availability`, 'Availability', 'Availability snapshots without guarantee claims.', 'campus_facilities.availability.read', 'spaces', [endpoint('GET', '/availability'), endpoint('POST', '/availability/metadata')]),
  routeDefinition('occupancy', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/occupancy`, 'Occupancy Visibility', 'Occupancy visibility metadata only.', 'campus_facilities.occupancy.read', 'spaces', [endpoint('GET', '/occupancy'), endpoint('POST', '/occupancy/metadata')]),
  routeDefinition('dormitories', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/dormitories`, 'Dormitories', 'Dormitory registry and readiness metadata.', 'campus_facilities.dormitories.read', 'housing', [endpoint('GET', '/dormitories'), endpoint('POST', '/dormitories/metadata')]),
  routeDefinition('housing-units', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/housing-units`, 'Housing Units', 'Housing units metadata.', 'campus_facilities.housing_units.read', 'housing', [endpoint('GET', '/housing-units'), endpoint('POST', '/housing-units/metadata')]),
  routeDefinition('housing-requests', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/housing-requests`, 'Housing Requests', 'Housing requests metadata queue.', 'campus_facilities.housing_requests.read', 'requests', [endpoint('GET', '/housing-requests'), endpoint('POST', '/housing-requests/metadata')], { sensitive: true }),
  routeDefinition('maintenance', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/maintenance`, 'Maintenance', 'Maintenance request metadata.', 'campus_facilities.maintenance.read', 'requests', [endpoint('GET', '/maintenance'), endpoint('POST', '/maintenance/metadata')]),
  routeDefinition('service-requests', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/service-requests`, 'Service Requests', 'Service request metadata.', 'campus_facilities.service_requests.read', 'requests', [endpoint('GET', '/service-requests'), endpoint('POST', '/service-requests/metadata')]),
  routeDefinition('work-orders', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/work-orders`, 'Work Orders', 'Work order metadata and evidence.', 'campus_facilities.work_orders.read', 'requests', [endpoint('GET', '/work-orders'), endpoint('POST', '/work-orders/metadata')]),
  routeDefinition('transport', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/transport`, 'Transport', 'Transport routes/vehicles/schedules metadata.', 'campus_facilities.transport.read', 'transport', [endpoint('GET', '/transport/routes'), endpoint('GET', '/transport/vehicles'), endpoint('GET', '/transport/schedules'), endpoint('POST', '/transport/routes/metadata'), endpoint('POST', '/transport/vehicles/metadata'), endpoint('POST', '/transport/schedules/metadata')]),
  routeDefinition('responsible-units', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/responsible-units`, 'Responsible Units', 'Owner responsibility registry.', 'campus_facilities.responsible_units.read', 'responsibility', [endpoint('GET', '/responsible-units'), endpoint('POST', '/responsible-units/metadata')]),
  routeDefinition('safety-readiness', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/safety-readiness`, 'Safety Readiness', 'Safety readiness evidence only.', 'campus_facilities.safety_readiness.read', 'readiness', [endpoint('GET', '/safety-readiness'), endpoint('POST', '/safety-readiness/evidence')]),
  routeDefinition('bridges-access-visitor', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/bridges/access-visitor`, 'Bridge: Access Visitor', 'Metadata bridge to access/visitor surfaces.', 'campus_facilities.bridges.access_visitor', 'bridges', [endpoint('GET', '/bridges/access-visitor'), endpoint('POST', '/bridges/access-visitor/metadata')], { bridgeRoute: true }),
  routeDefinition('bridges-student-services', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/bridges/student-services`, 'Bridge: Student Services', 'Metadata bridge to student services surfaces.', 'campus_facilities.bridges.student_services', 'bridges', [endpoint('GET', '/bridges/student-services'), endpoint('POST', '/bridges/student-services/metadata')], { bridgeRoute: true }),
  routeDefinition('bridges-finance-asset', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/bridges/finance-asset`, 'Bridge: Finance Asset', 'Metadata bridge to finance asset surfaces.', 'campus_facilities.bridges.finance_asset', 'bridges', [endpoint('GET', '/bridges/finance-asset'), endpoint('POST', '/bridges/finance-asset/metadata')], { bridgeRoute: true }),
  routeDefinition('bridges-hr-staff', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/bridges/hr-staff`, 'Bridge: HR Staff', 'Metadata bridge to HR/staff surfaces.', 'campus_facilities.bridges.hr_staff', 'bridges', [endpoint('GET', '/bridges/hr-staff'), endpoint('POST', '/bridges/hr-staff/metadata')], { bridgeRoute: true }),
  routeDefinition('audit-evidence', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/audit-evidence`, 'Audit Evidence', 'Audit evidence and control visibility.', 'campus_facilities.audit_evidence.read', 'audit', [endpoint('GET', '/audit-evidence')], { sensitive: true }),
  routeDefinition('limitations', `${CAMPUS_FACILITIES_ROUTE_FAMILY}/limitations`, 'Limitations', 'No-overclaim and non-production boundaries.', 'campus_facilities.limitations.read', 'limitations', [endpoint('GET', '/limitations'), endpoint('POST', '/limitations/metadata')]),
] as const satisfies readonly CampusFacilitiesRouteDefinition[];

export const CAMPUS_FACILITIES_DASHBOARD_CARDS: CampusFacilitiesDashboardCard[] = [
  {
    key: 'backend-route-count',
    title: 'Backend route contract',
    description: 'Backend contract remains metadata/readiness only.',
    backendEndpoints: [endpoint('GET', '/metadata-contract')],
    requiredPermission: 'campus_facilities.metadata_contract.read',
  },
  {
    key: 'table-count',
    title: 'Table inventory',
    description: 'Table inventory is visibility only and not operational control.',
    backendEndpoints: [endpoint('GET', '/metadata-contract')],
    requiredPermission: 'campus_facilities.metadata_contract.read',
  },
  {
    key: 'permission-count',
    title: 'Permission inventory',
    description: 'Permission set drives fail-closed access behavior.',
    backendEndpoints: [endpoint('GET', '/metadata-contract')],
    requiredPermission: 'campus_facilities.metadata_contract.read',
  },
  {
    key: 'safety-boundaries',
    title: 'Safety boundaries',
    description: 'Anti-fake and no-overclaim boundaries are always visible.',
    backendEndpoints: [endpoint('GET', '/safety-boundaries')],
    requiredPermission: 'campus_facilities.limitations.read',
  },
] as const;

export const CAMPUS_FACILITIES_BRIDGE_DEFINITIONS = [
  { key: 'access-visitor', title: 'Access / Visitor bridge', routeKey: 'bridges-access-visitor' as const, backendEndpoint: endpoint('GET', '/bridges/access-visitor'), requiredPermission: 'campus_facilities.bridges.access_visitor' },
  { key: 'student-services', title: 'Student Services bridge', routeKey: 'bridges-student-services' as const, backendEndpoint: endpoint('GET', '/bridges/student-services'), requiredPermission: 'campus_facilities.bridges.student_services' },
  { key: 'finance-asset', title: 'Finance Asset bridge', routeKey: 'bridges-finance-asset' as const, backendEndpoint: endpoint('GET', '/bridges/finance-asset'), requiredPermission: 'campus_facilities.bridges.finance_asset' },
  { key: 'hr-staff', title: 'HR Staff bridge', routeKey: 'bridges-hr-staff' as const, backendEndpoint: endpoint('GET', '/bridges/hr-staff'), requiredPermission: 'campus_facilities.bridges.hr_staff' },
] as const;

export const CAMPUS_FACILITIES_LIMITATIONS = [...CAMPUS_FACILITIES_NO_OVERCLAIM_COPY] as const;
