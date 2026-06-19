import { describe, expect, it } from 'vitest';
import {
  fakeFinanceData,
  fakeMetrics,
  fakePaymentData,
  FINANCE_PROCUREMENT_ASSET_API_BASE,
  FINANCE_PROCUREMENT_ASSET_BACKEND_ROUTE_COUNT,
  FINANCE_PROCUREMENT_ASSET_DATA_SOURCE,
  FINANCE_PROCUREMENT_ASSET_DASHBOARD_WIDGETS,
  FINANCE_PROCUREMENT_ASSET_PERMISSION_COUNT,
  FINANCE_PROCUREMENT_ASSET_PROVIDER_PROFILES,
  FINANCE_PROCUREMENT_ASSET_ROUTE_COUNT,
  FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY,
  FINANCE_PROCUREMENT_ASSET_ROUTES,
  FINANCE_PROCUREMENT_ASSET_RUNTIME_MODE,
  FINANCE_PROCUREMENT_ASSET_SAFETY_FLAGS,
  FINANCE_PROCUREMENT_ASSET_SOURCE_BACKEND_BASELINE_COMMIT,
  FINANCE_PROCUREMENT_ASSET_SOURCE_BACKEND_RUNTIME_COMMIT,
  FINANCE_PROCUREMENT_ASSET_WORKFLOWS,
} from '@/modules/finance-procurement-asset/constants';
import type {
  FpaDashboardSummary,
  FpaOverview,
  FpaPaymentReadiness,
  FpaSafetyFlags,
} from '@/modules/finance-procurement-asset/types';

describe('Finance Procurement Asset types', () => {
  it('exports the expected module constants', () => {
    expect(FINANCE_PROCUREMENT_ASSET_API_BASE).toBe('/api/admin/finance-procurement-asset');
    expect(FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY).toBe('/console/finance-procurement-asset');
    expect(FINANCE_PROCUREMENT_ASSET_ROUTE_COUNT).toBe(23);
    expect(FINANCE_PROCUREMENT_ASSET_BACKEND_ROUTE_COUNT).toBe(56);
    expect(FINANCE_PROCUREMENT_ASSET_PERMISSION_COUNT).toBe(50);
    expect(FINANCE_PROCUREMENT_ASSET_RUNTIME_MODE).toBe('METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY');
    expect(FINANCE_PROCUREMENT_ASSET_SOURCE_BACKEND_BASELINE_COMMIT).toBe('0453fbd');
    expect(FINANCE_PROCUREMENT_ASSET_SOURCE_BACKEND_RUNTIME_COMMIT).toBe('0394414');
    expect(FINANCE_PROCUREMENT_ASSET_DATA_SOURCE).toBe('computed_from_finance_procurement_asset_metadata');
  });

  it('keeps the full 23-route contract explicit', () => {
    expect(FINANCE_PROCUREMENT_ASSET_ROUTES).toHaveLength(23);
    expect(FINANCE_PROCUREMENT_ASSET_ROUTES[0]?.path).toBe('/console/finance-procurement-asset');
    expect(FINANCE_PROCUREMENT_ASSET_ROUTES[1]?.path).toBe('/console/finance-procurement-asset/dashboard');
    expect(FINANCE_PROCUREMENT_ASSET_ROUTES.map((route) => route.path)).toContain('/console/finance-procurement-asset/student-finance');
    expect(FINANCE_PROCUREMENT_ASSET_ROUTES.at(-1)?.path).toBe('/console/finance-procurement-asset/limitations');
  });

  it('defines the expected dashboard widgets and workflows', () => {
    expect(FINANCE_PROCUREMENT_ASSET_DASHBOARD_WIDGETS).toHaveLength(12);
    expect(FINANCE_PROCUREMENT_ASSET_WORKFLOWS).toHaveLength(12);
  });

  it('defines the expected deferred provider profiles', () => {
    expect(FINANCE_PROCUREMENT_ASSET_PROVIDER_PROFILES.map((profile) => profile.key)).toEqual([
      'BANK_CORE',
      'ERP_1C',
      'PAYMENT_GATEWAY',
      'HR_PAYROLL_BRIDGE',
      'DOCUMENT_CONTRACTS',
    ]);
  });

  it('models safety flags explicitly', () => {
    const flags: FpaSafetyFlags = {
      fake_metrics: false,
      fake_finance_data: false,
      fake_payment_data: false,
      provider_connected: false,
      live_bank_sync: false,
      live_erp_sync: false,
      payment_execution_enabled: false,
      automatic_procurement_approval_enabled: false,
      automatic_budget_approval_enabled: false,
      automatic_vendor_award_enabled: false,
      hidden_score_present: false,
      human_review_required: true,
      incomplete_data: true,
      limitations: ['Metadata/evidence-only finance foundation'],
    };

    expect(flags.fake_metrics).toBe(false);
    expect(flags.fake_finance_data).toBe(false);
    expect(flags.fake_payment_data).toBe(false);
    expect(flags.hidden_score_present).toBe(false);
  });

  it('models overview and dashboard trust fields', () => {
    const overview: FpaOverview = {
      ...FINANCE_PROCUREMENT_ASSET_SAFETY_FLAGS,
      tenant_id: 1,
      module: 'finance-procurement-asset',
      product_vertical: 'Finance / Procurement / Asset Suite',
      contract_version: 'A-040.3',
      runtime_mode: FINANCE_PROCUREMENT_ASSET_RUNTIME_MODE,
      table_count: 24,
      route_count: 56,
      permission_count: 50,
      planned_route_count: 23,
      data_source: FINANCE_PROCUREMENT_ASSET_DATA_SOURCE,
      boundary_summary: { fake_metrics: false },
    };

    const dashboard: FpaDashboardSummary = {
      ...FINANCE_PROCUREMENT_ASSET_SAFETY_FLAGS,
      tenant_id: 1,
      generated_at: '2026-05-26T00:00:00Z',
      contract_version: 'A-040.3',
      source_backend_baseline_commit: '0453fbd',
      source_backend_runtime_commit: '0394414',
      data_source: FINANCE_PROCUREMENT_ASSET_DATA_SOURCE,
      billing_summary: { visible: 3 },
      receivables_summary: { aging: 2 },
      budget_summary: { pending: 4 },
      procurement_summary: { requests: 5 },
      vendor_summary: { tracked: 6 },
      asset_summary: { visible: 7 },
      readiness_summary: { deferred: 4 },
      bridge_summary: { executive: 1 },
      audit_summary: { recorded: 2 },
      boundary_summary: { fake_metrics: false },
    };

    expect(overview.permission_count).toBe(50);
    expect(dashboard.data_source).toBe(FINANCE_PROCUREMENT_ASSET_DATA_SOURCE);
  });

  it('models payment readiness entities without hidden execution affordances', () => {
    const paymentReadiness: FpaPaymentReadiness = {
      ...FINANCE_PROCUREMENT_ASSET_SAFETY_FLAGS,
      id: 1,
      tenant_id: 1,
      status: 'DEFERRED',
      title: 'Payment readiness profile',
      description: null,
      metadata: {},
      read_only_first: true,
      mutation_allowed: false,
    };

    expect(paymentReadiness.payment_execution_enabled).toBe(false);
    expect(paymentReadiness.mutation_allowed).toBe(false);
  });

  it('keeps top-level false safety constants explicit', () => {
    expect(fakeMetrics).toBe(false);
    expect(fakeFinanceData).toBe(false);
    expect(fakePaymentData).toBe(false);
  });
});
