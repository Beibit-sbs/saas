import { expect, test, type Browser, type Page, type Route } from '@playwright/test';

const API_BASE = '/api/admin/finance-procurement-asset';
const BFF_BASE = '/api/bff/admin/finance-procurement-asset';
const BASE_URL = process.env.E2E_BASE_URL ?? 'https://nginx';

const FULL_PERMISSIONS = [
  'platform.admin.read',
  'finance_procurement_asset.overview.read',
  'finance_procurement_asset.readiness.read',
  'finance_procurement_asset.limitations.read',
  'finance_procurement_asset.dashboard.read',
  'finance_procurement_asset.billing.read',
  'finance_procurement_asset.billing.evidence',
  'finance_procurement_asset.receivables.read',
  'finance_procurement_asset.budget_plans.read',
  'finance_procurement_asset.budget_plans.manage',
  'finance_procurement_asset.budget_controls.read',
  'finance_procurement_asset.budget_controls.review',
  'finance_procurement_asset.procurement_requests.read',
  'finance_procurement_asset.procurement_requests.manage',
  'finance_procurement_asset.procurement_reviews.read',
  'finance_procurement_asset.procurement_reviews.review',
  'finance_procurement_asset.vendors.read',
  'finance_procurement_asset.vendors.manage',
  'finance_procurement_asset.contracts.read',
  'finance_procurement_asset.contracts.evidence',
  'finance_procurement_asset.purchase_requests.read',
  'finance_procurement_asset.purchase_requests.manage',
  'finance_procurement_asset.purchase_orders.read',
  'finance_procurement_asset.purchase_orders.metadata',
  'finance_procurement_asset.assets.read',
  'finance_procurement_asset.assets.metadata',
  'finance_procurement_asset.asset_lifecycle.read',
  'finance_procurement_asset.asset_lifecycle.manage',
  'finance_procurement_asset.inventory_movements.read',
  'finance_procurement_asset.inventory_movements.metadata',
  'finance_procurement_asset.payment_readiness.read',
  'finance_procurement_asset.payment_readiness.evidence',
  'finance_procurement_asset.erp_readiness.read',
  'finance_procurement_asset.erp_readiness.evidence',
  'finance_procurement_asset.bank_readiness.read',
  'finance_procurement_asset.bank_readiness.evidence',
  'finance_procurement_asset.payment_gateway_readiness.read',
  'finance_procurement_asset.payment_gateway_readiness.evidence',
  'finance_procurement_asset.provider_readiness.read',
  'finance_procurement_asset.provider_readiness.evidence',
  'finance_procurement_asset.audit.read',
  'finance_procurement_asset.audit.write',
  'finance_procurement_asset.evidence.read',
  'finance_procurement_asset.evidence.write',
  'finance_procurement_asset.bridges.executive.read',
  'finance_procurement_asset.bridges.hr_payroll.read',
  'finance_procurement_asset.bridges.document_contracts.read',
  'finance_procurement_asset.bridges.provider_readiness.read',
  'finance_procurement_asset.metadata.read',
] as const;

const REQUIRED_BOUNDARY_LABELS = [
  'Metadata/evidence-only finance foundation',
  'Human review required',
  'No live bank integration',
  'No live ERP/1C sync',
  'No payment execution',
  'No automatic procurement approval',
  'No automatic budget approval',
  'No automatic vendor award',
  'No official tax/regulatory filing',
  'No hidden finance/vendor score',
  'Incomplete data supported',
  'Provider readiness only',
  'Payment readiness only',
  'Bridge-first / read-only-first',
  'No production-ready claim',
  'No sales-ready claim',
  'No GCC-ready claim',
  'fakeMetrics=false',
  'fakeFinanceData=false',
  'fakePaymentData=false',
  'providerConnected=false',
  'liveBankSync=false',
  'liveErpSync=false',
  'paymentExecutionEnabled=false',
  'automaticProcurementApprovalEnabled=false',
  'automaticBudgetApprovalEnabled=false',
  'automaticVendorAwardEnabled=false',
  'hiddenScorePresent=false',
] as const;

const FORBIDDEN_DOM_LABELS = [
  'Execute payment',
  'Send payment',
  'Sync bank live',
  'Sync 1C live',
  'Connect bank live',
  'Connect ERP live',
  'Auto approve procurement',
  'Auto approve budget',
  'Auto award vendor',
  'Close financial period automatically',
  'File tax return',
  'Submit regulatory filing',
  'Publish vendor score',
  'Hidden finance score',
  'Hidden vendor score',
  'Production ready',
  'Sales ready',
  'GCC ready',
  'L5/L6 ready',
  'Payment sent',
  'Bank synced',
  '1C synced',
  'Provider connected live',
  'Real invoice',
  'Real payment data',
  'Real vendor score',
  'Real budget approval',
] as const;

const FORBIDDEN_EXACT_TEXTS = [
  /^Production ready$/i,
  /^Sales ready$/i,
  /^GCC ready$/i,
  /^L5\/L6 ready$/i,
  /^Payment sent$/i,
  /^Bank synced$/i,
  /^1C synced$/i,
  /^Provider connected live$/i,
  /^Real invoice$/i,
  /^Real payment data$/i,
  /^Real vendor score$/i,
  /^Real budget approval$/i,
] as const;

const BASE_FLAGS = {
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
  limitations: [
    'Metadata/evidence/readiness/human-review-only finance runtime.',
    'No live bank integration, live ERP/1C sync, payment execution, automatic approvals, hidden scoring, tax filing, or regulatory submission surfaces are implemented.',
    'No real invoice numbers, bank accounts, payment references, vendor identities, budget figures, provider credentials, or regulatory filing references are stored in the browser fixtures.',
  ],
  created_at: '2026-05-26T00:00:00Z',
  updated_at: '2026-05-26T00:00:00Z',
} as const;

type FpaRouteKey =
  | 'overview'
  | 'dashboard'
  | 'billing'
  | 'receivables'
  | 'budget-planning'
  | 'budget-control'
  | 'procurement-requests'
  | 'procurement-reviews'
  | 'vendors'
  | 'contracts'
  | 'purchase-requests'
  | 'purchase-orders'
  | 'assets'
  | 'asset-lifecycle'
  | 'inventory-movements'
  | 'payment-readiness'
  | 'erp-readiness'
  | 'bank-readiness'
  | 'provider-readiness'
  | 'bridges'
  | 'audit'
  | 'limitations';

interface FpaRouteSpec {
  path: string;
  routeKey: FpaRouteKey;
  title: string;
  requiredPermission: string;
  expectedBoundaryLabels: readonly string[];
  endpoints: readonly string[];
  dashboardLike: boolean;
  sensitive: boolean;
  humanReviewRequired: boolean;
}

function escapeRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function pageUrl(path: string) {
  return new URL(path, BASE_URL).toString();
}

