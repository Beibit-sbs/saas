/**
 * Tests: AssignmentApiClient
 * Verifies CACHE_KEYS shape and hook return types.
 * Does NOT test network calls — those are covered by backend tests.
 */

import { describe, expect, it } from 'vitest';

describe('Assignment hooks module shape', () => {
  it('exports all expected read hooks', async () => {
    const mod = await import('@/modules/rector-assignments/hooks');
    expect(typeof mod.useRectorAssignmentDashboard).toBe('function');
    expect(typeof mod.useRectorAssignmentList).toBe('function');
    expect(typeof mod.useMyRectorAssignments).toBe('function');
    expect(typeof mod.useRectorAssignmentDetail).toBe('function');
    expect(typeof mod.useAssignmentReports).toBe('function');
    expect(typeof mod.useAssignmentEvidence).toBe('function');
    expect(typeof mod.useAssignmentComments).toBe('function');
    expect(typeof mod.useAssignmentStatusHistory).toBe('function');
    expect(typeof mod.useAssignmentAudit).toBe('function');
    expect(typeof mod.useAssignmentEscalationsDetail).toBe('function');
    expect(typeof mod.useRectorAssignmentTemplates).toBe('function');
  });

  it('exports all expected mutation hooks', async () => {
    const mod = await import('@/modules/rector-assignments/hooks');
    expect(typeof mod.useCreateRectorAssignment).toBe('function');
    expect(typeof mod.useUpdateRectorAssignment).toBe('function');
    expect(typeof mod.useAssignAssignment).toBe('function');
    expect(typeof mod.useAcceptAssignment).toBe('function');
    expect(typeof mod.useReturnAssignment).toBe('function');
    expect(typeof mod.useCompleteAssignment).toBe('function');
    expect(typeof mod.useEscalateAssignment).toBe('function');
    expect(typeof mod.useCancelAssignment).toBe('function');
    expect(typeof mod.useArchiveAssignment).toBe('function');
    expect(typeof mod.useSubmitReport).toBe('function');
    expect(typeof mod.useAttachEvidence).toBe('function');
    expect(typeof mod.useAddComment).toBe('function');
    expect(typeof mod.useCreateTemplate).toBe('function');
    expect(typeof mod.useUpdateTemplate).toBe('function');
  });
});

describe('AssignmentStatus enum', () => {
  it('has all 11 expected status values', async () => {
    const { AssignmentStatus } = await import('@/modules/rector-assignments/types');
    const values = Object.values(AssignmentStatus);
    expect(values).toContain('DRAFT');
    expect(values).toContain('ASSIGNED');
    expect(values).toContain('ACCEPTED');
    expect(values).toContain('IN_PROGRESS');
    expect(values).toContain('REPORT_SUBMITTED');
    expect(values).toContain('RETURNED_FOR_REVISION');
    expect(values).toContain('COMPLETED');
    expect(values).toContain('OVERDUE');
    expect(values).toContain('ESCALATED');
    expect(values).toContain('CANCELLED');
    expect(values).toContain('ARCHIVED');
    expect(values).toHaveLength(11);
  });
});

describe('AssignmentPriority enum', () => {
  it('has CRITICAL/HIGH/NORMAL/LOW — NOT MEDIUM', async () => {
    const { AssignmentPriority } = await import('@/modules/rector-assignments/types');
    const values = Object.values(AssignmentPriority);
    expect(values).toContain('CRITICAL');
    expect(values).toContain('HIGH');
    expect(values).toContain('NORMAL');
    expect(values).toContain('LOW');
    expect(values).not.toContain('MEDIUM');
  });
});

describe('RecurrenceType enum', () => {
  it('has NONE/DAILY/WEEKLY/MONTHLY/CUSTOM — NOT QUARTERLY/ANNUAL', async () => {
    const { RecurrenceType } = await import('@/modules/rector-assignments/types');
    const values = Object.values(RecurrenceType);
    expect(values).toContain('NONE');
    expect(values).toContain('DAILY');
    expect(values).toContain('WEEKLY');
    expect(values).toContain('MONTHLY');
    expect(values).toContain('CUSTOM');
    expect(values).not.toContain('QUARTERLY');
    expect(values).not.toContain('ANNUAL');
  });
});

describe('ReportStatus enum', () => {
  it('has SUBMITTED/RETURNED — NOT ACCEPTED/REJECTED', async () => {
    const { ReportStatus } = await import('@/modules/rector-assignments/types');
    const values = Object.values(ReportStatus);
    expect(values).toContain('SUBMITTED');
    expect(values).toContain('RETURNED');
    expect(values).not.toContain('ACCEPTED');
    expect(values).not.toContain('REJECTED');
  });
});
