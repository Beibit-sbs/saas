import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FinanceProcurementAssetPage } from '@/modules/finance-procurement-asset/pages';
import { FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES } from '@/modules/finance-procurement-asset/constants';

describe('Finance Procurement Asset readiness and bridges', () => {
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