function makeRecord(id: number, recordKey: string, title: string, description: string, extra: Record<string, unknown> = {}) {
  return {
    id,
    tenant_id: 1,
    record_key: recordKey,
    title,
    description,
    status: 'ACTIVE',
    review_mode: 'HUMAN_REVIEW_ONLY',
    metadata_only: true,
    mutation_allowed: false,
    no_real_invoice_numbers: true,
    no_real_bank_accounts: true,
    no_real_payment_references: true,
    no_real_vendor_identities: true,
    no_real_budget_figures: true,
    no_provider_credentials: true,
    no_tax_filing_references: true,
    no_regulatory_submission_references: true,
    read_only_first: true,
    ...BASE_FLAGS,
    ...extra,
  };
}

const overviewFixture = {
  tenant_id: 1,
  module: 'finance_procurement_asset',
  product_vertical: 'Finance / Procurement / Asset Suite',
  contract_version: 'A-040.4-E2E',
  runtime_mode: 'METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY',
  table_count: 53,
  route_count: 22,
  permission_count: 48,
  planned_route_count: 22,
  data_source: 'computed_from_finance_procurement_asset_metadata',
  boundary_summary: {
    no_live_bank_integration: true,
    no_live_erp_sync: true,
    no_payment_execution: true,
    no_automatic_procurement_approval: true,
    no_automatic_budget_approval: true,
    no_automatic_vendor_award: true,
    no_hidden_finance_vendor_score: true,
  },
  ...BASE_FLAGS,
};

const readinessFixture = {
  contract_version: 'A-040.4-E2E',
  runtime_mode: 'METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY',
  backend_route_count: 53,
  backend_permission_count: 48,
  provider_profiles: [
    { key: 'BANK_CORE', title: 'Bank Core Integration', provider_connected: false, live_bank_sync: false, live_erp_sync: false },
    { key: 'ERP_1C', title: 'ERP / 1C', provider_connected: false, live_bank_sync: false, live_erp_sync: false },
    { key: 'PAYMENT_GATEWAY', title: 'Payment Gateway', provider_connected: false, live_bank_sync: false, live_erp_sync: false },
    { key: 'HR_PAYROLL_BRIDGE', title: 'HR / Payroll Bridge', provider_connected: false, live_bank_sync: false, live_erp_sync: false },
    { key: 'DOCUMENT_CONTRACTS', title: 'Document / Contracts Bridge', provider_connected: false, live_bank_sync: false, live_erp_sync: false },
  ],
  bridge_targets: ['EXECUTIVE', 'HR_PAYROLL', 'DOCUMENT_CONTRACTS', 'PROVIDER_READINESS'],
  ...BASE_FLAGS,
};

const limitationsFixture = {
  items: [
    'No fake finance data or fake payment data is generated in this runtime.',
    'No live bank integration, live ERP/1C sync, payment execution, automatic approvals, or hidden finance/vendor score is implemented.',
    'No official tax return or regulatory filing workflow is implemented.',
    'No production-ready, sales-ready, GCC-ready, or L5/L6 claim is implemented.',
  ],
};

const dashboardFixture = {
  tenant_id: 1,
  generated_at: '2026-05-26T00:00:00Z',
  contract_version: 'A-040.4-E2E',
  source_backend_baseline_commit: '0453fbd',
  source_backend_runtime_commit: '0394414',
  data_source: 'computed_from_finance_procurement_asset_metadata',
  billing_summary: { items: 1, pending: 1 },
  receivables_summary: { items: 1, incomplete: 1 },
  budget_summary: { plans: 1, controls: 1 },
  procurement_summary: { requests: 1, reviews: 1 },
  vendor_summary: { vendors: 1, contracts: 1 },
  asset_summary: { assets: 1, lifecycle: 1, movements: 1 },
  readiness_summary: { payment: 1, erp: 1, bank: 1, provider: 1 },
  bridge_summary: { executive: 1, hr_payroll: 1, document_contracts: 1, provider_readiness: 1 },
  audit_summary: { events: 1, evidence: 1 },
  boundary_summary: overviewFixture.boundary_summary,
  ...BASE_FLAGS,
};

const billingFixture = {
  items: [
    makeRecord(1, 'BILLING-META-001', 'Billing visibility metadata', 'Billing metadata and evidence posture only.', {
      billing_ref: 'BILLING-META-001',
      payment_execution_enabled: false,
      evidence_count: 2,
    }),
  ],
};

const receivablesFixture = {
  items: [
    makeRecord(2, 'RECV-META-001', 'Receivables metadata', 'Receivables aging visibility with incomplete data support.', {
      receivables_ref: 'RECV-META-001',
      incomplete_data: true,
    }),
  ],
};

const budgetPlansFixture = {
  items: [
    makeRecord(3, 'BUDGET-PLAN-001', 'Budget planning metadata', 'Budget planning metadata under human review only.', {
      budget_plan_ref: 'BUDGET-PLAN-001',
      fiscal_year: 2026,
      automatic_budget_approval_enabled: false,
    }),
  ],
};

const budgetControlsFixture = {
  items: [
    makeRecord(4, 'BUDGET-CTRL-001', 'Budget control review metadata', 'Budget control review queue without automatic approval.', {
      budget_control_ref: 'BUDGET-CTRL-001',
      approval_mode: 'HUMAN_REVIEW_ONLY',
    }),
  ],
};

const procurementRequestsFixture = {
  items: [
    makeRecord(5, 'PROC-REQ-001', 'Procurement request metadata', 'Procurement request intake metadata only.', {
      procurement_request_ref: 'PROC-REQ-001',
      review_status: 'PENDING_HUMAN_REVIEW',
    }),
  ],
};

const procurementReviewsFixture = {
  items: [
    makeRecord(6, 'PROC-REV-001', 'Procurement committee review metadata', 'Committee review metadata without automatic vendor award.', {
      procurement_review_ref: 'PROC-REV-001',
      automatic_procurement_approval_enabled: false,
      automatic_vendor_award_enabled: false,
    }),
  ],
};

const vendorsFixture = {
  items: [
    makeRecord(7, 'VENDOR-META-001', 'Vendor metadata visibility', 'Vendor readiness metadata without hidden scoring.', {
      vendor_ref: 'VENDOR-META-001',
      hidden_score_present: false,
    }),
  ],
};

const contractsFixture = {
  items: [
    makeRecord(8, 'CONTRACT-META-001', 'Contract evidence metadata', 'Contract evidence metadata only without regulatory filing.', {
      contract_ref: 'CONTRACT-META-001',
      regulatory_submission_enabled: false,
    }),
  ],
};

const purchaseRequestsFixture = {
  items: [
    makeRecord(9, 'PUR-REQ-001', 'Purchase request metadata', 'Purchase request intake under human review.', {
      purchase_request_ref: 'PUR-REQ-001',
      automatic_procurement_approval_enabled: false,
    }),
  ],
};

const purchaseOrdersFixture = {
  items: [
    makeRecord(10, 'PUR-ORDER-001', 'Purchase order metadata', 'Purchase order metadata only without automatic vendor award.', {
      purchase_order_ref: 'PUR-ORDER-001',
      automatic_vendor_award_enabled: false,
    }),
  ],
};

