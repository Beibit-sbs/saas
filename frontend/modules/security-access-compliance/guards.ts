import type { SacPermission, SacRouteKey } from './types';
import { SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS } from './constants';

type PermissionUser =
  | { permissions?: Array<string | SacPermission>; rolePermissions?: Array<string | SacPermission>; grantedPermissions?: Array<string | SacPermission> }
  | Array<string | SacPermission>
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

export const SECURITY_ACCESS_COMPLIANCE_PERMISSIONS = [
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

export const SECURITY_ACCESS_COMPLIANCE_PERMISSION_COUNT = SECURITY_ACCESS_COMPLIANCE_PERMISSIONS.length;

export const SECURITY_ACCESS_COMPLIANCE_ROUTE_PERMISSION_MAP = Object.fromEntries(
  SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS.map((route) => [route.key, route.requiredPermission]),
) as Record<SacRouteKey, SacPermission>;

export function hasSacPermission(userPermissions: PermissionUser, permission: SacPermission) {
  return permissionSet(userPermissions).has(permission);
}

export function hasAnySacPermission(userPermissions: PermissionUser, permissions: SacPermission[]) {
  const granted = permissionSet(userPermissions);
  return permissions.some((permission) => granted.has(permission));
}

export function getAllowedSacRoutes(userPermissions: PermissionUser) {
  return SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS.filter((route) =>
    hasSacPermission(userPermissions, route.requiredPermission),
  );
}
