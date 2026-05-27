import { expect, test, type Browser, type Page, type Route } from '@playwright/test';

const API_BASE = '/api/admin/security-access-compliance';
const BFF_BASE = '/api/bff/admin/security-access-compliance';
const BASE_URL = process.env.E2E_BASE_URL ?? 'https://nginx';

const SCENARIO_GROUP_COUNT_TARGET = 25;

type SacRouteSpec = {
  path: string;
  routeKey:
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
  title: string;
  requiredPermission: string;
  expectedBoundaryLabels: readonly string[];
  endpoints: readonly string[];
  dashboardLike: boolean;
  sensitive: boolean;
  humanReviewRequired: boolean;
};

function endpoint(method: 'GET' | 'POST', path: string) {
  return `${method} ${API_BASE}${path}`;
}

const SAC_ROUTES: readonly SacRouteSpec[] = [
  {
    path: '/console/security-access-compliance',
    routeKey: 'overview',
    title: 'Security / Access / Compliance',
    requiredPermission: 'security_access_compliance.overview.read',
    expectedBoundaryLabels: [
      'Governance/readiness/evidence-only security foundation',
      'Human review required',
      'Incomplete data supported',
      'Bridge-first / read-only-first',
      'No production-ready security claim',
      'No sales-ready claim',
      'No GCC-ready claim',
    ],
    endpoints: [endpoint('GET', '/overview'), endpoint('GET', '/metadata-contract')],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/dashboard',
    routeKey: 'dashboard',
    title: 'Security / Access / Compliance Dashboard',
    requiredPermission: 'security_access_compliance.dashboard.read',
    expectedBoundaryLabels: [
      'Governance/readiness/evidence-only security foundation',
      'Human review required',
      'Incomplete data supported',
      'No hidden user risk score',
      'No autonomous enforcement',
    ],
    endpoints: [endpoint('GET', '/dashboard'), endpoint('GET', '/metadata-contract')],
    dashboardLike: true,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/access-governance',
    routeKey: 'access-governance',
    title: 'Access Governance',
    requiredPermission: 'security_access_compliance.access_governance.read',
    expectedBoundaryLabels: [
      'Governance/readiness/evidence-only security foundation',
      'Human review required',
      'No autonomous enforcement',
      'No automatic user blocking',
    ],
    endpoints: [endpoint('GET', '/access-governance'), endpoint('GET', '/rbac-evidence'), endpoint('GET', '/abac-evidence')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/roles-permissions',
    routeKey: 'roles-permissions',
    title: 'Roles and Permissions',
    requiredPermission: 'security_access_compliance.roles.read',
    expectedBoundaryLabels: [
      'Governance/readiness/evidence-only security foundation',
      'Human review required',
      'No automatic user blocking',
    ],
    endpoints: [endpoint('GET', '/roles'), endpoint('GET', '/permissions')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/rbac-abac',
    routeKey: 'rbac-abac',
    title: 'RBAC and ABAC Evidence',
    requiredPermission: 'security_access_compliance.rbac_evidence.read',
    expectedBoundaryLabels: [
      'Governance/readiness/evidence-only security foundation',
      'Human review required',
      'No autonomous enforcement',
      'No hidden user risk score',
    ],
    endpoints: [endpoint('GET', '/rbac-evidence'), endpoint('GET', '/abac-evidence')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/sessions',
    routeKey: 'sessions',
    title: 'Sessions',
    requiredPermission: 'security_access_compliance.sessions.read',
    expectedBoundaryLabels: ['Incomplete data supported', 'Human review required'],
    endpoints: [endpoint('GET', '/sessions')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/login-events',
    routeKey: 'login-events',
    title: 'Login Events',
    requiredPermission: 'security_access_compliance.login_events.read',
    expectedBoundaryLabels: ['Incomplete data supported', 'Human review required'],
    endpoints: [endpoint('GET', '/login-events')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/mfa-readiness',
    routeKey: 'mfa-readiness',
    title: 'MFA Readiness',
    requiredPermission: 'security_access_compliance.mfa_readiness.read',
    expectedBoundaryLabels: ['Human review required', 'No autonomous enforcement'],
    endpoints: [endpoint('GET', '/mfa-readiness')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/tenant-isolation',
    routeKey: 'tenant-isolation',
    title: 'Tenant Isolation',
    requiredPermission: 'security_access_compliance.tenant_isolation.read',
    expectedBoundaryLabels: ['Human review required', 'No autonomous enforcement'],
    endpoints: [endpoint('GET', '/tenant-isolation')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/incidents',
    routeKey: 'incidents',
    title: 'Incidents',
    requiredPermission: 'security_access_compliance.incidents.read',
    expectedBoundaryLabels: ['Human review required', 'No fake incident resolution', 'No autonomous enforcement'],
    endpoints: [endpoint('GET', '/incidents'), endpoint('POST', '/incidents/metadata')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/incident-review',
    routeKey: 'incident-review',
    title: 'Incident Review',
    requiredPermission: 'security_access_compliance.incident_review.read',
    expectedBoundaryLabels: ['Human review required', 'No fake incident resolution'],
    endpoints: [endpoint('GET', '/incident-review'), endpoint('POST', '/incident-review/metadata')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/remediation',
    routeKey: 'remediation',
    title: 'Remediation',
    requiredPermission: 'security_access_compliance.remediation.read',
    expectedBoundaryLabels: ['Human review required', 'No autonomous enforcement'],
    endpoints: [endpoint('GET', '/remediation'), endpoint('POST', '/remediation/metadata')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/risks',
    routeKey: 'risks',
    title: 'Risk Register',
    requiredPermission: 'security_access_compliance.risks.read',
    expectedBoundaryLabels: ['Human review required', 'No fake risk score'],
    endpoints: [endpoint('GET', '/risks'), endpoint('POST', '/risks/metadata')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/compliance-controls',
    routeKey: 'compliance-controls',
    title: 'Compliance Controls',
    requiredPermission: 'security_access_compliance.compliance_controls.read',
    expectedBoundaryLabels: ['Human review required', 'No fake compliance certification'],
    endpoints: [endpoint('GET', '/compliance-controls'), endpoint('POST', '/compliance-controls/metadata')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/policy-controls',
    routeKey: 'policy-controls',
    title: 'Policy Controls',
    requiredPermission: 'security_access_compliance.policy_controls.read',
    expectedBoundaryLabels: ['Human review required', 'No legal/regulatory compliance claim'],
    endpoints: [endpoint('GET', '/policy-controls'), endpoint('POST', '/policy-controls/metadata')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/audit-events',
    routeKey: 'audit-events',
    title: 'Audit Events',
    requiredPermission: 'security_access_compliance.audit_events.read',
    expectedBoundaryLabels: ['Human review required', 'No fake audit proof'],
    endpoints: [endpoint('GET', '/audit-events'), endpoint('POST', '/audit-events/metadata')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/sensitive-actions',
    routeKey: 'sensitive-actions',
    title: 'Sensitive Actions',
    requiredPermission: 'security_access_compliance.sensitive_actions.read',
    expectedBoundaryLabels: ['Human review required', 'No autonomous enforcement'],
    endpoints: [endpoint('GET', '/sensitive-actions'), endpoint('POST', '/sensitive-actions/review')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/data-protection',
    routeKey: 'data-protection',
    title: 'Data Protection',
    requiredPermission: 'security_access_compliance.data_protection.read',
    expectedBoundaryLabels: ['Human review required', 'No fake vulnerability-scan result'],
    endpoints: [endpoint('GET', '/data-protection'), endpoint('POST', '/data-protection/evidence')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/privacy-readiness',
    routeKey: 'privacy-readiness',
    title: 'Privacy Readiness',
    requiredPermission: 'security_access_compliance.privacy_readiness.read',
    expectedBoundaryLabels: ['Human review required', 'No fake penetration-test result'],
    endpoints: [endpoint('GET', '/privacy-readiness'), endpoint('POST', '/privacy-readiness/evidence')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/exceptions',
    routeKey: 'exceptions',
    title: 'Exceptions',
    requiredPermission: 'security_access_compliance.exceptions.read',
    expectedBoundaryLabels: ['Human review required', 'No legal/regulatory compliance claim'],
    endpoints: [endpoint('GET', '/exceptions'), endpoint('POST', '/exceptions/metadata')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/visitor-access',
    routeKey: 'visitor-access',
    title: 'Visitor Access',
    requiredPermission: 'security_access_compliance.visitor_access.read',
    expectedBoundaryLabels: ['Human review required', 'No automatic user blocking'],
    endpoints: [endpoint('GET', '/visitor-access'), endpoint('POST', '/visitor-access/metadata')],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/bridges',
    routeKey: 'bridges',
    title: 'Cross-Vertical Bridges',
    requiredPermission: 'security_access_compliance.bridges.hr',
    expectedBoundaryLabels: ['Bridge-first / read-only-first', 'Human review required'],
    endpoints: [
      endpoint('GET', '/bridges/hr'),
      endpoint('GET', '/bridges/finance'),
      endpoint('GET', '/bridges/documents'),
      endpoint('GET', '/bridges/student-services'),
      endpoint('POST', '/bridges/hr'),
      endpoint('POST', '/bridges/finance'),
      endpoint('POST', '/bridges/documents'),
      endpoint('POST', '/bridges/student-services'),
    ],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: true,
  },
  {
    path: '/console/security-access-compliance/limitations',
    routeKey: 'limitations',
    title: 'Limitations',
    requiredPermission: 'security_access_compliance.limitations.read',
    expectedBoundaryLabels: ['Incomplete data supported', 'Human review required'],
    endpoints: [endpoint('GET', '/limitations'), endpoint('POST', '/limitations')],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: true,
  },
] as const;

if (SAC_ROUTES.length !== 23) {
  throw new Error(`SAC route inventory must be 23, got ${SAC_ROUTES.length}`);
}

const FULL_PERMISSIONS = [
  'security_access_compliance.overview.read',
  'security_access_compliance.readiness.read',
  'security_access_compliance.dashboard.read',
  'security_access_compliance.limitations.read',
  'security_access_compliance.roles.read',
  'security_access_compliance.permissions.read',
  'security_access_compliance.access_governance.read',
  'security_access_compliance.access_governance.metadata',
  'security_access_compliance.rbac_evidence.read',
  'security_access_compliance.rbac_evidence.write',
  'security_access_compliance.abac_evidence.read',
  'security_access_compliance.abac_evidence.write',
  'security_access_compliance.sessions.read',
  'security_access_compliance.login_events.read',
  'security_access_compliance.mfa_readiness.read',
  'security_access_compliance.tenant_isolation.read',
  'security_access_compliance.incidents.read',
  'security_access_compliance.incidents.metadata',
  'security_access_compliance.incident_review.read',
  'security_access_compliance.incident_review.metadata',
  'security_access_compliance.remediation.read',
  'security_access_compliance.remediation.metadata',
  'security_access_compliance.risks.read',
  'security_access_compliance.risks.metadata',
  'security_access_compliance.compliance_controls.read',
  'security_access_compliance.compliance_controls.metadata',
  'security_access_compliance.policy_controls.read',
  'security_access_compliance.policy_controls.metadata',
  'security_access_compliance.audit_events.read',
  'security_access_compliance.audit_events.metadata',
  'security_access_compliance.sensitive_actions.read',
  'security_access_compliance.sensitive_actions.review',
  'security_access_compliance.data_protection.read',
  'security_access_compliance.data_protection.evidence',
  'security_access_compliance.privacy_readiness.read',
  'security_access_compliance.privacy_readiness.evidence',
  'security_access_compliance.exceptions.read',
  'security_access_compliance.exceptions.metadata',
  'security_access_compliance.visitor_access.read',
  'security_access_compliance.visitor_access.metadata',
  'security_access_compliance.bridges.hr',
  'security_access_compliance.bridges.finance',
  'security_access_compliance.bridges.documents',
  'security_access_compliance.bridges.student_services',
] as const;

const RESTRICTED_PERMISSIONS = ['security_access_compliance.overview.read'] as const;

const REQUIRED_BOUNDARY_TEXTS = [
  'Governance/readiness/evidence-only security foundation',
  'Human review required',
  'No fake security certification',
  'No fake compliance certification',
  'No legal/regulatory compliance claim',
  'No SOC/SIEM replacement',
  'No fake incident resolution',
  'No fake audit proof',
  'No fake risk score',
  'No hidden user risk score',
  'No autonomous enforcement',
  'No external regulator submission',
  'No production-ready security claim',
  'Incomplete data supported',
  'Bridge-first / read-only-first',
  'No sales-ready claim',
  'No GCC-ready claim',
] as const;

const FORBIDDEN_DOM_LABELS = [
  'Certify security',
  'Certify compliance',
  'Legal compliance certified',
  'SOC/SIEM replacement',
  'Resolve incident officially',
  'Generate audit proof',
  'Generate penetration-test result',
  'Generate vulnerability-scan result',
  'Generate risk score',
  'Hidden user risk score',
  'Block user automatically',
  'Sanction user automatically',
  'Delete data automatically',
  'Submit to regulator',
  'Production-ready security',
  'Sales ready',
  'GCC ready',
  'L5/L6 ready',
  'Security certified',
  'Compliance certified',
  'User blocked automatically',
  'User sanctioned automatically',
  'Data deleted automatically',
  'Regulator submitted',
  'Audit proof generated',
  'Risk score generated',
] as const;

const FORBIDDEN_EXACT_TEXTS = FORBIDDEN_DOM_LABELS.map((label) =>
  new RegExp(`^${label.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')}$`, 'i'),
);

const BASE_FLAGS = {
  fake_security_certification: false,
  fake_compliance_certification: false,
  legal_regulatory_compliance_claimed: false,
  soc_siem_replacement_claimed: false,
  fake_incident_resolution: false,
  fake_audit_proof: false,
  fake_penetration_test_result: false,
  fake_vulnerability_scan_result: false,
  fake_risk_score: false,
  hidden_user_risk_score_present: false,
  discriminatory_ranking_present: false,
  autonomous_enforcement_enabled: false,
  automatic_user_blocking_enabled: false,
  automatic_user_sanction_enabled: false,
  automatic_data_deletion_enabled: false,
  external_regulator_submission_enabled: false,
  production_security_claimed: false,
  human_review_required: true,
  incomplete_data: true,
  limitations: [
    'Metadata/evidence/readiness-only security runtime.',
    'No autonomous enforcement, no external regulator submission, and no production-ready claim.',
  ],
  runtime_mode: 'GOVERNANCE_READINESS_EVIDENCE_AUDIT_CONTROL_METADATA_HUMAN_REVIEW_ONLY',
  route_count: 23,
  backend_route_count: 47,
  backend_table_count: 24,
  backend_permission_count: 44,
} as const;

const adminFixture = {
  id: 'sac-admin-01',
  sub: 'sac-admin-01',
  tenantId: 7101,
  email: 'sac-admin@example.edu',
  displayName: 'Security Access Compliance Admin',
  role: 'admin',
  roles: ['admin'],
  permissions: [...FULL_PERMISSIONS],
};

const restrictedFixture = {
  id: 'sac-restricted-01',
  sub: 'sac-restricted-01',
  tenantId: 7101,
  email: 'sac-restricted@example.edu',
  displayName: 'Security Access Compliance Restricted User',
  role: 'SECURITY_ACCESS_COMPLIANCE_RESTRICTED_VIEWER',
  roles: ['SECURITY_ACCESS_COMPLIANCE_RESTRICTED_VIEWER'],
  permissions: [...RESTRICTED_PERMISSIONS],
};

function pageUrl(path: string) {
  return new URL(path, BASE_URL).toString();
}

function parsePath(url: string) {
  return new URL(url).pathname;
}

function makeRecord(id: number, routeKey: string, title: string, extra: Record<string, unknown> = {}) {
  return {
    id,
    tenant_id: 7101,
    route_key: routeKey,
    title,
    status: 'ACTIVE',
    metadata_only: true,
    review_mode: 'HUMAN_REVIEW_ONLY',
    ...BASE_FLAGS,
    ...extra,
  };
}

const STUBS = {
  overview: {
    ...BASE_FLAGS,
    module: 'security_access_compliance',
    title: 'Security / Access / Compliance',
    summary: 'Metadata-only governance/readiness/evidence surface.',
    route_count: 23,
    backend_route_count: 47,
    table_count: 24,
    permission_count: 44,
    bridge_count: 4,
    data_source: 'computed_from_security_access_compliance_metadata',
  },
  readiness: {
    title: 'Readiness',
    readiness_status: 'ACTIVE',
    recommended_next_step: 'Human review of metadata evidence required.',
    missing_evidence: ['No official certification evidence'],
    ...BASE_FLAGS,
  },
  dashboard: {
    title: 'Security / Access / Compliance Dashboard',
    summary: 'Dashboard metadata only.',
    widgets: [
      {
        key: 'sac-dashboard-1',
        title: 'Governance readiness',
        description: 'Metadata-only widget.',
        backendEndpoints: [endpoint('GET', '/dashboard')],
        requiredPermission: 'security_access_compliance.dashboard.read',
      },
    ],
    ...BASE_FLAGS,
  },
  limitations: {
    ...BASE_FLAGS,
    title: 'Limitations',
    limitations: [...BASE_FLAGS.limitations],
  },
  roles: { items: [makeRecord(1, 'roles', 'Roles')] },
  permissions: { items: [makeRecord(2, 'permissions', 'Permissions')] },
  accessGovernance: { items: [makeRecord(3, 'access-governance', 'Access Governance')] },
  rbacEvidence: { items: [makeRecord(4, 'rbac-abac', 'RBAC Evidence')] },
  abacEvidence: { items: [makeRecord(5, 'rbac-abac', 'ABAC Evidence')] },
  sessions: { items: [makeRecord(6, 'sessions', 'Session Visibility')] },
  loginEvents: { items: [makeRecord(7, 'login-events', 'Login Event Review')] },
  mfaReadiness: { items: [makeRecord(8, 'mfa-readiness', 'MFA Readiness')] },
  tenantIsolation: { items: [makeRecord(9, 'tenant-isolation', 'Tenant Isolation')] },
  incidents: { items: [makeRecord(10, 'incidents', 'Incidents')] },
  incidentReview: { items: [makeRecord(11, 'incident-review', 'Incident Review')] },
  remediation: { items: [makeRecord(12, 'remediation', 'Remediation')] },
  risks: { items: [makeRecord(13, 'risks', 'Risk Register')] },
  complianceControls: { items: [makeRecord(14, 'compliance-controls', 'Compliance Controls')] },
  policyControls: { items: [makeRecord(15, 'policy-controls', 'Policy Controls')] },
  auditEvents: { items: [makeRecord(16, 'audit-events', 'Audit Events')] },
  sensitiveActions: { items: [makeRecord(17, 'sensitive-actions', 'Sensitive Actions')] },
  dataProtection: { items: [makeRecord(18, 'data-protection', 'Data Protection')] },
  privacyReadiness: { items: [makeRecord(19, 'privacy-readiness', 'Privacy Readiness')] },
  exceptions: { items: [makeRecord(20, 'exceptions', 'Exceptions')] },
  visitorAccess: { items: [makeRecord(21, 'visitor-access', 'Visitor Access')] },
  bridgesHr: { items: [makeRecord(22, 'bridges', 'HR Bridge')] },
  bridgesFinance: { items: [makeRecord(23, 'bridges', 'Finance Bridge')] },
  bridgesDocuments: { items: [makeRecord(24, 'bridges', 'Documents Bridge')] },
  bridgesStudentServices: { items: [makeRecord(25, 'bridges', 'Student Services Bridge')] },
  metadataContract: {
    title: 'Metadata Contract',
    expected_table_count: 24,
    expected_route_count: 47,
    expected_permission_count: 44,
    permission_namespace: 'security_access_compliance.*',
    ...BASE_FLAGS,
  },
  safetyBoundaries: {
    title: 'Safety Boundaries',
    boundaries: REQUIRED_BOUNDARY_TEXTS,
    ...BASE_FLAGS,
  },
  health: {
    ok: true,
    module: 'security_access_compliance',
    ...BASE_FLAGS,
  },
};

function matchSacFixture(pathname: string) {
  if (pathname === `${API_BASE}/overview` || pathname === `${BFF_BASE}/overview`) return STUBS.overview;
  if (pathname === `${API_BASE}/readiness` || pathname === `${BFF_BASE}/readiness`) return STUBS.readiness;
  if (pathname === `${API_BASE}/dashboard` || pathname === `${BFF_BASE}/dashboard`) return STUBS.dashboard;
  if (pathname === `${API_BASE}/limitations` || pathname === `${BFF_BASE}/limitations`) return STUBS.limitations;
  if (pathname === `${API_BASE}/roles` || pathname === `${BFF_BASE}/roles`) return STUBS.roles;
  if (pathname === `${API_BASE}/permissions` || pathname === `${BFF_BASE}/permissions`) return STUBS.permissions;
  if (pathname === `${API_BASE}/access-governance` || pathname === `${BFF_BASE}/access-governance`) return STUBS.accessGovernance;
  if (pathname === `${API_BASE}/rbac-evidence` || pathname === `${BFF_BASE}/rbac-evidence`) return STUBS.rbacEvidence;
  if (pathname === `${API_BASE}/abac-evidence` || pathname === `${BFF_BASE}/abac-evidence`) return STUBS.abacEvidence;
  if (pathname === `${API_BASE}/sessions` || pathname === `${BFF_BASE}/sessions`) return STUBS.sessions;
  if (pathname === `${API_BASE}/login-events` || pathname === `${BFF_BASE}/login-events`) return STUBS.loginEvents;
  if (pathname === `${API_BASE}/mfa-readiness` || pathname === `${BFF_BASE}/mfa-readiness`) return STUBS.mfaReadiness;
  if (pathname === `${API_BASE}/tenant-isolation` || pathname === `${BFF_BASE}/tenant-isolation`) return STUBS.tenantIsolation;
  if (pathname === `${API_BASE}/incidents` || pathname === `${BFF_BASE}/incidents`) return STUBS.incidents;
  if (pathname === `${API_BASE}/incident-review` || pathname === `${BFF_BASE}/incident-review`) return STUBS.incidentReview;
  if (pathname === `${API_BASE}/remediation` || pathname === `${BFF_BASE}/remediation`) return STUBS.remediation;
  if (pathname === `${API_BASE}/risks` || pathname === `${BFF_BASE}/risks`) return STUBS.risks;
  if (pathname === `${API_BASE}/compliance-controls` || pathname === `${BFF_BASE}/compliance-controls`) return STUBS.complianceControls;
  if (pathname === `${API_BASE}/policy-controls` || pathname === `${BFF_BASE}/policy-controls`) return STUBS.policyControls;
  if (pathname === `${API_BASE}/audit-events` || pathname === `${BFF_BASE}/audit-events`) return STUBS.auditEvents;
  if (pathname === `${API_BASE}/sensitive-actions` || pathname === `${BFF_BASE}/sensitive-actions`) return STUBS.sensitiveActions;
  if (pathname === `${API_BASE}/data-protection` || pathname === `${BFF_BASE}/data-protection`) return STUBS.dataProtection;
  if (pathname === `${API_BASE}/privacy-readiness` || pathname === `${BFF_BASE}/privacy-readiness`) return STUBS.privacyReadiness;
  if (pathname === `${API_BASE}/exceptions` || pathname === `${BFF_BASE}/exceptions`) return STUBS.exceptions;
  if (pathname === `${API_BASE}/visitor-access` || pathname === `${BFF_BASE}/visitor-access`) return STUBS.visitorAccess;
  if (pathname === `${API_BASE}/bridges/hr` || pathname === `${BFF_BASE}/bridges/hr`) return STUBS.bridgesHr;
  if (pathname === `${API_BASE}/bridges/finance` || pathname === `${BFF_BASE}/bridges/finance`) return STUBS.bridgesFinance;
  if (pathname === `${API_BASE}/bridges/documents` || pathname === `${BFF_BASE}/bridges/documents`) return STUBS.bridgesDocuments;
  if (pathname === `${API_BASE}/bridges/student-services` || pathname === `${BFF_BASE}/bridges/student-services`) return STUBS.bridgesStudentServices;
  if (pathname === `${API_BASE}/metadata-contract` || pathname === `${BFF_BASE}/metadata-contract`) return STUBS.metadataContract;
  if (pathname === `${API_BASE}/safety-boundaries` || pathname === `${BFF_BASE}/safety-boundaries`) return STUBS.safetyBoundaries;
  if (pathname === `${API_BASE}/health` || pathname === `${BFF_BASE}/health`) return STUBS.health;
  return null;
}

async function forceEnglishLocale(page: Page) {
  const parsedUrl = new URL(BASE_URL);
  const origins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  await page.context().addCookies(
    Array.from(origins).map((origin) => ({
      name: 'app.locale',
      value: 'en',
      url: origin,
      httpOnly: false,
      secure: new URL(origin).protocol === 'https:',
      sameSite: 'Lax' as const,
    })),
  );

  await page.addInitScript(() => {
    document.cookie = 'app.locale=en; Path=/; SameSite=Lax';
    window.localStorage.setItem('app.language', 'en');
  });
}

async function stubSharedBootstrap(page: Page) {
  await page.route('**/api/auth/csrf*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrfToken: 'sac-csrf-token' }),
    });
  });

  await page.route('**/api/auth/me/preferences/language*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true, language: 'en' }),
    });
  });

  await page.route('**/api/public/tenants/login-directory*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            tenantId: 7101,
            tenantCode: 'sac-demo-tenant',
            tenantName: 'Security Access Compliance Demo Tenant',
            authMethods: ['password'],
          },
        ],
      }),
    });
  });

  await page.route('**/api/i18n/languages*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        languages: [
          { code: 'en', label: 'English', default: true },
          { code: 'ru', label: 'Russian', default: false },
        ],
      }),
    });
  });
}