const assetsFixture = {
  items: [
    makeRecord(11, 'ASSET-META-001', 'Asset visibility metadata', 'Asset inventory visibility metadata with incomplete data support.', {
      asset_ref: 'ASSET-META-001',
      incomplete_data: true,
    }),
  ],
};

const assetLifecycleFixture = {
  items: [
    makeRecord(12, 'ASSET-LIFE-001', 'Asset lifecycle metadata', 'Asset lifecycle review metadata only.', {
      asset_lifecycle_ref: 'ASSET-LIFE-001',
      bridge_target: 'DOCUMENT_CONTRACTS',
    }),
  ],
};

const inventoryMovementsFixture = {
  items: [
    makeRecord(13, 'INV-MOVE-001', 'Inventory movement metadata', 'Inventory movement visibility with bridge-first posture.', {
      inventory_movement_ref: 'INV-MOVE-001',
      bridge_target: 'EXECUTIVE',
    }),
  ],
};

const paymentReadinessFixture = {
  items: [
    makeRecord(14, 'PAY-READY-001', 'Payment readiness metadata', 'Payment readiness evidence without execution.', {
      payment_readiness_ref: 'PAY-READY-001',
      payment_execution_enabled: false,
    }),
  ],
};

const erpReadinessFixture = {
  items: [
    makeRecord(15, 'ERP-READY-001', 'ERP / 1C readiness metadata', 'ERP/1C readiness evidence only without live synchronization.', {
      erp_readiness_ref: 'ERP-READY-001',
      live_erp_sync: false,
    }),
  ],
};

const bankReadinessFixture = {
  items: [
    makeRecord(16, 'BANK-READY-001', 'Bank readiness metadata', 'Bank readiness evidence only without live connectivity.', {
      bank_readiness_ref: 'BANK-READY-001',
      live_bank_sync: false,
    }),
  ],
};

const paymentGatewayReadinessFixture = {
  items: [
    makeRecord(17, 'GATEWAY-READY-001', 'Payment gateway readiness metadata', 'Gateway readiness evidence only without provider connection.', {
      payment_gateway_readiness_ref: 'GATEWAY-READY-001',
      provider_connected: false,
    }),
  ],
};

const providerReadinessFixture = {
  items: [
    makeRecord(18, 'PROVIDER-READY-001', 'Provider readiness metadata', 'Provider readiness evidence only with providerConnected=false.', {
      provider_readiness_ref: 'PROVIDER-READY-001',
      provider_key: 'PAYMENT_GATEWAY',
      provider_connected: false,
    }),
  ],
};

const auditEventsFixture = {
  items: [
    makeRecord(19, 'AUDIT-001', 'Audit event metadata', 'Audit event metadata only.', {
      event_type: 'EVIDENCE_REVIEWED',
      actor_ref: 'finance-admin-demo',
    }),
  ],
};

const evidenceFixture = {
  items: [
    makeRecord(20, 'EVIDENCE-001', 'Evidence metadata', 'Evidence payload metadata only.', {
      evidence_ref: 'EVIDENCE-001',
      entity_type: 'finance_procurement_asset',
    }),
  ],
};

const bridgesExecutiveFixture = {
  bridge_name: 'executive',
  bridge_title: 'Executive Bridge',
  connected_module: 'executive_ops',
  read_only: true,
  summary: { posture: 'READ_ONLY_FIRST', readiness: 'DEFERRED', records: 1 },
  ...BASE_FLAGS,
};

const bridgesHrPayrollFixture = {
  bridge_name: 'hr_payroll',
  bridge_title: 'HR Payroll Bridge',
  connected_module: 'hr_payroll',
  read_only: true,
  summary: { posture: 'READ_ONLY_FIRST', readiness: 'DEFERRED', records: 1 },
  ...BASE_FLAGS,
};

const bridgesDocumentContractsFixture = {
  bridge_name: 'document_contracts',
  bridge_title: 'Document Contracts Bridge',
  connected_module: 'document_contracts',
  read_only: true,
  summary: { posture: 'READ_ONLY_FIRST', readiness: 'DEFERRED', records: 1 },
  ...BASE_FLAGS,
};

const bridgesProviderReadinessFixture = {
  bridge_name: 'provider_readiness',
  bridge_title: 'Provider Readiness Bridge',
  connected_module: 'provider_readiness',
  read_only: true,
  summary: { posture: 'READ_ONLY_FIRST', readiness: 'DEFERRED', records: 1 },
  ...BASE_FLAGS,
};

const healthFixture = {
  tenant_id: 1,
  module: 'finance_procurement_asset',
  route_count: 22,
  scenario_group_count: 28,
  data_source: 'computed_from_finance_procurement_asset_metadata',
  ...BASE_FLAGS,
};

const rolesFixture = {
  items: [
    {
      key: 'finance_admin',
      title: 'Finance Admin',
      description: 'Metadata/evidence-only finance browser validation admin.',
      permissions: FULL_PERMISSIONS,
    },
  ],
};

const permissionsFixture = {
  items: [...FULL_PERMISSIONS],
};

const metadataContractFixture = {
  module: 'finance_procurement_asset',
  route_count: 22,
  permission_count: 48,
  runtime_mode: 'METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY',
  forbidden_actions: [...FORBIDDEN_DOM_LABELS],
  boundary_labels: [...REQUIRED_BOUNDARY_LABELS],
  ...BASE_FLAGS,
};

const FPA_FIXTURES = {
  overview: overviewFixture,
  readiness: readinessFixture,
  limitations: limitationsFixture,
  safetyBoundaries: { labels: REQUIRED_BOUNDARY_LABELS, flags: BASE_FLAGS },
  dashboard: dashboardFixture,
  billing: billingFixture,
  receivables: receivablesFixture,
  budgetPlans: budgetPlansFixture,
  budgetControls: budgetControlsFixture,
  procurementRequests: procurementRequestsFixture,
  procurementReviews: procurementReviewsFixture,
  vendors: vendorsFixture,
  contracts: contractsFixture,
  purchaseRequests: purchaseRequestsFixture,
  purchaseOrders: purchaseOrdersFixture,
  assets: assetsFixture,
  assetLifecycle: assetLifecycleFixture,
  inventoryMovements: inventoryMovementsFixture,
  paymentReadiness: paymentReadinessFixture,
  erpReadiness: erpReadinessFixture,
  bankReadiness: bankReadinessFixture,
  paymentGatewayReadiness: paymentGatewayReadinessFixture,
  providerReadiness: providerReadinessFixture,
  auditEvents: auditEventsFixture,
  evidence: evidenceFixture,
  bridgesExecutive: bridgesExecutiveFixture,
  bridgesHrPayroll: bridgesHrPayrollFixture,
  bridgesDocumentContracts: bridgesDocumentContractsFixture,
  bridgesProviderReadiness: bridgesProviderReadinessFixture,
  health: healthFixture,
  roles: rolesFixture,
  permissions: permissionsFixture,
  metadataContract: metadataContractFixture,
} as const;

