export enum DocumentStatus {
  DRAFT = 'DRAFT',
  REGISTERED = 'REGISTERED',
  UNDER_REVIEW = 'UNDER_REVIEW',
  RETURNED_FOR_REVISION = 'RETURNED_FOR_REVISION',
  APPROVED = 'APPROVED',
  SIGNED = 'SIGNED',
  ISSUED = 'ISSUED',
  LINKED_TO_ASSIGNMENT = 'LINKED_TO_ASSIGNMENT',
  IN_EXECUTION = 'IN_EXECUTION',
  EXECUTION_REPORTED = 'EXECUTION_REPORTED',
  ARCHIVED = 'ARCHIVED',
  CANCELLED = 'CANCELLED',
}

export enum DecreeStatus {
  DRAFT_ORDER = 'DRAFT_ORDER',
  LEGAL_REVIEW = 'LEGAL_REVIEW',
  RECTOR_REVIEW = 'RECTOR_REVIEW',
  APPROVED_FOR_SIGNING = 'APPROVED_FOR_SIGNING',
  SIGNED = 'SIGNED',
  REGISTERED = 'REGISTERED',
  PUBLISHED_INTERNAL = 'PUBLISHED_INTERNAL',
  ASSIGNED_FOR_EXECUTION = 'ASSIGNED_FOR_EXECUTION',
  EXECUTION_TRACKED = 'EXECUTION_TRACKED',
  COMPLETED = 'COMPLETED',
  ARCHIVED = 'ARCHIVED',
  CANCELLED = 'CANCELLED',
}

export enum CorrespondenceDirection {
  INCOMING = 'INCOMING',
  OUTGOING = 'OUTGOING',
}

export enum IncomingCorrespondenceStatus {
  RECEIVED = 'RECEIVED',
  REGISTERED = 'REGISTERED',
  CLASSIFIED = 'CLASSIFIED',
  ROUTED = 'ROUTED',
  ASSIGNED = 'ASSIGNED',
  IN_PROGRESS = 'IN_PROGRESS',
  RESPONDED = 'RESPONDED',
  ARCHIVED = 'ARCHIVED',
}

export enum OutgoingCorrespondenceStatus {
  DRAFT = 'DRAFT',
  UNDER_REVIEW = 'UNDER_REVIEW',
  APPROVED = 'APPROVED',
  REGISTERED = 'REGISTERED',
  SENT_METADATA_ONLY = 'SENT_METADATA_ONLY',
  DELIVERED_METADATA_ONLY = 'DELIVERED_METADATA_ONLY',
  ARCHIVED = 'ARCHIVED',
}

export enum DocumentType {
  INTERNAL_MEMO = 'INTERNAL_MEMO',
  ORDER = 'ORDER',
  DECREE = 'DECREE',
  LETTER = 'LETTER',
  PROTOCOL = 'PROTOCOL',
  RESOLUTION = 'RESOLUTION',
  REPORT = 'REPORT',
  OTHER = 'OTHER',
  CORRESPONDENCE = 'CORRESPONDENCE',
}

export enum ReviewDecision {
  APPROVED = 'APPROVED',
  RETURNED_FOR_REVISION = 'RETURNED_FOR_REVISION',
  REJECTED_METADATA_ONLY = 'REJECTED_METADATA_ONLY',
}

