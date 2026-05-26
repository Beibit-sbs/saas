import type { Permission } from '@/shared/config/permissions';

export type DdcRouteKey =
  | 'overview'
  | 'dashboard'
  | 'documents'
  | 'intake'
  | 'routing'
  | 'rector-resolutions'
  | 'decrees'
  | 'decree-drafts'
  | 'incoming'
  | 'outgoing'
  | 'templates'
  | 'committee-decisions'
  | 'assignments'
  | 'execution-control'
  | 'sla-deadlines'
  | 'evidence'
  | 'attachments'
  | 'audit'
  | 'archive'
  | 'signature-readiness'
  | 'delivery-readiness'
  | 'bridges'
  | 'limitations';

export interface DdcSafetyFlags {
  fake_documents: false;
  fake_decrees: false;
  fake_signatures: false;
  fake_delivery_confirmations: false;
  fake_archive_legal_record: false;
  official_legal_effect: false;
  external_submission_enabled: false;
  automatic_rector_decision_enabled: false;
  automatic_decree_approval_enabled: false;
  automatic_document_signing_enabled: false;
  hidden_score_present: false;
  human_review_required: true;
  incomplete_data: boolean;
  limitations: string[];
}

export interface DdcApiResult<T> {
  items: T[];
}

export interface DdcMetadataEntity extends DdcSafetyFlags {
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
  source_module?: string | null;
  source_record_id?: number | string | null;
  reference_uri?: string | null;
  read_only_first?: boolean;
  mutation_allowed?: boolean;
}

export interface DdcOverview extends DdcSafetyFlags {
  tenant_id: number;
  module: string;
  product_vertical: string;
  runtime_mode: string;
  table_count: number;
  route_count: number;
  permission_count: number;
  planned_route_count: number;
  backend_route_count: number;
  backend_permission_count: number;
  boundary_summary: Record<string, boolean>;
}

export interface DdcReadiness extends DdcSafetyFlags {
  runtime_mode: string;
  backend_route_count: number;
  backend_permission_count: number;
  bridge_targets: string[];
  statuses: Record<string, string>;
}

export interface DdcDashboard extends DdcSafetyFlags {
  tenant_id: number;
  generated_at: string | null;
  route_count: number;
  permission_count: number;
  cards: Record<string, number>;
  boundary_summary: Record<string, boolean>;
}

export interface DdcDocumentIntake extends DdcMetadataEntity {
  intake_channel?: string | null;
}

export interface DdcDocumentRegistration extends DdcMetadataEntity {
  registry_number?: string | null;
}

export interface DdcDocumentRouting extends DdcMetadataEntity {
  routed_to?: string | null;
}

export interface DdcRectorResolution extends DdcMetadataEntity {
  resolution_state?: string | null;
}

export interface DdcDecreeRegistry extends DdcMetadataEntity {
  decree_type?: string | null;
}

export interface DdcDecreeDraft extends DdcMetadataEntity {
  draft_version?: number | null;
}

export interface DdcIncomingCorrespondence extends DdcMetadataEntity {
  sender_name?: string | null;
}

export interface DdcOutgoingCorrespondence extends DdcMetadataEntity {
  recipient_name?: string | null;
}

export interface DdcTemplateMetadata extends DdcMetadataEntity {
  template_type?: string | null;
}

export interface DdcCommitteeDecisionBridge extends DdcMetadataEntity {
  committee_reference?: string | null;
}

export interface DdcAssignmentBridge extends DdcMetadataEntity {
  assignment_reference?: string | null;
}

export interface DdcExecutionControl extends DdcMetadataEntity {
  control_state?: string | null;
}

export interface DdcSlaDeadline extends DdcMetadataEntity {
  deadline_label?: string | null;
}

export interface DdcEvidenceItem extends DdcMetadataEntity {
  evidence_type?: string | null;
}

export interface DdcAttachmentMetadata extends DdcMetadataEntity {
  attachment_uri?: string | null;
}

export interface DdcAuditEvent extends DdcMetadataEntity {
  entity_type?: string | null;
  action?: string | null;
}

export interface DdcArchiveReadiness extends DdcMetadataEntity {
  archive_scope?: string | null;
}

export interface DdcRetentionMetadata extends DdcMetadataEntity {
  retention_rule?: string | null;
}

export interface DdcSignatureReadiness extends DdcMetadataEntity {
  provider_name?: string | null;
}

export interface DdcDeliveryReadiness extends DdcMetadataEntity {
  provider_name?: string | null;
}

export interface DdcBridge extends DdcMetadataEntity {
  bridge_family?: string | null;
  target_domain?: string | null;
}

export interface DdcLimitations {
  code: string;
  title: string;
  description: string;
}

export interface DdcMetadataContract extends DdcSafetyFlags {
  module: string;
  route_count: number;
  permission_count: number;
  runtime_mode: string;
  forbidden_actions: string[];
  boundary_labels: string[];
}

export interface DdcPermission {
  key: string;
  value: Permission;
  category: string;
}

export interface DdcRole {
  key: string;
  title: string;
  description: string;
  permissions: Permission[];
}

export interface DdcRouteDefinition {
  key: DdcRouteKey;
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

export interface DdcDashboardWidget {
  key: string;
  title: string;
  description: string;
  endpointRefs: string[];
  sourcePermission: Permission;
  drilldownPath: string;
  forbiddenAction: string;
  boundaryLabels: string[];
  relatedRoutes: DdcRouteKey[];
}

export interface DdcWorkflowDefinition {
  key: string;
  title: string;
  description: string;
  routeKeys: DdcRouteKey[];
  endpointRefs: string[];
  requiredPermissions: Permission[];
  humanReviewPoint: string;
  noOverclaimBoundary: string;
  futureE2eAssertion: string;
}