const fullAccessFinanceAdminFixture = {
  sub: 'finance-procurement-asset-admin',
  displayName: 'Finance Procurement Asset E2E Admin',
  roles: ['admin'],
  permissions: FULL_PERMISSIONS,
  tenantId: 1,
} as const;

const restrictedUserFixture = {
  sub: 'finance-procurement-asset-restricted',
  displayName: 'Finance Procurement Asset Restricted User',
  roles: ['admin'],
  permissions: ['platform.admin.read'],
  tenantId: 1,
} as const;

const FPA_ROUTES = [
  {
    path: '/console/finance-procurement-asset',
    routeKey: 'overview',
    title: 'Finance / Procurement / Asset Suite',
    requiredPermission: 'finance_procurement_asset.overview.read',
    expectedBoundaryLabels: ['Metadata/evidence-only finance foundation', 'Human review required', 'fakeMetrics=false', 'fakeFinanceData=false', 'fakePaymentData=false'],
    endpoints: ['GET /api/admin/finance-procurement-asset/overview', 'GET /api/admin/finance-procurement-asset/readiness', 'GET /api/admin/finance-procurement-asset/limitations'],
    dashboardLike: true,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/dashboard',
    routeKey: 'dashboard',
    title: 'Finance Operations Dashboard',
    requiredPermission: 'finance_procurement_asset.dashboard.read',
    expectedBoundaryLabels: ['Metadata/evidence-only finance foundation', 'fakeMetrics=false', 'Incomplete data supported'],
    endpoints: ['GET /api/admin/finance-procurement-asset/dashboard'],
    dashboardLike: true,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/billing',
    routeKey: 'billing',
    title: 'Billing Visibility',
    requiredPermission: 'finance_procurement_asset.billing.read',
    expectedBoundaryLabels: ['Metadata/evidence-only finance foundation', 'Human review required'],
    endpoints: ['GET /api/admin/finance-procurement-asset/billing', 'POST /api/admin/finance-procurement-asset/billing/evidence'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/receivables',
    routeKey: 'receivables',
    title: 'Receivables Metadata',
    requiredPermission: 'finance_procurement_asset.receivables.read',
    expectedBoundaryLabels: ['Metadata/evidence-only finance foundation', 'Incomplete data supported'],
    endpoints: ['GET /api/admin/finance-procurement-asset/receivables'],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: false,
  },
  {
    path: '/console/finance-procurement-asset/budget-planning',
    routeKey: 'budget-planning',
    title: 'Budget Planning',
    requiredPermission: 'finance_procurement_asset.budget_plans.read',
    expectedBoundaryLabels: ['Human review required', 'No automatic budget approval'],
    endpoints: ['GET /api/admin/finance-procurement-asset/budget-plans', 'POST /api/admin/finance-procurement-asset/budget-plans'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/budget-control',
    routeKey: 'budget-control',
    title: 'Budget Control Review',
    requiredPermission: 'finance_procurement_asset.budget_controls.read',
    expectedBoundaryLabels: ['Human review required', 'No automatic budget approval'],
    endpoints: ['GET /api/admin/finance-procurement-asset/budget-controls', 'POST /api/admin/finance-procurement-asset/budget-controls/review'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/procurement-requests',
    routeKey: 'procurement-requests',
    title: 'Procurement Requests',
    requiredPermission: 'finance_procurement_asset.procurement_requests.read',
    expectedBoundaryLabels: ['Human review required', 'No automatic procurement approval'],
    endpoints: ['GET /api/admin/finance-procurement-asset/procurement-requests', 'POST /api/admin/finance-procurement-asset/procurement-requests'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/procurement-reviews',
    routeKey: 'procurement-reviews',
    title: 'Procurement Committee Reviews',
    requiredPermission: 'finance_procurement_asset.procurement_reviews.read',
    expectedBoundaryLabels: ['Human review required', 'No automatic procurement approval', 'No automatic vendor award'],
    endpoints: ['GET /api/admin/finance-procurement-asset/procurement-reviews', 'POST /api/admin/finance-procurement-asset/procurement-reviews'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/vendors',
    routeKey: 'vendors',
    title: 'Vendor Metadata',
    requiredPermission: 'finance_procurement_asset.vendors.read',
    expectedBoundaryLabels: ['Metadata/evidence-only finance foundation', 'No hidden finance/vendor score'],
    endpoints: ['GET /api/admin/finance-procurement-asset/vendors', 'POST /api/admin/finance-procurement-asset/vendors'],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: false,
  },
  {
    path: '/console/finance-procurement-asset/contracts',
    routeKey: 'contracts',
    title: 'Contract Evidence',
    requiredPermission: 'finance_procurement_asset.contracts.read',
    expectedBoundaryLabels: ['Metadata/evidence-only finance foundation', 'No official tax/regulatory filing'],
    endpoints: ['GET /api/admin/finance-procurement-asset/contracts', 'POST /api/admin/finance-procurement-asset/contracts/evidence'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/purchase-requests',
    routeKey: 'purchase-requests',
    title: 'Purchase Requests',
    requiredPermission: 'finance_procurement_asset.purchase_requests.read',
    expectedBoundaryLabels: ['Human review required', 'No automatic procurement approval'],
    endpoints: ['GET /api/admin/finance-procurement-asset/purchase-requests', 'POST /api/admin/finance-procurement-asset/purchase-requests'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/purchase-orders',
    routeKey: 'purchase-orders',
    title: 'Purchase Orders',
    requiredPermission: 'finance_procurement_asset.purchase_orders.read',
    expectedBoundaryLabels: ['Metadata/evidence-only finance foundation', 'No automatic vendor award'],
    endpoints: ['GET /api/admin/finance-procurement-asset/purchase-orders', 'POST /api/admin/finance-procurement-asset/purchase-orders/metadata'],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: false,
  },
  {
    path: '/console/finance-procurement-asset/assets',
    routeKey: 'assets',
    title: 'Asset Visibility',
    requiredPermission: 'finance_procurement_asset.assets.read',
    expectedBoundaryLabels: ['Metadata/evidence-only finance foundation', 'Incomplete data supported'],
    endpoints: ['GET /api/admin/finance-procurement-asset/assets', 'POST /api/admin/finance-procurement-asset/assets/metadata'],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: false,
  },
  {
    path: '/console/finance-procurement-asset/asset-lifecycle',
    routeKey: 'asset-lifecycle',
    title: 'Asset Lifecycle',
    requiredPermission: 'finance_procurement_asset.asset_lifecycle.read',
    expectedBoundaryLabels: ['Human review required', 'Bridge-first / read-only-first'],
    endpoints: ['GET /api/admin/finance-procurement-asset/asset-lifecycle', 'POST /api/admin/finance-procurement-asset/asset-lifecycle'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/inventory-movements',
    routeKey: 'inventory-movements',
    title: 'Inventory Movements',
    requiredPermission: 'finance_procurement_asset.inventory_movements.read',
    expectedBoundaryLabels: ['Metadata/evidence-only finance foundation', 'Bridge-first / read-only-first'],
    endpoints: ['GET /api/admin/finance-procurement-asset/inventory-movements', 'POST /api/admin/finance-procurement-asset/inventory-movements/metadata'],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: false,
  },
  {
    path: '/console/finance-procurement-asset/payment-readiness',
    routeKey: 'payment-readiness',
    title: 'Payment Readiness',
    requiredPermission: 'finance_procurement_asset.payment_readiness.read',
    expectedBoundaryLabels: ['Payment readiness only', 'No payment execution'],
    endpoints: ['GET /api/admin/finance-procurement-asset/payment-readiness', 'POST /api/admin/finance-procurement-asset/payment-readiness/evidence'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/erp-readiness',
    routeKey: 'erp-readiness',
    title: 'ERP / 1C Readiness',
    requiredPermission: 'finance_procurement_asset.erp_readiness.read',
    expectedBoundaryLabels: ['Provider readiness only', 'No live ERP/1C sync'],
    endpoints: ['GET /api/admin/finance-procurement-asset/erp-readiness', 'POST /api/admin/finance-procurement-asset/erp-readiness/evidence'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/bank-readiness',
    routeKey: 'bank-readiness',
    title: 'Bank Readiness',
    requiredPermission: 'finance_procurement_asset.bank_readiness.read',
    expectedBoundaryLabels: ['Provider readiness only', 'No live bank integration'],
    endpoints: ['GET /api/admin/finance-procurement-asset/bank-readiness', 'POST /api/admin/finance-procurement-asset/bank-readiness/evidence'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/provider-readiness',
    routeKey: 'provider-readiness',
    title: 'Provider Readiness',
    requiredPermission: 'finance_procurement_asset.provider_readiness.read',
    expectedBoundaryLabels: ['Provider readiness only', 'Bridge-first / read-only-first'],
    endpoints: ['GET /api/admin/finance-procurement-asset/provider-readiness', 'GET /api/admin/finance-procurement-asset/payment-gateway-readiness', 'POST /api/admin/finance-procurement-asset/provider-readiness/evidence', 'POST /api/admin/finance-procurement-asset/payment-gateway-readiness/evidence'],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: false,
  },
  {
    path: '/console/finance-procurement-asset/bridges',
    routeKey: 'bridges',
    title: 'Bridge Visibility',
    requiredPermission: 'finance_procurement_asset.bridges.executive.read',
    expectedBoundaryLabels: ['Bridge-first / read-only-first', 'No payment execution'],
    endpoints: ['GET /api/admin/finance-procurement-asset/bridges/executive', 'GET /api/admin/finance-procurement-asset/bridges/hr-payroll', 'GET /api/admin/finance-procurement-asset/bridges/document-contracts', 'GET /api/admin/finance-procurement-asset/bridges/provider-readiness'],
    dashboardLike: false,
    sensitive: false,
    humanReviewRequired: false,
  },
  {
    path: '/console/finance-procurement-asset/audit',
    routeKey: 'audit',
    title: 'Audit / Evidence',
    requiredPermission: 'finance_procurement_asset.audit.read',
    expectedBoundaryLabels: ['Human review required', 'Metadata/evidence-only finance foundation'],
    endpoints: ['GET /api/admin/finance-procurement-asset/audit-events', 'GET /api/admin/finance-procurement-asset/evidence', 'POST /api/admin/finance-procurement-asset/audit-events', 'POST /api/admin/finance-procurement-asset/evidence'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
  {
    path: '/console/finance-procurement-asset/limitations',
    routeKey: 'limitations',
    title: 'Limitations / Safety Boundaries',
    requiredPermission: 'finance_procurement_asset.limitations.read',
    expectedBoundaryLabels: [...REQUIRED_BOUNDARY_LABELS],
    endpoints: ['GET /api/admin/finance-procurement-asset/limitations', 'GET /api/admin/finance-procurement-asset/safety-boundaries', 'GET /api/admin/finance-procurement-asset/metadata-contract'],
    dashboardLike: false,
    sensitive: true,
    humanReviewRequired: true,
  },
] as const satisfies readonly FpaRouteSpec[];

const ROUTE_TITLE_GROUPS = [
  { label: 'A', routes: FPA_ROUTES.slice(0, 6) },
  { label: 'B', routes: FPA_ROUTES.slice(6, 12) },
  { label: 'C', routes: FPA_ROUTES.slice(12, 18) },
  { label: 'D', routes: FPA_ROUTES.slice(18, 22) },
] as const;

if (FPA_ROUTES.length !== 22) {
  throw new Error(`Finance procurement asset browser route flow must stay at 22, received ${FPA_ROUTES.length}`);
}

async function forceEnglishLocale(page: Page) {
  const url = pageUrl('/');
  const parsedUrl = new URL(url);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);

  await page.context().addCookies(
    Array.from(cookieOrigins).map((origin) => ({
      name: 'app.locale',
      value: 'en',
      url: origin,
      httpOnly: false,
      secure: new URL(origin).protocol === 'https:',
      sameSite: 'Lax' as const,
    })),
  );

  await page.addInitScript(() => {
    document.cookie = 'app.locale=en; Path=/; SameSite=Lax';
    window.localStorage.setItem('app.language', 'en');
  });
}

async function stubSharedBootstrap(page: Page) {
  await page.route('**/api/auth/csrf*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrfToken: 'finance-procurement-asset-csrf-token' }),
    });
  });

  await page.route('**/api/auth/me/preferences/language*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ ok: true, language: 'en' }),
    });
  });

  await page.route('**/api/public/tenants/login-directory*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          {
            tenantId: 1,
            tenantCode: 'finance-procurement-asset-demo',
            tenantName: 'Finance Procurement Asset Demo Tenant',
            authMethods: ['password'],
          },
        ],
      }),
    });
  });

  await page.route('**/api/i18n/languages*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        languages: [
          { code: 'en', label: 'English', default: true },
          { code: 'ru', label: 'Russian', default: false },
        ],
      }),
    });
  });
}

