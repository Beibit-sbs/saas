/**
 * Rector Assignment Types
 * Enums and interfaces matching backend rector_assignment_workflow domain.
 * Status values must match backend AssignmentStatus class exactly (uppercase strings).
 */

// ---------------------------------------------------------------------------
// Enums — must match backend string literals exactly
// ---------------------------------------------------------------------------

export enum AssignmentStatus {
  DRAFT = 'DRAFT',
  ASSIGNED = 'ASSIGNED',
  ACCEPTED = 'ACCEPTED',
  IN_PROGRESS = 'IN_PROGRESS',
  REPORT_SUBMITTED = 'REPORT_SUBMITTED',
  RETURNED_FOR_REVISION = 'RETURNED_FOR_REVISION',
  COMPLETED = 'COMPLETED',
  OVERDUE = 'OVERDUE',
  ESCALATED = 'ESCALATED',
  CANCELLED = 'CANCELLED',
  ARCHIVED = 'ARCHIVED',
}

export enum AssignmentPriority {
  LOW = 'LOW',
  NORMAL = 'NORMAL',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL',
}

export enum RecurrenceType {
  NONE = 'NONE',
  DAILY = 'DAILY',
  WEEKLY = 'WEEKLY',
  MONTHLY = 'MONTHLY',
  CUSTOM = 'CUSTOM',
}

/** Backend ReportStatus: SUBMITTED | RETURNED */
export enum ReportStatus {
  SUBMITTED = 'SUBMITTED',
  RETURNED = 'RETURNED',
}

export enum EvidenceType {
  FILE = 'FILE',
  LINK = 'LINK',
  TEXT = 'TEXT',
}

export enum CommentVisibility {
  INTERNAL = 'INTERNAL',
  ASSIGNEES = 'ASSIGNEES',
  LEADERSHIP = 'LEADERSHIP',
}

export enum AssigneeRole {
  RESPONSIBLE = 'RESPONSIBLE',
  CO_EXECUTOR = 'CO_EXECUTOR',
  OBSERVER = 'OBSERVER',
  CONTROLLER = 'CONTROLLER',
}

// ---------------------------------------------------------------------------
// Core entities
// ---------------------------------------------------------------------------

export interface RectorAssignment {
  id: number;
  tenant_id: number;
  title: string;
  description?: string;
  status: AssignmentStatus;
  priority: AssignmentPriority;
  due_date?: string;           // ISO date string
  responsible_unit_id?: number;
  recurrence_type: RecurrenceType;
  version: number;             // optimistic lock
  is_overdue: boolean;         // computed server-side
  created_by: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  cancelled_at?: string;
  archived_at?: string;
}

export interface AssignmentTask {
  id: number;
  assignment_id: number;
  title: string;
  description?: string;
  is_completed: boolean;
  completed_at?: string;
  completed_by?: number;
  sort_order: number;
}

export interface AssignmentAssignee {
  id: number;
  assignment_id: number;
  user_id: number;
  role_on_assignment: AssigneeRole;
  assigned_at: string;
  is_lead: boolean;
}

export interface AssignmentReport {
  id: number;
  assignment_id: number;
  submitted_by: number;
  reporting_period_start: string;
  reporting_period_end: string;
  progress_percent: number;
  summary: string;
  blockers?: string;
  next_steps?: string;
  status: ReportStatus;
  submitted_at: string;
  reviewed_at?: string;
  reviewed_by?: number;
}

export interface AssignmentEvidence {
  id: number;
  assignment_id: number;
  evidence_type: EvidenceType;
  title: string;
  url?: string;               // HTTPS only for LINK type
  description?: string;
  uploaded_by: number;
  uploaded_at: string;
  report_id?: number;
}

export interface AssignmentComment {
  id: number;
  assignment_id: number;
  author_id: number;
  content: string;
  visibility: CommentVisibility;
  created_at: string;
  updated_at?: string;
}

/** INSERT-ONLY: never updated or deleted */
export interface AssignmentStatusHistory {
  id: number;
  assignment_id: number;
  old_status?: AssignmentStatus;
  new_status: AssignmentStatus;
  changed_by: number;
  changed_at: string;
  reason?: string;
}

