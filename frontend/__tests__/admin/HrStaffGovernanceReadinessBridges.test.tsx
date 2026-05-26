import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { HrStaffGovernancePage } from '@/modules/hr-staff-governance/pages';
import { HR_STAFF_GOVERNANCE_PERMISSION_VALUES, HR_STAFF_GOVERNANCE_PROVIDER_PROFILES } from '@/modules/hr-staff-governance/constants';

describe('HR Staff Governance readiness and bridges', () => {
  it('renders the workload bridge as read-only-first', () => {
    render(<HrStaffGovernancePage routeKey="workload-bridge" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.workloadBridgeRead]} />);

    expect(screen.getAllByText('Bridge-first / read-only-first').length).toBeGreaterThan(0);
    expect(screen.getByText(/No cross-module write/i)).toBeInTheDocument();
  });

  it('renders the payroll readiness badge and boundary', () => {
    render(<HrStaffGovernancePage routeKey="payroll-readiness" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.payrollReadinessRead]} />);

    expect(screen.getByTestId('hr-payroll-readiness-badge')).toBeInTheDocument();
    expect(screen.getAllByText('No payroll execution').length).toBeGreaterThan(0);
  });

  it('renders the provider deferred badge and provider profiles', () => {
    render(<HrStaffGovernancePage routeKey="provider-readiness" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.providerReadinessRead]} />);

    expect(screen.getByTestId('hr-provider-deferred-badge')).toBeInTheDocument();
    expect(screen.getAllByText('No provider live sync').length).toBeGreaterThan(0);
    for (const profile of HR_STAFF_GOVERNANCE_PROVIDER_PROFILES) {
      expect(screen.getByText(profile.title)).toBeInTheDocument();
    }
  });

  it('renders access lifecycle review as review-only', () => {
    render(<HrStaffGovernancePage routeKey="access-lifecycle" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.accessLifecycleRead]} />);

    expect(screen.getAllByText('Access lifecycle review only').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/No autonomous access revocation/i).length).toBeGreaterThan(0);
  });

  it('renders limitations with full safety boundary coverage', () => {
    render(<HrStaffGovernancePage routeKey="limitations" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.limitationsRead]} />);

    expect(screen.getAllByText('No provider live sync').length).toBeGreaterThan(0);
    expect(screen.getAllByText('No production-ready claim').length).toBeGreaterThan(0);
    expect(screen.getAllByText('No GCC-ready claim').length).toBeGreaterThan(0);
  });
});