async function stubAuth(page: Page, userFixture: typeof fullAccessFinanceAdminFixture | typeof restrictedUserFixture) {
  const parsedUrl = new URL(BASE_URL);
  const cookieOrigins = new Set<string>([
    `${parsedUrl.protocol}//${parsedUrl.host}`,
    `http://${parsedUrl.host}`,
    `https://${parsedUrl.host}`,
  ]);
  const payloadJson = JSON.stringify({
    sub: userFixture.sub,
    display_name: userFixture.displayName,
    roles: userFixture.roles,
    permissions: userFixture.permissions,
    tenant_id: userFixture.tenantId,
    exp: Math.floor(Date.now() / 1000) + 3600,
  });
  const payload = Buffer.from(payloadJson).toString('base64url');
  const fakeToken = `fakeheader.${payload}.fakesig`;

  await page.context().addCookies(
    Array.from(cookieOrigins).flatMap((origin) => {
      const secure = new URL(origin).protocol === 'https:';
      return [
        { name: 'admin_token', value: fakeToken, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
        { name: 'app_access_token', value: fakeToken, url: origin, httpOnly: true, secure, sameSite: 'Lax' as const },
      ];
    }),
  );

  for (const pattern of ['**/api/auth/me*', '**/api/bff/auth/me*']) {
    await page.route(pattern, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          user: userFixture,
        }),
      });
    });
  }
}

