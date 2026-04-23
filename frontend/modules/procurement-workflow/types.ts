/**
 * Procurement Workflow Types
 * Defines interfaces for request-to-order lifecycle and audit trail
 */

export enum ProcurementStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  UNDER_REVIEW = 'under_review',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  ORDERED = 'ordered',
  FULFILLED = 'fulfilled',
  CANCELLED = 'cancelled',
}

export enum ProcurementPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export enum ProcurementCategory {
  EQUIPMENT = 'equipment',
  SOFTWARE = 'software',
  SERVICES = 'services',
  FACILITIES = 'facilities',
  SUPPLIES = 'supplies',
  OTHER = 'other',
}

export interface VendorMetadata {
  vendor_id: string;
  vendor_name: string;
  contact_email?: string;
  contact_phone?: string;
  preferred: boolean;
  created_at: string;
}

export interface RequestItem {
  item_id: string;
  request_id: string;
  sku?: string;
  description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  category: ProcurementCategory;
}

export interface ApprovalStep {
  step_id: string;
  request_id: string;
  sequence: number;
  approver_id: string;
  approver_name: string;
  status: 'pending' | 'approved' | 'rejected' | 'skipped';
  decision_at?: string;
  comment?: string;
}

export interface ProcurementRequest {
  request_id: string;
  request_number: string;
  requester_id: string;
  requester_name: string;
  department_id: string;
  department_name: string;
  title: string;
  description?: string;
  status: ProcurementStatus;
  priority: ProcurementPriority;
  estimated_total: number;
  currency: string;
  needed_by_date?: string;
  created_at: string;
  updated_at: string;
  submitted_at?: string;
}

export interface ProcurementOrder {
  order_id: string;
  request_id: string;
  vendor_id: string;
  vendor_name: string;
  order_number: string;
  order_date: string;
  expected_delivery_date?: string;
  total_amount: number;
  currency: string;
  status: 'issued' | 'partially_received' | 'received' | 'cancelled';
}

export interface ProcurementAuditEntry {
  audit_id: string;
  request_id: string;
  action: string;
  actor_id: string;
  actor_name: string;
  from_status?: ProcurementStatus;
  to_status?: ProcurementStatus;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface ProcurementDashboardSummary {
  total_requests: number;
  status_breakdown: {
    draft: number;
    submitted: number;
    under_review: number;
    approved: number;
    rejected: number;
    ordered: number;
    fulfilled: number;
  };
  total_pending_approvals: number;
  total_ordered_value: number;
  overdue_requests: number;
  last_updated: string;
}

export interface ProcurementListItem {
  request_id: string;
  request_number: string;
  title: string;
  requester_name: string;
  department_name: string;
  status: ProcurementStatus;
  priority: ProcurementPriority;
  estimated_total: number;
  created_at: string;
  updated_at: string;
}

export interface ProcurementRequestCreatePayload {
  department_id: string;
  title: string;
  description?: string;
  priority: ProcurementPriority;
  needed_by_date?: string;
  items: Array<{
    description: string;
    quantity: number;
    unit_price: number;
    category: ProcurementCategory;
  }>;
}

export interface ProcurementRequestUpdatePayload {
  title?: string;
  description?: string;
  priority?: ProcurementPriority;
  needed_by_date?: string;
}

export interface ProcurementStatusUpdatePayload {
  status: ProcurementStatus;
  comment?: string;
}

export interface ProcurementOrderCreatePayload {
  request_id: string;
  vendor_id: string;
  order_number: string;
  expected_delivery_date?: string;
}
