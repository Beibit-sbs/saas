import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { HR_STAFF_GOVERNANCE_PERMISSION_VALUES } from '@/modules/hr-staff-governance/constants';
import {
  getHrBoundaryLabels,
  HR_STAFF_GOVERNANCE_BOUNDARY_COPY,
  HR_STAFF_GOVERNANCE_BOUNDARY_LABELS,
  HR_STAFF_GOVERNANCE_FORBIDDEN_LABELS,
} from '@/modules/hr-staff-governance/boundaryLabels';
import { HrBoundaryBanner, HrStaffGovernancePage } from '@/modules/hr-staff-governance/pages';

describe('HR Staff Governance boundary labels', () => {
  it('exports the required boundary labels', () => {
    expect(HR_STAFF_GOVERNANCE_BOUNDARY_COPY).toContain(HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.metadataEvidenceOnlyHrFoundation);
    expect(HR_STAFF_GOVERNANCE_BOUNDARY_COPY).toContain(HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noPayrollExecution);
    expect(HR_STAFF_GOVERNANCE_BOUNDARY_COPY).toContain(HR_STAFF_GOVERNANCE_BOUNDARY_LABELS.noProviderLiveSync);
  });

  it('exports the forbidden label list for negative assertions', () => {
    expect(HR_STAFF_GOVERNANCE_FORBIDDEN_LABELS).toContain('Execute payroll');
    expect(HR_STAFF_GOVERNANCE_FORBIDDEN_LABELS).toContain('Connect provider live');
  });

  it('returns route-specific boundary labels', () => {
    expect(getHrBoundaryLabels('dashboard')).toContain('fakeMetrics=false');
    expect(getHrBoundaryLabels('provider-readiness')).toContain('No provider live sync');
  });

  it('renders the boundary banner chips', () => {
    render(<HrBoundaryBanner labels={getHrBoundaryLabels('limitations')} />);

    expect(screen.getByTestId('hr-boundary-banner')).toBeInTheDocument();
    expect(screen.getByText('Metadata/evidence-only HR foundation')).toBeInTheDocument();
    expect(screen.getAllByText('No automatic hiring/firing').length).toBeGreaterThan(0);
  });

  it('renders overview boundary copy and incomplete data support', () => {
    render(
      <HrStaffGovernancePage
        routeKey="overview"
        userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.overviewRead]}
      />,
    );

    expect(screen.getByText('Incomplete data supported')).toBeInTheDocument();
    expect(screen.getAllByText('fakeMetrics=false').length).toBeGreaterThan(0);
  });

  it('renders a fail-closed permission denied state', () => {
    render(<HrStaffGovernancePage routeKey="limitations" userPermissions={[]} />);

    expect(screen.getByTestId('hr-permission-denied-panel')).toBeInTheDocument();
    expect(screen.getByText(/fail-closed/i)).toBeInTheDocument();
  });
});