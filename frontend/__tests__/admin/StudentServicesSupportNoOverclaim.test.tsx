import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { STUDENT_SERVICES_FORBIDDEN_LABELS } from '@/modules/student_services_support/boundaryLabels';
import { STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES, STUDENT_SERVICES_SUPPORT_ROUTES } from '@/modules/student_services_support/constants';
import { studentServicesSupportApi } from '@/modules/student_services_support/api';
import { StudentServicesSupportPage } from '@/modules/student_services_support/pages';

describe('Student Services Support no-overclaim contract', () => {
  it('does not render forbidden overclaim labels', () => {
    render(
      <StudentServicesSupportPage
        routeKey="overview"
        userPermissions={[STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read]}
      />,
    );

    for (const label of STUDENT_SERVICES_FORBIDDEN_LABELS) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('renders explicit no-overclaim footer assertions', () => {
    render(
      <StudentServicesSupportPage
        routeKey="overview"
        userPermissions={[STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read]}
      />,
    );

    expect(screen.getByText('No automatic hardship approval UI.')).toBeInTheDocument();
    expect(screen.getByText('No automatic accommodation approval UI.')).toBeInTheDocument();
    expect(screen.getByText('No production/sales/GCC/L5/L6 claim.')).toBeInTheDocument();
  });

  it('keeps route inventory fixed at 10 routes', () => {
    expect(STUDENT_SERVICES_SUPPORT_ROUTES).toHaveLength(10);
  });

  it('does not expose forbidden API helper names', () => {
    expect('approveHardshipAutomatically' in studentServicesSupportApi).toBe(false);
    expect('approveAccommodationAutomatically' in studentServicesSupportApi).toBe(false);
    expect('resolveComplaintAutomatically' in studentServicesSupportApi).toBe(false);
    expect('submitToGovernment' in studentServicesSupportApi).toBe(false);
    expect('generateFakeEvidence' in studentServicesSupportApi).toBe(false);
  });
});
