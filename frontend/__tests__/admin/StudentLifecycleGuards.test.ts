import { describe, expect, it } from 'vitest';
import {
  STUDENT_LIFECYCLE_APPEAL_PERMISSIONS,
  STUDENT_LIFECYCLE_APPLICANT_PERMISSIONS,
  STUDENT_LIFECYCLE_DASHBOARD_PERMISSIONS,
  STUDENT_LIFECYCLE_RECORD_PERMISSIONS,
  StudentLifecycleDataQualityError,
  assertTrustedDegreeProgress,
  assertTrustedStudentLifecycleDashboard,
  assertTrustedStudentLifecycleHealth,
  canAutoDecide,
  canCreateTranscriptPreview,
  canIssueOfficialTranscript,
  canManageApplicants,
  canManageInterventions,
  canReviewAppeals,
  canReviewGraduationReadiness,
  canSyncProvider,
  canViewAcademicRecords,
  canViewStudentLifecycleDashboard,
  hasStudentLifecyclePermission,
} from '@/modules/student-lifecycle/guards';
import { EXPECTED_DATA_SOURCE } from '@/modules/student-lifecycle/constants';

const adminUser = {
  permissions: [
    STUDENT_LIFECYCLE_DASHBOARD_PERMISSIONS.read,
    STUDENT_LIFECYCLE_APPLICANT_PERMISSIONS.create,
    STUDENT_LIFECYCLE_RECORD_PERMISSIONS.read,
    STUDENT_LIFECYCLE_APPEAL_PERMISSIONS.review,
  ],
};

describe('Student Lifecycle guards', () => {
  it('evaluates permission sets from user permissions', () => {
    expect(hasStudentLifecyclePermission(adminUser, STUDENT_LIFECYCLE_DASHBOARD_PERMISSIONS.read)).toBe(true);
    expect(canViewStudentLifecycleDashboard(adminUser)).toBe(true);
    expect(canManageApplicants(adminUser)).toBe(true);
    expect(canViewAcademicRecords(adminUser)).toBe(true);
    expect(canReviewAppeals(adminUser)).toBe(true);
  });

  it('returns false when the user lacks mutation permissions', () => {
    expect(canCreateTranscriptPreview({ permissions: [] })).toBe(false);
    expect(canReviewGraduationReadiness({ permissions: [] })).toBe(false);
    expect(canManageInterventions({ permissions: [] })).toBe(false);
  });

  it('asserts dashboard trust boundaries', () => {
    expect(() =>
      assertTrustedStudentLifecycleDashboard({
        tenant_id: 1,
        generated_at: '2026-05-22T00:00:00Z',
        fake_metrics: true,
        data_source: EXPECTED_DATA_SOURCE,
        incomplete_data: true,
        limitations: [],
        applicant_counts_by_status: {},
        student_counts_by_status: {},
        enrollment_counts_by_status: {},
        transcript_preview_counts: {},
        degree_progress_counts: {},
        request_counts_by_status: {},
        appeal_counts_by_status: {},
        intervention_counts_by_status: {},
        human_review_required_count: 0,
        provider_integration_enabled: false,
        automated_decision_count: 0,
        hidden_score_present: false,
      }),
    ).toThrow(StudentLifecycleDataQualityError);
  });

  it('asserts health trust boundaries', () => {
    expect(() =>
      assertTrustedStudentLifecycleHealth({
        tenant_id: 1,
        generated_at: '2026-05-22T00:00:00Z',
        module_name: 'student_lifecycle',
        route_count: 44,
        table_count: 14,
        fake_metrics: false,
        data_source: 'other_source' as typeof EXPECTED_DATA_SOURCE,
        incomplete_data: false,
        limitations: [],
        provider_integration_enabled: false,
        automated_decision_count: 0,
        hidden_score_present: false,
      }),
    ).toThrow(/data source mismatch/i);
  });

  it('asserts degree progress hidden-score boundaries', () => {
    expect(() =>
      assertTrustedDegreeProgress({
        id: 1,
        tenant_id: 1,
        status: 'HUMAN_REVIEW_REQUIRED',
        student_id: 2,
        data_source: EXPECTED_DATA_SOURCE,
        incomplete_data: true,
        hidden_score_present: true,
        completion_summary: {},
        created_at: '2026-05-22T00:00:00Z',
        updated_at: '2026-05-22T00:00:00Z',
        human_review_required: true,
        automated_decision: false,
        provider_integration_enabled: false,
        limitations: [],
      }),
    ).toThrow(/hidden_score_present=true/i);
  });

  it('keeps forbidden automation and official issuance disabled', () => {
    expect(canIssueOfficialTranscript()).toBe(false);
    expect(canSyncProvider()).toBe(false);
    expect(canAutoDecide()).toBe(false);
  });
});