function matchFpaFixture(path: string) {
  if (path === `${API_BASE}/health` || path === `${BFF_BASE}/health`) return FPA_FIXTURES.health;
  if (path === `${API_BASE}/overview` || path === `${BFF_BASE}/overview`) return FPA_FIXTURES.overview;
  if (path === `${API_BASE}/readiness` || path === `${BFF_BASE}/readiness`) return FPA_FIXTURES.readiness;
  if (path === `${API_BASE}/limitations` || path === `${BFF_BASE}/limitations`) return FPA_FIXTURES.limitations;
  if (path === `${API_BASE}/safety-boundaries` || path === `${BFF_BASE}/safety-boundaries`) return FPA_FIXTURES.safetyBoundaries;
  if (path === `${API_BASE}/dashboard` || path === `${BFF_BASE}/dashboard`) return FPA_FIXTURES.dashboard;
  if (path === `${API_BASE}/billing` || path === `${BFF_BASE}/billing`) return FPA_FIXTURES.billing;
  if (path === `${API_BASE}/receivables` || path === `${BFF_BASE}/receivables`) return FPA_FIXTURES.receivables;
  if (path === `${API_BASE}/budget-plans` || path === `${BFF_BASE}/budget-plans`) return FPA_FIXTURES.budgetPlans;
  if (path === `${API_BASE}/budget-controls` || path === `${BFF_BASE}/budget-controls`) return FPA_FIXTURES.budgetControls;
  if (path === `${API_BASE}/procurement-requests` || path === `${BFF_BASE}/procurement-requests`) return FPA_FIXTURES.procurementRequests;
  if (path === `${API_BASE}/procurement-reviews` || path === `${BFF_BASE}/procurement-reviews`) return FPA_FIXTURES.procurementReviews;
  if (path === `${API_BASE}/vendors` || path === `${BFF_BASE}/vendors`) return FPA_FIXTURES.vendors;
  if (path === `${API_BASE}/contracts` || path === `${BFF_BASE}/contracts`) return FPA_FIXTURES.contracts;
  if (path === `${API_BASE}/purchase-requests` || path === `${BFF_BASE}/purchase-requests`) return FPA_FIXTURES.purchaseRequests;
  if (path === `${API_BASE}/purchase-orders` || path === `${BFF_BASE}/purchase-orders`) return FPA_FIXTURES.purchaseOrders;
  if (path === `${API_BASE}/assets` || path === `${BFF_BASE}/assets`) return FPA_FIXTURES.assets;
  if (path === `${API_BASE}/asset-lifecycle` || path === `${BFF_BASE}/asset-lifecycle`) return FPA_FIXTURES.assetLifecycle;
  if (path === `${API_BASE}/inventory-movements` || path === `${BFF_BASE}/inventory-movements`) return FPA_FIXTURES.inventoryMovements;
  if (path === `${API_BASE}/payment-readiness` || path === `${BFF_BASE}/payment-readiness`) return FPA_FIXTURES.paymentReadiness;
  if (path === `${API_BASE}/erp-readiness` || path === `${BFF_BASE}/erp-readiness`) return FPA_FIXTURES.erpReadiness;
  if (path === `${API_BASE}/bank-readiness` || path === `${BFF_BASE}/bank-readiness`) return FPA_FIXTURES.bankReadiness;
  if (path === `${API_BASE}/payment-gateway-readiness` || path === `${BFF_BASE}/payment-gateway-readiness`) return FPA_FIXTURES.paymentGatewayReadiness;
  if (path === `${API_BASE}/provider-readiness` || path === `${BFF_BASE}/provider-readiness`) return FPA_FIXTURES.providerReadiness;
  if (path === `${API_BASE}/audit-events` || path === `${BFF_BASE}/audit-events`) return FPA_FIXTURES.auditEvents;
  if (path === `${API_BASE}/evidence` || path === `${BFF_BASE}/evidence`) return FPA_FIXTURES.evidence;
  if (path === `${API_BASE}/roles` || path === `${BFF_BASE}/roles`) return FPA_FIXTURES.roles;
  if (path === `${API_BASE}/permissions` || path === `${BFF_BASE}/permissions`) return FPA_FIXTURES.permissions;
  if (path === `${API_BASE}/metadata-contract` || path === `${BFF_BASE}/metadata-contract`) return FPA_FIXTURES.metadataContract;
  if (path.endsWith('/bridges/executive')) return FPA_FIXTURES.bridgesExecutive;
  if (path.endsWith('/bridges/hr-payroll')) return FPA_FIXTURES.bridgesHrPayroll;
  if (path.endsWith('/bridges/document-contracts')) return FPA_FIXTURES.bridgesDocumentContracts;
  if (path.endsWith('/bridges/provider-readiness')) return FPA_FIXTURES.bridgesProviderReadiness;
  return null;
}

async function stubFpaApi(page: Page) {
  const fulfillFpaRoute = async (route: Route) => {
    const request = route.request();
    const url = new URL(request.url());
    const payload = matchFpaFixture(url.pathname);

    const ok = async (body: unknown, status = 200) => {
      await route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(body),
      });
    };

    if (payload) {
      await ok(payload);
      return;
    }

    if (request.method() === 'POST' || request.method() === 'PATCH') {
      await ok({
        ok: true,
        accepted: true,
        mutation_applied: false,
        mode: 'metadata_evidence_only',
        ...BASE_FLAGS,
      });
      return;
    }

    await ok({ detail: `Unhandled Finance Procurement Asset stub path: ${url.pathname}` }, 404);
  };

  await page.route(`**${API_BASE}**`, fulfillFpaRoute);
  await page.route(`**${BFF_BASE}**`, fulfillFpaRoute);
}

async function setAuthenticatedFinanceAdmin(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, fullAccessFinanceAdminFixture);
  await stubFpaApi(page);
}

async function setRestrictedFinanceUser(page: Page) {
  await forceEnglishLocale(page);
  await stubSharedBootstrap(page);
  await stubAuth(page, restrictedUserFixture);
  await stubFpaApi(page);
}

async function gotoFpaRoute(page: Page, path: string) {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      await page.goto(pageUrl(path), { waitUntil: 'domcontentloaded' });
      return;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      const isTransientNavigationFailure = /ERR_ABORTED|frame was detached/i.test(message);
      if (!isTransientNavigationFailure || attempt === 2) {
        throw error;
      }
    }
  }
}

async function expectRequiredBoundaryLabels(page: Page) {
  for (const label of REQUIRED_BOUNDARY_LABELS) {
    await expect(page.locator('body')).toContainText(label);
  }
}

