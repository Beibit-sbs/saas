import type { Permission } from '@/shared/config/permissions';

export type HrRouteKey =
  | 'overview'
  | 'dashboard'
  | 'recruitment'
  | 'onboarding'
  | 'employee-records'
  | 'staff-profiles'
  | 'faculty-profile'
  | 'leave'
  | 'performance'
  | 'training'
  | 'requests'
  | 'appeals'
  | 'policy-exceptions'
  | 'disciplinary'
  | 'offboarding'
  | 'access-lifecycle'
  | 'workload-bridge'
  | 'payroll-readiness'
  | 'provider-readiness'
  | 'limitations';

export interface HrSafetyFlags {
  fake_metrics: false;
  fake_hr_data: false;
  provider_connected: false;
  live_provider_sync: false;
  payroll_execution_enabled: false;
  automatic_decision_enabled: false;
  hidden_score_present: false;
  human_review_required: true;
  incomplete_data: boolean;
  limitations: string[];
}

export interface HrApiResult<T> {
  items: T[];
}

export interface HrMetadataEntity extends HrSafetyFlags {
  id: number | string;
  tenant_id?: number;
  status: string;
  title: string;
  description?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  metadata?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  payload?: Record<string, unknown>;
  owner_ref?: string | null;
  reviewer_ref?: string | null;
  source_capability_id?: string | null;
  source_family_id?: string | null;
  reference?: string | null;
  read_only_first?: boolean;
  mutation_allowed?: boolean;
}

export interface HrFoundationSummary extends HrSafetyFlags {
  tenant_id: number;
  module: string;
  product_vertical: string;
  contract_version: string;
  runtime_mode: string;
  table_count: number;
  route_count: number;
  permission_count: number;
  detailed_capability_count: number;
  capability_family_count: number;
  workflow_group_count: number;
  role_count: number;
  data_source: string;
  boundary_summary: Record<string, boolean>;
}

export interface HrSafetyBoundary extends HrSafetyFlags {
  module: string;
  route_count: number;
  permission_count: number;
  runtime_mode: string;
  forbidden_actions: string[];
  boundary_labels: string[];
}

export interface HrDashboardSummary extends HrSafetyFlags {
  tenant_id: number;
  generated_at: string | null;
  contract_version: string;
  source_spec_commit: string;
  source_backend_baseline_commit: string;
  data_source: string;
  staff_lifecycle_summary: Record<string, number>;
  recruitment_summary: Record<string, number>;
  onboarding_summary: Record<string, number>;
  employee_record_summary: Record<string, number>;
  leave_summary: Record<string, number>;
  training_summary: Record<string, number>;
  disciplinary_summary: Record<string, number>;
  offboarding_summary: Record<string, number>;
  workload_bridge_summary: Record<string, number>;
  payroll_readiness_summary: Record<string, number>;
  provider_readiness_summary: Record<string, number>;
  boundary_summary: Record<string, boolean>;
}

export interface HrStaffProfile extends HrMetadataEntity {
  staff_profile_ref?: string | null;
  department_ref?: string | null;
  faculty_ref?: string | null;
}

export interface HrEmployeeRecord extends HrMetadataEntity {
  employee_record_ref?: string | null;
  employment_type?: string | null;
}

export interface HrRecruitmentRequest extends HrMetadataEntity {
  recruitment_ref?: string | null;
  committee_ref?: string | null;
}

export interface HrHiringEvidence extends HrMetadataEntity {
  evidence_ref?: string | null;
  recruitment_ref?: string | null;
}

export interface HrOnboardingCase extends HrMetadataEntity {
  onboarding_ref?: string | null;
  staff_profile_ref?: string | null;
}

export interface HrProbationReview extends HrMetadataEntity {
  probation_ref?: string | null;
  onboarding_ref?: string | null;
}

export interface HrLeaveRequest extends HrMetadataEntity {
  leave_ref?: string | null;
  attendance_ref?: string | null;
}

export interface HrAppraisal extends HrMetadataEntity {
  appraisal_ref?: string | null;
  cycle_ref?: string | null;
}

export interface HrTrainingCertification extends HrMetadataEntity {
  training_ref?: string | null;
  certification_ref?: string | null;
}

export interface HrStaffRequest extends HrMetadataEntity {
  request_ref?: string | null;
}

export interface HrStaffAppeal extends HrMetadataEntity {
  appeal_ref?: string | null;
}

export interface HrPolicyException extends HrMetadataEntity {
  policy_exception_ref?: string | null;
}

export interface HrDisciplinaryCase extends HrMetadataEntity {
  disciplinary_case_ref?: string | null;
}

export interface HrOffboardingCase extends HrMetadataEntity {
  offboarding_ref?: string | null;
}

export interface HrAccessLifecycleReview extends HrMetadataEntity {
  access_lifecycle_ref?: string | null;
}

export interface HrWorkloadBridgeRecord extends HrMetadataEntity {
  workload_bridge_ref?: string | null;
  bridge_name?: string | null;
}

export interface HrPayrollReadinessProfile extends HrMetadataEntity {
  payroll_readiness_ref?: string | null;
}

export interface HrProviderReadinessEvidence extends HrMetadataEntity {
  provider_readiness_ref?: string | null;
  provider_key?: string | null;
}

export interface HrAuditEvent extends HrMetadataEntity {
  event_type?: string | null;
  actor_ref?: string | null;
}

export interface HrEvidenceItem extends HrMetadataEntity {
  evidence_ref?: string | null;
  entity_type?: string | null;
}

export interface HrLimitation {
  code: string;
  title: string;
  description: string;
}

export interface HrBridgeSummary extends HrSafetyFlags {
  bridge_name: string;
  bridge_title: string;
  connected_module: string;
  read_only: true;
  summary: Record<string, number | string | boolean>;
}

export interface HrBrainSignal extends HrSafetyFlags {
  signal_key: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
}

export interface HrProviderProfile {
  key: 'ONE_C_KZ' | 'HR_PAYROLL_PROVIDER' | 'IDP_SSO_KZ' | 'EDS_KZ' | 'EGOV_LABOR_REGISTRY';
  title: string;
  description: string;
  provider_connected: false;
  live_provider_sync: false;
}

export interface HrPermission {
  key: string;
  value: Permission;
  category: string;
}

export interface HrRole {
  key: string;
  title: string;
  description: string;
  permissions: Permission[];
}

export interface HrReadiness extends HrSafetyFlags {
  contract_version: string;
  runtime_mode: string;
  backend_route_count: number;
  backend_permission_count: number;
  provider_profiles: HrProviderProfile[];
  bridge_targets: string[];
}

export interface HrRouteDefinition {
  key: HrRouteKey;
  title: string;
  path: string;
  requiredPermission: Permission;
  backendEndpoints: string[];
  boundaryLabels: string[];
  description: string;
  dashboardLike: boolean;
  sensitive: boolean;
  humanReviewRequired: boolean;
}

export interface HrDashboardWidget {
  key: string;
  title: string;
  description: string;
  endpointRefs: string[];
  sourcePermission: Permission;
  drilldownPath: string;
  forbiddenAction: string;
  boundaryLabels: string[];
  relatedRoutes: HrRouteKey[];
}

export interface HrWorkflowDefinition {
  key: string;
  title: string;
  description: string;
  routeKeys: HrRouteKey[];
  endpointRefs: string[];
  requiredPermissions: Permission[];
  humanReviewPoint: string;
  noOverclaimBoundary: string;
  futureE2eAssertion: string;
}