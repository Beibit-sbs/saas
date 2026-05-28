export type CampusFacilitiesPermission = string;

export type CampusFacilitiesRouteKey =
  | 'overview'
  | 'dashboard'
  | 'campus'
  | 'facilities'
  | 'buildings'
  | 'floors'
  | 'rooms'
  | 'availability'
  | 'occupancy'
  | 'dormitories'
  | 'housing-units'
  | 'housing-requests'
  | 'maintenance'
  | 'service-requests'
  | 'work-orders'
  | 'transport'
  | 'responsible-units'
  | 'safety-readiness'
  | 'bridges-access-visitor'
  | 'bridges-student-services'
  | 'bridges-finance-asset'
  | 'bridges-hr-staff'
  | 'audit-evidence'
  | 'limitations';

export interface CampusFacilitiesSafetyFlags {
  liveIotEnabled: false;
  liveGpsTrackingEnabled: false;
  buildingAutomationEnabled: false;
  accessControlEnforcementEnabled: false;
  safetyCertificationClaimed: false;
  maintenanceCompletionGuaranteed: false;
  automaticHousingDecisionEnabled: false;
  automaticEvictionEnabled: false;
  automaticStudentStaffSanctionEnabled: false;
  autonomousDispatchEnabled: false;
  externalProviderSyncEnabled: false;
  productionFacilitiesClaimed: false;
  salesReadyClaimed: false;
  gccReadyClaimed: false;
  l5L6Claimed: false;
  humanReviewRequired: true;
  incompleteData: boolean;
}

export interface CampusFacilitiesModuleBase {
  module: string;
  contractVersion: string;
  runtimeMode: string;
  tenantId: number;
  safetyFlags: CampusFacilitiesSafetyFlags;
}

export type CampusFacilitiesApiResult<T> = CampusFacilitiesModuleBase & T;

export interface CampusFacilitiesOverview extends CampusFacilitiesModuleBase {
  title: string;
  summary: string;
  routeCount: number;
  backendRouteCount: number;
  tableCount: number;
  permissionCount: number;
  bridgeCount: number;
}

export interface CampusFacilitiesDashboard extends CampusFacilitiesModuleBase {
  title: string;
  summary: string;
  widgets: CampusFacilitiesDashboardCard[];
  incompleteData: boolean;
}

export interface CampusProfile extends CampusFacilitiesModuleBase {
  title: string;
  campusCount: number;
  notes: string[];
}

export interface FacilityRecord extends CampusFacilitiesModuleBase {
  title: string;
  items: string[];
}

export interface BuildingRecord extends CampusFacilitiesModuleBase {
  title: string;
  items: string[];
}

export interface FloorRecord extends CampusFacilitiesModuleBase {
  title: string;
  items: string[];
}

export interface RoomRecord extends CampusFacilitiesModuleBase {
  title: string;
  items: string[];
}

export interface RoomTypeRecord extends CampusFacilitiesModuleBase {
  title: string;
  items: string[];
}

export interface AvailabilitySnapshot extends CampusFacilitiesModuleBase {
  title: string;
  availabilityWindows: string[];
}

export interface OccupancyVisibility extends CampusFacilitiesModuleBase {
  title: string;
  occupancyWindows: string[];
}

export interface DormitoryRecord extends CampusFacilitiesModuleBase {
  title: string;
  dormitories: string[];
}

export interface HousingUnit extends CampusFacilitiesModuleBase {
  title: string;
  units: string[];
}

export interface HousingRequestMetadata extends CampusFacilitiesModuleBase {
  title: string;
  requests: string[];
}

export interface MaintenanceRequest extends CampusFacilitiesModuleBase {
  title: string;
  requests: string[];
}

export interface ServiceRequest extends CampusFacilitiesModuleBase {
  title: string;
  requests: string[];
}

export interface WorkOrderMetadata extends CampusFacilitiesModuleBase {
  title: string;
  workOrders: string[];
}

export interface TransportRoute extends CampusFacilitiesModuleBase {
  title: string;
  routes: string[];
}

export interface TransportVehicleMetadata extends CampusFacilitiesModuleBase {
  title: string;
  vehicles: string[];
}

export interface TransportScheduleMetadata extends CampusFacilitiesModuleBase {
  title: string;
  schedules: string[];
}

export interface ResponsibleUnit extends CampusFacilitiesModuleBase {
  title: string;
  units: string[];
}

export interface SafetyReadiness extends CampusFacilitiesModuleBase {
  title: string;
  readiness: string;
  evidence: string[];
}

export interface AccessVisitorBridge extends CampusFacilitiesModuleBase {
  title: string;
  bridgeFamily: 'access-visitor';
  endpoints: string[];
}

export interface StudentServicesBridge extends CampusFacilitiesModuleBase {
  title: string;
  bridgeFamily: 'student-services';
  endpoints: string[];
}

export interface FinanceAssetBridge extends CampusFacilitiesModuleBase {
  title: string;
  bridgeFamily: 'finance-asset';
  endpoints: string[];
}

export interface HrStaffBridge extends CampusFacilitiesModuleBase {
  title: string;
  bridgeFamily: 'hr-staff';
  endpoints: string[];
}

export interface AuditEvidence extends CampusFacilitiesModuleBase {
  title: string;
  evidenceItems: string[];
}

export interface Limitations extends CampusFacilitiesModuleBase {
  title: string;
  limitations: string[];
}

export interface MetadataContract extends CampusFacilitiesModuleBase {
  title: string;
  expectedRouteCount: number;
  expectedTableCount: number;
  expectedPermissionCount: number;
  permissionNamespace: string;
}

export interface HealthResponse extends CampusFacilitiesModuleBase {
  title: string;
  status: string;
}

export interface CampusFacilitiesRouteDefinition {
  routeKey: CampusFacilitiesRouteKey;
  path: string;
  title: string;
  description: string;
  requiredPermission: CampusFacilitiesPermission;
  endpointGroup: string;
  backendEndpoints: string[];
  dashboardLike: boolean;
  bridgeRoute: boolean;
  sensitive: boolean;
  humanReviewRequired: true;
  incompleteDataSupported: true;
  forbiddenClaims: string[];
  boundaryLabels: string[];
}

export interface CampusFacilitiesPageModel extends CampusFacilitiesRouteDefinition {
  backendApiBase: string;
}

export interface CampusFacilitiesDashboardCard {
  key: string;
  title: string;
  description: string;
  backendEndpoints: string[];
  requiredPermission: CampusFacilitiesPermission;
}

export interface CampusFacilitiesPermissionSummary {
  total: number;
  granted: number;
  denied: number;
  missing: string[];
}
