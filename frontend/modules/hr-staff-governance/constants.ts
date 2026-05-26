import type { Permission } from '@/shared/config/permissions';
import { HR_STAFF_GOVERNANCE_BOUNDARY_LABELS, getHrBoundaryLabels } from './boundaryLabels';
import type {
  HrDashboardWidget,
  HrProviderProfile,
  HrRouteDefinition,
  HrRouteKey,
  HrSafetyFlags,
  HrWorkflowDefinition,
} from './types';

export const HR_STAFF_GOVERNANCE_MODULE = 'hr-staff-governance';
export const HR_STAFF_GOVERNANCE_ROUTE_FAMILY = '/console/hr-staff-governance';
export const HR_STAFF_GOVERNANCE_API_BASE = '/api/admin/hr-staff-governance';
export const HR_STAFF_GOVERNANCE_PLANNED_ROUTE_COUNT = 20;
export const HR_STAFF_GOVERNANCE_BACKEND_ROUTE_COUNT = 62;
export const HR_STAFF_GOVERNANCE_PERMISSION_COUNT = 56;
export const HR_STAFF_GOVERNANCE_RUNTIME_MODE = 'METADATA_EVIDENCE_HUMAN_REVIEW_ONLY';
export const HR_STAFF_GOVERNANCE_SOURCE_SPEC_COMMIT = '4fa0ff0';
export const HR_STAFF_GOVERNANCE_BACKEND_BASELINE_COMMIT = 'c72e6c0';
export const HR_STAFF_GOVERNANCE_DATA_SOURCE = 'computed_from_hr_staff_governance_metadata';

export const fakeMetrics = false;
export const fakeHrData = false;
export const providerConnected = false;
export const liveProviderSync = false;
export const payrollExecutionEnabled = false;
export const automaticDecisionEnabled = false;
export const hiddenScorePresent = false;
export const humanReviewRequired = true;

export const HR_STAFF_GOVERNANCE_SAFETY_FLAGS: HrSafetyFlags = {
  fake_metrics: false,
  fake_hr_data: false,
  provider_connected: false,
  live_provider_sync: false,
  payroll_execution_enabled: false,
  automatic_decision_enabled: false,
  hidden_score_present: false,
  human_review_required: true,
  incomplete_data: true,
  limitations: [
    'Metadata/evidence/human-review-only HR runtime.',
    'No provider live sync, payroll execution, or hidden score surfaces are implemented.',
  ],
};

