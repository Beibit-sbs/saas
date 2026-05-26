import type { FpaRouteKey } from './types';

export const FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS = {
  metadataEvidenceOnlyFinanceFoundation: 'Metadata/evidence-only finance foundation',
  humanReviewRequired: 'Human review required',
  noLiveBankIntegration: 'No live bank integration',
  noLiveErpSync: 'No live ERP/1C sync',
  noPaymentExecution: 'No payment execution',
  noAutomaticProcurementApproval: 'No automatic procurement approval',
  noAutomaticBudgetApproval: 'No automatic budget approval',
  noAutomaticVendorAward: 'No automatic vendor award',
  noOfficialTaxRegulatoryFiling: 'No official tax/regulatory filing',
  noHiddenFinanceVendorScore: 'No hidden finance/vendor score',
  incompleteDataSupported: 'Incomplete data supported',
  providerReadinessOnly: 'Provider readiness only',
  paymentReadinessOnly: 'Payment readiness only',
  bridgeFirstReadOnlyFirst: 'Bridge-first / read-only-first',
  noProductionReadyClaim: 'No production-ready claim',
  noSalesReadyClaim: 'No sales-ready claim',
  noGccReadyClaim: 'No GCC-ready claim',
  fakeMetricsFalse: 'fakeMetrics=false',
  fakeFinanceDataFalse: 'fakeFinanceData=false',
  fakePaymentDataFalse: 'fakePaymentData=false',
  providerConnectedFalse: 'providerConnected=false',
  liveBankSyncFalse: 'liveBankSync=false',
  liveErpSyncFalse: 'liveErpSync=false',
  paymentExecutionEnabledFalse: 'paymentExecutionEnabled=false',
  automaticProcurementApprovalEnabledFalse: 'automaticProcurementApprovalEnabled=false',
  automaticBudgetApprovalEnabledFalse: 'automaticBudgetApprovalEnabled=false',
  automaticVendorAwardEnabledFalse: 'automaticVendorAwardEnabled=false',
  hiddenScorePresentFalse: 'hiddenScorePresent=false',
} as const;

export const FINANCE_PROCUREMENT_ASSET_BOUNDARY_COPY = [
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.metadataEvidenceOnlyFinanceFoundation,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.humanReviewRequired,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noLiveBankIntegration,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noLiveErpSync,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noPaymentExecution,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticProcurementApproval,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticBudgetApproval,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticVendorAward,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noOfficialTaxRegulatoryFiling,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noHiddenFinanceVendorScore,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.incompleteDataSupported,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.providerReadinessOnly,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.paymentReadinessOnly,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noProductionReadyClaim,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noSalesReadyClaim,
  FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noGccReadyClaim,
] as const;

export const FINANCE_PROCUREMENT_ASSET_FORBIDDEN_LABELS = [
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
  'Production ready',
  'Sales ready',
  'GCC ready',
  'L5/L6 ready',
] as const;

export const FINANCE_PROCUREMENT_ASSET_PAGE_BOUNDARY_LABELS: Record<FpaRouteKey, string[]> = {
  overview: [...FINANCE_PROCUREMENT_ASSET_BOUNDARY_COPY, FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.fakeMetricsFalse, FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.fakeFinanceDataFalse, FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.fakePaymentDataFalse],
  dashboard: [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.metadataEvidenceOnlyFinanceFoundation,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.fakeMetricsFalse,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.incompleteDataSupported,
  ],
  billing: [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.metadataEvidenceOnlyFinanceFoundation,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.humanReviewRequired,
  ],
  receivables: [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.metadataEvidenceOnlyFinanceFoundation,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.incompleteDataSupported,
  ],
  'budget-planning': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.humanReviewRequired,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticBudgetApproval,
  ],
  'budget-control': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.humanReviewRequired,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticBudgetApproval,
  ],
  'procurement-requests': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.humanReviewRequired,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticProcurementApproval,
  ],
  'procurement-reviews': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.humanReviewRequired,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticProcurementApproval,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticVendorAward,
  ],
  vendors: [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.metadataEvidenceOnlyFinanceFoundation,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noHiddenFinanceVendorScore,
  ],
  contracts: [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.metadataEvidenceOnlyFinanceFoundation,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noOfficialTaxRegulatoryFiling,
  ],
  'purchase-requests': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.humanReviewRequired,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticProcurementApproval,
  ],
  'purchase-orders': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.metadataEvidenceOnlyFinanceFoundation,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noAutomaticVendorAward,
  ],
  assets: [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.metadataEvidenceOnlyFinanceFoundation,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.incompleteDataSupported,
  ],
  'asset-lifecycle': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.humanReviewRequired,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst,
  ],
  'inventory-movements': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.metadataEvidenceOnlyFinanceFoundation,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst,
  ],
  'payment-readiness': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.paymentReadinessOnly,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noPaymentExecution,
  ],
  'erp-readiness': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.providerReadinessOnly,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noLiveErpSync,
  ],
  'bank-readiness': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.providerReadinessOnly,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noLiveBankIntegration,
  ],
  'provider-readiness': [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.providerReadinessOnly,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst,
  ],
  bridges: [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.bridgeFirstReadOnlyFirst,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.noPaymentExecution,
  ],
  audit: [
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.humanReviewRequired,
    FINANCE_PROCUREMENT_ASSET_BOUNDARY_LABELS.metadataEvidenceOnlyFinanceFoundation,
  ],
  limitations: [...FINANCE_PROCUREMENT_ASSET_BOUNDARY_COPY],
};

export function getFpaBoundaryLabels(routeKey: FpaRouteKey) {
  return FINANCE_PROCUREMENT_ASSET_PAGE_BOUNDARY_LABELS[routeKey];
}
