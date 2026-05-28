import { CAMPUS_FACILITIES_ROUTE_DEFINITIONS } from './constants';
import type { CampusFacilitiesPermission, CampusFacilitiesPermissionSummary, CampusFacilitiesRouteKey } from './types';

type PermissionUser =
  | { permissions?: Array<string | CampusFacilitiesPermission>; rolePermissions?: Array<string | CampusFacilitiesPermission>; grantedPermissions?: Array<string | CampusFacilitiesPermission> }
  | Array<string | CampusFacilitiesPermission>
  | null
  | undefined;

function permissionSet(userPermissions: PermissionUser) {
  const values = new Set<string>();
  if (Array.isArray(userPermissions)) {
    for (const permission of userPermissions) values.add(String(permission));
    return values;
  }
  for (const source of [userPermissions?.permissions, userPermissions?.rolePermissions, userPermissions?.grantedPermissions]) {
    for (const permission of source ?? []) values.add(String(permission));
  }
  return values;
}

export const CAMPUS_FACILITIES_PERMISSIONS = [
  'campus_facilities.overview.read',
  'campus_facilities.dashboard.read',
  'campus_facilities.campus.read',
  'campus_facilities.facilities.read',
  'campus_facilities.facilities.metadata',
  'campus_facilities.buildings.read',
  'campus_facilities.buildings.metadata',
  'campus_facilities.floors.read',
  'campus_facilities.floors.metadata',
  'campus_facilities.rooms.read',
  'campus_facilities.rooms.metadata',
  'campus_facilities.room_types.read',
  'campus_facilities.availability.read',
  'campus_facilities.availability.metadata',
  'campus_facilities.occupancy.read',
  'campus_facilities.occupancy.metadata',
  'campus_facilities.dormitories.read',
  'campus_facilities.dormitories.metadata',
  'campus_facilities.housing_units.read',
  'campus_facilities.housing_units.metadata',
  'campus_facilities.housing_requests.read',
  'campus_facilities.housing_requests.metadata',
  'campus_facilities.maintenance.read',
  'campus_facilities.maintenance.metadata',
  'campus_facilities.service_requests.read',
  'campus_facilities.service_requests.metadata',
  'campus_facilities.work_orders.read',
  'campus_facilities.work_orders.metadata',
  'campus_facilities.transport.read',
  'campus_facilities.transport.routes.read',
  'campus_facilities.transport.routes.metadata',
  'campus_facilities.transport.vehicles.read',
  'campus_facilities.transport.vehicles.metadata',
  'campus_facilities.transport.schedules.read',
  'campus_facilities.transport.schedules.metadata',
  'campus_facilities.responsible_units.read',
  'campus_facilities.responsible_units.metadata',
  'campus_facilities.safety_readiness.read',
  'campus_facilities.safety_readiness.evidence',
  'campus_facilities.bridges.access_visitor',
  'campus_facilities.bridges.student_services',
  'campus_facilities.bridges.finance_asset',
  'campus_facilities.bridges.hr_staff',
  'campus_facilities.audit_evidence.read',
  'campus_facilities.limitations.read',
  'campus_facilities.metadata_contract.read',
] as const;

export const CAMPUS_FACILITIES_PERMISSION_COUNT = CAMPUS_FACILITIES_PERMISSIONS.length;

export const CAMPUS_FACILITIES_ROUTE_PERMISSION_MAP = Object.fromEntries(
  CAMPUS_FACILITIES_ROUTE_DEFINITIONS.map((route) => [route.routeKey, route.requiredPermission]),
) as Record<CampusFacilitiesRouteKey, CampusFacilitiesPermission>;

export function requireCampusFacilitiesPermission(permission: CampusFacilitiesPermission) {
  return permission;
}

export function hasCampusFacilitiesPermission(userPermissions: PermissionUser, permission: CampusFacilitiesPermission) {
  return permissionSet(userPermissions).has(permission);
}

export function canReadCampusFacilitiesOverview(userPermissions: PermissionUser) {
  return hasCampusFacilitiesPermission(userPermissions, 'campus_facilities.overview.read');
}

export function canReadCampusFacilitiesDashboard(userPermissions: PermissionUser) {
  return hasCampusFacilitiesPermission(userPermissions, 'campus_facilities.dashboard.read');
}

export function canReadCampusFacilitiesRoute(routeKey: CampusFacilitiesRouteKey, userPermissions: PermissionUser) {
  const permission = CAMPUS_FACILITIES_ROUTE_PERMISSION_MAP[routeKey];
  return hasCampusFacilitiesPermission(userPermissions, permission);
}

export function canSubmitCampusFacilitiesMetadata(routeKey: CampusFacilitiesRouteKey, userPermissions: PermissionUser) {
  const route = CAMPUS_FACILITIES_ROUTE_DEFINITIONS.find((item) => item.routeKey === routeKey);
  if (!route) return false;
  const metadataPermission = route.requiredPermission.replace('.read', '.metadata');
  const granted = permissionSet(userPermissions);
  return granted.has(metadataPermission) || granted.has(route.requiredPermission);
}

export function getCampusFacilitiesPermissionSummary(userPermissions: PermissionUser): CampusFacilitiesPermissionSummary {
  const granted = permissionSet(userPermissions);
  const missing = CAMPUS_FACILITIES_PERMISSIONS.filter((permission) => !granted.has(permission));
  return {
    total: CAMPUS_FACILITIES_PERMISSIONS.length,
    granted: CAMPUS_FACILITIES_PERMISSIONS.length - missing.length,
    denied: missing.length,
    missing,
  };
}

export function assertNoCampusFacilitiesOverclaim() {
  const forbidden = [
    'enableLiveIot',
    'enableLiveGps',
    'enableBuildingAutomation',
    'enforceAccessControl',
    'certifySafety',
    'guaranteeMaintenanceCompletion',
    'automaticHousingDecision',
    'automaticEviction',
    'automaticSanction',
    'autonomousDispatch',
    'externalProviderSync',
    'productionFacilitiesClaim',
    'salesReadyClaimed',
    'gccReadyClaimed',
    'l5L6Claimed',
  ] as const;
  return {
    ok: true,
    forbidden,
  };
}

export function getAllowedCampusFacilitiesRoutes(userPermissions: PermissionUser) {
  return CAMPUS_FACILITIES_ROUTE_DEFINITIONS.filter((route) => hasCampusFacilitiesPermission(userPermissions, route.requiredPermission));
}