export const HR_STAFF_GOVERNANCE_PERMISSION_VALUES = {
  overviewRead: 'hr_staff_governance.overview.read' as Permission,
  dashboardRead: 'hr_staff_governance.dashboard.read' as Permission,
  healthRead: 'hr_staff_governance.health.read' as Permission,
  limitationsRead: 'hr_staff_governance.limitations.read' as Permission,
  auditRead: 'hr_staff_governance.audit.read' as Permission,
  staffProfilesRead: 'hr_staff_governance.staff_profiles.read' as Permission,
  staffProfilesCreate: 'hr_staff_governance.staff_profiles.create' as Permission,
  staffProfilesUpdate: 'hr_staff_governance.staff_profiles.update' as Permission,
  employeeRecordsRead: 'hr_staff_governance.employee_records.read' as Permission,
  employeeRecordsCreate: 'hr_staff_governance.employee_records.create' as Permission,
  employeeRecordsUpdate: 'hr_staff_governance.employee_records.update' as Permission,
  facultyProfilesRead: 'hr_staff_governance.faculty_profiles.read' as Permission,
  facultyProfilesUpdate: 'hr_staff_governance.faculty_profiles.update' as Permission,
  recruitmentRead: 'hr_staff_governance.recruitment.read' as Permission,
  recruitmentCreate: 'hr_staff_governance.recruitment.create' as Permission,
  recruitmentReview: 'hr_staff_governance.recruitment.review' as Permission,
  hiringEvidenceRead: 'hr_staff_governance.hiring_evidence.read' as Permission,
  hiringEvidenceCreate: 'hr_staff_governance.hiring_evidence.create' as Permission,
  onboardingRead: 'hr_staff_governance.onboarding.read' as Permission,
  onboardingCreate: 'hr_staff_governance.onboarding.create' as Permission,
  onboardingUpdate: 'hr_staff_governance.onboarding.update' as Permission,
  probationRead: 'hr_staff_governance.probation.read' as Permission,
  probationReview: 'hr_staff_governance.probation.review' as Permission,
  leaveRead: 'hr_staff_governance.leave.read' as Permission,
  leaveCreate: 'hr_staff_governance.leave.create' as Permission,
  leaveReview: 'hr_staff_governance.leave.review' as Permission,
  attendanceRead: 'hr_staff_governance.attendance.read' as Permission,
  staffRequestsRead: 'hr_staff_governance.staff_requests.read' as Permission,
  staffRequestsCreate: 'hr_staff_governance.staff_requests.create' as Permission,
  staffRequestsReview: 'hr_staff_governance.staff_requests.review' as Permission,
  staffAppealsRead: 'hr_staff_governance.staff_appeals.read' as Permission,
  staffAppealsCreate: 'hr_staff_governance.staff_appeals.create' as Permission,
  staffAppealsReview: 'hr_staff_governance.staff_appeals.review' as Permission,
  policyExceptionsRead: 'hr_staff_governance.policy_exceptions.read' as Permission,
  policyExceptionsCreate: 'hr_staff_governance.policy_exceptions.create' as Permission,
  policyExceptionsReview: 'hr_staff_governance.policy_exceptions.review' as Permission,
  appraisalsRead: 'hr_staff_governance.appraisals.read' as Permission,
  appraisalsCreate: 'hr_staff_governance.appraisals.create' as Permission,
  appraisalsReview: 'hr_staff_governance.appraisals.review' as Permission,
  trainingRead: 'hr_staff_governance.training.read' as Permission,
  trainingCreate: 'hr_staff_governance.training.create' as Permission,
  trainingUpdate: 'hr_staff_governance.training.update' as Permission,
  disciplinaryCasesRead: 'hr_staff_governance.disciplinary_cases.read' as Permission,
  disciplinaryCasesCreate: 'hr_staff_governance.disciplinary_cases.create' as Permission,
  disciplinaryCasesReview: 'hr_staff_governance.disciplinary_cases.review' as Permission,
  disciplinaryEvidenceRead: 'hr_staff_governance.disciplinary_evidence.read' as Permission,
  disciplinaryEvidenceCreate: 'hr_staff_governance.disciplinary_evidence.create' as Permission,
  offboardingRead: 'hr_staff_governance.offboarding.read' as Permission,
  offboardingCreate: 'hr_staff_governance.offboarding.create' as Permission,
  offboardingUpdate: 'hr_staff_governance.offboarding.update' as Permission,
  accessLifecycleRead: 'hr_staff_governance.access_lifecycle.read' as Permission,
  accessLifecycleReview: 'hr_staff_governance.access_lifecycle.review' as Permission,
  workloadBridgeRead: 'hr_staff_governance.workload_bridge.read' as Permission,
  payrollReadinessRead: 'hr_staff_governance.payroll_readiness.read' as Permission,
  payrollReadinessReview: 'hr_staff_governance.payroll_readiness.review' as Permission,
  providerReadinessRead: 'hr_staff_governance.provider_readiness.read' as Permission,
} as const;

function apiPath(path: string) {
  return `${HR_STAFF_GOVERNANCE_API_BASE}${path}`;
}

function endpoint(method: 'GET' | 'POST' | 'PATCH', path: string) {
  return `${method} ${apiPath(path)}`;
}

