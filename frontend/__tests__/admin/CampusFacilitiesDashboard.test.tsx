import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { CampusFacilitiesPage } from '@/modules/campus-facilities/pages';
import { CAMPUS_FACILITIES_DASHBOARD_CARDS } from '@/modules/campus-facilities/constants';

describe('Campus Facilities dashboard', () => {
  it('renders dashboard shell', () => {
    render(<CampusFacilitiesPage routeKey="dashboard" userPermissions={['campus_facilities.dashboard.read']} />);
    expect(screen.getByTestId('campus-facilities-page-shell')).toBeInTheDocument();
    expect(screen.getByTestId('campus-facilities-registry-table')).toBeInTheDocument();
  });

  it('renders metrics cards', () => {
    render(<CampusFacilitiesPage routeKey="dashboard" userPermissions={['campus_facilities.dashboard.read']} />);
    expect(screen.getByText('Backend routes')).toBeInTheDocument();
    expect(screen.getByText('52')).toBeInTheDocument();
    expect(screen.getByText('26')).toBeInTheDocument();
    expect(screen.getByText('46')).toBeInTheDocument();
    expect(screen.getByText('24')).toBeInTheDocument();
  });

  it('renders all configured dashboard cards', () => {
    render(<CampusFacilitiesPage routeKey="dashboard" userPermissions={['campus_facilities.dashboard.read']} />);
    for (const card of CAMPUS_FACILITIES_DASHBOARD_CARDS) {
      expect(screen.getByTestId(`campus-facilities-dashboard-card-${card.key}`)).toBeInTheDocument();
    }
  });

  it('renders route contract metadata panel', () => {
    render(<CampusFacilitiesPage routeKey="dashboard" userPermissions={['campus_facilities.dashboard.read']} />);
    expect(screen.getByTestId('campus-facilities-metadata-panel')).toBeInTheDocument();
    expect(screen.getByTestId('campus-facilities-state-gallery')).toBeInTheDocument();
    expect(screen.getByText('Runtime mode: METADATA_READINESS_EVIDENCE_CONTROL_VISIBILITY_HUMAN_REVIEW_ONLY')).toBeInTheDocument();
  });
});
