import type { Permission } from '@/shared/config/permissions';
import { FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS, getFpaBoundaryLabels } from './boundaryLabels';
import type {
  FpaDashboardWidget,
  FpaProviderProfile,
  FpaRouteDefinition,
  FpaRouteKey,
  FpaSafetyFlags,
  FpaWorkflowDefinition,
} from './types';

export const FINANCE_PROCUREMENT_ASSET_MODULE = 'finance-procurement-asset';
export const FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY = '/console/finance-procurement-asset';
export const FINANCE_PROCUREMENT_ASSET_API_BASE = '/api/admin/finance-procurement-asset';
export const FINANCE_PROCUREMENT_ASSET_PLANNED_ROUTE_COUNT = 23;
export const FINANCE_PROCUREMENT_ASSET_BACKEND_ROUTE_COUNT = 57;
export const FINANCE_PROCUREMENT_ASSET_PERMISSION_COUNT = 51;
export const FINANCE_PROCUREMENT_ASSET_RUNTIME_MODE = 'METADATA_EVIDENCE_READINESS_HUMAN_REVIEW_ONLY';
export const FINANCE_PROCUREMENT_ASSET_SOURCE_BACKEND_BASELINE_COMMIT = '0453fbd';
export const FINANCE_PROCUREMENT_ASSET_SOURCE_BACKEND_RUNTIME_COMMIT = '0394414';
export const FINANCE_PROCUREMENT_ASSET_DATA_SOURCE = 'computed_from_finance_procurement_asset_metadata';

export const fakeMetrics = false;
export const fakeFinanceData = false;
export const fakePaymentData = false;
export const providerConnected = false;
export const liveBankSync = false;
export const liveErpSync = false;
export const paymentExecutionEnabled = false;
export const automaticProcurementApprovalEnabled = false;
export const automaticBudgetApprovalEnabled = false;
export const automaticVendorAwardEnabled = false;
export const hiddenScorePresent = false;
export const humanReviewRequired = true;

export const FINANCE_PROCUREMENT_ASSET_SAFETY_FLAGS: FpaSafetyFlags = {
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
    'No live bank integration, live ERP sync, payment execution, automatic approvals, or hidden scoring surfaces are implemented.',
  ],
};

