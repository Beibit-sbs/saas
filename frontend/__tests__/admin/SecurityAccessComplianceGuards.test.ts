import { describe, expect, it } from 'vitest';
import {
  SECURITY_ACCESS_COMPLIANCE_PERMISSION_COUNT,
  SECURITY_ACCESS_COMPLIANCE_PERMISSIONS,
  SECURITY_ACCESS_COMPLIANCE_ROUTE_PERMISSION_MAP,
  getAllowedSacRoutes,
  hasAnySacPermission,
  hasSacPermission,
} from '@/modules/security-access-compliance/guards';
import { SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS } from '@/modules/security-access-compliance/constants';

describe('Security / Access / Compliance guards', () => {
  it('keeps the permission inventory fixed at 44', () => {
    expect(SECURITY_ACCESS_COMPLIANCE_PERMISSION_COUNT).toBe(44);
    expect(SECURITY_ACCESS_COMPLIANCE_PERMISSIONS).toHaveLength(44);
  });

  it('fails closed for missing permissions', () => {
    expect(hasSacPermission(null, SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[0])).toBe(false);
    expect(hasSacPermission(undefined, SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[0])).toBe(false);
    expect(hasSacPermission([], SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[0])).toBe(false);
  });

  it('grants exact permission checks', () => {
    const permissions = [SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[0], SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[1]];

    expect(hasSacPermission(permissions, SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[0])).toBe(true);
    expect(hasSacPermission(permissions, SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[2])).toBe(false);
  });

  it('supports any-permission checks', () => {
    const permissions = [SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[8]];

    expect(hasAnySacPermission(permissions, [SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[8], SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[9]])).toBe(true);
    expect(hasAnySacPermission(permissions, [SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[10], SECURITY_ACCESS_COMPLIANCE_PERMISSIONS[11]])).toBe(false);
  });

  it('keeps the route permission map aligned to the 23-route contract', () => {
    expect(SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS).toHaveLength(23);
    expect(Object.keys(SECURITY_ACCESS_COMPLIANCE_ROUTE_PERMISSION_MAP)).toHaveLength(23);
  });

  it.each(SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS.map((route) => [route.key, route.requiredPermission] as const))(
    'maps %s to required permission',
    (routeKey, requiredPermission) => {
      expect(SECURITY_ACCESS_COMPLIANCE_ROUTE_PERMISSION_MAP[routeKey]).toBe(requiredPermission);
    },
  );

  it('returns only allowed routes for a single permission', () => {
    const allowed = getAllowedSacRoutes(['security_access_compliance.dashboard.read']).map((route) => route.key);
    expect(allowed).toContain('dashboard');
    expect(allowed).not.toContain('incidents');
  });

  it('keeps the permission set free of forbidden capability markers', () => {
    expect(SECURITY_ACCESS_COMPLIANCE_PERMISSIONS).not.toContain('certifySecurity');
    expect(SECURITY_ACCESS_COMPLIANCE_PERMISSIONS).not.toContain('blockUserAutomatically');
    expect(SECURITY_ACCESS_COMPLIANCE_PERMISSIONS).not.toContain('submitToRegulator');
    expect(SECURITY_ACCESS_COMPLIANCE_PERMISSIONS).not.toContain('hiddenUserRiskScore');
  });
});
