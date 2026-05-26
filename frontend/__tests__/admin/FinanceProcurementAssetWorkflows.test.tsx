import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { buildFpaPageModel, FinanceProcurementAssetPage, getFpaRouteDefinition } from '@/modules/finance-procurement-asset/pages';
import { FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES, FINANCE_PROCUREMENT_ASSET_WORKFLOWS } from '@/modules/finance-procurement-asset/constants';

describe('Finance Procurement Asset workflows', () => {
  it('builds budget control page model with workflow and state text', () => {
    const model = buildFpaPageModel('budget-control');

    expect(model.route.key).toBe('budget-control');
    expect(model.workflows.length).toBeGreaterThan(0);
    expect(model.emptyState).toContain('Budget Control Review');
    expect(model.incompleteDataMessage).toContain('Incomplete data');
  });

  it('builds provider readiness model with route definition and drilldowns', () => {
    const route = getFpaRouteDefinition('provider-readiness');
    const model = buildFpaPageModel('provider-readiness');

    expect(route.path).toBe('/console/finance-procurement-asset/provider-readiness');
    expect(model.route.backendEndpoints).toContain('GET /api/admin/finance-procurement-asset/payment-gateway-readiness');
  });

  it('keeps the workflow inventory explicit', () => {
    expect(FINANCE_PROCUREMENT_ASSET_WORKFLOWS.map((workflow) => workflow.key)).toContain('procurement-committee-review');
    expect(FINANCE_PROCUREMENT_ASSET_WORKFLOWS.map((workflow) => workflow.key)).toContain('payment-provider-readiness');
  });

  it('renders workflow-backed evidence and review panels on procurement reviews route', () => {
    render(<FinanceProcurementAssetPage routeKey="procurement-reviews" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.procurementReviewsRead]} />);

    expect(screen.getByTestId('fpa-evidence-table')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-audit-timeline')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-review-panel-human-review-boundary')).toBeInTheDocument();
  });

  it('renders limitations and metadata form shell on budget planning route', () => {
    render(<FinanceProcurementAssetPage routeKey="budget-planning" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.budgetPlansRead]} />);

    expect(screen.getByTestId('fpa-limitations-panel')).toBeInTheDocument();
    expect(screen.getByTestId('fpa-form-shell-budget-planning-surface')).toBeInTheDocument();
  });

  it('keeps human-review messaging visible on audit route', () => {
    render(<FinanceProcurementAssetPage routeKey="audit" userPermissions={[FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.auditRead]} />);

    expect(screen.getAllByTestId('fpa-human-review-badge').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole('heading', { level: 1, name: 'Audit / Evidence' })).toBeInTheDocument();
  });
});