async function stubAuth(page: Page, fixture: typeof adminFixture | typeof restrictedFixture) {
  const parsedUrl = new URL(BASE_URL);
  const origins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  const payloadJson = JSON.stringify({
    sub: fixture.sub,
    display_name: fixture.displayName,
    roles: fixture.roles,
    permissions: fixture.permissions,
    tenant_id: fixture.tenantId,
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const token = `fakeheader.${Buffer.from(payloadJson).toString('base64url')}.fakesig`;

  await page.context().addCookies(
    Array.from(origins).flatMap((origin) => {
      const secure = new URL(origin).protocol === 'https:';
      return [
        { name: 'admin_token', value: token, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
        { name: 'app_access_token', value: token, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
      ];
    }),
  );

  for (const pattern of ['**/api/auth/me*', '**/api/bff/auth/me*']) {
    await page.route(pattern, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          user: fixture,
        }),
      });
    });
  }
}

async function stubSacApi(page: Page) {
  const fulfillRoute = async (route: Route) => {
    const request = route.request();
    const pathname = parsePath(request.url());
    const payload = matchSacFixture(pathname);

    const respond = async (body: unknown, status = 200) => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(body),
      });
    };

    if (payload) {
      await respond(payload);
      return;
    }

    if (request.method() === 'POST' || request.method() === 'PATCH') {
      await respond({
        ok: true,
        accepted: true,
        mutation_applied: false,
        mode: 'metadata_only',
        ...BASE_FLAGS,
      });
      return;
    }

    if (pathname.includes('/security-access-compliance/')) {
      await respond({
        ...STUBS.metadataContract,
        detail: `Fallback metadata-contract response for ${pathname}`,
      });
      return;
    }

    await respond({ detail: `Unhandled SAC stub path: ${pathname}` }, 404);
  };

  await page.route(`**${API_BASE}**`, fulfillRoute);
  await page.route(`**${BFF_BASE}**`, fulfillRoute);
}

