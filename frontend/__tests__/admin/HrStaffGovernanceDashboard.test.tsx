import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { HrStaffGovernancePage } from '@/modules/hr-staff-governance/pages';
import { HR_STAFF_GOVERNANCE_DASHBOARD_WIDGETS, HR_STAFF_GOVERNANCE_PERMISSION_VALUES } from '@/modules/hr-staff-governance/constants';

describe('HR Staff Governance dashboard', () => {
  it('renders the dashboard root and widget grid', () => {
    render(<HrStaffGovernancePage routeKey="dashboard" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.dashboardRead]} />);

    expect(screen.getByTestId('hr-page-dashboard')).toBeInTheDocument();
    expect(screen.getByTestId('hr-dashboard-grid')).toBeInTheDocument();
  });

  it('renders backend baseline counts and data source', () => {
    render(<HrStaffGovernancePage routeKey="dashboard" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.dashboardRead]} />);

    expect(screen.getByText(/Backend route count used: 62/i)).toBeInTheDocument();
    expect(screen.getByText(/Backend permission count used: 56/i)).toBeInTheDocument();
    expect(screen.getByText(/computed_from_hr_staff_governance_metadata/i)).toBeInTheDocument();
  });

  it('renders the visible safety flags for dashboard-like surfaces', () => {
    render(<HrStaffGovernancePage routeKey="dashboard" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.dashboardRead]} />);

    expect(screen.getAllByText('false').length).toBeGreaterThan(1);
    expect(screen.getByText(/humanReviewRequired=true/i)).toBeInTheDocument();
    expect(screen.getAllByText(/fakeMetrics=false/i).length).toBeGreaterThan(0);
  });

  it('renders all 12 dashboard widgets', () => {
    render(<HrStaffGovernancePage routeKey="dashboard" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.dashboardRead]} />);

    for (const widget of HR_STAFF_GOVERNANCE_DASHBOARD_WIDGETS) {
      expect(screen.getByTestId(`hr-widget-${widget.key}`)).toBeInTheDocument();
    }
  });

  it('renders incomplete data support and no-overclaim footer', () => {
    render(<HrStaffGovernancePage routeKey="dashboard" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.dashboardRead]} />);

    expect(screen.getByTestId('hr-incomplete-data-notice')).toBeInTheDocument();
    expect(screen.getByTestId('hr-no-overclaim-footer')).toBeInTheDocument();
  });

  it('fails closed without dashboard permission', () => {
    render(<HrStaffGovernancePage routeKey="dashboard" userPermissions={[]} />);

    expect(screen.getByTestId('hr-permission-denied-panel')).toBeInTheDocument();
  });
});