import { SECURITY_ACCESS_COMPLIANCE_BOUNDARY_LABELS, SECURITY_ACCESS_COMPLIANCE_NO_OVERCLAIM_COPY, getSacBoundaryLabels } from './boundaryLabels';
import type { SacRouteDefinition, SacRouteKey, SacSafetyFlags } from './types';

export const SECURITY_ACCESS_COMPLIANCE_MODULE = 'security-access-compliance';
export const SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY = '/console/security-access-compliance';
export const SECURITY_ACCESS_COMPLIANCE_API_BASE = '/api/admin/security-access-compliance';
export const SECURITY_ACCESS_COMPLIANCE_PLANNED_ROUTE_COUNT = 23;
export const SECURITY_ACCESS_COMPLIANCE_BACKEND_ROUTE_COUNT = 47;
export const SECURITY_ACCESS_COMPLIANCE_TABLE_COUNT = 24;
export const SECURITY_ACCESS_COMPLIANCE_PERMISSION_COUNT = 44;
export const SECURITY_ACCESS_COMPLIANCE_RUNTIME_MODE = 'GOVERNANCE_READINESS_EVIDENCE_AUDIT_CONTROL_METADATA_HUMAN_REVIEW_ONLY';
export const SECURITY_ACCESS_COMPLIANCE_SOURCE_BACKEND_RUNTIME_COMMIT = '353b97a';
export const SECURITY_ACCESS_COMPLIANCE_SOURCE_BACKEND_B1_COMMIT = '4c7e89a';

export const SECURITY_ACCESS_COMPLIANCE_SAFETY_FLAGS = {
  fakeSecurityCertification: false,
  fakeComplianceCertification: false,
  legalRegulatoryComplianceClaimed: false,
  socSiemReplacementClaimed: false,
  fakeIncidentResolution: false,
  fakeAuditProof: false,
  fakePenetrationTestResult: false,
  fakeVulnerabilityScanResult: false,
  fakeRiskScore: false,
  hiddenUserRiskScorePresent: false,
  discriminatoryRankingPresent: false,
  autonomousEnforcementEnabled: false,
  automaticUserBlockingEnabled: false,
  automaticUserSanctionEnabled: false,
  automaticDataDeletionEnabled: false,
  externalRegulatorSubmissionEnabled: false,
  productionSecurityClaimed: false,
  humanReviewRequired: true,
} as const satisfies {
  fakeSecurityCertification: false;
  fakeComplianceCertification: false;
  legalRegulatoryComplianceClaimed: false;
  socSiemReplacementClaimed: false;
  fakeIncidentResolution: false;
  fakeAuditProof: false;
  fakePenetrationTestResult: false;
  fakeVulnerabilityScanResult: false;
  fakeRiskScore: false;
  hiddenUserRiskScorePresent: false;
  discriminatoryRankingPresent: false;
  autonomousEnforcementEnabled: false;
  automaticUserBlockingEnabled: false;
  automaticUserSanctionEnabled: false;
  automaticDataDeletionEnabled: false;
  externalRegulatorSubmissionEnabled: false;
  productionSecurityClaimed: false;
  humanReviewRequired: true;
};

function endpoint(method: 'GET' | 'POST', path: string) {
  return `${method} ${SECURITY_ACCESS_COMPLIANCE_API_BASE}${path}`;
}

function routeDefinition(
  key: SacRouteKey,
  title: string,
  route: string,
  requiredPermission: string,
  backendEndpoints: string[],
  primaryWidgets: string[],
  noForbiddenUiActions: string[],
): SacRouteDefinition {
  return {
    key,
    title,
    route,
    requiredPermission,
    backendEndpoints,
    primaryWidgets,
    safetyBoundaryLabels: getSacBoundaryLabels(key),
    emptyState: `${title} data is not available yet.`,
    incompleteDataNotice: 'incompleteData=true. Missing fields remain explicit and are never replaced with fake values.',
    permissionDeniedState: `This route requires ${requiredPermission}.`,
    noOverclaimFooter: [...SECURITY_ACCESS_COMPLIANCE_NO_OVERCLAIM_COPY],
    humanReviewBadge: 'Human review required',
    noForbiddenUiActions,
  };
}

