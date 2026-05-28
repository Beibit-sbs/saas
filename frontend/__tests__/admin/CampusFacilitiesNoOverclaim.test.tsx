import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { CAMPUS_FACILITIES_NO_OVERCLAIM_COPY } from '@/modules/campus-facilities/boundaryLabels';
import { assertNoCampusFacilitiesOverclaim } from '@/modules/campus-facilities/guards';
import { CampusFacilitiesPage } from '@/modules/campus-facilities/pages';

const forbiddenPositiveLabels = [
  'Live IoT connected',
  'GPS tracking live',
  'Building automation enabled',
  'Access control enforced',
  'Safety certified',
  'Maintenance completed automatically',
  'Occupancy guaranteed',
  'Housing decision automatic',
  'Eviction automatic',
  'Student/staff sanctioned automatically',
  'Autonomous dispatch enabled',
  'Provider sync active',
  'Production ready',
  'Sales ready',
  'GCC ready',
  'L5/L6 ready',
] as const;

describe('Campus Facilities no-overclaim contract', () => {
  it('renders no-overclaim footer lines', () => {
    render(<CampusFacilitiesPage routeKey="overview" userPermissions={['campus_facilities.overview.read']} />);
    for (const line of CAMPUS_FACILITIES_NO_OVERCLAIM_COPY) {
      expect(screen.getAllByText(line).length).toBeGreaterThan(0);
    }
  });

  it('does not render forbidden positive labels', () => {
    render(<CampusFacilitiesPage routeKey="dashboard" userPermissions={['campus_facilities.dashboard.read']} />);
    for (const label of forbiddenPositiveLabels) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('exposes forbidden action inventory for scans', () => {
    const overclaim = assertNoCampusFacilitiesOverclaim();
    expect(overclaim.forbidden).toContain('enableLiveIot');
    expect(overclaim.forbidden).toContain('autonomousDispatch');
    expect(overclaim.forbidden).toContain('productionFacilitiesClaim');
    expect(overclaim.ok).toBe(true);
  });

  it('keeps no-overclaim footer visible on limitations', () => {
    render(<CampusFacilitiesPage routeKey="limitations" userPermissions={['campus_facilities.limitations.read']} />);
    expect(screen.getByTestId('campus-facilities-no-overclaim-footer')).toBeInTheDocument();
  });
});
