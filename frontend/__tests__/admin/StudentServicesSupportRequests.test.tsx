import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES } from '@/modules/student_services_support/constants';
import { StudentServicesSupportPage } from '@/modules/student_services_support/pages';

describe('Student Services Support requests surfaces', () => {
  const permissions = [
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.write,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.assign,
  ];

  it('renders request list and request detail blocks', () => {
    render(<StudentServicesSupportPage routeKey="requests" userPermissions={permissions} />);
    expect(screen.getByTestId('sss-request-list')).toBeInTheDocument();

    const { unmount } = render(<StudentServicesSupportPage routeKey="request-detail" userPermissions={permissions} />);
    expect(screen.getByTestId('sss-request-detail')).toBeInTheDocument();
    expect(screen.getByTestId('sss-assignment-panel')).toBeInTheDocument();
    unmount();
  });

  it('renders loading and error states', () => {
    const { rerender } = render(
      <StudentServicesSupportPage routeKey="requests" userPermissions={permissions} stateOverride={{ loading: true }} />,
    );
    expect(screen.getByTestId('sss-loading-state')).toBeInTheDocument();

    rerender(
      <StudentServicesSupportPage routeKey="requests" userPermissions={permissions} stateOverride={{ loading: false, error: 'boom' }} />,
    );
    expect(screen.getByTestId('sss-error-state')).toBeInTheDocument();
  });

  it('renders empty states', () => {
    render(
      <StudentServicesSupportPage
        routeKey="requests"
        userPermissions={permissions}
        stateOverride={{ requests: [] }}
      />,
    );
    expect(screen.getByTestId('sss-requests-empty')).toBeInTheDocument();
  });
});
