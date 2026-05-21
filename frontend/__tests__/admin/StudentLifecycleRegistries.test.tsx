import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  AcademicRecordRegistry,
  ApplicantRegistry,
  DegreeProgressDashboard,
  EnrollmentRegistry,
  InterventionDashboard,
  StudentAppealRegistry,
  StudentLifecycleAuditLog,
  StudentRegistry,
  StudentRequestRegistry,
  TranscriptPreviewRegistry,
} from '@/modules/student-lifecycle/components';
import { EXPECTED_DATA_SOURCE } from '@/modules/student-lifecycle/constants';

describe('Student Lifecycle registries', () => {
  it('renders applicants, students, enrollment, and records registries', () => {
    render(
      <div>
        <ApplicantRegistry applicants={[{ id: 1, tenant_id: 1, applicant_code: 'A-1', program_interest: 'CS', entry_term: '2026-FALL', notes: null, source_available: true, archived_at: null, status: 'UNDER_REVIEW', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }]} />
        <StudentRegistry students={[{ id: 2, tenant_id: 1, student_code: 'S-1', source_applicant_id: 1, program_code: 'CS', notes: null, archived_at: null, status: 'ACTIVE', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }]} />
        <EnrollmentRegistry enrollments={[{ id: 3, tenant_id: 1, student_id: 2, term_code: '2026-FALL', notes: null, archived_at: null, status: 'REGISTRAR_REVIEW', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }]} />
        <AcademicRecordRegistry records={[{ id: 4, tenant_id: 1, student_id: 2, record_name: 'Semester 1', source_available: false, result_metadata: {}, status: 'REVIEW_REQUIRED', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }]} />
      </div>,
    );

    expect(screen.getByText('A-1')).toBeInTheDocument();
    expect(screen.getByText('S-1')).toBeInTheDocument();
    expect(screen.getByText('2026-FALL')).toBeInTheDocument();
    expect(screen.getByText(/semester 1/i)).toBeInTheDocument();
    expect(screen.getByTestId('metadata-only-label')).toBeInTheDocument();
  });

  it('renders transcripts, degree progress, requests, appeals, interventions, and audit', () => {
    render(
      <div>
        <TranscriptPreviewRegistry transcripts={[{ id: 5, tenant_id: 1, student_id: 2, academic_record_id: 4, official_document: false, preview_payload: { gpa: 3.9 }, status: 'GENERATED_UNOFFICIAL_PREVIEW', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }]} />
        <DegreeProgressDashboard snapshot={{ id: 6, tenant_id: 1, student_id: 2, data_source: EXPECTED_DATA_SOURCE, incomplete_data: true, hidden_score_present: false, completion_summary: { completed: 90 }, status: 'HUMAN_REVIEW_REQUIRED', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }} />
        <StudentRequestRegistry requests={[{ id: 7, tenant_id: 1, student_id: 2, request_type: 'LEAVE', description: 'Leave request', decision_note: null, archived_at: null, status: 'UNDER_REVIEW', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }]} />
        <StudentAppealRegistry appeals={[{ id: 8, tenant_id: 1, student_id: 2, appeal_type: 'GRADE', description: 'Appeal request', decision_note: null, archived_at: null, status: 'COMMITTEE_REVIEW', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }]} />
        <InterventionDashboard plans={[{ id: 9, tenant_id: 1, student_id: 2, signal_type: 'ATTENDANCE', plan_summary: 'Advisor outreach', hidden_score_present: false, followups: [{ step: 'Call' }], archived_at: null, status: 'ADVISOR_REVIEW_REQUIRED', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }]} />
        <StudentLifecycleAuditLog audit={[{ id: 10, tenant_id: 1, entity_type: 'appeal', entity_id: 8, event_type: 'STUDENT_APPEAL_REVIEWED', actor_user_id: 'admin', previous_status: 'SUBMITTED', new_status: 'COMMITTEE_REVIEW', human_review_required: true, automated_decision: false, provider_integration_enabled: false, action: 'review_appeal', request_id: 'req-1', payload: {}, created_at: '2026-05-22T00:00:00Z' }]} />
      </div>,
    );

    expect(screen.getByTestId('unofficial-preview-label')).toBeInTheDocument();
    expect(screen.getByText(/completed/i)).toBeInTheDocument();
    expect(screen.getByText('LEAVE')).toBeInTheDocument();
    expect(screen.getByText('GRADE')).toBeInTheDocument();
    expect(screen.getByText('ATTENDANCE')).toBeInTheDocument();
    expect(screen.getAllByText(/audit-backed transitions/i).length).toBeGreaterThanOrEqual(1);
  });
});