export const FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES = {
  overviewRead: 'finance_procurement_asset.overview.read' as Permission,
  readinessRead: 'finance_procurement_asset.readiness.read' as Permission,
  limitationsRead: 'finance_procurement_asset.limitations.read' as Permission,
  dashboardRead: 'finance_procurement_asset.dashboard.read' as Permission,
  billingRead: 'finance_procurement_asset.billing.read' as Permission,
  billingEvidence: 'finance_procurement_asset.billing.evidence' as Permission,
  receivablesRead: 'finance_procurement_asset.receivables.read' as Permission,
  receivablesMetadata: 'finance_procurement_asset.receivables.metadata' as Permission,
  budgetPlansRead: 'finance_procurement_asset.budget_plans.read' as Permission,
  budgetPlansManage: 'finance_procurement_asset.budget_plans.manage' as Permission,
  budgetControlsRead: 'finance_procurement_asset.budget_controls.read' as Permission,
  budgetControlsReview: 'finance_procurement_asset.budget_controls.review' as Permission,
  procurementRequestsRead: 'finance_procurement_asset.procurement_requests.read' as Permission,
  procurementRequestsManage: 'finance_procurement_asset.procurement_requests.manage' as Permission,
  procurementReviewsRead: 'finance_procurement_asset.procurement_reviews.read' as Permission,
  procurementReviewsReview: 'finance_procurement_asset.procurement_reviews.review' as Permission,
  vendorsRead: 'finance_procurement_asset.vendors.read' as Permission,
  vendorsManage: 'finance_procurement_asset.vendors.manage' as Permission,
  contractsRead: 'finance_procurement_asset.contracts.read' as Permission,
  contractsEvidence: 'finance_procurement_asset.contracts.evidence' as Permission,
  purchaseRequestsRead: 'finance_procurement_asset.purchase_requests.read' as Permission,
  purchaseRequestsManage: 'finance_procurement_asset.purchase_requests.manage' as Permission,
  purchaseOrdersRead: 'finance_procurement_asset.purchase_orders.read' as Permission,
  purchaseOrdersMetadata: 'finance_procurement_asset.purchase_orders.metadata' as Permission,
  assetsRead: 'finance_procurement_asset.assets.read' as Permission,
  assetsMetadata: 'finance_procurement_asset.assets.metadata' as Permission,
  assetLifecycleRead: 'finance_procurement_asset.asset_lifecycle.read' as Permission,
  assetLifecycleManage: 'finance_procurement_asset.asset_lifecycle.manage' as Permission,
  inventoryMovementsRead: 'finance_procurement_asset.inventory_movements.read' as Permission,
  inventoryMovementsMetadata: 'finance_procurement_asset.inventory_movements.metadata' as Permission,
  paymentReadinessRead: 'finance_procurement_asset.payment_readiness.read' as Permission,
  paymentReadinessEvidence: 'finance_procurement_asset.payment_readiness.evidence' as Permission,
  erpReadinessRead: 'finance_procurement_asset.erp_readiness.read' as Permission,
  erpReadinessEvidence: 'finance_procurement_asset.erp_readiness.evidence' as Permission,
  bankReadinessRead: 'finance_procurement_asset.bank_readiness.read' as Permission,
  bankReadinessEvidence: 'finance_procurement_asset.bank_readiness.evidence' as Permission,
  paymentGatewayReadinessRead: 'finance_procurement_asset.payment_gateway_readiness.read' as Permission,
  paymentGatewayReadinessEvidence: 'finance_procurement_asset.payment_gateway_readiness.evidence' as Permission,
  providerReadinessRead: 'finance_procurement_asset.provider_readiness.read' as Permission,
  providerReadinessEvidence: 'finance_procurement_asset.provider_readiness.evidence' as Permission,
  auditRead: 'finance_procurement_asset.audit.read' as Permission,
  auditWrite: 'finance_procurement_asset.audit.write' as Permission,
  evidenceRead: 'finance_procurement_asset.evidence.read' as Permission,
  evidenceWrite: 'finance_procurement_asset.evidence.write' as Permission,
  bridgesExecutiveRead: 'finance_procurement_asset.bridges.executive.read' as Permission,
  bridgesHrPayrollRead: 'finance_procurement_asset.bridges.hr_payroll.read' as Permission,
  bridgesDocumentContractsRead: 'finance_procurement_asset.bridges.document_contracts.read' as Permission,
  bridgesProviderReadinessRead: 'finance_procurement_asset.bridges.provider_readiness.read' as Permission,
  bridgesStudentFinanceRead: 'finance_procurement_asset.bridges.student_finance.read' as Permission,
  bridgesStudentFinanceAcknowledge: 'finance_procurement_asset.bridges.student_finance.acknowledge' as Permission,
  metadataRead: 'finance_procurement_asset.metadata.read' as Permission,
} as const;

function apiPath(path: string) {
  return `${FINANCE_PROCUREMENT_ASSET_API_BASE}${path}`;
}

function endpoint(method: 'GET' | 'POST', path: string) {
  return `${method} ${apiPath(path)}`;
}

function stateFromTitle(title: string) {
  return `${title} metadata is not populated yet. This runtime keeps incomplete data explicit and review-only.`;
}

function routeDefinition(
  key: FpaRouteKey,
  title: string,
  path: string,
  requiredPermission: Permission,
  backendEndpoints: string[],
  description: string,
  dashboardLike: boolean,
  sensitive: boolean,
): FpaRouteDefinition {
  return {
    key,
    title,
    path,
    requiredPermission,
    backendEndpoints,
    boundaryLabels: getFpaBoundaryLabels(key),
    description,
    dashboardLike,
    sensitive,
    humanReviewRequired: sensitive || key === 'limitations' || key === 'overview' || key === 'dashboard',
    emptyState: stateFromTitle(title),
    incompleteDataState: 'Incomplete data is expected and explicitly supported in this runtime.',
    permissionDeniedState: `This route is fail-closed and requires ${requiredPermission}.`,
  };
}

