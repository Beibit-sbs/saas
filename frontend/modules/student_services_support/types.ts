import type { Permission } from '@/shared/config/permissions';

export type StudentServicesSupportRouteKey =
  | 'overview'
  | 'requests'
  | 'request-detail'
  | 'cases'
  | 'case-detail'
  | 'hardship'
  | 'accommodations'
  | 'complaints'
  | 'escalations'
  | 'dashboard';

export interface StudentServicesSafetyFlags {
  fake_metrics: false;
  provider_live_enabled: false;
  autonomous_decision_enabled: false;
  hidden_score_present: false;
  human_review_required: true;
  incomplete_data: boolean;
}

export interface StudentServicesModuleBase extends StudentServicesSafetyFlags {
  tenant_id: number;
  module: string;
  contract_version: string;
  runtime_mode: string;
}

export type SupportPriority = 'low' | 'medium' | 'high' | 'critical';

export interface ServiceRequestRecord {
  id: number;
  tenant_id: number;
  request_type: string;
  status: string;
  support_priority: SupportPriority;
  student_id: string;
  assigned_to_user_id?: string | null;
  subject?: string | null;
  description?: string | null;
  metadata?: Record<string, unknown>;
}

export interface SupportCaseRecord {
  id: number;
  tenant_id: number;
  case_type: string;
  status: string;
  request_id?: number | null;
  assigned_to_user_id?: string | null;
  title?: string | null;
  metadata?: Record<string, unknown>;
}

export interface SupportCaseNoteRecord {
  id: number;
  tenant_id: number;
  case_id: number;
  note: string;
  metadata?: Record<string, unknown>;
}

export interface SupportEvidenceRecord {
  id: number;
  tenant_id: number;
  case_id: number;
  evidence_type: string;
  evidence_ref?: string | null;
  source_available: boolean;
  limitations?: string | null;
  metadata?: Record<string, unknown>;
}

export interface ReadinessRecord {
  id: number;
  tenant_id: number;
  request_id?: number | null;
  status: string;
  readiness_status: string;
  missing_evidence: string[];
  recommended_next_step?: string | null;
}

export interface ComplaintRecord {
  id: number;
  tenant_id: number;
  status: string;
  request_id?: number | null;
  routed_to?: string | null;
  complaint_summary?: string | null;
  metadata?: Record<string, unknown>;
}

export interface EscalationRecord {
  id: number;
  tenant_id: number;
  case_id: number;
  escalation_status: string;
  reason: string;
  metadata?: Record<string, unknown>;
}

export interface DashboardSummary extends StudentServicesModuleBase {
  data_source: string;
  open_requests: number;
  open_support_cases: number;
  escalated_cases: number;
  hardship_readiness_counts: Record<string, number>;
  accommodation_readiness_counts: Record<string, number>;
  complaint_counts: Record<string, number>;
}

export interface ServiceRequestListResponse extends StudentServicesModuleBase {
  items: ServiceRequestRecord[];
}

export interface ServiceRequestItemResponse extends StudentServicesModuleBase {
  item: ServiceRequestRecord;
}

export interface SupportCaseListResponse extends StudentServicesModuleBase {
  items: SupportCaseRecord[];
}

export interface SupportCaseItemResponse extends StudentServicesModuleBase {
  item: SupportCaseRecord;
}

export interface SupportCaseNoteItemResponse extends StudentServicesModuleBase {
  item: SupportCaseNoteRecord;
}

export interface SupportEvidenceItemResponse extends StudentServicesModuleBase {
  item: SupportEvidenceRecord;
}

export interface ReadinessItemResponse extends StudentServicesModuleBase {
  item: ReadinessRecord;
}

export interface ComplaintItemResponse extends StudentServicesModuleBase {
  item: ComplaintRecord;
}

export interface EscalationItemResponse extends StudentServicesModuleBase {
  item: EscalationRecord;
}

export interface ServiceRequestCreatePayload {
  request_type: string;
  student_id: string;
  support_priority?: SupportPriority;
  subject?: string | null;
  description?: string | null;
  metadata?: Record<string, unknown>;
}

export interface ServiceRequestAssignPayload {
  assigned_to_user_id: string;
}

export interface ServiceRequestStatusPayload {
  status: string;
  reason?: string | null;
}

export interface SupportCaseCreatePayload {
  case_type: string;
  request_id?: number | null;
  title?: string | null;
  assigned_to_user_id?: string | null;
  metadata?: Record<string, unknown>;
}

export interface SupportCaseNoteCreatePayload {
  note: string;
  metadata?: Record<string, unknown>;
}

export interface SupportEvidenceCreatePayload {
  evidence_type: string;
  evidence_ref?: string | null;
  source_available?: boolean;
  limitations?: string | null;
  metadata?: Record<string, unknown>;
}

export interface HardshipCreatePayload {
  request_id?: number | null;
  evidence_refs?: string[];
  metadata?: Record<string, unknown>;
}

export interface AccommodationCreatePayload {
  request_id?: number | null;
  evidence_refs?: string[];
  metadata?: Record<string, unknown>;
}

export interface ComplaintCreatePayload {
  request_id?: number | null;
  complaint_summary: string;
  route_to?: string | null;
  metadata?: Record<string, unknown>;
}

export interface EscalationCreatePayload {
  case_id: number;
  reason: string;
  metadata?: Record<string, unknown>;
}

export interface StudentServicesSupportRouteDefinition {
  key: StudentServicesSupportRouteKey;
  title: string;
  path: string;
  requiredPermission: Permission;
  backendEndpoints: string[];
  dashboardLike: boolean;
  emptyState: string;
  permissionDeniedState: string;
}
