import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { STUDENT_SERVICES_BOUNDARY_COPY } from '@/modules/student_services_support/boundaryLabels';
import { STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES } from '@/modules/student_services_support/constants';
import { StudentServicesSupportPage } from '@/modules/student_services_support/pages';

describe('Student Services Support boundary labels', () => {
  it('renders core boundary labels on overview', () => {
    render(
      <StudentServicesSupportPage
        routeKey="overview"
        userPermissions={[STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read]}
      />,
    );

    for (const label of STUDENT_SERVICES_BOUNDARY_COPY) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }

    expect(screen.getByTestId('sss-boundary-banner')).toBeInTheDocument();
  });

  it('renders permission denied state when route permission missing', () => {
    render(
      <StudentServicesSupportPage
        routeKey="escalations"
        userPermissions={[STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read]}
      />,
    );
    expect(screen.getByTestId('sss-permission-denied-state')).toBeInTheDocument();
  });
});