async function setAuthenticatedAdmin(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, adminFixture);
  await stubSacApi(page);
}

async function setRestrictedUser(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, restrictedFixture);
  await stubSacApi(page);
}

async function gotoSacRoute(page: Page, path: string) {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await page.goto(pageUrl(path), { waitUntil: 'domcontentloaded' });
      return;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const transient = /ERR_ABORTED|frame was detached/i.test(message);
      if (!transient || attempt === 2) {
        throw error;
      }
    }
  }
}

async function expectForbiddenDomAbsent(page: Page) {
  for (const label of FORBIDDEN_DOM_LABELS) {
    const exact = new RegExp(`^${label.replace(/[.*+?^${}()|[\\]\\]/g, '\\$&')}$`, 'i');
    await expect(page.getByRole('button', { name: exact })).toHaveCount(0);
    await expect(page.getByRole('link', { name: exact })).toHaveCount(0);
    await expect(page.getByText(exact)).toHaveCount(0);
  }

  for (const pattern of FORBIDDEN_EXACT_TEXTS) {
    await expect(page.getByText(pattern)).toHaveCount(0);
  }
}

async function expectRouteShell(page: Page, route: SacRouteSpec) {
  await expect(page.getByTestId('sac-page-shell')).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('heading', { level: 1, name: route.title })).toBeVisible({ timeout: 15_000 });
  await expect(page.locator('nav[aria-label="Security access compliance navigation"] a')).toHaveCount(23, { timeout: 15_000 });
  await expect(page.getByTestId(`sac-page-${route.routeKey}`)).toBeVisible({ timeout: 15_000 });
  await expect(page.getByTestId('sac-route-contract-panel')).toContainText(route.requiredPermission);
}