export const FINANCE_PROCUREMENT_ASSET_API_PATHS = {
  health: apiPath('/health'),
  overview: apiPath('/overview'),
  readiness: apiPath('/readiness'),
  limitations: apiPath('/limitations'),
  safetyBoundaries: apiPath('/safety-boundaries'),
  dashboard: apiPath('/dashboard'),
  billing: apiPath('/billing'),
  receivables: apiPath('/receivables'),
  budgetPlans: apiPath('/budget-plans'),
  budgetControls: apiPath('/budget-controls'),
  procurementRequests: apiPath('/procurement-requests'),
  procurementReviews: apiPath('/procurement-reviews'),
  vendors: apiPath('/vendors'),
  contracts: apiPath('/contracts'),
  purchaseRequests: apiPath('/purchase-requests'),
  purchaseOrders: apiPath('/purchase-orders'),
  assets: apiPath('/assets'),
  assetLifecycle: apiPath('/asset-lifecycle'),
  inventoryMovements: apiPath('/inventory-movements'),
  paymentReadiness: apiPath('/payment-readiness'),
  erpReadiness: apiPath('/erp-readiness'),
  bankReadiness: apiPath('/bank-readiness'),
  paymentGatewayReadiness: apiPath('/payment-gateway-readiness'),
  providerReadiness: apiPath('/provider-readiness'),
  auditEvents: apiPath('/audit-events'),
  evidence: apiPath('/evidence'),
  bridgeExecutive: apiPath('/bridges/executive'),
  bridgeHrPayroll: apiPath('/bridges/hr-payroll'),
  bridgeDocumentContracts: apiPath('/bridges/document-contracts'),
  bridgeProviderReadiness: apiPath('/bridges/provider-readiness'),
  bridgeStudentFinance: apiPath('/bridges/student-finance'),
  bridgeStudentFinanceReferrals: apiPath('/bridges/student-finance-referrals'),
  bridgeStudentFinanceReferralAcknowledge: apiPath('/bridges/student-finance-referrals/acknowledge'),
  roles: apiPath('/roles'),
  permissions: apiPath('/permissions'),
  metadataContract: apiPath('/metadata-contract'),
  readinessEvidence: apiPath('/readiness/evidence'),
  billingEvidence: apiPath('/billing/evidence'),
  receivablesMetadata: apiPath('/receivables/metadata'),
  budgetControlsReview: apiPath('/budget-controls/review'),
  contractsEvidence: apiPath('/contracts/evidence'),
  purchaseOrdersMetadata: apiPath('/purchase-orders/metadata'),
  assetsMetadata: apiPath('/assets/metadata'),
  inventoryMovementsMetadata: apiPath('/inventory-movements/metadata'),
  paymentReadinessEvidence: apiPath('/payment-readiness/evidence'),
  erpReadinessEvidence: apiPath('/erp-readiness/evidence'),
  bankReadinessEvidence: apiPath('/bank-readiness/evidence'),
  paymentGatewayReadinessEvidence: apiPath('/payment-gateway-readiness/evidence'),
  providerReadinessEvidence: apiPath('/provider-readiness/evidence'),
} as const;