export const HR_STAFF_GOVERNANCE_API_PATHS = {
  health: apiPath('/health'),
  overview: apiPath('/overview'),
  dashboard: apiPath('/dashboard'),
  safetyBoundaries: apiPath('/safety-boundaries'),
  readiness: apiPath('/readiness'),
  brainSignals: apiPath('/brain-signals'),
  bridgeSummary: (bridgeName: string) => apiPath(`/workload-bridge/${bridgeName}/summary`),
  staffProfiles: apiPath('/staff-profiles'),
  employeeRecords: apiPath('/employee-records'),
  facultyProfiles: apiPath('/faculty-profiles'),
  recruitmentRequests: apiPath('/recruitment-requests'),
  hiringEvidence: apiPath('/hiring-evidence'),
  onboardingCases: apiPath('/onboarding-cases'),
  probationReviews: apiPath('/probation-reviews'),
  leaveRequests: apiPath('/leave-requests'),
  attendance: apiPath('/attendance'),
  staffRequests: apiPath('/staff-requests'),
  staffAppeals: apiPath('/staff-appeals'),
  policyExceptions: apiPath('/policy-exceptions'),
  appraisals: apiPath('/appraisals'),
  appraisalReviews: apiPath('/appraisal-reviews'),
  trainingCertifications: apiPath('/training-certifications'),
  disciplinaryCases: apiPath('/disciplinary-cases'),
  disciplinaryEvidence: apiPath('/disciplinary-evidence'),
  offboardingCases: apiPath('/offboarding-cases'),
  accessLifecycleReviews: apiPath('/access-lifecycle-reviews'),
  workloadBridgeRecords: apiPath('/workload-bridge-records'),
  payrollReadinessProfiles: apiPath('/payroll-readiness-profiles'),
  providerReadinessEvidence: apiPath('/provider-readiness-evidence'),
  audit: apiPath('/audit'),
  limitations: apiPath('/limitations'),
  roles: apiPath('/roles'),
  permissions: apiPath('/permissions'),
  metadataContract: apiPath('/metadata-contract'),
} as const;

function routeDefinition(
  key: HrRouteKey,
  title: string,
  path: string,
  requiredPermission: Permission,
  backendEndpoints: string[],
  description: string,
  dashboardLike: boolean,
  sensitive: boolean,
) : HrRouteDefinition {
  return {
    key,
    title,
    path,
    requiredPermission,
    backendEndpoints,
    boundaryLabels: getHrBoundaryLabels(key),
    description,
    dashboardLike,
    sensitive,
    humanReviewRequired: sensitive || key === 'limitations' || key === 'dashboard' || key === 'overview',
  };
}

