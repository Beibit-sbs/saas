import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  CAMPUS_FACILITIES_ROUTE_DEFINITIONS,
  CAMPUS_FACILITIES_ROUTE_FAMILY,
} from '@/modules/campus-facilities/constants';
import { buildCampusFacilitiesPageModel, getCampusFacilitiesRouteDefinition } from '@/modules/campus-facilities/pages';
import { CampusFacilitiesPage } from '@/modules/campus-facilities/pages';

describe('Campus Facilities routes', () => {
  it('keeps frontend route inventory fixed at 24', () => {
    expect(CAMPUS_FACILITIES_ROUTE_DEFINITIONS).toHaveLength(24);
  });

  it('keeps route family anchored', () => {
    expect(CAMPUS_FACILITIES_ROUTE_FAMILY).toBe('/console/campus-facilities');
    expect(CAMPUS_FACILITIES_ROUTE_DEFINITIONS[0]?.path).toBe('/console/campus-facilities');
  });

  it.each(CAMPUS_FACILITIES_ROUTE_DEFINITIONS.map((route) => route.routeKey))('builds page model for %s', (routeKey) => {
    const model = buildCampusFacilitiesPageModel(routeKey);
    expect(model.path.startsWith('/console/campus-facilities')).toBe(true);
    expect(model.backendApiBase).toBe('/api/admin/campus-facilities');
    expect(model.boundaryLabels.length).toBeGreaterThan(0);
    expect(model.forbiddenClaims.length).toBeGreaterThan(0);
  });

  it('renders route navigation links', () => {
    render(<CampusFacilitiesPage routeKey="overview" userPermissions={['campus_facilities.overview.read']} />);
    expect(screen.getByRole('link', { name: 'Campus Facilities Dashboard' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Limitations' })).toBeInTheDocument();
  });

  it('resolves known route definitions', () => {
    expect(getCampusFacilitiesRouteDefinition('bridges-hr-staff').path).toBe('/console/campus-facilities/bridges/hr-staff');
    expect(getCampusFacilitiesRouteDefinition('audit-evidence').path).toBe('/console/campus-facilities/audit-evidence');
  });
});
