import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES } from '@/modules/student_services_support/constants';
import { StudentServicesSupportPage } from '@/modules/student_services_support/pages';

describe('Student Services Support readiness and workflow panels', () => {
  const permissions = [
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.write,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.escalate,
  ];

  it('renders hardship and accommodation readiness panels', () => {
    render(<StudentServicesSupportPage routeKey="hardship" userPermissions={permissions} />);
    expect(screen.getByTestId('sss-hardship-panel')).toBeInTheDocument();

    const { unmount } = render(<StudentServicesSupportPage routeKey="accommodations" userPermissions={permissions} />);
    expect(screen.getByTestId('sss-accommodation-panel')).toBeInTheDocument();
    unmount();
  });

  it('renders complaint and escalation panels', () => {
    render(<StudentServicesSupportPage routeKey="complaints" userPermissions={permissions} />);
    expect(screen.getByTestId('sss-complaint-panel')).toBeInTheDocument();

    const { unmount } = render(<StudentServicesSupportPage routeKey="escalations" userPermissions={permissions} />);
    expect(screen.getByTestId('sss-escalation-panel')).toBeInTheDocument();
    unmount();
  });
});