export const HR_STAFF_GOVERNANCE_ROUTES: HrRouteDefinition[] = [
  routeDefinition('overview', 'HR / Staff Governance Suite', HR_STAFF_GOVERNANCE_ROUTE_FAMILY, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.overviewRead, [endpoint('GET', '/overview'), endpoint('GET', '/readiness'), endpoint('GET', '/limitations')], 'Operational overview of the HR metadata and safety boundary baseline.', true, true),
  routeDefinition('dashboard', 'HR Operations Dashboard', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/dashboard`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.dashboardRead, [endpoint('GET', '/dashboard')], 'Dashboard visibility across recruitment, onboarding, leave, training, discipline, offboarding, and readiness.', true, true),
  routeDefinition('recruitment', 'Recruitment / Hiring Readiness', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/recruitment`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.recruitmentRead, [endpoint('GET', '/recruitment-requests'), endpoint('POST', '/recruitment-requests'), endpoint('POST', '/recruitment-requests/{resource_id}/review')], 'Metadata and evidence-only recruitment review surface.', false, true),
  routeDefinition('onboarding', 'Staff Onboarding', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/onboarding`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.onboardingRead, [endpoint('GET', '/onboarding-cases'), endpoint('POST', '/onboarding-cases'), endpoint('PATCH', '/onboarding-cases/{resource_id}')], 'Onboarding checklist and probation metadata managed under human review.', false, true),
  routeDefinition('employee-records', 'Employee Records', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/employee-records`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.employeeRecordsRead, [endpoint('GET', '/employee-records'), endpoint('POST', '/employee-records'), endpoint('PATCH', '/employee-records/{resource_id}')], 'Tenant-scoped employee record metadata without hidden scoring.', false, false),
  routeDefinition('staff-profiles', 'Staff Profiles', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/staff-profiles`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.staffProfilesRead, [endpoint('GET', '/staff-profiles'), endpoint('POST', '/staff-profiles'), endpoint('PATCH', '/staff-profiles/{resource_id}')], 'Core staff profile metadata and evidence links.', false, false),
  routeDefinition('faculty-profile', 'Faculty Profile / Academic Staff Portfolio', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/faculty-profile`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.facultyProfilesRead, [endpoint('GET', '/faculty-profiles'), endpoint('GET', '/workload-bridge/academic-operations/summary')], 'Read-only faculty portfolio context bridged from HR and academic operations.', false, false),
  routeDefinition('leave', 'Leave / Absence Review', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/leave`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.leaveRead, [endpoint('GET', '/leave-requests'), endpoint('POST', '/leave-requests'), endpoint('POST', '/leave-requests/{resource_id}/review')], 'Leave metadata and human review outcomes only.', false, true),
  routeDefinition('performance', 'Performance Appraisal Metadata', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/performance`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.appraisalsRead, [endpoint('GET', '/appraisals'), endpoint('POST', '/appraisals'), endpoint('POST', '/appraisal-reviews')], 'Performance cycle and review metadata without hidden employee scores.', false, true),
  routeDefinition('training', 'Training / Certification Compliance', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/training`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.trainingRead, [endpoint('GET', '/training-certifications'), endpoint('POST', '/training-certifications'), endpoint('PATCH', '/training-certifications/{resource_id}')], 'Certification compliance evidence and expiry metadata.', false, false),
  routeDefinition('requests', 'Staff Requests', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/requests`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.staffRequestsRead, [endpoint('GET', '/staff-requests'), endpoint('POST', '/staff-requests'), endpoint('POST', '/staff-requests/{resource_id}/review')], 'Staff request metadata routed into human review.', false, true),
  routeDefinition('appeals', 'Staff Appeals', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/appeals`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.staffAppealsRead, [endpoint('GET', '/staff-appeals'), endpoint('POST', '/staff-appeals'), endpoint('POST', '/staff-appeals/{resource_id}/review')], 'Appeal metadata with review-only actions.', false, true),
  routeDefinition('policy-exceptions', 'HR Policy Exceptions', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/policy-exceptions`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.policyExceptionsRead, [endpoint('GET', '/policy-exceptions'), endpoint('POST', '/policy-exceptions'), endpoint('POST', '/policy-exceptions/{resource_id}/review')], 'Policy exception tracking and review evidence only.', false, true),
  routeDefinition('disciplinary', 'Disciplinary Case Governance', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/disciplinary`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.disciplinaryCasesRead, [endpoint('GET', '/disciplinary-cases'), endpoint('POST', '/disciplinary-cases'), endpoint('POST', '/disciplinary-cases/{resource_id}/review')], 'Disciplinary case metadata and evidence without automatic outcomes.', false, true),
  routeDefinition('offboarding', 'Exit / Offboarding', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/offboarding`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.offboardingRead, [endpoint('GET', '/offboarding-cases'), endpoint('POST', '/offboarding-cases'), endpoint('PATCH', '/offboarding-cases/{resource_id}')], 'Offboarding metadata coordinated with access review and payroll readiness.', false, true),
  routeDefinition('access-lifecycle', 'Access Lifecycle Review', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/access-lifecycle`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.accessLifecycleRead, [endpoint('GET', '/access-lifecycle-reviews'), endpoint('POST', '/access-lifecycle-reviews'), endpoint('GET', '/workload-bridge/iam-access/summary')], 'Access lifecycle review metadata with no autonomous revocation.', false, true),
  routeDefinition('workload-bridge', 'Teaching Load / Workload Bridge', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/workload-bridge`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.workloadBridgeRead, [endpoint('GET', '/workload-bridge-records'), endpoint('POST', '/workload-bridge-records'), endpoint('GET', '/workload-bridge/academic-operations/summary')], 'Read-only-first bridge into academic operations workload context.', false, false),
  routeDefinition('payroll-readiness', 'Payroll / 1C Readiness', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/payroll-readiness`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.payrollReadinessRead, [endpoint('GET', '/payroll-readiness-profiles'), endpoint('POST', '/payroll-readiness-profiles'), endpoint('GET', '/workload-bridge/finance-payroll/summary')], 'Payroll readiness metadata only with no payroll execution UI.', false, true),
  routeDefinition('provider-readiness', 'Provider Readiness', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/provider-readiness`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.providerReadinessRead, [endpoint('GET', '/provider-readiness-evidence'), endpoint('GET', '/readiness'), endpoint('GET', '/workload-bridge/document-contracts/summary')], 'Provider readiness evidence with providerConnected=false and liveProviderSync=false.', false, false),
  routeDefinition('limitations', 'Limitations / Safety Boundaries', `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/limitations`, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.limitationsRead, [endpoint('GET', '/limitations'), endpoint('GET', '/safety-boundaries'), endpoint('GET', '/metadata-contract')], 'Explicit limitations, no-overclaim boundaries, and safety assertions for the HR frontend runtime.', false, true),
];

