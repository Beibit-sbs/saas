import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { HrStaffGovernancePage } from '@/modules/hr-staff-governance/pages';
import { HR_STAFF_GOVERNANCE_PERMISSION_VALUES, HR_STAFF_GOVERNANCE_WORKFLOWS } from '@/modules/hr-staff-governance/constants';

describe('HR Staff Governance workflows', () => {
  it('keeps the full 12 workflow definitions', () => {
    expect(HR_STAFF_GOVERNANCE_WORKFLOWS).toHaveLength(12);
  });

  it('renders the recruitment workflow with a human review boundary', () => {
    render(<HrStaffGovernancePage routeKey="recruitment" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.recruitmentRead]} />);

    expect(screen.getByText('Recruitment Metadata -> Committee Review Evidence')).toBeInTheDocument();
    expect(screen.getAllByText('No automatic hiring/firing').length).toBeGreaterThan(0);
  });

  it('renders the leave workflow with explicit review-only language', () => {
    render(<HrStaffGovernancePage routeKey="leave" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.leaveRead]} />);

    expect(screen.getByText('Leave Request -> Human Review -> Evidence Status')).toBeInTheDocument();
    expect(screen.getAllByText('No automatic leave approval/rejection').length).toBeGreaterThan(0);
  });

  it('renders the disciplinary workflow with no automatic decision boundary', () => {
    render(<HrStaffGovernancePage routeKey="disciplinary" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.disciplinaryCasesRead]} />);

    expect(screen.getByText('Disciplinary Case -> Human Review -> No Automatic Decision Boundary')).toBeInTheDocument();
    expect(screen.getAllByText('No automatic disciplinary decision').length).toBeGreaterThan(0);
  });

  it('renders the offboarding workflow with access review language', () => {
    render(<HrStaffGovernancePage routeKey="offboarding" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.offboardingRead]} />);

    expect(screen.getByText('Offboarding -> Access Lifecycle Review -> No Autonomous Revocation Boundary')).toBeInTheDocument();
    expect(screen.getAllByText('Access lifecycle review only').length).toBeGreaterThan(0);
  });

  it('renders the performance workflow without hidden scoring', () => {
    render(<HrStaffGovernancePage routeKey="performance" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.appraisalsRead]} />);

    expect(screen.getByText('Appraisal Cycle -> Review Evidence -> No Score Boundary')).toBeInTheDocument();
    expect(screen.getAllByText('No hidden employee/faculty score').length).toBeGreaterThan(0);
  });

  it('renders workflow review panels on sensitive pages', () => {
    render(<HrStaffGovernancePage routeKey="requests" userPermissions={[HR_STAFF_GOVERNANCE_PERMISSION_VALUES.staffRequestsRead]} />);

    expect(screen.getByTestId('hr-review-panel-human-review-boundary')).toBeInTheDocument();
    expect(screen.getAllByTestId('hr-human-review-badge').length).toBeGreaterThan(0);
  });
});