async function expectForbiddenDomAbsent(page: Page) {
  for (const label of FORBIDDEN_DOM_LABELS) {
    const exactLabelPattern = new RegExp(`^${escapeRegExp(label)}$`, 'i');
    await expect(page.getByRole('button', { name: exactLabelPattern })).toHaveCount(0);
    await expect(page.getByRole('link', { name: exactLabelPattern })).toHaveCount(0);
    await expect(page.getByText(exactLabelPattern)).toHaveCount(0);
  }

  for (const pattern of FORBIDDEN_EXACT_TEXTS) {
    await expect(page.getByText(pattern)).toHaveCount(0);
  }

  await expect(page.locator('body')).not.toContainText(/provider connected live/i);
  await expect(page.locator('body')).not.toContainText(/real invoice/i);
  await expect(page.locator('body')).not.toContainText(/real payment data/i);
  await expect(page.locator('body')).not.toContainText(/real vendor score/i);
  await expect(page.locator('body')).not.toContainText(/real budget approval/i);
}

async function expectCommonRuntimeSafety(page: Page) {
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('fakeMetrics=false');
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('fakeFinanceData=false');
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('fakePaymentData=false');
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('providerConnected=false');
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('liveBankSync=false');
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('liveErpSync=false');
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('paymentExecutionEnabled=false');
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('automaticProcurementApprovalEnabled=false');
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('automaticBudgetApprovalEnabled=false');
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('automaticVendorAwardEnabled=false');
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('hiddenScorePresent=false');
  await expect(page.getByTestId('fpa-safety-checklist')).toContainText('humanReviewRequired=true');
  await expect(page.getByTestId('fpa-incomplete-data-notice')).toContainText('incompleteData=true');
  await expect(page.locator('body')).toContainText('No live bank integration UI.');
  await expect(page.locator('body')).toContainText('No live ERP/1C sync UI.');
  await expect(page.locator('body')).toContainText('No payment execution UI.');
  await expect(page.locator('body')).toContainText('No automatic procurement approval UI.');
  await expect(page.locator('body')).toContainText('No automatic budget approval UI.');
  await expect(page.locator('body')).toContainText('No automatic vendor award UI.');
  await expect(page.locator('body')).toContainText('No hidden finance/vendor score UI.');
  await expect(page.locator('body')).toContainText('No production/sales/GCC/L5/L6 claim.');
}

async function expectRouteShell(page: Page, route: (typeof FPA_ROUTES)[number]) {
  const shell = page.getByTestId('fpa-page-shell');
  await expect(shell).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('heading', { name: route.title, level: 1 })).toBeVisible({ timeout: 15_000 });
  await expect(shell).toContainText('Finance / Procurement / Asset Suite', { timeout: 15_000 });
  await expect(page.locator('nav[aria-label="Finance procurement asset navigation"] a')).toHaveCount(22, { timeout: 15_000 });
  await expect(page.getByRole('link', { name: 'Finance / Procurement / Asset Suite' })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('link', { name: 'Finance Operations Dashboard' })).toBeVisible({ timeout: 15_000 });
  await expect(page.getByRole('link', { name: 'Limitations / Safety Boundaries' })).toBeVisible({ timeout: 15_000 });
}

async function expectPermissionDeniedOrSafeFallback(page: Page) {
  const deniedPanel = page.getByTestId('fpa-permission-denied-panel');
  const outerAccessDenied = page.getByRole('heading', { name: /Access Denied/i });

  if (await deniedPanel.count()) {
    await expect(deniedPanel).toBeVisible();
    await expect(deniedPanel).toContainText('Permission required');
    await expect(deniedPanel).toContainText('fail-closed');
  } else if (await outerAccessDenied.count()) {
    await expect(outerAccessDenied).toBeVisible();
    await expect(page.locator('body')).toContainText(/fail-closed/i);
  } else {
    await expect(page.locator('body')).toContainText(/fail-closed/i);
  }

  await expect(page.getByTestId('fpa-dashboard-grid')).toHaveCount(0);
  await expect(page.getByTestId('fpa-payment-readiness-badge')).toHaveCount(0);
  await expect(page.getByTestId('fpa-provider-deferred-badge')).toHaveCount(0);
  await expectForbiddenDomAbsent(page);
}

async function openAndAssertRoute(page: Page, route: (typeof FPA_ROUTES)[number]) {
  await gotoFpaRoute(page, route.path);
  await expectRouteShell(page, route);

  const routePage = page.getByTestId(`fpa-page-${route.routeKey}`);
  await expect(routePage).toBeVisible();
  await expect(page.locator('body')).toContainText(route.requiredPermission);

  for (const label of route.expectedBoundaryLabels) {
    await expect(page.locator('body')).toContainText(label);
  }

  for (const endpoint of route.endpoints) {
    await expect(page.getByTestId('fpa-evidence-table')).toContainText(endpoint);
  }

  await expectCommonRuntimeSafety(page);
  await expectForbiddenDomAbsent(page);
}

async function visitRouteWithFreshPage(browser: Browser, route: (typeof FPA_ROUTES)[number]) {
  const page = await browser.newPage({ ignoreHTTPSErrors: true });

  try {
    page.setDefaultTimeout(15_000);
    page.setDefaultNavigationTimeout(15_000);
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, route);
  } finally {
    await page.close();
  }
}