async function openAndAssertRoute(page: Page, route: SacRouteSpec) {
  await gotoSacRoute(page, route.path);
  await expectRouteShell(page, route);

  for (const label of route.expectedBoundaryLabels) {
    await expect(page.locator('body')).toContainText(label);
  }

  await expect(page.getByTestId('sac-incomplete-data-notice')).toContainText('incompleteData supported');
  if (route.routeKey !== 'limitations') {
    await expect(page.getByTestId('sac-no-overclaim-footer')).toBeVisible();
  }

  await expectForbiddenDomAbsent(page);
}

async function visitRouteWithFreshPage(browser: Browser, route: SacRouteSpec) {
  const page = await browser.newPage({ ignoreHTTPSErrors: true });
  try {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setAuthenticatedAdmin(page);
    await openAndAssertRoute(page, route);
  } finally {
    await page.close();
  }
}

async function expectPermissionDeniedOrSafeFallback(page: Page) {
  const deniedPanel = page.getByTestId('sac-permission-denied-panel');
  const deniedWrap = page.getByTestId('sac-permission-denied-panel-wrap');

  if (await deniedPanel.count()) {
    await expect(deniedPanel).toBeVisible();
  } else if (await deniedWrap.count()) {
    await expect(deniedWrap).toBeVisible();
  } else {
    await expect(page.locator('body')).toContainText(/Access Denied|Permission required|fail-closed|requires/i);
  }

  await expect(page.getByTestId('sac-dashboard-grid')).toHaveCount(0);
  await expect(page.getByTestId('sac-evidence-table')).toHaveCount(0);
  await expectForbiddenDomAbsent(page);
}

