import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { HR_STAFF_GOVERNANCE_FORBIDDEN_LABELS } from '@/modules/hr-staff-governance/boundaryLabels';
import { HR_STAFF_GOVERNANCE_PERMISSION_VALUES, HR_STAFF_GOVERNANCE_ROUTES } from '@/modules/hr-staff-governance/constants';
import { HrStaffGovernancePage } from '@/modules/hr-staff-governance/pages';
import { hrStaffGovernanceApi } from '@/modules/hr-staff-governance/api';

describe('HR Staff Governance no-overclaim boundaries', () => {
  it('does not render forbidden labels on the overview page', () => {
    render(<HrStaffGovernancePage routeKey="overview" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.overviewRead]} />);

    for (const label of HR_STAFF_GOVERNANCE_FORBIDDEN_LABELS) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('does not render forbidden labels on the dashboard page', () => {
    render(<HrStaffGovernancePage routeKey="dashboard" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.dashboardRead]} />);

    for (const label of HR_STAFF_GOVERNANCE_FORBIDDEN_LABELS) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('does not render forbidden labels on provider readiness or offboarding pages', () => {
    render(<HrStaffGovernancePage routeKey="provider-readiness" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.providerReadinessRead]} />);
    render(<HrStaffGovernancePage routeKey="offboarding" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.offboardingRead]} />);

    for (const label of HR_STAFF_GOVERNANCE_FORBIDDEN_LABELS) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('renders the explicit no-overclaim footer assertions', () => {
    render(<HrStaffGovernancePage routeKey="overview" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.overviewRead]} />);

    expect(screen.getByText('No automatic hiring/firing UI.')).toBeInTheDocument();
    expect(screen.getByText('No provider live sync UI.')).toBeInTheDocument();
    expect(screen.getByText('No production/sales/GCC/L5/L6 claim.')).toBeInTheDocument();
  });

  it('keeps the route inventory fixed at 20 routes', () => {
    expect(HR_STAFF_GOVERNANCE_ROUTES).toHaveLength(20);
  });

  it('does not expose forbidden API helpers', () => {
    expect('executePayroll' in hrStaffGovernanceApi).toBe(false);
    expect('automaticHireDecision' in hrStaffGovernanceApi).toBe(false);
    expect('connectProviderLive' in hrStaffGovernanceApi).toBe(false);
  });
});