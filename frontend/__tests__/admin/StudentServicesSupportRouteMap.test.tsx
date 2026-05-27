import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES,
  STUDENT_SERVICES_SUPPORT_ROUTES,
} from '@/modules/student_services_support/constants';
import { StudentServicesSupportPage } from '@/modules/student_services_support/pages';

describe('Student Services Support route rendering', () => {
  const fullPermissions = Object.values(STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES);

  it('renders shell and navigation', () => {
    render(<StudentServicesSupportPage routeKey="overview" userPermissions={fullPermissions} />);
    expect(screen.getByTestId('sss-page-shell')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Student Services / Welfare / Support' })).toBeInTheDocument();
  });

  it('renders each planned route key content', () => {
    for (const route of STUDENT_SERVICES_SUPPORT_ROUTES) {
      const { unmount } = render(<StudentServicesSupportPage routeKey={route.key} userPermissions={fullPermissions} />);
      expect(screen.getByTestId(`sss-page-${route.key}`)).toBeInTheDocument();
      unmount();
    }
  });

  it('shows permission denied state when permission missing', () => {
    render(<StudentServicesSupportPage routeKey="dashboard" userPermissions={[STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read]} />);
    expect(screen.getByTestId('sss-permission-denied-state')).toBeInTheDocument();
  });
});