export const SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS = [
  routeDefinition(
    'overview',
    'Security / Access / Compliance',
    SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY,
    'security_access_compliance.overview.read',
    [endpoint('GET', '/overview'), endpoint('GET', '/metadata-contract')],
    ['governance-summary', 'readiness-summary', 'evidence-summary'],
    ['No certification action', 'No autonomous enforcement', 'No hidden score'],
  ),
  routeDefinition(
    'dashboard',
    'Security / Access / Compliance Dashboard',
    `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/dashboard`,
    'security_access_compliance.dashboard.read',
    [endpoint('GET', '/dashboard'), endpoint('GET', '/metadata-contract')],
    ['dashboard-metrics', 'human-review', 'safety-checklist'],
    ['No production-ready security claim', 'No hidden user score'],
  ),
  routeDefinition(
    'access-governance',
    'Access Governance',
    `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/access-governance`,
    'security_access_compliance.access_governance.read',
    [endpoint('GET', '/access-governance'), endpoint('GET', '/rbac-evidence'), endpoint('GET', '/abac-evidence')],
    ['access-governance-metrics', 'rbac-evidence', 'abac-evidence'],
    ['No automatic user blocking', 'No autonomous enforcement'],
  ),
  routeDefinition(
    'roles-permissions',
    'Roles and Permissions',
    `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/roles-permissions`,
    'security_access_compliance.roles.read',
    [endpoint('GET', '/roles'), endpoint('GET', '/permissions')],
    ['roles-table', 'permissions-table'],
    ['No automatic user blocking', 'No automatic user sanction'],
  ),
  routeDefinition(
    'rbac-abac',
    'RBAC and ABAC Evidence',
    `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/rbac-abac`,
    'security_access_compliance.rbac_evidence.read',
    [endpoint('GET', '/rbac-evidence'), endpoint('GET', '/abac-evidence')],
    ['rbac-evidence', 'abac-evidence'],
    ['No hidden user risk score', 'No autonomous enforcement'],
  ),
  routeDefinition('sessions', 'Sessions', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/sessions`, 'security_access_compliance.sessions.read', [endpoint('GET', '/sessions')], ['session-visibility'], ['No hidden user risk score']),
  routeDefinition('login-events', 'Login Events', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/login-events`, 'security_access_compliance.login_events.read', [endpoint('GET', '/login-events')], ['login-review'], ['No hidden user risk score']),
  routeDefinition('mfa-readiness', 'MFA Readiness', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/mfa-readiness`, 'security_access_compliance.mfa_readiness.read', [endpoint('GET', '/mfa-readiness')], ['mfa-readiness'], ['No automatic user blocking']),
  routeDefinition('tenant-isolation', 'Tenant Isolation', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/tenant-isolation`, 'security_access_compliance.tenant_isolation.read', [endpoint('GET', '/tenant-isolation')], ['tenant-isolation'], ['No autonomous enforcement']),
  routeDefinition('incidents', 'Incidents', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/incidents`, 'security_access_compliance.incidents.read', [endpoint('GET', '/incidents'), endpoint('POST', '/incidents/metadata')], ['incident-list', 'incident-metadata'], ['No fake incident resolution', 'No autonomous enforcement']),
  routeDefinition('incident-review', 'Incident Review', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/incident-review`, 'security_access_compliance.incident_review.read', [endpoint('GET', '/incident-review'), endpoint('POST', '/incident-review/metadata')], ['incident-review-timeline'], ['No fake incident resolution']),
  routeDefinition('remediation', 'Remediation', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/remediation`, 'security_access_compliance.remediation.read', [endpoint('GET', '/remediation'), endpoint('POST', '/remediation/metadata')], ['remediation-tracker'], ['No autonomous enforcement']),
  routeDefinition('risks', 'Risk Register', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/risks`, 'security_access_compliance.risks.read', [endpoint('GET', '/risks'), endpoint('POST', '/risks/metadata')], ['risk-register'], ['No fake risk score']),
  routeDefinition('compliance-controls', 'Compliance Controls', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/compliance-controls`, 'security_access_compliance.compliance_controls.read', [endpoint('GET', '/compliance-controls'), endpoint('POST', '/compliance-controls/metadata')], ['compliance-controls'], ['No fake compliance certification']),
  routeDefinition('policy-controls', 'Policy Controls', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/policy-controls`, 'security_access_compliance.policy_controls.read', [endpoint('GET', '/policy-controls'), endpoint('POST', '/policy-controls/metadata')], ['policy-controls'], ['No legal/regulatory compliance claim']),
  routeDefinition('audit-events', 'Audit Events', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/audit-events`, 'security_access_compliance.audit_events.read', [endpoint('GET', '/audit-events'), endpoint('POST', '/audit-events/metadata')], ['audit-timeline'], ['No fake audit proof']),
  routeDefinition('sensitive-actions', 'Sensitive Actions', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/sensitive-actions`, 'security_access_compliance.sensitive_actions.read', [endpoint('GET', '/sensitive-actions'), endpoint('POST', '/sensitive-actions/review')], ['sensitive-action-review'], ['No autonomous enforcement']),
  routeDefinition('data-protection', 'Data Protection', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/data-protection`, 'security_access_compliance.data_protection.read', [endpoint('GET', '/data-protection'), endpoint('POST', '/data-protection/evidence')], ['data-protection-evidence'], ['No fake vulnerability-scan result']),
  routeDefinition('privacy-readiness', 'Privacy Readiness', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/privacy-readiness`, 'security_access_compliance.privacy_readiness.read', [endpoint('GET', '/privacy-readiness'), endpoint('POST', '/privacy-readiness/evidence')], ['privacy-readiness-evidence'], ['No fake penetration-test result']),
  routeDefinition('exceptions', 'Exceptions', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/exceptions`, 'security_access_compliance.exceptions.read', [endpoint('GET', '/exceptions'), endpoint('POST', '/exceptions/metadata')], ['exception-register'], ['No legal/regulatory compliance claim']),
  routeDefinition('visitor-access', 'Visitor Access', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/visitor-access`, 'security_access_compliance.visitor_access.read', [endpoint('GET', '/visitor-access'), endpoint('POST', '/visitor-access/metadata')], ['visitor-access-bridge'], ['No automatic user blocking']),
  routeDefinition('bridges', 'Cross-Vertical Bridges', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/bridges`, 'security_access_compliance.bridges.hr', [endpoint('GET', '/bridges/hr'), endpoint('GET', '/bridges/finance'), endpoint('GET', '/bridges/documents'), endpoint('GET', '/bridges/student-services'), endpoint('POST', '/bridges/hr'), endpoint('POST', '/bridges/finance'), endpoint('POST', '/bridges/documents'), endpoint('POST', '/bridges/student-services')], ['bridge-families'], ['No external regulator submission', 'No autonomous enforcement']),
  routeDefinition('limitations', 'Limitations', `${SECURITY_ACCESS_COMPLIANCE_ROUTE_FAMILY}/limitations`, 'security_access_compliance.limitations.read', [endpoint('GET', '/limitations'), endpoint('POST', '/limitations')], ['limitations'], ['No production-ready security claim', 'No sales-ready claim', 'No GCC-ready claim']),
] as const satisfies readonly SacRouteDefinition[];
