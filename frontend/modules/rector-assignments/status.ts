/**
 * Rector Assignment Status Helpers
 * Label maps, badge variant maps, and lifecycle logic for the UI.
 */

import { AssignmentStatus } from './types';

// ---------------------------------------------------------------------------
// Status label map
// ---------------------------------------------------------------------------

export const STATUS_LABELS: Record<AssignmentStatus, string> = {
  [AssignmentStatus.DRAFT]: 'Draft',
  [AssignmentStatus.ASSIGNED]: 'Assigned',
  [AssignmentStatus.ACCEPTED]: 'Accepted',
  [AssignmentStatus.IN_PROGRESS]: 'In Progress',
  [AssignmentStatus.REPORT_SUBMITTED]: 'Report Submitted',
  [AssignmentStatus.RETURNED_FOR_REVISION]: 'Returned for Revision',
  [AssignmentStatus.COMPLETED]: 'Completed',
  [AssignmentStatus.OVERDUE]: 'Overdue',
  [AssignmentStatus.ESCALATED]: 'Escalated',
  [AssignmentStatus.CANCELLED]: 'Cancelled',
  [AssignmentStatus.ARCHIVED]: 'Archived',
};

// ---------------------------------------------------------------------------
// Badge variant map (maps to existing Badge component variants)
// ---------------------------------------------------------------------------

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'success' | 'info' | 'warning';

export const STATUS_BADGE_VARIANTS: Record<AssignmentStatus, BadgeVariant> = {
  [AssignmentStatus.DRAFT]: 'secondary',
  [AssignmentStatus.ASSIGNED]: 'info',
  [AssignmentStatus.ACCEPTED]: 'info',
  [AssignmentStatus.IN_PROGRESS]: 'info',
  [AssignmentStatus.REPORT_SUBMITTED]: 'warning',
  [AssignmentStatus.RETURNED_FOR_REVISION]: 'warning',
  [AssignmentStatus.COMPLETED]: 'success',
  [AssignmentStatus.OVERDUE]: 'destructive',
  [AssignmentStatus.ESCALATED]: 'destructive',
  [AssignmentStatus.CANCELLED]: 'secondary',
  [AssignmentStatus.ARCHIVED]: 'secondary',
};

// ---------------------------------------------------------------------------
// Lifecycle order (for timeline display)
// ---------------------------------------------------------------------------

export const STATUS_ORDER: AssignmentStatus[] = [
  AssignmentStatus.DRAFT,
  AssignmentStatus.ASSIGNED,
  AssignmentStatus.ACCEPTED,
  AssignmentStatus.IN_PROGRESS,
  AssignmentStatus.REPORT_SUBMITTED,
  AssignmentStatus.COMPLETED,
];

// ---------------------------------------------------------------------------
// Predicate helpers
// ---------------------------------------------------------------------------

const TERMINAL_STATUSES = new Set<AssignmentStatus>([
  AssignmentStatus.COMPLETED,
  AssignmentStatus.CANCELLED,
  AssignmentStatus.ARCHIVED,
]);

export function isTerminalStatus(status: AssignmentStatus): boolean {
  return TERMINAL_STATUSES.has(status);
}

const REPORT_ELIGIBLE_STATUSES = new Set<AssignmentStatus>([
  AssignmentStatus.ACCEPTED,
  AssignmentStatus.IN_PROGRESS,
  AssignmentStatus.RETURNED_FOR_REVISION,
  AssignmentStatus.OVERDUE,
  AssignmentStatus.ESCALATED,
]);

export function canSubmitReportByStatus(status: AssignmentStatus): boolean {
  return REPORT_ELIGIBLE_STATUSES.has(status);
}

const ARCHIVE_ELIGIBLE_STATUSES = new Set<AssignmentStatus>([
  AssignmentStatus.COMPLETED,
  AssignmentStatus.CANCELLED,
]);

export function canArchiveByStatus(status: AssignmentStatus): boolean {
  return ARCHIVE_ELIGIBLE_STATUSES.has(status);
}

const CANCEL_ELIGIBLE_STATUSES = new Set<AssignmentStatus>([
  AssignmentStatus.DRAFT,
  AssignmentStatus.ASSIGNED,
  AssignmentStatus.ACCEPTED,
  AssignmentStatus.IN_PROGRESS,
]);

export function canCancelByStatus(status: AssignmentStatus): boolean {
  return CANCEL_ELIGIBLE_STATUSES.has(status);
}

const ESCALATE_ELIGIBLE_STATUSES = new Set<AssignmentStatus>([
  AssignmentStatus.OVERDUE,
  AssignmentStatus.IN_PROGRESS,
  AssignmentStatus.ACCEPTED,
]);

export function canEscalateByStatus(status: AssignmentStatus): boolean {
  return ESCALATE_ELIGIBLE_STATUSES.has(status);
}

export function canReturnByStatus(status: AssignmentStatus): boolean {
  return status === AssignmentStatus.REPORT_SUBMITTED;
}

export function canCompleteByStatus(status: AssignmentStatus): boolean {
  return (
    status === AssignmentStatus.REPORT_SUBMITTED ||
    status === AssignmentStatus.ESCALATED
  );
}

export function canAssignByStatus(status: AssignmentStatus): boolean {
  return status === AssignmentStatus.DRAFT;
}

export function canAcceptByStatus(status: AssignmentStatus): boolean {
  return status === AssignmentStatus.ASSIGNED;
}
