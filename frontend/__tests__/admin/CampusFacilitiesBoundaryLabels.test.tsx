import React from 'react';
import { render, screen } from '@testing-library/react';
import { within } from '@testing-library/dom';
import { describe, expect, it } from 'vitest';
import {
  CAMPUS_FACILITIES_BOUNDARY_LABELS,
  CAMPUS_FACILITIES_ROUTE_BOUNDARY_LABELS,
} from '@/modules/campus-facilities/boundaryLabels';
import { CampusFacilitiesPage } from '@/modules/campus-facilities/pages';

describe('Campus Facilities boundary labels', () => {
  it('renders overview boundary labels', () => {
    render(<CampusFacilitiesPage routeKey="overview" userPermissions={['campus_facilities.overview.read']} />);
    const banner = screen.getByTestId('campus-facilities-boundary-banner');
    for (const label of CAMPUS_FACILITIES_ROUTE_BOUNDARY_LABELS.overview) {
      expect(within(banner).getByText(label)).toBeInTheDocument();
    }
  });

  it('renders required contract labels', () => {
    render(<CampusFacilitiesPage routeKey="dashboard" userPermissions={['campus_facilities.dashboard.read']} />);
    expect(screen.getByText(CAMPUS_FACILITIES_BOUNDARY_LABELS.metadataOnly)).toBeInTheDocument();
    expect(screen.getByText(CAMPUS_FACILITIES_BOUNDARY_LABELS.humanReviewRequired)).toBeInTheDocument();
    expect(screen.getAllByText(CAMPUS_FACILITIES_BOUNDARY_LABELS.noL5L6Claim).length).toBeGreaterThan(0);
  });

  it('renders incomplete data notice', () => {
    render(<CampusFacilitiesPage routeKey="overview" userPermissions={['campus_facilities.overview.read']} />);
    expect(screen.getByTestId('campus-facilities-incomplete-data-notice')).toBeInTheDocument();
  });

  it('fails closed when permission is missing', () => {
    render(<CampusFacilitiesPage routeKey="maintenance" userPermissions={[]} />);
    expect(screen.getByTestId('campus-facilities-permission-denied')).toBeInTheDocument();
  });
});