export const HR_STAFF_GOVERNANCE_ROUTE_COUNT = HR_STAFF_GOVERNANCE_ROUTES.length;

export const HR_STAFF_GOVERNANCE_NAV_ITEMS = HR_STAFF_GOVERNANCE_ROUTES.map((route) => ({
  key: route.key,
  title: route.title,
  href: route.path,
}));

export const HR_STAFF_GOVERNANCE_PROVIDER_PROFILES: HrProviderProfile[] = [
  { key: 'ONE_C_KZ', title: '1C KZ', description: 'Deferred payroll/accounting provider readiness only.', provider_connected: false, live_provider_sync: false },
  { key: 'HR_PAYROLL_PROVIDER', title: 'HR Payroll Provider', description: 'Deferred provider readiness, not connected to live payroll execution.', provider_connected: false, live_provider_sync: false },
  { key: 'IDP_SSO_KZ', title: 'IDP / SSO KZ', description: 'Identity provider readiness only for access lifecycle review context.', provider_connected: false, live_provider_sync: false },
  { key: 'EDS_KZ', title: 'EDS KZ', description: 'Digital signature provider readiness only; no live provider activation.', provider_connected: false, live_provider_sync: false },
  { key: 'EGOV_LABOR_REGISTRY', title: 'eGov Labor Registry', description: 'Registry readiness only; no external database sync or live verification.', provider_connected: false, live_provider_sync: false },
];