test.describe('A-040.4 Finance / Procurement / Asset route coverage', () => {
  test.describe.configure({ timeout: 240_000 });

  test('R4-GROUP-00 route inventory has exactly 22 routes', async () => {
    expect(FPA_ROUTES).toHaveLength(22);
  });

  test('R4-GROUP-01 full-access finance admin can visit all 22 routes', async ({ browser }) => {
    for (const route of FPA_ROUTES) {
      await test.step(`full-access ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });

  test('R4-GROUP-02 route-title group A, routes 1-6', async ({ browser }) => {
    for (const route of ROUTE_TITLE_GROUPS[0].routes) {
      await test.step(`route-title ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });

  test('R4-GROUP-03 route-title group B, routes 7-12', async ({ browser }) => {
    for (const route of ROUTE_TITLE_GROUPS[1].routes) {
      await test.step(`route-title ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });

  test('R4-GROUP-04 route-title group C, routes 13-18', async ({ browser }) => {
    for (const route of ROUTE_TITLE_GROUPS[2].routes) {
      await test.step(`route-title ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });

  test('R4-GROUP-05 route-title group D, routes 19-22', async ({ browser }) => {
    for (const route of ROUTE_TITLE_GROUPS[3].routes) {
      await test.step(`route-title ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });
});

test.describe('A-040.4 Finance / Procurement / Asset scenario groups', () => {
  test.describe.configure({ timeout: 180_000 });

  test('R4-GROUP-06 overview / readiness / limitations', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[0]);
    await gotoFpaRoute(page, FPA_ROUTES[21].path);
    await expectRequiredBoundaryLabels(page);
    await expect(page.getByTestId('fpa-readiness-runtime-baseline')).toContainText('Backend route count used: 53');
  });

  test('R4-GROUP-07 dashboard incomplete-data and fakeMetrics=false boundary', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[1]);
    await expect(page.getByTestId('fpa-boundary-fakemetrics-false')).toBeVisible();
    await expect(page.getByTestId('fpa-dashboard-grid')).toContainText('Billing Visibility');
    await expect(page.getByTestId('fpa-metric-fakemetrics')).toContainText('false');
  });

  test('R4-GROUP-08 billing visibility', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[2]);
    await expect(page.getByTestId('fpa-form-shell-billing-visibility-surface')).toContainText('Billing Visibility metadata is not populated yet.');
    await expect(page.getByTestId('fpa-evidence-table')).toContainText('POST /api/admin/finance-procurement-asset/billing/evidence');
  });

  test('R4-GROUP-09 receivables metadata', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[3]);
    await expect(page.getByTestId('fpa-page-receivables')).toContainText('Receivables aging and visibility metadata with incomplete-data support.');
  });

  test('R4-GROUP-10 budget planning metadata', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[4]);
    await expect(page.getByTestId('fpa-page-budget-planning')).toContainText('Budget planning metadata and evidence-only updates under human review.');
  });

  test('R4-GROUP-11 budget control review metadata', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[5]);
    await expect(page.getByTestId('fpa-page-budget-control')).toContainText('Budget control review metadata without automatic approval.');
    await expect(page.getByTestId('fpa-review-panel-human-review-boundary')).toContainText('No payment execution or settlement controls are available.');
  });

  test('R4-GROUP-12 procurement request intake', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[6]);
    await expect(page.getByTestId('fpa-page-procurement-requests')).toContainText('Procurement request intake metadata under review-only governance.');
  });

  test('R4-GROUP-13 procurement review human-review-only boundary', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[7]);
    await expect(page.getByTestId('fpa-boundary-no-automatic-procurement-approval')).toBeVisible();
    await expect(page.getByTestId('fpa-boundary-no-automatic-vendor-award')).toBeVisible();
  });

  test('R4-GROUP-14 vendor metadata boundary', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[8]);
    await expect(page.getByTestId('fpa-boundary-no-hidden-finance-vendor-score')).toBeVisible();
  });

  test('R4-GROUP-15 contract evidence boundary', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[9]);
    await expect(page.getByTestId('fpa-boundary-no-official-tax-regulatory-filing')).toBeVisible();
  });

  test('R4-GROUP-16 purchase request/order metadata', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[10]);
    await gotoFpaRoute(page, FPA_ROUTES[11].path);
    await openAndAssertRoute(page, FPA_ROUTES[11]);
  });

  test('R4-GROUP-17 asset inventory visibility', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[12]);
    await expect(page.getByTestId('fpa-boundary-incomplete-data-supported')).toBeVisible();
  });

  test('R4-GROUP-18 asset lifecycle and inventory movement metadata', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[13]);
    await gotoFpaRoute(page, FPA_ROUTES[14].path);
    await openAndAssertRoute(page, FPA_ROUTES[14]);
  });

  test('R4-GROUP-19 payment readiness non-live boundary', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[15]);
    await expect(page.getByTestId('fpa-payment-readiness-badge')).toContainText('paymentExecutionEnabled=false');
    await expect(page.getByTestId('fpa-boundary-no-payment-execution')).toBeVisible();
  });

  test('R4-GROUP-20 ERP/1C readiness non-live boundary', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[16]);
    await expect(page.getByTestId('fpa-provider-deferred-badge')).toContainText('providerConnected=false / liveBankSync=false / liveErpSync=false');
    await expect(page.getByTestId('fpa-boundary-no-live-erp-1c-sync')).toBeVisible();
  });

  test('R4-GROUP-21 bank/payment gateway readiness non-live boundary', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[17]);
    await expect(page.getByTestId('fpa-provider-deferred-badge')).toContainText('providerConnected=false / liveBankSync=false / liveErpSync=false');
    await gotoFpaRoute(page, FPA_ROUTES[18].path);
    await openAndAssertRoute(page, FPA_ROUTES[18]);
    await expect(page.getByTestId('fpa-bridge-payment-gateway')).toBeVisible();
  });

  test('R4-GROUP-22 provider readiness deferred boundary', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[18]);
    await expect(page.getByTestId('fpa-boundary-provider-readiness-only')).toBeVisible();
    await expect(page.getByTestId('fpa-provider-deferred-badge')).toContainText('providerConnected=false / liveBankSync=false / liveErpSync=false');
  });

  test('R4-GROUP-23 bridges: executive, HR payroll, document contracts, provider readiness', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[19]);
    await expect(page.getByTestId('fpa-bridge-bank-core')).toBeVisible();
    await expect(page.getByTestId('fpa-bridge-erp-1c')).toBeVisible();
    await expect(page.getByTestId('fpa-bridge-hr-payroll-bridge')).toBeVisible();
    await expect(page.getByTestId('fpa-bridge-document-contracts')).toBeVisible();
    await expect(page.getByTestId('fpa-bridge-payment-gateway')).toBeVisible();
  });

  test('R4-GROUP-24 audit/evidence/limitations', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[20]);
    await expect(page.getByTestId('fpa-audit-timeline')).toContainText('Audit / Review Timeline');
    await gotoFpaRoute(page, FPA_ROUTES[21].path);
    await openAndAssertRoute(page, FPA_ROUTES[21]);
    await expect(page.getByTestId('fpa-limitations-panel')).toContainText('No live bank integration or ERP sync controls are available.');
  });

  test('R4-GROUP-25 no-overclaim DOM scan across all routes', async ({ browser }) => {
    for (const route of FPA_ROUTES) {
      await test.step(`no-overclaim ${route.routeKey} ${route.path} -> ${route.title}`, async () => {
        await visitRouteWithFreshPage(browser, route);
      });
    }
  });

  test('R4-GROUP-26 permission-denial smoke', async ({ page }) => {
    await setRestrictedFinanceUser(page);

    for (const path of [
      '/console/finance-procurement-asset/dashboard',
      '/console/finance-procurement-asset/procurement-reviews',
      '/console/finance-procurement-asset/payment-readiness',
      '/console/finance-procurement-asset/erp-readiness',
      '/console/finance-procurement-asset/bank-readiness',
      '/console/finance-procurement-asset/provider-readiness',
      '/console/finance-procurement-asset/audit',
      '/console/finance-procurement-asset/limitations',
    ]) {
      await gotoFpaRoute(page, path);
      await expectPermissionDeniedOrSafeFallback(page);
    }
  });

  test('R4-GROUP-27 suite closeout', async ({ page }) => {
    await setAuthenticatedFinanceAdmin(page);
    await openAndAssertRoute(page, FPA_ROUTES[0]);
    expect(FPA_ROUTES).toHaveLength(22);
    await expect(page.locator('nav[aria-label="Finance procurement asset navigation"] a')).toHaveCount(22);
  });
});