import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FinanceProcurementAssetPage, FpaStudentFinanceReferralAcknowledgementLedger } from '@/modules/finance-procurement-asset/pages';
import { FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES } from '@/modules/finance-procurement-asset/constants';

describe('Finance Procurement Asset readiness and bridges', () => {
  it('live-renders acknowledgement records from the bridge ledger without payment controls', () => {
    render(
      <FpaStudentFinanceReferralAcknowledgementLedger
        records={[
          {
            id: 11,
            tenant_id: 1,
            status: 'HUMAN_REVIEW_REQUIRED',
            source_record_id: 7,
            metadata: {
              acknowledgement_state: 'non_executing_acknowledged',
              referred_by_user_id: 'reviewer-9',
              source_hardship_id: 7,
              referral_target: 'student_finance_office',
            },
            limitations: [],
          },
        ]}
      />,
    );
    expect(screen.getByTestId('fpa-student-finance-referral-acknowledgement-rows')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-student-finance-referral-acknowledgement-row')).toHaveTextContent('referred_by_user_id=reviewer-9');
    expect(screen.getByTestId('fpa-student-finance-referral-acknowledgement-row')).toHaveTextContent('source_hardship_id=7');
  });

  it('renders payment readiness badge on payment readiness route', () => {
    render(<FinanceProcurementAssetPage routeKey="payment-readiness" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.paymentReadinessRead]} />);

    expect(screen.getByTestId('fpa-payment-readiness-badge')).toHaveTextContent('paymentExecutionEnabled=false');
  });

  it('renders provider deferred badge on provider readiness route', () => {
    render(<FinanceProcurementAssetPage routeKey="provider-readiness" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.providerReadinessRead]} />);

    expect(screen.getByTestId('fpa-provider-deferred-badge')).toHaveTextContent('providerConnected=false');
  });

  it('renders provider bridge cards on provider readiness route', () => {
    render(<FinanceProcurementAssetPage routeKey="provider-readiness" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.providerReadinessRead]} />);

    expect(screen.getByTestId('fpa-bridge-bank-core')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-bridge-erp-1c')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-bridge-payment-gateway')).toBeInTheDocument();
  });

  it('renders bridge cards on bridges route', () => {
    render(<FinanceProcurementAssetPage routeKey="bridges" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bridgesExecutiveRead]} />);

    expect(screen.getByRole('heading', { level: 1, name: 'Bridge Visibility' })).toBeInTheDocument();
    expect(screen.getByTestId('fpa-bridge-hr-payroll-bridge')).toBeInTheDocument();
  });

  it('renders student finance bridge without payment execution controls', () => {
    render(<FinanceProcurementAssetPage routeKey="student-finance" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bridgesStudentFinanceRead]} />);

    expect(screen.getByRole('heading', { level: 1, name: 'Student Finance Bridge' })).toBeInTheDocument();
    expect(screen.getByTestId('fpa-student-finance-bridge-panel')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-receivables-intake-shell')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-hardship-handoff-link')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-student-finance-referral-intake-panel')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-student-finance-referral-intake-shell')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-student-finance-referral-acknowledge-shell')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-student-finance-referral-acknowledgement-ledger')).toBeInTheDocument();
    expect(screen.getAllByText('acknowledgement_state=non_executing_acknowledged').length).toBeGreaterThan(0);
    expect(screen.getByText(/referred_by_user_id \(acknowledging reviewer\)/)).toBeInTheDocument();
    expect(screen.getAllByText('POST /api/admin/finance-procurement-asset/bridges/student-finance-referrals/acknowledge').length).toBeGreaterThan(0);
    expect(screen.getAllByText('GET /api/admin/finance-procurement-asset/bridges/student-finance-referrals').length).toBeGreaterThan(0);
    expect(screen.getAllByText('referral_target=student_finance_office').length).toBeGreaterThan(0);
    expect(screen.getAllByText('noPaymentExecution=true').length).toBeGreaterThan(0);
    expect(screen.getByText('tuitionChargeCreation=false')).toBeInTheDocument();
    expect(screen.getAllByText('paymentExecutionEnabled=false').length).toBeGreaterThan(0);
    expect(screen.getAllByText('POST /api/admin/finance-procurement-asset/receivables/metadata').length).toBeGreaterThan(0);
  });

  it('renders ERP and bank readiness routes with deferred boundaries', () => {
    render(<FinanceProcurementAssetPage routeKey="erp-readiness" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.erpReadinessRead]} />);
    render(<FinanceProcurementAssetPage routeKey="bank-readiness" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bankReadinessRead]} />);

    expect(screen.getAllByTestId('fpa-provider-deferred-badge').length).toBeGreaterThanOrEqual(2);
  });

  it('keeps audit route read-only when only read permission is granted', () => {
    render(<FinanceProcurementAssetPage routeKey="audit" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.auditRead]} />);

    expect(screen.getByRole('heading', { level: 1, name: 'Audit / Evidence' })).toBeInTheDocument();
    expect(screen.getAllByText('metadata/evidence-only').length).toBeGreaterThanOrEqual(1);
  });
});
