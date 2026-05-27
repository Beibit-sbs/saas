import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES } from '@/modules/student_services_support/constants';
import { StudentServicesSupportPage } from '@/modules/student_services_support/pages';

describe('Student Services Support dashboard contract', () => {
  it('renders required dashboard boundary booleans and data source', () => {
    render(
      <StudentServicesSupportPage
        routeKey="dashboard"
        userPermissions={[STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.dashboardRead]}
      />,
    );

    expect(screen.getAllByText('fake_metrics=false').length).toBeGreaterThan(0);
    expect(screen.getByText('data_source=computed_from_student_services_support_records')).toBeInTheDocument();
    expect(screen.getByText('incomplete_data=true')).toBeInTheDocument();
    expect(screen.getAllByText('hidden_score_present=false').length).toBeGreaterThan(0);
    expect(screen.getByText('No hidden student score. No discriminatory risk score.')).toBeInTheDocument();
  });

  it('renders dashboard cards', () => {
    render(
      <StudentServicesSupportPage
        routeKey="dashboard"
        userPermissions={[STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.dashboardRead]}
      />,
    );

    expect(screen.getByTestId('sss-dashboard-card-open-requests')).toBeInTheDocument();
    expect(screen.getByTestId('sss-dashboard-card-open-cases')).toBeInTheDocument();
    expect(screen.getByTestId('sss-dashboard-card-escalated')).toBeInTheDocument();
  });
});