export const HR_STAFF_GOVERNANCE_DASHBOARD_WIDGETS: HrDashboardWidget[] = [
  { key: 'staff-lifecycle-summary', title: 'Staff Lifecycle Summary', description: 'Lifecycle counts across active metadata records.', endpointRefs: [endpoint('GET', '/dashboard')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.dashboardRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/staff-profiles`, forbiddenAction: 'No hiring or firing action', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noAutomaticHiringFiring], relatedRoutes: ['dashboard', 'staff-profiles'] },
  { key: 'recruitment-readiness', title: 'Recruitment Readiness', description: 'Recruitment pipeline readiness and review queue.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/recruitment-requests')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.recruitmentRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/recruitment`, forbiddenAction: 'No automatic hiring', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noAutomaticHiringFiring], relatedRoutes: ['dashboard', 'recruitment'] },
  { key: 'onboarding-progress', title: 'Onboarding Progress', description: 'Checklist and probation metadata progression.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/onboarding-cases')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.onboardingRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/onboarding`, forbiddenAction: 'No automatic onboarding completion', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.humanReviewRequired], relatedRoutes: ['dashboard', 'onboarding'] },
  { key: 'employee-record-completeness', title: 'Employee Record Completeness', description: 'Completeness of employee record metadata.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/employee-records')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.employeeRecordsRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/employee-records`, forbiddenAction: 'No hidden score or legal decision', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noHiddenEmployeeFacultyScore], relatedRoutes: ['dashboard', 'employee-records'] },
  { key: 'leave-review-status', title: 'Leave Request Review Status', description: 'Pending leave review queue and evidence posture.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/leave-requests')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.leaveRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/leave`, forbiddenAction: 'No automatic approval or rejection', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noAutomaticLeaveApprovalRejection], relatedRoutes: ['dashboard', 'leave'] },
  { key: 'training-certification-risk', title: 'Training Certification Risk', description: 'Certification expiry and training evidence status.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/training-certifications')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.trainingRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/training`, forbiddenAction: 'No fake compliance score', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.incompleteDataSupported], relatedRoutes: ['dashboard', 'training'] },
  { key: 'disciplinary-review-queue', title: 'Disciplinary Human Review Queue', description: 'Human review queue for disciplinary metadata.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/disciplinary-cases')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.disciplinaryCasesRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/disciplinary`, forbiddenAction: 'No automatic disciplinary outcome', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noAutomaticDisciplinaryDecision], relatedRoutes: ['dashboard', 'disciplinary'] },
  { key: 'offboarding-access-review', title: 'Offboarding Access Review', description: 'Offboarding and access review metadata.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/offboarding-cases'), endpoint('GET', '/workload-bridge/iam-access/summary')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.offboardingRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/offboarding`, forbiddenAction: 'No autonomous access revocation', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.accessLifecycleReviewOnly], relatedRoutes: ['dashboard', 'offboarding', 'access-lifecycle'] },
  { key: 'workload-bridge-visibility', title: 'Workload Bridge Visibility', description: 'Bridge visibility into academic operations workload context.', endpointRefs: [endpoint('GET', '/workload-bridge-records'), endpoint('GET', '/workload-bridge/academic-operations/summary')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.workloadBridgeRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/workload-bridge`, forbiddenAction: 'No cross-module write', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst], relatedRoutes: ['dashboard', 'workload-bridge', 'faculty-profile'] },
  { key: 'payroll-readiness-profile', title: 'Payroll Readiness Profile', description: 'Payroll readiness metadata and finance bridge visibility.', endpointRefs: [endpoint('GET', '/payroll-readiness-profiles'), endpoint('GET', '/workload-bridge/finance-payroll/summary')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.payrollReadinessRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/payroll-readiness`, forbiddenAction: 'No payroll execution', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noPayrollExecution], relatedRoutes: ['dashboard', 'payroll-readiness'] },
  { key: 'provider-readiness-status', title: 'Provider Readiness Status', description: 'Provider readiness evidence without live sync.', endpointRefs: [endpoint('GET', '/provider-readiness-evidence'), endpoint('GET', '/readiness')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.providerReadinessRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/provider-readiness`, forbiddenAction: 'No live provider sync or credentials entry', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noProviderLiveSync], relatedRoutes: ['dashboard', 'provider-readiness'] },
  { key: 'limitations-safety-boundaries', title: 'Limitations / Safety Boundaries', description: 'Surface-wide no-overclaim and safety assertions.', endpointRefs: [endpoint('GET', '/limitations'), endpoint('GET', '/safety-boundaries')], sourcePermission: HR_STAFF_GOVERNANCE_PERMISSION_VALUES.limitationsRead, drilldownPath: `${HR_STAFF_GOVERNANCE_ROUTE_FAMILY}/limitations`, forbiddenAction: 'No hidden score or false readiness claim', boundaryLabels: [HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noProductionReadyClaim], relatedRoutes: ['dashboard', 'limitations', 'overview'] },
];

export const HR_STAFF_GOVERNANCE_WORKFLOWS: HrWorkflowDefinition[] = [
  { key: 'overview-readiness-limitations', title: 'HR Overview -> Readiness -> Limitations', description: 'Open the overview, inspect readiness, and review explicit limitations.', routeKeys: ['overview', 'limitations'], endpointRefs: [endpoint('GET', '/overview'), endpoint('GET', '/readiness'), endpoint('GET', '/limitations')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.overviewRead, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.limitationsRead], humanReviewPoint: 'Boundary banner marks the slice as human-review-only.', noOverclaimBoundary: 'No automatic HR action UI.', futureE2eAssertion: 'Readiness and limitations boundary labels render together.' },
  { key: 'dashboard-incomplete-data-drilldown', title: 'Dashboard -> Incomplete Data -> Drilldown', description: 'Inspect dashboard summaries and drill into permitted pages while keeping incomplete data visible.', routeKeys: ['dashboard'], endpointRefs: [endpoint('GET', '/dashboard')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.dashboardRead], humanReviewPoint: 'Sensitive widgets retain review-only cues.', noOverclaimBoundary: 'fakeMetrics=false and fakeHrData=false remain visible.', futureE2eAssertion: 'Incomplete-data notice is visible on dashboard surfaces.' },
  { key: 'recruitment-review-evidence', title: 'Recruitment Metadata -> Committee Review Evidence', description: 'Create recruitment metadata and record committee review evidence.', routeKeys: ['recruitment'], endpointRefs: [endpoint('GET', '/recruitment-requests'), endpoint('POST', '/recruitment-requests'), endpoint('POST', '/recruitment-requests/{resource_id}/review')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.recruitmentRead, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.recruitmentReview], humanReviewPoint: 'Committee review panel records evidence only.', noOverclaimBoundary: 'No automatic hiring language or action.', futureE2eAssertion: 'Review action requires review permission and boundary banner.' },
  { key: 'onboarding-probation', title: 'Onboarding Checklist -> Probation Review Metadata', description: 'Update onboarding checklist metadata and attach probation review metadata.', routeKeys: ['onboarding'], endpointRefs: [endpoint('GET', '/onboarding-cases'), endpoint('POST', '/onboarding-cases'), endpoint('PATCH', '/onboarding-cases/{resource_id}'), endpoint('POST', '/probation-reviews')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.onboardingRead, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.probationReview], humanReviewPoint: 'Probation review must be manually confirmed.', noOverclaimBoundary: 'No automatic completion or status inference.', futureE2eAssertion: 'Probation review action is labeled human review required.' },
  { key: 'employee-profile-audit', title: 'Employee Record -> Staff Profile -> Audit Trail', description: 'Navigate between employee records, staff profiles, and audit references.', routeKeys: ['employee-records', 'staff-profiles'], endpointRefs: [endpoint('GET', '/employee-records'), endpoint('GET', '/staff-profiles'), endpoint('GET', '/audit')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.employeeRecordsRead, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.staffProfilesRead, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.auditRead], humanReviewPoint: 'Audit trail supports manual verification only.', noOverclaimBoundary: 'No hidden employee score or decision scoring.', futureE2eAssertion: 'Audit timeline remains read-only.' },
  { key: 'leave-review-evidence', title: 'Leave Request -> Human Review -> Evidence Status', description: 'Review leave requests and track evidence status without automatic decisions.', routeKeys: ['leave'], endpointRefs: [endpoint('GET', '/leave-requests'), endpoint('POST', '/leave-requests'), endpoint('POST', '/leave-requests/{resource_id}/review')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.leaveRead, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.leaveReview], humanReviewPoint: 'Review action panel is explicitly manual.', noOverclaimBoundary: 'No automatic approval or rejection.', futureE2eAssertion: 'Human-review-only copy is visible on leave review panel.' },
  { key: 'appraisal-no-score-boundary', title: 'Appraisal Cycle -> Review Evidence -> No Score Boundary', description: 'Track performance appraisal metadata without hidden employee or faculty scores.', routeKeys: ['performance'], endpointRefs: [endpoint('GET', '/appraisals'), endpoint('POST', '/appraisals'), endpoint('POST', '/appraisal-reviews')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.appraisalsRead, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.appraisalsReview], humanReviewPoint: 'Appraisal review evidence is manually recorded.', noOverclaimBoundary: 'No hidden employee or faculty score.', futureE2eAssertion: 'No-score boundary label is visible on performance route.' },
  { key: 'training-compliance-evidence', title: 'Training Certification -> Expiry Risk -> Compliance Evidence', description: 'Track training/certification expiry risk with incomplete-data support.', routeKeys: ['training'], endpointRefs: [endpoint('GET', '/training-certifications'), endpoint('POST', '/training-certifications'), endpoint('PATCH', '/training-certifications/{resource_id}')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.trainingRead, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.trainingUpdate], humanReviewPoint: 'Evidence confirmation remains manual.', noOverclaimBoundary: 'No fake compliance metric or hidden score.', futureE2eAssertion: 'Incomplete-data notice stays visible on training surfaces.' },
  { key: 'disciplinary-human-review', title: 'Disciplinary Case -> Human Review -> No Automatic Decision Boundary', description: 'Track disciplinary cases, evidence, and review metadata without automatic outcomes.', routeKeys: ['disciplinary'], endpointRefs: [endpoint('GET', '/disciplinary-cases'), endpoint('POST', '/disciplinary-cases'), endpoint('POST', '/disciplinary-cases/{resource_id}/review')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.disciplinaryCasesRead, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.disciplinaryCasesReview], humanReviewPoint: 'Disciplinary review panel requires a human reviewer.', noOverclaimBoundary: 'No automatic disciplinary decision.', futureE2eAssertion: 'No forbidden auto-discipline labels appear.' },
  { key: 'offboarding-access-review', title: 'Offboarding -> Access Lifecycle Review -> No Autonomous Revocation Boundary', description: 'Coordinate offboarding metadata with access lifecycle reviews and IAM bridge context.', routeKeys: ['offboarding', 'access-lifecycle'], endpointRefs: [endpoint('GET', '/offboarding-cases'), endpoint('PATCH', '/offboarding-cases/{resource_id}'), endpoint('GET', '/access-lifecycle-reviews'), endpoint('POST', '/access-lifecycle-reviews'), endpoint('GET', '/workload-bridge/iam-access/summary')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.offboardingRead, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.accessLifecycleReview], humanReviewPoint: 'Access lifecycle review submissions stay manual.', noOverclaimBoundary: 'No autonomous access revocation.', futureE2eAssertion: 'Review-only badge is visible on access lifecycle page.' },
  { key: 'workload-bridge-read-only', title: 'Workload Bridge -> Academic Operations Read-only Context', description: 'Inspect workload bridge context without any cross-suite write affordance.', routeKeys: ['workload-bridge', 'faculty-profile'], endpointRefs: [endpoint('GET', '/workload-bridge-records'), endpoint('GET', '/workload-bridge/academic-operations/summary')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.workloadBridgeRead], humanReviewPoint: 'Bridge data informs manual review only.', noOverclaimBoundary: 'Bridge-first / read-only-first.', futureE2eAssertion: 'No cross-module mutation controls render.' },
  { key: 'payroll-provider-deferred', title: 'Payroll Readiness -> Provider Deferred Boundary', description: 'Review payroll readiness and provider readiness metadata while keeping provider connection disabled.', routeKeys: ['payroll-readiness', 'provider-readiness'], endpointRefs: [endpoint('GET', '/payroll-readiness-profiles'), endpoint('POST', '/payroll-readiness-profiles'), endpoint('GET', '/provider-readiness-evidence'), endpoint('GET', '/readiness'), endpoint('GET', '/workload-bridge/finance-payroll/summary')], requiredPermissions: [HR_STAFF_GOVERNANCE_PERMISSION_VALUES.payrollReadinessRead, HR_STAFF_GOVERNANCE_PERMISSION_VALUES.providerReadinessRead], humanReviewPoint: 'Payroll/provider readiness remains manual and deferred.', noOverclaimBoundary: 'No payroll execution and no live provider sync.', futureE2eAssertion: 'Provider deferred badge renders and no sync-now control exists.' },
];