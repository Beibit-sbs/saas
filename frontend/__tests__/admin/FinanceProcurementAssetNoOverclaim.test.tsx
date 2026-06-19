import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS } from '@/modules/finance-procurement-asset/boundaryLabels';
import { FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES, FINANCE_PROCUREMENT_ASSET_ROUTES } from '@/modules/finance-procurement-asset/constants';
import { financeProcurementAssetApi } from '@/modules/finance-procurement-asset/api';
import { FinanceProcurementAssetPage } from '@/modules/finance-procurement-asset/pages';

describe('Finance Procurement Asset no-overclaim boundaries', () => {
  it('does not render forbidden labels on the overview page', () => {
    render(<FinanceProcurementAssetPage routeKey="overview" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead]} />);

    for (const label of FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('does not render forbidden labels on provider readiness or bridges pages', () => {
    render(<FinanceProcurementAssetPage routeKey="provider-readiness" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.providerReadinessRead]} />);
    render(<FinanceProcurementAssetPage routeKey="bridges" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bridgesExecutiveRead]} />);

    for (const label of FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
  });

  it('renders the explicit no-overclaim footer assertions', () => {
    render(<FinanceProcurementAssetPage routeKey="overview" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead]} />);

    expect(screen.getByText('No live bank integration UI.')).toBeInTheDocument();
    expect(screen.getByText('No payment execution UI.')).toBeInTheDocument();
    expect(screen.getByText('No production/sales/GCC/L5/L6 claim.')).toBeInTheDocument();
  });

  it('keeps the route inventory fixed at 23 routes', () => {
    expect(FINANCE_PROCUREMENT_ASSET_ROUTES).toHaveLength(23);
  });

  it('does not expose forbidden API helpers', () => {
    expect('executePayment' in financeProcurementAssetApi).toBe(false);
    expect('connectBankLive' in financeProcurementAssetApi).toBe(false);
    expect('connectErpLive' in financeProcurementAssetApi).toBe(false);
    expect('autoApproveProcurement' in financeProcurementAssetApi).toBe(false);
    expect('hiddenVendorScore' in financeProcurementAssetApi).toBe(false);
  });

  it('does not render a positive GCC or sales-ready claim on limitations route', () => {
    render(<FinanceProcurementAssetPage routeKey="limitations" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.limitationsRead]} />);

    expect(screen.queryByText('GCC ready')).not.toBeInTheDocument();
    expect(screen.queryByText('Sales ready')).not.toBeInTheDocument();
    expect(screen.queryByText('Production ready')).not.toBeInTheDocument();
  });
});
