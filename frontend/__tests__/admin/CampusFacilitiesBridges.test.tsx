import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  CAMPUS_FACILITIES_BRIDGE_DEFINITIONS,
  CAMPUS_FACILITIES_ROUTE_DEFINITIONS,
} from '@/modules/campus-facilities/constants';
import { CampusFacilitiesPage } from '@/modules/campus-facilities/pages';

describe('Campus Facilities bridge panels', () => {
  it('keeps bridge definitions count fixed at 4', () => {
    expect(CAMPUS_FACILITIES_BRIDGE_DEFINITIONS).toHaveLength(4);
  });

  it('marks four bridge routes in route map', () => {
    expect(CAMPUS_FACILITIES_ROUTE_DEFINITIONS.filter((route) => route.bridgeRoute)).toHaveLength(4);
  });

  it('renders access visitor bridge panel', () => {
    render(<CampusFacilitiesPage routeKey="bridges-access-visitor" userPermissions={['campus_facilities.bridges.access_visitor']} />);
    expect(screen.getByTestId('campus-facilities-bridge-panel')).toBeInTheDocument();
    expect(screen.getByTestId('campus-facilities-bridge-access-visitor')).toBeInTheDocument();
  });

  it('renders all bridge cards', () => {
    render(<CampusFacilitiesPage routeKey="bridges-finance-asset" userPermissions={['campus_facilities.bridges.finance_asset']} />);
    expect(screen.getByTestId('campus-facilities-bridge-access-visitor')).toBeInTheDocument();
    expect(screen.getByTestId('campus-facilities-bridge-student-services')).toBeInTheDocument();
    expect(screen.getByTestId('campus-facilities-bridge-finance-asset')).toBeInTheDocument();
    expect(screen.getByTestId('campus-facilities-bridge-hr-staff')).toBeInTheDocument();
  });
});