export const FINANCE_PROCUREMENT_ASSET_ROUTES: FpaRouteDefinition[] = [
  routeDefinition('overview', 'Finance / Procurement / Asset Suite', FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead, [endpoint('GET', '/overview'), endpoint('GET', '/readiness'), endpoint('GET', '/limitations')], 'Operational overview of the finance procurement asset metadata and safety boundary baseline.', true, true),
  routeDefinition('dashboard', 'Finance Operations Dashboard', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/dashboard`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.dashboardRead, [endpoint('GET', '/dashboard')], 'Dashboard visibility across billing, receivables, budget, procurement, assets, readiness, and bridge posture.', true, true),
  routeDefinition('billing', 'Billing Visibility', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/billing`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.billingRead, [endpoint('GET', '/billing'), endpoint('POST', '/billing/evidence')], 'Billing metadata and evidence capture without payment execution.', false, true),
  routeDefinition('receivables', 'Receivables Metadata', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/receivables`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.receivablesRead, [endpoint('GET', '/receivables'), endpoint('POST', '/receivables/metadata')], 'Receivables aging and visibility metadata with incomplete-data support.', false, false),
  routeDefinition('budget-planning', 'Budget Planning', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/budget-planning`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.budgetPlansRead, [endpoint('GET', '/budget-plans'), endpoint('POST', '/budget-plans')], 'Budget planning metadata and evidence-only updates under human review.', false, true),
  routeDefinition('budget-control', 'Budget Control Review', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/budget-control`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.budgetControlsRead, [endpoint('GET', '/budget-controls'), endpoint('POST', '/budget-controls/review')], 'Budget control review metadata without automatic approval.', false, true),
  routeDefinition('procurement-requests', 'Procurement Requests', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/procurement-requests`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.procurementRequestsRead, [endpoint('GET', '/procurement-requests'), endpoint('POST', '/procurement-requests')], 'Procurement request intake metadata under review-only governance.', false, true),
  routeDefinition('procurement-reviews', 'Procurement Committee Reviews', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/procurement-reviews`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.procurementReviewsRead, [endpoint('GET', '/procurement-reviews'), endpoint('POST', '/procurement-reviews')], 'Committee review metadata without automatic procurement approval or vendor award.', false, true),
  routeDefinition('vendors', 'Vendor Metadata', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/vendors`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.vendorsRead, [endpoint('GET', '/vendors'), endpoint('POST', '/vendors')], 'Vendor readiness and metadata visibility without hidden vendor scoring.', false, false),
  routeDefinition('contracts', 'Contract Evidence', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/contracts`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.contractsRead, [endpoint('GET', '/contracts'), endpoint('POST', '/contracts/evidence')], 'Contract evidence and visibility metadata without regulatory filing execution.', false, true),
  routeDefinition('purchase-requests', 'Purchase Requests', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/purchase-requests`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.purchaseRequestsRead, [endpoint('GET', '/purchase-requests'), endpoint('POST', '/purchase-requests')], 'Purchase request metadata and intake evidence routed into human review.', false, true),
  routeDefinition('purchase-orders', 'Purchase Orders', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/purchase-orders`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.purchaseOrdersRead, [endpoint('GET', '/purchase-orders'), endpoint('POST', '/purchase-orders/metadata')], 'Purchase order metadata only with no automatic vendor award or financial close execution.', false, false),
  routeDefinition('assets', 'Asset Visibility', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/assets`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.assetsRead, [endpoint('GET', '/assets'), endpoint('POST', '/assets/metadata')], 'Asset inventory visibility metadata with incomplete-data support.', false, false),
  routeDefinition('asset-lifecycle', 'Asset Lifecycle', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/asset-lifecycle`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.assetLifecycleRead, [endpoint('GET', '/asset-lifecycle'), endpoint('POST', '/asset-lifecycle')], 'Asset lifecycle metadata and review-only updates.', false, true),
  routeDefinition('inventory-movements', 'Inventory Movements', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/inventory-movements`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.inventoryMovementsRead, [endpoint('GET', '/inventory-movements'), endpoint('POST', '/inventory-movements/metadata')], 'Inventory movement metadata with bridge-first visibility.', false, false),
  routeDefinition('payment-readiness', 'Payment Readiness', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/payment-readiness`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.paymentReadinessRead, [endpoint('GET', '/payment-readiness'), endpoint('POST', '/payment-readiness/evidence')], 'Payment readiness metadata only with paymentExecutionEnabled=false.', false, true),
  routeDefinition('erp-readiness', 'ERP / 1C Readiness', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/erp-readiness`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.erpReadinessRead, [endpoint('GET', '/erp-readiness'), endpoint('POST', '/erp-readiness/evidence')], 'ERP/1C readiness metadata only with liveErpSync=false.', false, true),
  routeDefinition('bank-readiness', 'Bank Readiness', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/bank-readiness`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bankReadinessRead, [endpoint('GET', '/bank-readiness'), endpoint('POST', '/bank-readiness/evidence')], 'Bank readiness metadata only with liveBankSync=false.', false, true),
  routeDefinition('provider-readiness', 'Provider Readiness', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/provider-readiness`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.providerReadinessRead, [endpoint('GET', '/provider-readiness'), endpoint('GET', '/payment-gateway-readiness'), endpoint('POST', '/provider-readiness/evidence'), endpoint('POST', '/payment-gateway-readiness/evidence')], 'Provider and payment gateway readiness evidence with providerConnected=false.', false, false),
  routeDefinition('bridges', 'Bridge Visibility', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/bridges`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bridgesExecutiveRead, [endpoint('GET', '/bridges/executive'), endpoint('GET', '/bridges/hr-payroll'), endpoint('GET', '/bridges/document-contracts'), endpoint('GET', '/bridges/provider-readiness'), endpoint('GET', '/bridges/student-finance')], 'Read-only-first bridge surfaces into executive, HR/payroll, document/contracts, provider readiness, and student finance contexts.', false, false),
  routeDefinition('student-finance', 'Student Finance Bridge', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/student-finance`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bridgesStudentFinanceRead, [endpoint('GET', '/bridges/student-finance'), endpoint('GET', '/bridges/student-finance-referrals'), endpoint('POST', '/bridges/student-finance-referrals/acknowledge'), endpoint('GET', '/receivables'), endpoint('POST', '/receivables/metadata'), endpoint('GET', '/billing'), endpoint('GET', '/payment-readiness')], 'Read-only student finance bridge from academic lifecycle into receivables, billing visibility, and payment readiness metadata.', false, false),
  routeDefinition('audit', 'Audit / Evidence', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/audit`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.auditRead, [endpoint('GET', '/audit-events'), endpoint('GET', '/evidence'), endpoint('POST', '/audit-events'), endpoint('POST', '/evidence')], 'Audit and evidence surfaces remain metadata-only and human-reviewed.', false, true),
  routeDefinition('limitations', 'Limitations / Safety Boundaries', `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/limitations`, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.limitationsRead, [endpoint('GET', '/limitations'), endpoint('GET', '/safety-boundaries'), endpoint('GET', '/metadata-contract')], 'Explicit limitations, no-overclaim boundaries, and safety assertions for the FPA frontend runtime.', false, true),
];

export const FINANCE_PROCUREMENT_ASSET_ROUTE_COUNT = FINANCE_PROCUREMENT_ASSET_ROUTES.length;

export const FINANCE_PROCUREMENT_ASSET_NAV_ITEMS = FINANCE_PROCUREMENT_ASSET_ROUTES.map((route) => ({
  key: route.key,
  title: route.title,
  href: route.path,
}));

export const FINANCE_PROCUREMENT_ASSET_PROVIDER_PROFILES: FpaProviderProfile[] = [
  { key: 'BANK_CORE', title: 'Bank Core Integration', description: 'Deferred bank connectivity readiness only; no live bank session or transfer execution.', provider_connected: false, live_bank_sync: false, live_erp_sync: false },
  { key: 'ERP_1C', title: 'ERP / 1C', description: 'Deferred ERP/1C readiness only; no live synchronization or credentialed session.', provider_connected: false, live_bank_sync: false, live_erp_sync: false },
  { key: 'PAYMENT_GATEWAY', title: 'Payment Gateway', description: 'Deferred gateway readiness only; no payment execution or settlement action.', provider_connected: false, live_bank_sync: false, live_erp_sync: false },
  { key: 'HR_PAYROLL_BRIDGE', title: 'HR / Payroll Bridge', description: 'Read-only bridge context for payroll readiness dependencies.', provider_connected: false, live_bank_sync: false, live_erp_sync: false },
  { key: 'DOCUMENT_CONTRACTS', title: 'Document / Contracts Bridge', description: 'Read-only document and contract readiness context with no write-back.', provider_connected: false, live_bank_sync: false, live_erp_sync: false },
];

export const FINANCE_PROCUREMENT_ASSET_DASHBOARD_WIDGETS: FpaDashboardWidget[] = [
  { key: 'billing-visibility', title: 'Billing Visibility', description: 'Billing metadata completeness and evidence posture.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/billing')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.billingRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/billing`, forbiddenAction: 'No payment execution', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noPaymentExecution], relatedRoutes: ['dashboard', 'billing'] },
  { key: 'receivables-aging', title: 'Receivables Aging Metadata', description: 'Receivables visibility and incomplete-data status.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/receivables')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.receivablesRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/receivables`, forbiddenAction: 'No fake finance data', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.incompleteDataSupported], relatedRoutes: ['dashboard', 'receivables'] },
  { key: 'budget-planning-health', title: 'Budget Planning Health', description: 'Budget planning metadata and review readiness.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/budget-plans')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.budgetPlansRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/budget-planning`, forbiddenAction: 'No automatic budget approval', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticBudgetApproval], relatedRoutes: ['dashboard', 'budget-planning'] },
  { key: 'budget-control-review-queue', title: 'Budget Control Review Queue', description: 'Human-review-only budget control items.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/budget-controls')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.budgetControlsRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/budget-control`, forbiddenAction: 'No automatic budget approval', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.humanReviewRequired], relatedRoutes: ['dashboard', 'budget-control'] },
  { key: 'procurement-intake', title: 'Procurement Intake', description: 'Request intake and review queue visibility.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/procurement-requests')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.procurementRequestsRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/procurement-requests`, forbiddenAction: 'No automatic procurement approval', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticProcurementApproval], relatedRoutes: ['dashboard', 'procurement-requests'] },
  { key: 'vendor-review-risk', title: 'Vendor Review Metadata', description: 'Vendor readiness and metadata completeness.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/vendors')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.vendorsRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/vendors`, forbiddenAction: 'No hidden vendor score', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noHiddenFinanceVendorScore], relatedRoutes: ['dashboard', 'vendors'] },
  { key: 'purchase-order-visibility', title: 'Purchase Order Visibility', description: 'Purchase request/order metadata without award automation.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/purchase-orders')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.purchaseOrdersRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/purchase-orders`, forbiddenAction: 'No automatic vendor award', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticVendorAward], relatedRoutes: ['dashboard', 'purchase-orders', 'purchase-requests'] },
  { key: 'asset-lifecycle-visibility', title: 'Asset Lifecycle Visibility', description: 'Asset inventory and lifecycle metadata posture.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/assets'), endpoint('GET', '/asset-lifecycle')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.assetsRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/assets`, forbiddenAction: 'No automatic financial close', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst], relatedRoutes: ['dashboard', 'assets', 'asset-lifecycle'] },
  { key: 'inventory-movement-bridge', title: 'Inventory Movement Bridge', description: 'Read-only inventory movement visibility and bridge context.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/inventory-movements')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.inventoryMovementsRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/inventory-movements`, forbiddenAction: 'No cross-module mutation', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst], relatedRoutes: ['dashboard', 'inventory-movements', 'bridges'] },
  { key: 'payment-readiness-status', title: 'Payment Readiness Status', description: 'Payment readiness evidence without execution or settlement.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/payment-readiness')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.paymentReadinessRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/payment-readiness`, forbiddenAction: 'No payment execution', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.paymentReadinessOnly], relatedRoutes: ['dashboard', 'payment-readiness'] },
  { key: 'provider-readiness-status', title: 'Provider Readiness Status', description: 'Bank, ERP, gateway, and provider readiness remain deferred.', endpointRefs: [endpoint('GET', '/dashboard'), endpoint('GET', '/provider-readiness'), endpoint('GET', '/erp-readiness'), endpoint('GET', '/bank-readiness')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.providerReadinessRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/provider-readiness`, forbiddenAction: 'No live sync or connection action', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.providerReadinessOnly], relatedRoutes: ['dashboard', 'provider-readiness', 'erp-readiness', 'bank-readiness'] },
  { key: 'limitations-boundaries', title: 'Limitations / Boundaries', description: 'Surface-wide no-overclaim and deferred-provider assertions.', endpointRefs: [endpoint('GET', '/limitations'), endpoint('GET', '/safety-boundaries')], sourcePermission: FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.limitationsRead, drilldownPath: `${FINANCE_PROCUREMENT_ASSET_ROUTE_FAMILY}/limitations`, forbiddenAction: 'No production/sales/GCC/L5/L6 claim', boundaryLabels: [FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noProductionReadyClaim], relatedRoutes: ['dashboard', 'limitations', 'overview'] },
];

