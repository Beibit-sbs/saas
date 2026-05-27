export type SacPermission = string;

export type SacRouteKey =
  | 'overview'
  | 'dashboard'
  | 'access-governance'
  | 'roles-permissions'
  | 'rbac-abac'
  | 'sessions'
  | 'login-events'
  | 'mfa-readiness'
  | 'tenant-isolation'
  | 'incidents'
  | 'incident-review'
  | 'remediation'
  | 'risks'
  | 'compliance-controls'
  | 'policy-controls'
  | 'audit-events'
  | 'sensitive-actions'
  | 'data-protection'
  | 'privacy-readiness'
  | 'exceptions'
  | 'visitor-access'
  | 'bridges'
  | 'limitations';

export interface SacSafetyFlags {
  fake_security_certification: false;
  fake_compliance_certification: false;
  legal_regulatory_compliance_claimed: false;
  soc_siem_replacement_claimed: false;
  fake_incident_resolution: false;
  fake_audit_proof: false;
  fake_penetration_test_result: false;
  fake_vulnerability_scan_result: false;
  fake_risk_score: false;
  hidden_user_risk_score_present: false;
  discriminatory_ranking_present: false;
  autonomous_enforcement_enabled: false;
  automatic_user_blocking_enabled: false;
  automatic_user_sanction_enabled: false;
  automatic_data_deletion_enabled: false;
  external_regulator_submission_enabled: false;
  production_security_claimed: false;
  human_review_required: true;
  incomplete_data: boolean;
  limitations: string[];
}

export interface SacModuleBase {
  module: string;
  contract_version: string;
  runtime_mode: string;
  tenant_id: number;
  safety_flags: SacSafetyFlags;
}

export type SacApiResult<T> = SacModuleBase & T;

export interface SacOverview extends SacModuleBase {
  title: string;
  summary: string;
  route_count: number;
  backend_route_count: number;
  table_count: number;
  permission_count: number;
  bridge_count: number;
  data_source: string;
}

export interface SacReadiness extends SacModuleBase {
  title: string;
  readiness_status: string;
  recommended_next_step: string;
  missing_evidence: string[];
}

export interface SacDashboard extends SacModuleBase {
  title: string;
  summary: string;
  widgets: SacDashboardWidget[];
  incomplete_data: boolean;
}

export interface SacLimitations extends SacModuleBase {
  title: string;
  limitations: string[];
}

export interface SacRole {
  role: string;
  scope: string;
  permissions: SacPermission[];
}

export interface SacPermissionRecord {
  permission: SacPermission;
  description?: string;
}

export interface SacAccessGovernance extends SacModuleBase {
  title: string;
  summary: string;
  routes: SacRouteDefinition[];
}

export interface SacRbacEvidence extends SacModuleBase {
  title: string;
  evidence_status: string;
  limitations: string[];
}

export interface SacAbacEvidence extends SacModuleBase {
  title: string;
  evidence_status: string;
  limitations: string[];
}

export interface SacSessionVisibility extends SacModuleBase {
  title: string;
  sessions: string[];
}

export interface SacLoginEventReview extends SacModuleBase {
  title: string;
  login_events: string[];
}

export interface SacMfaReadiness extends SacModuleBase {
  title: string;
  readiness_status: string;
  evidence_items: string[];
}

export interface SacTenantIsolationEvidence extends SacModuleBase {
  title: string;
  evidence_items: string[];
}

export interface SacSecurityIncident extends SacModuleBase {
  title: string;
  incidents: string[];
}

export interface SacIncidentReview extends SacModuleBase {
  title: string;
  reviews: string[];
}

export interface SacRemediationTracking extends SacModuleBase {
  title: string;
  items: string[];
}

export interface SacRiskRegister extends SacModuleBase {
  title: string;
  risks: string[];
}

export interface SacComplianceControl extends SacModuleBase {
  title: string;
  controls: string[];
}

export interface SacPolicyControlBridge extends SacModuleBase {
  title: string;
  policies: string[];
}

export interface SacAuditEventReview extends SacModuleBase {
  title: string;
  events: string[];
}

export interface SacSensitiveActionReview extends SacModuleBase {
  title: string;
  reviews: string[];
}

export interface SacDataProtectionReadiness extends SacModuleBase {
  title: string;
  evidence: string[];
}

export interface SacPrivacyReadiness extends SacModuleBase {
  title: string;
  evidence: string[];
}

export interface SacSecurityException extends SacModuleBase {
  title: string;
  exceptions: string[];
}

export interface SacVisitorAccessBridge extends SacModuleBase {
  title: string;
  visitors: string[];
}

export interface SacCrossVerticalBridge extends SacModuleBase {
  title: string;
  bridge_family: string;
  endpoints: string[];
}

export interface SacMetadataContract extends SacModuleBase {
  title: string;
  expected_table_count: number;
  expected_route_count: number;
  expected_permission_count: number;
  permission_namespace: string;
}

export interface SacDashboardWidget {
  key: string;
  title: string;
  description: string;
  backendEndpoints: string[];
  requiredPermission: SacPermission;
}

export interface SacWorkflowDefinition {
  key: string;
  title: string;
  routeKey: SacRouteKey;
  summary: string;
  humanReviewPoint: string;
}

export interface SacBridgeFamily {
  key: string;
  title: string;
  routeKey: SacRouteKey;
  summary: string;
  backendEndpoint: string;
  requiredPermission: SacPermission;
}

export interface SacRouteDefinition {
  key: SacRouteKey;
  title: string;
  route: string;
  requiredPermission: SacPermission;
  backendEndpoints: string[];
  primaryWidgets: string[];
  safetyBoundaryLabels: string[];
  emptyState: string;
  incompleteDataNotice: string;
  permissionDeniedState: string;
  noOverclaimFooter: string[];
  humanReviewBadge: string;
  noForbiddenUiActions: string[];
}

export interface SacPageModel extends SacRouteDefinition {
  backendApiBase: string;
  humanReviewRequired: true;
}
