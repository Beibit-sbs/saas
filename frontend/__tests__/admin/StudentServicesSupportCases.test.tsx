import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES } from '@/modules/student_services_support/constants';
import { StudentServicesSupportPage } from '@/modules/student_services_support/pages';

describe('Student Services Support case surfaces', () => {
  const permissions = [
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.read,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.write,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.auditRead,
  ];

  it('renders case list/detail, note timeline, and evidence panel', () => {
    render(<StudentServicesSupportPage routeKey="cases" userPermissions={permissions} />);
    expect(screen.getByTestId('sss-case-list')).toBeInTheDocument();

    const { unmount } = render(<StudentServicesSupportPage routeKey="case-detail" userPermissions={permissions} />);
    expect(screen.getByTestId('sss-case-detail')).toBeInTheDocument();
    expect(screen.getByTestId('sss-note-timeline')).toBeInTheDocument();
    expect(screen.getByTestId('sss-evidence-panel')).toBeInTheDocument();
    unmount();
  });

  it('renders empty states', () => {
    render(
      <StudentServicesSupportPage
        routeKey="cases"
        userPermissions={permissions}
        stateOverride={{ cases: [] }}
      />,
    );
    expect(screen.getByTestId('sss-cases-empty')).toBeInTheDocument();
  });
});