export const FINANCE_PROCUREMENT_ASSET_WORKFLOWS: FpaWorkflowDefinition[] = [
  { key: 'overview-readiness-limitations', title: 'Overview -> Readiness -> Limitations', description: 'Inspect the suite overview, readiness status, and explicit limitations together.', routeKeys: ['overview', 'limitations'], endpointRefs: [endpoint('GET', '/overview'), endpoint('GET', '/readiness'), endpoint('GET', '/limitations')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.overviewRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.limitationsRead], humanReviewPoint: 'Boundary banner marks the slice as human-review-only.', noOverclaimBoundary: 'No execution or auto-approval UI.', futureE2eAssertion: 'Readiness and limitations labels render together.' },
  { key: 'dashboard-incomplete-data', title: 'Dashboard -> Incomplete Data Drilldown', description: 'Inspect dashboard summaries and preserve incomplete-data visibility across drilldowns.', routeKeys: ['dashboard'], endpointRefs: [endpoint('GET', '/dashboard')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.dashboardRead], humanReviewPoint: 'Sensitive widgets retain review-only cues.', noOverclaimBoundary: 'fakeMetrics=false and fakeFinanceData=false remain visible.', futureE2eAssertion: 'Incomplete-data notice is visible on dashboard surfaces.' },
  { key: 'billing-evidence-flow', title: 'Billing Visibility -> Evidence Capture', description: 'Read billing visibility metadata and attach evidence without payment execution.', routeKeys: ['billing'], endpointRefs: [endpoint('GET', '/billing'), endpoint('POST', '/billing/evidence')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.billingRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.billingEvidence], humanReviewPoint: 'Evidence capture remains metadata-only.', noOverclaimBoundary: 'No execute payment action.', futureE2eAssertion: 'No payment execution button appears on billing route.' },
  { key: 'budget-planning-review', title: 'Budget Planning -> Budget Control Review', description: 'Create budget planning metadata and route it into manual control review.', routeKeys: ['budget-planning', 'budget-control'], endpointRefs: [endpoint('GET', '/budget-plans'), endpoint('POST', '/budget-plans'), endpoint('GET', '/budget-controls'), endpoint('POST', '/budget-controls/review')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.budgetPlansRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.budgetControlsReview], humanReviewPoint: 'Budget control review remains manual.', noOverclaimBoundary: 'No automatic budget approval.', futureE2eAssertion: 'Human review badge is visible on budget-control route.' },
  { key: 'procurement-committee-review', title: 'Procurement Request -> Committee Review', description: 'Capture procurement request metadata and committee review evidence.', routeKeys: ['procurement-requests', 'procurement-reviews'], endpointRefs: [endpoint('GET', '/procurement-requests'), endpoint('POST', '/procurement-requests'), endpoint('GET', '/procurement-reviews'), endpoint('POST', '/procurement-reviews')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.procurementRequestsRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.procurementReviewsReview], humanReviewPoint: 'Procurement committee decisions remain manual.', noOverclaimBoundary: 'No automatic procurement approval or vendor award.', futureE2eAssertion: 'No auto-approval labels render on procurement routes.' },
  { key: 'vendor-contract-evidence', title: 'Vendor Metadata -> Contract Evidence', description: 'Inspect vendor metadata and record contract evidence without hidden scoring.', routeKeys: ['vendors', 'contracts'], endpointRefs: [endpoint('GET', '/vendors'), endpoint('POST', '/vendors'), endpoint('GET', '/contracts'), endpoint('POST', '/contracts/evidence')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.vendorsRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.contractsEvidence], humanReviewPoint: 'Contract evidence is manually recorded.', noOverclaimBoundary: 'No hidden finance/vendor score and no regulatory filing execution.', futureE2eAssertion: 'No hidden score copy appears on vendor or contract routes.' },
  { key: 'purchase-order-metadata', title: 'Purchase Request -> Purchase Order Metadata', description: 'Manage purchase request/order metadata with review-only constraints.', routeKeys: ['purchase-requests', 'purchase-orders'], endpointRefs: [endpoint('GET', '/purchase-requests'), endpoint('POST', '/purchase-requests'), endpoint('GET', '/purchase-orders'), endpoint('POST', '/purchase-orders/metadata')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.purchaseRequestsRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.purchaseOrdersMetadata], humanReviewPoint: 'Purchase order metadata remains manual.', noOverclaimBoundary: 'No automatic vendor award.', futureE2eAssertion: 'Metadata-only affordances render on purchase order route.' },
  { key: 'asset-lifecycle-bridge', title: 'Assets -> Asset Lifecycle -> Inventory Movements', description: 'Inspect asset visibility, lifecycle, and inventory movement metadata together.', routeKeys: ['assets', 'asset-lifecycle', 'inventory-movements'], endpointRefs: [endpoint('GET', '/assets'), endpoint('POST', '/assets/metadata'), endpoint('GET', '/asset-lifecycle'), endpoint('POST', '/asset-lifecycle'), endpoint('GET', '/inventory-movements'), endpoint('POST', '/inventory-movements/metadata')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.assetsRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.assetLifecycleManage, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.inventoryMovementsRead], humanReviewPoint: 'Lifecycle changes remain metadata-only under review.', noOverclaimBoundary: 'Bridge-first / read-only-first asset visibility.', futureE2eAssertion: 'Inventory movement route keeps bridge-first language.' },
  { key: 'payment-provider-readiness', title: 'Payment -> ERP -> Bank -> Provider Readiness', description: 'Review readiness evidence across payment, ERP, bank, and provider surfaces.', routeKeys: ['payment-readiness', 'erp-readiness', 'bank-readiness', 'provider-readiness'], endpointRefs: [endpoint('GET', '/payment-readiness'), endpoint('POST', '/payment-readiness/evidence'), endpoint('GET', '/erp-readiness'), endpoint('POST', '/erp-readiness/evidence'), endpoint('GET', '/bank-readiness'), endpoint('POST', '/bank-readiness/evidence'), endpoint('GET', '/provider-readiness'), endpoint('POST', '/provider-readiness/evidence'), endpoint('GET', '/payment-gateway-readiness'), endpoint('POST', '/payment-gateway-readiness/evidence')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.paymentReadinessRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.erpReadinessRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bankReadinessRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.providerReadinessRead], humanReviewPoint: 'All readiness evidence remains manual and deferred.', noOverclaimBoundary: 'No payment execution and no live bank/ERP sync.', futureE2eAssertion: 'Deferred/provider badges render without sync-now controls.' },
  { key: 'bridge-visibility', title: 'Executive / HR Payroll / Document Contracts Bridges', description: 'Inspect read-only bridge surfaces across adjacent domains.', routeKeys: ['bridges'], endpointRefs: [endpoint('GET', '/bridges/executive'), endpoint('GET', '/bridges/hr-payroll'), endpoint('GET', '/bridges/document-contracts'), endpoint('GET', '/bridges/provider-readiness'), endpoint('GET', '/bridges/student-finance')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bridgesExecutiveRead], humanReviewPoint: 'Bridge insights inform manual review only.', noOverclaimBoundary: 'No cross-module mutation controls.', futureE2eAssertion: 'Bridge cards remain read-only-first.' },
  { key: 'student-finance-bridge', title: 'Student Lifecycle -> Finance Bridge', description: 'Inspect how student, enrollment, degree progress, and alumni context enters finance as read-only receivables/payment readiness metadata.', routeKeys: ['student-finance', 'receivables', 'billing', 'payment-readiness'], endpointRefs: [endpoint('GET', '/bridges/student-finance'), endpoint('GET', '/receivables'), endpoint('POST', '/receivables/metadata'), endpoint('GET', '/billing'), endpoint('GET', '/payment-readiness')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.bridgesStudentFinanceRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.receivablesRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.receivablesMetadata], humanReviewPoint: 'Student finance review remains manual and metadata-only.', noOverclaimBoundary: 'No tuition charge creation, payment execution, or ERP posting.', futureE2eAssertion: 'Student finance bridge renders without payment execution controls.' },
  { key: 'audit-evidence-limitations', title: 'Audit / Evidence / Limitations', description: 'Review audit events, evidence items, and explicit limitations together.', routeKeys: ['audit', 'limitations'], endpointRefs: [endpoint('GET', '/audit-events'), endpoint('GET', '/evidence'), endpoint('POST', '/audit-events'), endpoint('POST', '/evidence'), endpoint('GET', '/limitations'), endpoint('GET', '/metadata-contract')], requiredPermissions: [FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.auditRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.evidenceRead, FINANCE_PROCUREMENT_ASSET_PERMISSION_VALUES.limitationsRead], humanReviewPoint: 'Audit and evidence events remain insert-only and manually reviewed.', noOverclaimBoundary: 'No execution, filing, or hidden scoring.', futureE2eAssertion: 'No-overclaim footer remains visible on audit and limitations routes.' },
];