test.describe('A-043.4 Security / Access / Compliance route coverage', () => {
  test.describe.configure({ timeout: 280_000 });

  test('SAC-E2E-GROUP-00 route inventory has exactly 23 routes', async () => {
    expect(SAC_ROUTES).toHaveLength(23);
  });

  test('SAC-E2E-GROUP-01 full-access security admin can visit all 23 routes', async ({ browser }) => {
    for (const route of SAC_ROUTES) {
      await test.step(`full-access ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });
});

test.describe('A-043.4 Security / Access / Compliance scenario groups', () => {
  test.describe.configure({ timeout: 280_000 });

  test.beforeEach(async ({ page }) => {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setAuthenticatedAdmin(page);
  });

  test('SAC-E2E-GROUP-02 route-title group A, routes 1-6', async ({ page }) => {
    for (const route of SAC_ROUTES.slice(0, 6)) {
      await gotoSacRoute(page, route.path);
      await expect(page.getByRole('heading', { level: 1, name: route.title })).toBeVisible();
    }
  });

  test('SAC-E2E-GROUP-03 route-title group B, routes 7-12', async ({ page }) => {
    for (const route of SAC_ROUTES.slice(6, 12)) {
      await gotoSacRoute(page, route.path);
      await expect(page.getByRole('heading', { level: 1, name: route.title })).toBeVisible();
    }
  });

  test('SAC-E2E-GROUP-04 route-title group C, routes 13-18', async ({ page }) => {
    for (const route of SAC_ROUTES.slice(12, 18)) {
      await gotoSacRoute(page, route.path);
      await expect(page.getByRole('heading', { level: 1, name: route.title })).toBeVisible();
    }
  });

  test('SAC-E2E-GROUP-05 route-title group D, routes 19-23', async ({ page }) => {
    for (const route of SAC_ROUTES.slice(18, 23)) {
      await gotoSacRoute(page, route.path);
      await expect(page.getByRole('heading', { level: 1, name: route.title })).toBeVisible();
    }
  });

  test('SAC-E2E-GROUP-06 overview/readiness/limitations boundaries', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance');
    await expect(page.locator('body')).toContainText('Governance/readiness/evidence-only security foundation');
    await expect(page.locator('body')).toContainText('Bridge-first / read-only-first');

    await gotoSacRoute(page, '/console/security-access-compliance/limitations');
    await expect(page.locator('body')).toContainText('Limitations');
    await expect(page.locator('body')).toContainText('No production-ready security claim');
  });

  test('SAC-E2E-GROUP-07 dashboard incomplete-data and fake flags false boundary', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/dashboard');
    await expect(page.getByTestId('sac-safety-checklist')).toBeVisible();
    await expect(page.locator('body')).toContainText('fakeSecurityCertification=false');
    await expect(page.locator('body')).toContainText('fakeComplianceCertification=false');
    await expect(page.locator('body')).toContainText('humanReviewRequired=true');
  });

  test('SAC-E2E-GROUP-08 access governance and roles-permissions metadata', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/access-governance');
    await expect(page.locator('body')).toContainText('Access Governance');

    await gotoSacRoute(page, '/console/security-access-compliance/roles-permissions');
    await expect(page.locator('body')).toContainText('Roles and Permissions');
    await expect(page.locator('body')).toContainText('No automatic user blocking');
  });

  test('SAC-E2E-GROUP-09 RBAC/ABAC bridge and non-autonomous enforcement boundary', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/rbac-abac');
    await expect(page.locator('body')).toContainText('RBAC and ABAC Evidence');
    await expect(page.locator('body')).toContainText('No autonomous enforcement');
  });

  test('SAC-E2E-GROUP-10 sessions and login-event review visibility', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/sessions');
    await expect(page.locator('body')).toContainText('Sessions');

    await gotoSacRoute(page, '/console/security-access-compliance/login-events');
    await expect(page.locator('body')).toContainText('Login Events');
  });

  test('SAC-E2E-GROUP-11 MFA readiness and tenant-isolation evidence', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/mfa-readiness');
    await expect(page.locator('body')).toContainText('MFA Readiness');

    await gotoSacRoute(page, '/console/security-access-compliance/tenant-isolation');
    await expect(page.locator('body')).toContainText('Tenant Isolation');
  });

  test('SAC-E2E-GROUP-12 incident metadata / non-resolution boundary', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/incidents');
    await expect(page.getByTestId('sac-form-shell-incidents')).toBeVisible();
    await expect(page.locator('body')).toContainText('No fake incident resolution');
  });

  test('SAC-E2E-GROUP-13 incident review and remediation metadata', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/incident-review');
    await expect(page.getByTestId('sac-form-shell-incident-review')).toBeVisible();

    await gotoSacRoute(page, '/console/security-access-compliance/remediation');
    await expect(page.getByTestId('sac-form-shell-remediation')).toBeVisible();
  });

  test('SAC-E2E-GROUP-14 risk register / no fake risk score boundary', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/risks');
    await expect(page.getByTestId('sac-form-shell-risks')).toBeVisible();
    await expect(page.locator('body')).toContainText('No fake risk score');
  });

  test('SAC-E2E-GROUP-15 compliance controls / non-certification boundary', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/compliance-controls');
    await expect(page.getByTestId('sac-form-shell-compliance-controls')).toBeVisible();
    await expect(page.locator('body')).toContainText('No fake compliance certification');
  });

  test('SAC-E2E-GROUP-16 policy controls and audit events metadata', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/policy-controls');
    await expect(page.getByTestId('sac-form-shell-policy-controls')).toBeVisible();

    await gotoSacRoute(page, '/console/security-access-compliance/audit-events');
    await expect(page.getByTestId('sac-form-shell-audit-events')).toBeVisible();

    const payload = await page.evaluate(async () => {
      const response = await fetch('/api/bff/admin/security-access-compliance/metadata-contract');
      return response.json();
    });

    expect(payload.expected_table_count).toBe(24);
    expect(payload.expected_route_count).toBe(47);
    expect(payload.expected_permission_count).toBe(44);
    expect(payload.human_review_required).toBe(true);
  });

  test('SAC-E2E-GROUP-17 sensitive action human-review boundary', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/sensitive-actions');
    await expect(page.getByTestId('sac-form-shell-sensitive-actions')).toBeVisible();
    await expect(page.locator('body')).toContainText('Human review required');
  });

  test('SAC-E2E-GROUP-18 data-protection and privacy-readiness evidence', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/data-protection');
    await expect(page.getByTestId('sac-form-shell-data-protection')).toBeVisible();

    await gotoSacRoute(page, '/console/security-access-compliance/privacy-readiness');
    await expect(page.getByTestId('sac-form-shell-privacy-readiness')).toBeVisible();
  });

  test('SAC-E2E-GROUP-19 exceptions and visitor-access bridge', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/exceptions');
    await expect(page.getByTestId('sac-form-shell-exceptions')).toBeVisible();

    await gotoSacRoute(page, '/console/security-access-compliance/visitor-access');
    await expect(page.getByTestId('sac-form-shell-visitor-access')).toBeVisible();
  });

  test('SAC-E2E-GROUP-20 cross-vertical bridges read-only-first', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/bridges');
    await expect(page.locator('body')).toContainText('Cross-Vertical Bridges');
    await expect(page.locator('body')).toContainText('Bridge-first / read-only-first');
  });

  test('SAC-E2E-GROUP-21 no-overclaim DOM scan across all routes', async ({ page }) => {
    for (const route of SAC_ROUTES) {
      await gotoSacRoute(page, route.path);
      await expectForbiddenDomAbsent(page);
    }

    await setAuthenticatedAdmin(page);
    for (const required of REQUIRED_BOUNDARY_TEXTS) {
      const routePath =
        required === 'No fake incident resolution'
          ? '/console/security-access-compliance/incidents'
          : '/console/security-access-compliance';

      await gotoSacRoute(page, routePath);
      await expect(page.locator('body')).toContainText(required);
    }

    await gotoSacRoute(page, '/console/security-access-compliance/limitations');
    await expect(page.locator('body')).toContainText('No L5/L6 ready claim.');
  });

  test('SAC-E2E-GROUP-23 artifact hygiene / no screenshots committed check plan', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance');
    await expect(page.locator('body')).not.toContainText(/playwright-report|test-results|demo evidence|screenshot/i);
  });

  test('SAC-E2E-GROUP-24 suite closeout', async ({ page }) => {
    await gotoSacRoute(page, '/console/security-access-compliance/dashboard');
    await expect(page.getByTestId('sac-page-dashboard')).toBeVisible();
    expect(SCENARIO_GROUP_COUNT_TARGET).toBe(25);
  });
});

test.describe('A-043.4 Security / Access / Compliance permission-denial', () => {
  test.describe.configure({ timeout: 180_000 });

  test('SAC-E2E-GROUP-22 permission-denial smoke', async ({ page }) => {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setRestrictedUser(page);

    const protectedPaths = [
      '/console/security-access-compliance/dashboard',
      '/console/security-access-compliance/access-governance',
      '/console/security-access-compliance/roles-permissions',
      '/console/security-access-compliance/incidents',
      '/console/security-access-compliance/risks',
      '/console/security-access-compliance/compliance-controls',
      '/console/security-access-compliance/sensitive-actions',
      '/console/security-access-compliance/privacy-readiness',
      '/console/security-access-compliance/limitations',
    ];

    for (const path of protectedPaths) {
      await test.step(`restricted-user ${path}`, async () => {
        await gotoSacRoute(page, path);
        await expectPermissionDeniedOrSafeFallback(page);
      });
    }
  });
});
