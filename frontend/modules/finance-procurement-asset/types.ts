import type { Permission } from '@/shared/config/permissions';

export type FpaRouteKey =
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

export interface FpaSafetyFlags {
  fake_metrics: false;
  fake_finance_data: false;
  fake_payment_data: false;
  provider_connected: false;
  live_bank_sync: false;
  live_erp_sync: false;
  payment_execution_enabled: false;
  automatic_procurement_approval_enabled: false;
  automatic_budget_approval_enabled: false;
  automatic_vendor_award_enabled: false;
  hidden_score_present: false;
  human_review_required: true;
  incomplete_data: boolean;
  limitations: string[];
}

export interface FpaApiResult<T> {
  items: T[];
}

export interface FpaMetadataEntity extends FpaSafetyFlags {
  id: number | string;
  tenant_id?: number;
  status: string;
  title: string;
  description?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  metadata?: Record<string, unknown>;
  summary?: Record<string, unknown>;
  payload?: Record<string, unknown>;
  owner_ref?: string | null;
  reviewer_ref?: string | null;
  source_module?: string | null;
  source_record_id?: number | string | null;
  reference_uri?: string | null;
  read_only_first?: boolean;
  mutation_allowed?: boolean;
}

export interface FpaOverview extends FpaSafetyFlags {
  tenant_id: number;
  module: string;
  product_vertical: string;
  contract_version: string;
  runtime_mode: string;
  table_count: number;
  route_count: number;
  permission_count: number;
  planned_route_count: number;
  data_source: string;
  boundary_summary: Record<string, boolean>;
}

export interface FpaReadiness extends FpaSafetyFlags {
  contract_version: string;
  runtime_mode: string;
  backend_route_count: number;
  backend_permission_count: number;
  provider_profiles: FpaProviderProfile[];
  bridge_targets: string[];
}

export interface FpaDashboardSummary extends FpaSafetyFlags {
  tenant_id: number;
  generated_at: string | null;
  contract_version: string;
  source_backend_baseline_commit: string;
  source_backend_runtime_commit: string;
  data_source: string;
  billing_summary: Record<string, number>;
  receivables_summary: Record<string, number>;
  budget_summary: Record<string, number>;
  procurement_summary: Record<string, number>;
  vendor_summary: Record<string, number>;
  asset_summary: Record<string, number>;
  readiness_summary: Record<string, number>;
  bridge_summary: Record<string, number>;
  audit_summary: Record<string, number>;
  boundary_summary: Record<string, boolean>;
}

export interface FpaBillingVisibility extends FpaMetadataEntity {
  billing_ref?: string | null;
}

export interface FpaReceivablesMetadata extends FpaMetadataEntity {
  receivables_ref?: string | null;
}

export interface FpaBudgetPlan extends FpaMetadataEntity {
  budget_plan_ref?: string | null;
  fiscal_year?: number | null;
}

export interface FpaBudgetControl extends FpaMetadataEntity {
  budget_control_ref?: string | null;
}

export interface FpaProcurementRequest extends FpaMetadataEntity {
  procurement_request_ref?: string | null;
}

export interface FpaProcurementReview extends FpaMetadataEntity {
  procurement_review_ref?: string | null;
}

export interface FpaVendorMetadata extends FpaMetadataEntity {
  vendor_ref?: string | null;
}

export interface FpaContractEvidence extends FpaMetadataEntity {
  contract_ref?: string | null;
}

export interface FpaPurchaseRequest extends FpaMetadataEntity {
  purchase_request_ref?: string | null;
}

export interface FpaPurchaseOrderMetadata extends FpaMetadataEntity {
  purchase_order_ref?: string | null;
}

export interface FpaAssetVisibility extends FpaMetadataEntity {
  asset_ref?: string | null;
}

export interface FpaAssetLifecycle extends FpaMetadataEntity {
  asset_lifecycle_ref?: string | null;
}

export interface FpaInventoryMovementMetadata extends FpaMetadataEntity {
  inventory_movement_ref?: string | null;
}

export interface FpaPaymentReadiness extends FpaMetadataEntity {
  payment_readiness_ref?: string | null;
}

export interface FpaErpReadiness extends FpaMetadataEntity {
  erp_readiness_ref?: string | null;
}

export interface FpaBankReadiness extends FpaMetadataEntity {
  bank_readiness_ref?: string | null;
}

export interface FpaPaymentGatewayReadiness extends FpaMetadataEntity {
  payment_gateway_readiness_ref?: string | null;
}

export interface FpaProviderReadiness extends FpaMetadataEntity {
  provider_readiness_ref?: string | null;
  provider_key?: string | null;
}

export interface FpaAuditEvent extends FpaMetadataEntity {
  event_type?: string | null;
  actor_ref?: string | null;
}

export interface FpaEvidenceItem extends FpaMetadataEntity {
  evidence_ref?: string | null;
  entity_type?: string | null;
}

export interface FpaBridgeSummary extends FpaSafetyFlags {
  bridge_name: string;
  bridge_title: string;
  connected_module: string;
  read_only: true;
  summary: Record<string, number | string | boolean>;
}

export interface FpaLimitations {
  code: string;
  title: string;
  description: string;
}

export interface FpaMetadataContract extends FpaSafetyFlags {
  module: string;
  route_count: number;
  permission_count: number;
  runtime_mode: string;
  forbidden_actions: string[];
  boundary_labels: string[];
}

export interface FpaPermission {
  key: string;
  value: Permission;
  category: string;
}

export interface FpaRole {
  key: string;
  title: string;
  description: string;
  permissions: Permission[];
}

export interface FpaRouteDefinition {
  key: FpaRouteKey;
  title: string;
  path: string;
  requiredPermission: Permission;
  backendEndpoints: string[];
  boundaryLabels: string[];
  description: string;
  dashboardLike: boolean;
  sensitive: boolean;
  humanReviewRequired: boolean;
  emptyState: string;
  incompleteDataState: string;
  permissionDeniedState: string;
}

export interface FpaDashboardWidget {
  key: string;
  title: string;
  description: string;
  endpointRefs: string[];
  sourcePermission: Permission;
  drilldownPath: string;
  forbiddenAction: string;
  boundaryLabels: string[];
  relatedRoutes: FpaRouteKey[];
}

export interface FpaWorkflowDefinition {
  key: string;
  title: string;
  description: string;
  routeKeys: FpaRouteKey[];
  endpointRefs: string[];
  requiredPermissions: Permission[];
  humanReviewPoint: string;
  noOverclaimBoundary: string;
  futureE2eAssertion: string;
}

export interface FpaProviderProfile {
  key: 'BANK_CORE' | 'ERP_1C' | 'PAYMENT_GATEWAY' | 'HR_PAYROLL_BRIDGE' | 'DOCUMENT_CONTRACTS';
  title: string;
  description: string;
  provider_connected: false;
  live_bank_sync: false;
  live_erp_sync: false;
}
