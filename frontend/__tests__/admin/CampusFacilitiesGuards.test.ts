import { describe, expect, it } from 'vitest';
import {
  CAMPUS_FACILITIES_PERMISSION_COUNT,
  CAMPUS_FACILITIES_PERMISSIONS,
  CAMPUS_FACILITIES_ROUTE_PERMISSION_MAP,
  assertNoCampusFacilitiesOverclaim,
  canReadCampusFacilitiesDashboard,
  canReadCampusFacilitiesOverview,
  canReadCampusFacilitiesRoute,
  canSubmitCampusFacilitiesMetadata,
  getAllowedCampusFacilitiesRoutes,
  getCampusFacilitiesPermissionSummary,
  requireCampusFacilitiesPermission,
} from '@/modules/campus-facilities/guards';
import { CAMPUS_FACILITIES_ROUTE_DEFINITIONS } from '@/modules/campus-facilities/constants';

describe('Campus Facilities guards', () => {
  it('keeps permission inventory fixed at 46', () => {
    expect(CAMPUS_FACILITIES_PERMISSION_COUNT).toBe(46);
    expect(CAMPUS_FACILITIES_PERMISSIONS).toHaveLength(46);
  });

  it('fails closed for missing permissions', () => {
    expect(canReadCampusFacilitiesOverview(null)).toBe(false);
    expect(canReadCampusFacilitiesDashboard(undefined)).toBe(false);
    expect(canReadCampusFacilitiesRoute('overview', [])).toBe(false);
  });

  it('reads overview/dashboard permissions', () => {
    expect(canReadCampusFacilitiesOverview(['campus_facilities.overview.read'])).toBe(true);
    expect(canReadCampusFacilitiesDashboard(['campus_facilities.dashboard.read'])).toBe(true);
  });

  it('maps route permission map to 24 routes', () => {
    expect(CAMPUS_FACILITIES_ROUTE_DEFINITIONS).toHaveLength(24);
    expect(Object.keys(CAMPUS_FACILITIES_ROUTE_PERMISSION_MAP)).toHaveLength(24);
  });

  it.each(CAMPUS_FACILITIES_ROUTE_DEFINITIONS.map((route) => [route.routeKey, route.requiredPermission] as const))(
    'maps %s required permission',
    (routeKey, requiredPermission) => {
      expect(CAMPUS_FACILITIES_ROUTE_PERMISSION_MAP[routeKey]).toBe(requiredPermission);
    },
  );

  it('computes metadata submit checks', () => {
    expect(canSubmitCampusFacilitiesMetadata('facilities', ['campus_facilities.facilities.metadata'])).toBe(true);
    expect(canSubmitCampusFacilitiesMetadata('facilities', ['campus_facilities.facilities.read'])).toBe(true);
    expect(canSubmitCampusFacilitiesMetadata('facilities', [])).toBe(false);
  });

  it('returns allowed routes only', () => {
    const allowed = getAllowedCampusFacilitiesRoutes(['campus_facilities.dashboard.read']).map((route) => route.routeKey);
    expect(allowed).toContain('dashboard');
    expect(allowed).not.toContain('maintenance');
  });

  it('returns permission summary shape', () => {
    const summary = getCampusFacilitiesPermissionSummary(['campus_facilities.dashboard.read']);
    expect(summary.total).toBe(46);
    expect(summary.granted).toBe(1);
    expect(summary.denied).toBe(45);
  });

  it('keeps no-overclaim assertion contract', () => {
    const result = assertNoCampusFacilitiesOverclaim();
    expect(result.ok).toBe(true);
    expect(result.forbidden).toContain('enableLiveIot');
    expect(result.forbidden).toContain('productionFacilitiesClaim');
  });

  it('keeps require permission helper pass-through', () => {
    expect(requireCampusFacilitiesPermission('campus_facilities.dashboard.read')).toBe('campus_facilities.dashboard.read');
  });
});
