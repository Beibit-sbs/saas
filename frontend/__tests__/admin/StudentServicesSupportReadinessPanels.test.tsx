import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES } from '@/modules/student_services_support/constants';
import { StudentServicesSupportPage } from '@/modules/student_services_support/pages';

describe('Student Services Support readiness and workflow panels', () => {
  const permissions = [
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.write,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.escalate,
    STUDENT_SERVICES_SUPPORT_PERMISSION_VALUES.dashboardRead,
  ];

  it('renders hardship and accommodation readiness panels', () => {
    render(<StudentServicesSupportPage routeKey="hardship" userPermissions={permissions} />);
    expect(screen.getByTestId('sss-hardship-panel')).toBeInTheDocument();
    expect(screen.getByTestId('sss-finance-hardship-handoff-panel')).toBeInTheDocument();
    expect(screen.getByText('POST /api/admin/student-services/hardship/from-finance-handoff')).toBeInTheDocument();

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

  it('renders finance hardship dashboard visibility without decision controls', () => {
    render(<StudentServicesSupportPage routeKey="dashboard" userPermissions={permissions} />);
    expect(screen.getByTestId('sss-dashboard-finance-hardship-visibility')).toBeInTheDocument();
    expect(screen.getByTestId('sss-finance-hardship-reviewer-queue')).toBeInTheDocument();
    expect(screen.getByTestId('sss-finance-hardship-reviewer-queue-item')).toBeInTheDocument();
    expect(screen.getByTestId('sss-finance-hardship-evidence-gap-intake-shell')).toBeInTheDocument();
    expect(screen.getByTestId('sss-finance-hardship-human-review-outcome-note-shell')).toBeInTheDocument();
    expect(screen.getByTestId('sss-finance-hardship-finance-office-referral-shell')).toBeInTheDocument();
    expect(screen.getByText('2 finance-origin hardship requests')).toBeInTheDocument();
    expect(screen.getByText('GET /api/admin/student-services/hardship/from-finance-handoff/reviewer-queue')).toBeInTheDocument();
    expect(screen.getByText('POST /api/admin/student-services/hardship/from-finance-handoff/1/evidence-gap')).toBeInTheDocument();
    expect(screen.getByText('POST /api/admin/student-services/hardship/from-finance-handoff/1/human-review-outcome-note')).toBeInTheDocument();
    expect(screen.getByText('POST /api/admin/student-services/hardship/from-finance-handoff/1/finance-office-referral')).toBeInTheDocument();
    expect(screen.getByText('satisfies_gap=balance_statement')).toBeInTheDocument();
    expect(screen.getByText('outcome_label=manual_review_recorded')).toBeInTheDocument();
    expect(screen.getByText('referral_target=student_finance_office')).toBeInTheDocument();
    expect(screen.getAllByText('noPaymentExecution=true').length).toBeGreaterThan(0);
    expect(screen.getByText('balance_statement')).toBeInTheDocument();
    expect(screen.getAllByText('noAutomaticAidDecision=true').length).toBeGreaterThan(0);
    expect(screen.getAllByText('noBillingBalanceMutation=true').length).toBeGreaterThan(0);
  });

  it('renders finance-office referral queue visibility without payment controls', () => {
    render(<StudentServicesSupportPage routeKey="dashboard" userPermissions={permissions} />);
    expect(screen.getByTestId('sss-finance-hardship-finance-office-referral-queue')).toBeInTheDocument();
    expect(screen.getByTestId('sss-finance-hardship-finance-office-referral-queue-item')).toBeInTheDocument();
    expect(
      screen.getByText('GET /api/admin/student-services/hardship/from-finance-handoff/finance-office-referral-queue'),
    ).toBeInTheDocument();
    expect(screen.getByText('student_finance_office')).toBeInTheDocument();
    expect(screen.getByText('manual_follow_up')).toBeInTheDocument();
    expect(screen.getByText('target_module=finance_procurement_asset referred_by_user_id=reviewer-1')).toBeInTheDocument();
    expect(screen.getAllByText('noPaymentExecution=true').length).toBeGreaterThan(0);
  });
});
