import { beforeEach, describe, expect, it, vi } from 'vitest';

const client = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

vi.mock('@/shared/api/client', () => client);

import { financeProcurementAssetApi } from '@/modules/finance-procurement-asset/api';
import { FINANCE_PROCUREMENT_ASSET_API_PATHS } from '@/modules/finance-procurement-asset/constants';

describe('Finance Procurement Asset API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    client.apiGet.mockResolvedValue(undefined);
    client.apiPost.mockResolvedValue(undefined);
  });

  it('maps overview, readiness, limitations, dashboard, and health reads', async () => {
    await financeProcurementAssetApi.getFpaOverview();
    await financeProcurementAssetApi.getFpaReadiness();
    await financeProcurementAssetApi.getFpaLimitations();
    await financeProcurementAssetApi.getFpaSafetyBoundaries();
    await financeProcurementAssetApi.getFpaDashboard();
    await financeProcurementAssetApi.getFpaHealth();

    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.overview);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.readiness);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.limitations);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.safetyBoundaries);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.dashboard);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.health);
  });

  it('maps billing, receivables, budget, and procurement reads', async () => {
    await financeProcurementAssetApi.getFpaBilling();
    await financeProcurementAssetApi.getFpaReceivables();
    await financeProcurementAssetApi.getFpaBudgetPlans();
    await financeProcurementAssetApi.getFpaBudgetControls();
    await financeProcurementAssetApi.getFpaProcurementRequests();
    await financeProcurementAssetApi.getFpaProcurementReviews();

    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.billing);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.receivables);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.budgetPlans);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.budgetControls);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.procurementRequests);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.procurementReviews);
  });

  it('maps vendor, contract, purchasing, and asset reads', async () => {
    await financeProcurementAssetApi.getFpaVendors();
    await financeProcurementAssetApi.getFpaContracts();
    await financeProcurementAssetApi.getFpaPurchaseRequests();
    await financeProcurementAssetApi.getFpaPurchaseOrders();
    await financeProcurementAssetApi.getFpaAssets();
    await financeProcurementAssetApi.getFpaAssetLifecycle();
    await financeProcurementAssetApi.getFpaInventoryMovements();

    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.vendors);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.contracts);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.purchaseRequests);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.purchaseOrders);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.assets);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.assetLifecycle);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.inventoryMovements);
  });

  it('maps readiness, bridge, audit, role, permission, and metadata reads', async () => {
    await financeProcurementAssetApi.getFpaPaymentReadiness();
    await financeProcurementAssetApi.getFpaErpReadiness();
    await financeProcurementAssetApi.getFpaBankReadiness();
    await financeProcurementAssetApi.getFpaPaymentGatewayReadiness();
    await financeProcurementAssetApi.getFpaProviderReadiness();
    await financeProcurementAssetApi.getFpaAuditEvents();
    await financeProcurementAssetApi.getFpaEvidence();
    await financeProcurementAssetApi.getFpaBridgeExecutive();
    await financeProcurementAssetApi.getFpaBridgeHrPayroll();
    await financeProcurementAssetApi.getFpaBridgeDocumentContracts();
    await financeProcurementAssetApi.getFpaBridgeProviderReadiness();
    await financeProcurementAssetApi.getFpaBridgeStudentFinance();
    await financeProcurementAssetApi.getFpaRoles();
    await financeProcurementAssetApi.getFpaPermissions();
    await financeProcurementAssetApi.getFpaMetadataContract();

    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.paymentReadiness);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.erpReadiness);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.bankReadiness);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.paymentGatewayReadiness);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.providerReadiness);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.auditEvents);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.evidence);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.bridgeExecutive);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.bridgeHrPayroll);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.bridgeDocumentContracts);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.bridgeProviderReadiness);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.bridgeStudentFinance);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.roles);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.permissions);
    expect(client.apiGet).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.metadataContract);
  });

  it('maps metadata and evidence post helpers', async () => {
    await financeProcurementAssetApi.createFpaReadinessEvidence({ title: 'readiness' });
    await financeProcurementAssetApi.createFpaBillingEvidence({ title: 'billing' });
    await financeProcurementAssetApi.createFpaReceivablesMetadata({ title: 'receivable' });
    await financeProcurementAssetApi.createFpaBudgetPlan({ title: 'budget plan' });
    await financeProcurementAssetApi.reviewFpaBudgetControl({ title: 'budget review' });
    await financeProcurementAssetApi.createFpaProcurementRequest({ title: 'request' });
    await financeProcurementAssetApi.reviewFpaProcurement({ title: 'review' });
    await financeProcurementAssetApi.createFpaVendorMetadata({ title: 'vendor' });
    await financeProcurementAssetApi.createFpaContractEvidence({ title: 'contract' });

    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.readinessEvidence, { title: 'readiness' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.billingEvidence, { title: 'billing' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.receivablesMetadata, { title: 'receivable' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.budgetPlans, { title: 'budget plan' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.budgetControlsReview, { title: 'budget review' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.procurementRequests, { title: 'request' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.procurementReviews, { title: 'review' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.vendors, { title: 'vendor' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.contractsEvidence, { title: 'contract' });
  });

  it('maps purchasing, asset, readiness, evidence, and audit post helpers', async () => {
    await financeProcurementAssetApi.createFpaPurchaseRequest({ title: 'purchase request' });
    await financeProcurementAssetApi.createFpaPurchaseOrderMetadata({ title: 'purchase order' });
    await financeProcurementAssetApi.createFpaAssetMetadata({ title: 'asset' });
    await financeProcurementAssetApi.createFpaAssetLifecycle({ title: 'lifecycle' });
    await financeProcurementAssetApi.createFpaInventoryMovementMetadata({ title: 'inventory' });
    await financeProcurementAssetApi.createFpaPaymentReadinessEvidence({ title: 'payment readiness' });
    await financeProcurementAssetApi.createFpaErpReadinessEvidence({ title: 'erp readiness' });
    await financeProcurementAssetApi.createFpaBankReadinessEvidence({ title: 'bank readiness' });
    await financeProcurementAssetApi.createFpaPaymentGatewayReadinessEvidence({ title: 'gateway readiness' });
    await financeProcurementAssetApi.createFpaProviderReadinessEvidence({ title: 'provider readiness' });
    await financeProcurementAssetApi.createFpaEvidence({ title: 'evidence' });
    await financeProcurementAssetApi.createFpaAuditEvent({ title: 'audit' });

    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.purchaseRequests, { title: 'purchase request' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.purchaseOrdersMetadata, { title: 'purchase order' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.assetsMetadata, { title: 'asset' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.assetLifecycle, { title: 'lifecycle' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.inventoryMovementsMetadata, { title: 'inventory' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.paymentReadinessEvidence, { title: 'payment readiness' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.erpReadinessEvidence, { title: 'erp readiness' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.bankReadinessEvidence, { title: 'bank readiness' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.paymentGatewayReadinessEvidence, { title: 'gateway readiness' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.providerReadinessEvidence, { title: 'provider readiness' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.evidence, { title: 'evidence' });
    expect(client.apiPost).toHaveBeenCalledWith(FINANCE_PROCUREMENT_ASSET_API_PATHS.auditEvents, { title: 'audit' });
  });

  it('does not expose forbidden executor helpers', () => {
    expect('executePayment' in financeProcurementAssetApi).toBe(false);
    expect('sendPayment' in financeProcurementAssetApi).toBe(false);
    expect('syncBankLive' in financeProcurementAssetApi).toBe(false);
    expect('sync1CLive' in financeProcurementAssetApi).toBe(false);
    expect('autoApproveBudget' in financeProcurementAssetApi).toBe(false);
    expect('hiddenFinanceScore' in financeProcurementAssetApi).toBe(false);
  });
});
