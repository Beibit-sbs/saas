import { describe, expect, it } from 'vitest';
import { SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS } from '@/modules/security-access-compliance/constants';
import { buildSacPageModel, getSacRouteDefinition } from '@/modules/security-access-compliance/pages';

describe('Security / Access / Compliance route map', () => {
  it('keeps the route inventory fixed at 23', () => {
    expect(SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS).toHaveLength(23);
  });

  it.each(SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS)('maps %s route contract correctly', (route) => {
    const fromLookup = getSacRouteDefinition(route.key);
    const model = buildSacPageModel(route.key);

    expect(fromLookup.route).toBe(route.route);
    expect(fromLookup.requiredPermission).toBe(route.requiredPermission);
    expect(model.backendApiBase).toBe('/api/admin/security-access-compliance');
    expect(model.primaryWidgets.length).toBeGreaterThan(0);
    expect(model.safetyBoundaryLabels.length).toBeGreaterThan(0);
    expect(model.noForbiddenUiActions.length).toBeGreaterThan(0);
  });

  it('covers the exact route family', () => {
    expect(SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS.map((route) => route.route)).toContain('/console/security-access-compliance');
    expect(SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS.map((route) => route.route)).toContain('/console/security-access-compliance/dashboard');
    expect(SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS.map((route) => route.route)).toContain('/console/security-access-compliance/limitations');
  });

  it('keeps backend endpoint references aligned with 47-route backend baseline', () => {
    const endpointSet = new Set(SECURITY_ACCESS_COMPLIANCE_ROUTE_DEFINITIONS.flatMap((route) => route.backendEndpoints));
    expect(endpointSet.size).toBeGreaterThan(20);
  });
});