export interface AssignmentEscalation {
  id: number;
  assignment_id: number;
  escalated_by: number;
  escalated_to_role: string;
  escalated_to_user_id?: number;
  reason: string;
  is_resolved: boolean;
  resolved_at?: string;
  resolved_by?: number;
  created_at: string;
}

export interface AssignmentTemplate {
  id: number;
  name: string;
  description?: string;
  default_priority: AssignmentPriority;
  default_due_days?: number;
  default_recurrence_type: RecurrenceType;
  template_body?: string;
  is_active: boolean;
  created_by: number;
  created_at: string;
}

/** INSERT-ONLY audit events — no update/delete */
export interface AssignmentAuditEvent {
  id: number;
  assignment_id: number;
  event_type: string;
  actor_id: number;
  request_id?: string;
  payload?: Record<string, unknown>;
  created_at: string;
}

/** Dashboard summary from GET /api/admin/rector-assignments/dashboard/summary */
export interface DashboardSummary {
  tenant_id: number;
  computed_at: string;
  total_assignments: number;
  active_count: number;
  draft_count: number;
  overdue_count: number;
  escalated_count: number;
  completed_count: number;
  cancelled_count: number;
  report_submitted_count: number;
  returned_count: number;
  due_this_week: number;
  due_today: number;
  completion_rate_30d: number;
  average_days_to_complete: number | null;
  by_status: Record<string, number>;
  by_priority: Record<string, number>;
  by_unit: { unit_id: number; unit_name: string; count: number }[];
  top_overdue: Record<string, unknown>[];
  /** MUST always equal "computed_from_assignments" — assert before rendering KPIs */
  data_source: string;
  /** MUST always be false — assert before rendering KPIs */
  fake_metrics: boolean;
}

/** Paginated list response */
export interface AssignmentListResponse {
  items: RectorAssignment[];
  total: number;
  page: number;
  page_size: number;
}

/** Assignment detail response (includes nested relations) */
export interface AssignmentDetailResponse extends RectorAssignment {
  tasks?: AssignmentTask[];
  assignees?: AssignmentAssignee[];
}

// ---------------------------------------------------------------------------
// List filters
// ---------------------------------------------------------------------------

export interface AssignmentListFilters {
  status?: AssignmentStatus | 'all';
  priority?: AssignmentPriority;
  unit_id?: number;
  assignee_id?: number;
  overdue_only?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
  my_assignments?: boolean;
}

// ---------------------------------------------------------------------------
// Payload types — sent to backend on write operations
// ---------------------------------------------------------------------------

export interface AssignmentCreatePayload {
  title: string;
  description?: string;
  priority: AssignmentPriority;
  due_date?: string;
  responsible_unit_id?: number;
  assignee_ids?: number[];
  tasks?: { title: string; description?: string; sort_order?: number }[];
  template_id?: number;
  recurrence_type?: RecurrenceType;
  publish_now?: boolean;
}

export interface AssignmentUpdatePayload {
  title?: string;
  description?: string;
  priority?: AssignmentPriority;
  due_date?: string;
  responsible_unit_id?: number;
  recurrence_type?: RecurrenceType;
}

export interface AssignmentReportCreatePayload {
  reporting_period_start: string;
  reporting_period_end: string;
  progress_percent: number;
  summary: string;
  blockers?: string;
  next_steps?: string;
}

export interface EvidenceCreatePayload {
  evidence_type: EvidenceType;
  title: string;
  url?: string;
  description?: string;
  report_id?: number;
}

export interface CommentCreatePayload {
  content: string;
  visibility?: CommentVisibility;
}

export interface StatusActionPayload {
  reason?: string;
  assignee_ids?: number[];
}

export interface AssignmentTemplateCreatePayload {
  name: string;
  description?: string;
  default_priority?: AssignmentPriority;
  default_due_days?: number;
  default_recurrence_type?: RecurrenceType;
  template_body?: string;
  is_active?: boolean;
}

export interface AssignmentTemplateUpdatePayload {
  name?: string;
  description?: string;
  default_priority?: AssignmentPriority;
  default_due_days?: number;
  default_recurrence_type?: RecurrenceType;
  template_body?: string;
  is_active?: boolean;
}
