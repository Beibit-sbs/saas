/**
 * Tests: AssignmentActionsBar
 * Verifies lifecycle action button visibility based on status predicates.
 */

import { describe, expect, it } from 'vitest';
import { AssignmentStatus } from '@/modules/rector-assignments/types';
import {
  canAssignByStatus,
  canAcceptByStatus,
  canReturnByStatus,
  canCompleteByStatus,
  canEscalateByStatus,
  canCancelByStatus,
  canArchiveByStatus,
  canSubmitReportByStatus,
  isTerminalStatus,
} from '@/modules/rector-assignments/status';

describe('Status predicate functions (AssignmentActionsBar)', () => {
  describe('canAssignByStatus', () => {
    it('returns true only for DRAFT', () => {
      expect(canAssignByStatus(AssignmentStatus.DRAFT)).toBe(true);
      expect(canAssignByStatus(AssignmentStatus.ASSIGNED)).toBe(false);
      expect(canAssignByStatus(AssignmentStatus.IN_PROGRESS)).toBe(false);
      expect(canAssignByStatus(AssignmentStatus.COMPLETED)).toBe(false);
    });
  });

  describe('canAcceptByStatus', () => {
    it('returns true only for ASSIGNED', () => {
      expect(canAcceptByStatus(AssignmentStatus.ASSIGNED)).toBe(true);
      expect(canAcceptByStatus(AssignmentStatus.IN_PROGRESS)).toBe(false);
      expect(canAcceptByStatus(AssignmentStatus.DRAFT)).toBe(false);
    });
  });

  describe('canReturnByStatus', () => {
    it('returns true only for REPORT_SUBMITTED', () => {
      expect(canReturnByStatus(AssignmentStatus.REPORT_SUBMITTED)).toBe(true);
      expect(canReturnByStatus(AssignmentStatus.IN_PROGRESS)).toBe(false);
      expect(canReturnByStatus(AssignmentStatus.COMPLETED)).toBe(false);
    });
  });

  describe('canCompleteByStatus', () => {
    it('returns true for REPORT_SUBMITTED and ESCALATED', () => {
      expect(canCompleteByStatus(AssignmentStatus.REPORT_SUBMITTED)).toBe(true);
      expect(canCompleteByStatus(AssignmentStatus.ESCALATED)).toBe(true);
      expect(canCompleteByStatus(AssignmentStatus.IN_PROGRESS)).toBe(false);
      expect(canCompleteByStatus(AssignmentStatus.DRAFT)).toBe(false);
    });
  });

  describe('canEscalateByStatus', () => {
    it('returns true for OVERDUE, IN_PROGRESS, ACCEPTED', () => {
      expect(canEscalateByStatus(AssignmentStatus.OVERDUE)).toBe(true);
      expect(canEscalateByStatus(AssignmentStatus.IN_PROGRESS)).toBe(true);
      expect(canEscalateByStatus(AssignmentStatus.ACCEPTED)).toBe(true);
      expect(canEscalateByStatus(AssignmentStatus.DRAFT)).toBe(false);
      expect(canEscalateByStatus(AssignmentStatus.COMPLETED)).toBe(false);
    });
  });

  describe('canCancelByStatus', () => {
    it('returns true for DRAFT, ASSIGNED, ACCEPTED, IN_PROGRESS', () => {
      expect(canCancelByStatus(AssignmentStatus.DRAFT)).toBe(true);
      expect(canCancelByStatus(AssignmentStatus.ASSIGNED)).toBe(true);
      expect(canCancelByStatus(AssignmentStatus.ACCEPTED)).toBe(true);
      expect(canCancelByStatus(AssignmentStatus.IN_PROGRESS)).toBe(true);
      expect(canCancelByStatus(AssignmentStatus.COMPLETED)).toBe(false);
      expect(canCancelByStatus(AssignmentStatus.CANCELLED)).toBe(false);
    });
  });

  describe('canArchiveByStatus', () => {
    it('returns true only for COMPLETED or CANCELLED', () => {
      expect(canArchiveByStatus(AssignmentStatus.COMPLETED)).toBe(true);
      expect(canArchiveByStatus(AssignmentStatus.CANCELLED)).toBe(true);
      expect(canArchiveByStatus(AssignmentStatus.IN_PROGRESS)).toBe(false);
      expect(canArchiveByStatus(AssignmentStatus.DRAFT)).toBe(false);
    });
  });

  describe('canSubmitReportByStatus', () => {
    it('returns true for ACCEPTED, IN_PROGRESS, RETURNED_FOR_REVISION, OVERDUE, ESCALATED', () => {
      expect(canSubmitReportByStatus(AssignmentStatus.ACCEPTED)).toBe(true);
      expect(canSubmitReportByStatus(AssignmentStatus.IN_PROGRESS)).toBe(true);
      expect(canSubmitReportByStatus(AssignmentStatus.RETURNED_FOR_REVISION)).toBe(true);
      expect(canSubmitReportByStatus(AssignmentStatus.OVERDUE)).toBe(true);
      expect(canSubmitReportByStatus(AssignmentStatus.ESCALATED)).toBe(true);
      expect(canSubmitReportByStatus(AssignmentStatus.DRAFT)).toBe(false);
      expect(canSubmitReportByStatus(AssignmentStatus.COMPLETED)).toBe(false);
      expect(canSubmitReportByStatus(AssignmentStatus.REPORT_SUBMITTED)).toBe(false);
    });
  });

  describe('isTerminalStatus', () => {
    it('returns true for COMPLETED, CANCELLED, ARCHIVED', () => {
      expect(isTerminalStatus(AssignmentStatus.COMPLETED)).toBe(true);
      expect(isTerminalStatus(AssignmentStatus.CANCELLED)).toBe(true);
      expect(isTerminalStatus(AssignmentStatus.ARCHIVED)).toBe(true);
      expect(isTerminalStatus(AssignmentStatus.IN_PROGRESS)).toBe(false);
      expect(isTerminalStatus(AssignmentStatus.DRAFT)).toBe(false);
    });
  });
});