export enum AuditEventType {
  DOCUMENT_CREATED = 'DOCUMENT_CREATED',
  DOCUMENT_UPDATED = 'DOCUMENT_UPDATED',
  DOCUMENT_REGISTERED = 'DOCUMENT_REGISTERED',
  DOCUMENT_SUBMITTED_FOR_REVIEW = 'DOCUMENT_SUBMITTED_FOR_REVIEW',
  DOCUMENT_RETURNED = 'DOCUMENT_RETURNED',
  DOCUMENT_APPROVED = 'DOCUMENT_APPROVED',
  DOCUMENT_SIGNED_METADATA_RECORDED = 'DOCUMENT_SIGNED_METADATA_RECORDED',
  DOCUMENT_ISSUED = 'DOCUMENT_ISSUED',
  DOCUMENT_ARCHIVED = 'DOCUMENT_ARCHIVED',
  DOCUMENT_CANCELLED = 'DOCUMENT_CANCELLED',
  DOCUMENT_ASSIGNMENT_LINKED = 'DOCUMENT_ASSIGNMENT_LINKED',
  DECREE_CREATED = 'DECREE_CREATED',
  DECREE_UPDATED = 'DECREE_UPDATED',
  DECREE_LEGAL_REVIEW_STARTED = 'DECREE_LEGAL_REVIEW_STARTED',
  DECREE_APPROVED_FOR_SIGNING = 'DECREE_APPROVED_FOR_SIGNING',
  DECREE_SIGNED_METADATA_RECORDED = 'DECREE_SIGNED_METADATA_RECORDED',
  DECREE_REGISTERED = 'DECREE_REGISTERED',
  DECREE_ARCHIVED = 'DECREE_ARCHIVED',
  DECREE_CANCELLED = 'DECREE_CANCELLED',
  CORRESPONDENCE_REGISTERED = 'CORRESPONDENCE_REGISTERED',
  CORRESPONDENCE_ROUTED = 'CORRESPONDENCE_ROUTED',
  CORRESPONDENCE_SENT_METADATA_RECORDED = 'CORRESPONDENCE_SENT_METADATA_RECORDED',
  CORRESPONDENCE_ARCHIVED = 'CORRESPONDENCE_ARCHIVED',
  RESOLUTION_CREATED = 'RESOLUTION_CREATED',
  RESOLUTION_ASSIGNMENT_LINKED = 'RESOLUTION_ASSIGNMENT_LINKED',
  ASSIGNMENT_LINKED = 'ASSIGNMENT_LINKED',
  DASHBOARD_VIEWED = 'DASHBOARD_VIEWED',
  ARCHIVE_RECORDED = 'ARCHIVE_RECORDED',
}

export interface DocumentVersion {
  id: number;
  document_id: number;
  version_number: number;
  title: string;
  body_text?: string | null;
  metadata_json: Record<string, unknown>;
  created_by_user_id: number;
  created_at: string;
}

export interface DocumentStatusHistory {
  id: number;
  document_id: number;
  from_status?: string | null;
  to_status: string;
  actor_user_id: number;
  reason?: string | null;
  created_at: string;
}

export interface DocumentAuditEvent {
  id: number;
  entity_type: string;
  entity_id: number;
  event_type: string;
  actor_user_id: number;
  actor_role?: string | null;
  action: string;
  payload_json: Record<string, unknown>;
  created_at: string;
}

export interface DocumentReview {
  id: number;
  document_id: number;
  reviewer_user_id: number;
  decision: string;
  comment?: string | null;
  created_at: string;
}

export interface DocumentAssignmentLink {
  id: number;
  document_id: number;
  assignment_id: number;
  link_type: string;
  created_by_user_id: number;
  created_at: string;
}

export interface Document {
  id: number;
  tenant_id: number;
  title: string;
  document_type: string;
  status: string;
  registry_number?: string | null;
  registry_date?: string | null;
  source_department_id?: number | null;
  owner_user_id?: number | null;
  created_by_user_id: number;
  linked_assignment_id?: number | null;
  linked_decree_id?: number | null;
  version: number;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
}

export interface DocumentDetail extends Document {
  versions: DocumentVersion[];
  reviews: DocumentReview[];
  assignment_links: DocumentAssignmentLink[];
}

export interface OrderDecree {
  id: number;
  tenant_id: number;
  title: string;
  decree_type: string;
  status: string;
  registry_number?: string | null;
  registry_date?: string | null;
  effective_date?: string | null;
  signed_by_user_id?: number | null;
  signed_at?: string | null;
  linked_document_id?: number | null;
  linked_assignment_id?: number | null;
  created_by_user_id: number;
  version: number;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
}

export interface CorrespondenceItem {
  id: number;
  tenant_id: number;
  direction: string;
  subject: string;
  correspondence_type: string;
  sender_name?: string | null;
  sender_organization?: string | null;
  recipient_name?: string | null;
  recipient_organization?: string | null;
  status: string;
  registry_number?: string | null;
  registry_date?: string | null;
  received_at?: string | null;
  sent_at?: string | null;
  linked_document_id?: number | null;
  linked_assignment_id?: number | null;
  created_by_user_id: number;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
}

export interface CorrespondenceRoute {
  id: number;
  correspondence_id: number;
  from_user_id?: number | null;
  to_user_id?: number | null;
  to_role?: string | null;
  route_comment?: string | null;
  created_by_user_id: number;
  created_at: string;
}

