import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FinanceProcurementAssetPage } from '@/modules/finance-procurement-asset/pages';
import { FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES } from '@/modules/finance-procurement-asset/constants';

describe('Finance Procurement Asset dashboard and shell', () => {
  it('renders the overview page shell and navigation', () => {
    render(<FinanceProcurementAssetPage routeKey="overview" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead]} />);

    expect(screen.getByRole('heading', { level: 1, name: 'Finance / Procurement / Asset Suite' })).toBeInTheDocument();
    expect(screen.getByText('Route: /console/finance-procurement-asset')).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Finance procurement asset navigation' })).toBeInTheDocument();
  });

  it('renders dashboard widgets and incomplete-data notice on dashboard route', () => {
    render(<FinanceProcurementAssetPage routeKey="dashboard" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.dashboardRead]} />);

    expect(screen.getByTestId('fpa-dashboard-grid')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-registry-table')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-state-gallery')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-incomplete-data-notice')).toBeInTheDocument();
    expect(screen.getAllByText('Billing Visibility').length).toBeGreaterThanOrEqual(1);
  });

  it('renders the safety checklist and no-overclaim footer', () => {
    render(<FinanceProcurementAssetPage routeKey="dashboard" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.dashboardRead]} />);

    expect(screen.getByTestId('fpa-safety-checklist')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-no-overclaim-footer')).toBeInTheDocument();
    expect(screen.getByText('No payment execution UI.')).toBeInTheDocument();
  });

  it('renders human review badge on sensitive billing route', () => {
    render(<FinanceProcurementAssetPage routeKey="billing" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.billingRead]} />);

    expect(screen.getAllByTestId('fpa-human-review-badge').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole('heading', { level: 1, name: 'Billing Visibility' })).toBeInTheDocument();
  });

  it('renders permission denied panel for missing route permission', () => {
    render(<FinanceProcurementAssetPage routeKey="billing" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead]} />);

    expect(screen.getByTestId('fpa-permission-denied-panel')).toBeInTheDocument();
    expect(screen.getByText(/finance_procurement_asset\.billing\.read/)).toBeInTheDocument();
  });

  it('renders metric cards with false safety values', () => {
    render(<FinanceProcurementAssetPage routeKey="overview" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead]} />);

    expect(screen.getByTestId('fpa-metric-fakemetrics')).toHaveTextContent('false');
    expect(screen.getByTestId('fpa-metric-fakefinancedata')).toHaveTextContent('false');
    expect(screen.getByTestId('fpa-metric-fakepaymentdata')).toHaveTextContent('false');
  });
});