import { describe, expect, it } from 'vitest';
import {
  CAMPUS_FACILITIES_BACKEND_ENDPOINTS,
  CAMPUS_FACILITIES_BACKEND_ENDPOINT_COUNT,
  CAMPUS_FACILITIES_ROUTE_DEFINITIONS,
} from '@/modules/campus-facilities/constants';
import { buildCampusFacilitiesPageModel, getCampusFacilitiesRouteDefinition } from '@/modules/campus-facilities/pages';

describe('Campus Facilities route map', () => {
  it('keeps route count at 24', () => {
    expect(CAMPUS_FACILITIES_ROUTE_DEFINITIONS).toHaveLength(24);
  });

  it('keeps backend endpoint count at 52', () => {
    expect(CAMPUS_FACILITIES_BACKEND_ENDPOINT_COUNT).toBe(52);
    expect(CAMPUS_FACILITIES_BACKEND_ENDPOINTS).toHaveLength(52);
  });

  it('keeps unique endpoint set size at 52', () => {
    expect(new Set(CAMPUS_FACILITIES_BACKEND_ENDPOINTS).size).toBe(52);
  });

  it.each(CAMPUS_FACILITIES_ROUTE_DEFINITIONS.map((route) => route.routeKey))('resolves route lookup for %s', (routeKey) => {
    const lookup = getCampusFacilitiesRouteDefinition(routeKey);
    const model = buildCampusFacilitiesPageModel(routeKey);

    expect(lookup.path).toBe(model.path);
    expect(lookup.requiredPermission).toBe(model.requiredPermission);
    expect(model.backendApiBase).toBe('/api/admin/campus-facilities');
    expect(model.boundaryLabels.length).toBeGreaterThan(0);
  });

  it('contains all four bridge route paths', () => {
    const paths = CAMPUS_FACILITIES_ROUTE_DEFINITIONS.map((route) => route.path);
    expect(paths).toContain('/console/campus-facilities/bridges/access-visitor');
    expect(paths).toContain('/console/campus-facilities/bridges/student-services');
    expect(paths).toContain('/console/campus-facilities/bridges/finance-asset');
    expect(paths).toContain('/console/campus-facilities/bridges/hr-staff');
  });
});
