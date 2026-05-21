import { describe, expect, it } from 'vitest';
import {
  API_BASE_PATH,
  EXPECTED_DATA_SOURCE,
  FAKE_METRICS_ENABLED,
  HIDDEN_SCORE_ENABLED,
  MODULE_NAME,
  STUDENT_LIFECYCLE_BOUNDARY_LABELS,
  UI_BASE_PATH,
} from '@/modules/student-lifecycle/constants';
import {
  AcademicRecordStatus,
  ApplicantStatus,
  DegreeProgressStatus,
  EnrollmentStatus,
  InterventionStatus,
  StudentAppealStatus,
  StudentLifecycleAuditEventType,
  StudentRequestStatus,
  StudentStatus,
  TranscriptPreviewStatus,
  type StudentLifecycleDashboardResponse,
  type TranscriptPreviewResponse,
} from '@/modules/student-lifecycle/types';

describe('Student Lifecycle types', () => {
  it('exports the expected module paths and safety constants', () => {
    expect(MODULE_NAME).toBe('student-lifecycle');
    expect(API_BASE_PATH).toBe('/api/admin/student-lifecycle');
    expect(UI_BASE_PATH).toBe('/console/student-lifecycle');
    expect(EXPECTED_DATA_SOURCE).toBe('computed_from_student_lifecycle_metadata');
    expect(FAKE_METRICS_ENABLED).toBe(false);
    expect(HIDDEN_SCORE_ENABLED).toBe(false);
  });

  it('keeps all required boundary labels explicit', () => {
    expect(STUDENT_LIFECYCLE_BOUNDARY_LABELS.humanReviewRequired).toMatch(/human review required/i);
    expect(STUDENT_LIFECYCLE_BOUNDARY_LABELS.noAutomatedDecision).toMatch(/no automated decision/i);
    expect(STUDENT_LIFECYCLE_BOUNDARY_LABELS.unofficialPreview).toMatch(/unofficial preview/i);
    expect(STUDENT_LIFECYCLE_BOUNDARY_LABELS.providerNotEnabled).toMatch(/provider integration not enabled/i);
    expect(STUDENT_LIFECYCLE_BOUNDARY_LABELS.noHiddenRiskScore).toMatch(/no hidden risk score/i);
  });

  it('exposes backend-aligned status enums for the runtime subset', () => {
    expect(ApplicantStatus.ACCEPTED).toBe('ACCEPTED');
    expect(StudentStatus.GRADUATED_METADATA).toBe('GRADUATED_METADATA');
    expect(EnrollmentStatus.REGISTRAR_REVIEW).toBe('REGISTRAR_REVIEW');
    expect(AcademicRecordStatus.RESULTS_METADATA_ENTERED).toBe('RESULTS_METADATA_ENTERED');
    expect(TranscriptPreviewStatus.GENERATED_UNOFFICIAL_PREVIEW).toBe('GENERATED_UNOFFICIAL_PREVIEW');
    expect(DegreeProgressStatus.ADVISOR_REVIEW_REQUIRED).toBe('ADVISOR_REVIEW_REQUIRED');
    expect(StudentRequestStatus.DECISION_METADATA_RECORDED).toBe('DECISION_METADATA_RECORDED');
    expect(StudentAppealStatus.COMMITTEE_REVIEW).toBe('COMMITTEE_REVIEW');
    expect(InterventionStatus.OUTCOME_METADATA_RECORDED).toBe('OUTCOME_METADATA_RECORDED');
    expect(StudentLifecycleAuditEventType.TRANSCRIPT_PREVIEW_GENERATED).toBe('TRANSCRIPT_PREVIEW_GENERATED');
  });

  it('models dashboard safety fields explicitly', () => {
    const dashboard: StudentLifecycleDashboardResponse = {
      tenant_id: 1,
      generated_at: '2026-05-22T00:00:00Z',
      fake_metrics: false,
      data_source: EXPECTED_DATA_SOURCE,
      incomplete_data: true,
      limitations: ['Human review required'],
      applicant_counts_by_status: { DRAFT: 2 },
      student_counts_by_status: { ACTIVE: 3 },
      enrollment_counts_by_status: { ENROLLED: 4 },
      transcript_preview_counts: { GENERATED_UNOFFICIAL_PREVIEW: 1 },
      degree_progress_counts: { HUMAN_REVIEW_REQUIRED: 2 },
      request_counts_by_status: { SUBMITTED: 1 },
      appeal_counts_by_status: { REVIEWER_REVIEW: 1 },
      intervention_counts_by_status: { SIGNAL_REGISTERED: 1 },
      human_review_required_count: 7,
      provider_integration_enabled: false,
      automated_decision_count: 0,
      hidden_score_present: false,
    };

    expect(dashboard.fake_metrics).toBe(false);
    expect(dashboard.data_source).toBe(EXPECTED_DATA_SOURCE);
    expect(dashboard.automated_decision_count).toBe(0);
    expect(dashboard.hidden_score_present).toBe(false);
  });

  it('keeps transcript previews preview-only and non-official', () => {
    const preview: TranscriptPreviewResponse = {
      id: 10,
      tenant_id: 1,
      status: TranscriptPreviewStatus.GENERATED_UNOFFICIAL_PREVIEW,
      student_id: 200,
      academic_record_id: 300,
      official_document: false,
      preview_payload: { gpa: 3.8 },
      created_at: '2026-05-22T00:00:00Z',
      updated_at: '2026-05-22T00:00:00Z',
      human_review_required: true,
      automated_decision: false,
      provider_integration_enabled: false,
      limitations: ['Unofficial preview'],
    };

    expect(preview.official_document).toBe(false);
    expect(preview.automated_decision).toBe(false);
    expect(preview.provider_integration_enabled).toBe(false);
  });
});