export interface Resolution {
  id: number;
  tenant_id: number;
  title: string;
  text: string;
  status: string;
  created_by_user_id: number;
  assigned_to_user_id?: number | null;
  linked_document_id?: number | null;
  linked_decree_id?: number | null;
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
}

export interface ResolutionAssignmentLink {
  id: number;
  resolution_id: number;
  assignment_id: number;
  created_by_user_id: number;
  created_at: string;
}

export interface ArchiveRecord {
  kind: 'document' | 'decree' | 'correspondence';
  id: number;
  title: string;
  status: string;
  archived_at?: string | null;
  registry_number?: string | null;
}

export interface DashboardSummary {
  tenant_id: number;
  total_documents: number;
  registered_documents: number;
  under_review_count: number;
  returned_for_revision_count: number;
  approved_count: number;
  signed_count: number;
  archived_count: number;
  incoming_correspondence_count: number;
  outgoing_correspondence_count: number;
  overdue_document_reviews: number;
  documents_linked_to_assignments: number;
  decrees_pending_signature: number;
  average_review_cycle_days?: number | null;
  data_source: string;
  fake_metrics: boolean;
  generated_at: string;
  incomplete_data: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export type DocumentListResponse = PaginatedResponse<Document>;
export type DecreeListResponse = PaginatedResponse<OrderDecree>;
export type CorrespondenceListResponse = PaginatedResponse<CorrespondenceItem>;

export interface DocumentListFilters {
  status?: string;
  document_type?: string;
  page?: number;
  page_size?: number;
}

export interface DecreeListFilters {
  status?: string;
  decree_type?: string;
  page?: number;
  page_size?: number;
}

export interface CorrespondenceListFilters {
  direction?: string;
  status?: string;
  page?: number;
  page_size?: number;
}

export interface DocumentCreatePayload {
  title: string;
  document_type: string;
  source_department_id?: number;
  owner_user_id?: number;
  linked_assignment_id?: number;
}

export interface DocumentUpdatePayload {
  title?: string;
  document_type?: string;
  owner_user_id?: number;
  version: number;
}

export interface DocumentRegisterPayload {
  registry_number: string;
  registry_date?: string;
  version: number;
}

export interface DocumentReviewPayload {
  reviewer_user_id?: number;
  note?: string;
  version: number;
}

export interface DocumentReturnPayload {
  reason: string;
  version: number;
}

export interface DocumentApprovePayload {
  comment?: string;
  version: number;
}

export interface DocumentSignedMetadataPayload {
  signed_by_user_id: number;
  signed_at?: string;
  note?: string;
  version: number;
}

export interface DocumentArchivePayload {
  reason?: string;
  version: number;
}

export interface DecreeCreatePayload {
  title: string;
  decree_type: string;
  effective_date?: string;
  linked_document_id?: number;
}

export interface DecreeUpdatePayload {
  title?: string;
  effective_date?: string;
  version: number;
}

export interface DecreeLegalReviewPayload {
  note?: string;
  version: number;
}

export interface DecreeApprovePayload {
  comment?: string;
  version: number;
}

export interface DecreeSignedMetadataPayload {
  signed_by_user_id: number;
  signed_at?: string;
  version: number;
}

export interface DecreeRegisterPayload {
  registry_number: string;
  registry_date?: string;
  version: number;
}

export interface DecreeArchivePayload {
  reason?: string;
  version: number;
}

export interface CorrespondenceIncomingCreatePayload {
  subject: string;
  correspondence_type?: string;
  sender_name?: string;
  sender_organization?: string;
  received_at?: string;
  linked_document_id?: number;
}

export interface CorrespondenceOutgoingCreatePayload {
  subject: string;
  correspondence_type?: string;
  recipient_name?: string;
  recipient_organization?: string;
  linked_document_id?: number;
}

export interface CorrespondenceRegisterPayload {
  registry_number: string;
  registry_date?: string;
}

export interface CorrespondenceRoutePayload {
  to_user_id?: number;
  to_role?: string;
  route_comment?: string;
}

export interface CorrespondenceArchivePayload {
  reason?: string;
}

export interface ResolutionCreatePayload {
  title: string;
  text: string;
  assigned_to_user_id?: number;
  linked_document_id?: number;
  linked_decree_id?: number;
}

export interface LinkAssignmentPayload {
  link_type?: 'SOURCE_DOCUMENT' | 'EXECUTION_DOCUMENT' | 'EVIDENCE';
}