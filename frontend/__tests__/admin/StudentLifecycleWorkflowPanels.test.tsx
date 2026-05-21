import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  ApplicantStatusTimeline,
  AuditTrailPanel,
  EnrollmentReviewPanel,
  GraduationReadinessPanel,
  InterventionFollowupTimeline,
  InterventionPlanPanel,
  StudentAppealReviewPanel,
  StudentRequestReviewPanel,
  TranscriptPreviewPanel,
} from '@/modules/student-lifecycle/components';
import { EXPECTED_DATA_SOURCE } from '@/modules/student-lifecycle/constants';

describe('Student Lifecycle workflow panels', () => {
  it('renders transcript preview and graduation readiness boundaries', () => {
    render(
      <div>
        <TranscriptPreviewPanel preview={{ id: 1, tenant_id: 1, student_id: 2, academic_record_id: 3, official_document: false, preview_payload: {}, status: 'GENERATED_UNOFFICIAL_PREVIEW', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }} />
        <GraduationReadinessPanel snapshot={{ id: 2, tenant_id: 1, student_id: 2, data_source: EXPECTED_DATA_SOURCE, incomplete_data: true, hidden_score_present: false, completion_summary: {}, status: 'HUMAN_REVIEW_REQUIRED', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }} />
      </div>,
    );

    expect(screen.getByText(/official document not issued/i)).toBeInTheDocument();
    expect(screen.getByText(/digital signature not enabled/i)).toBeInTheDocument();
    expect(screen.getByText(/no automatic graduation eligibility decision/i)).toBeInTheDocument();
  });

  it('renders request and appeal review panels with explicit human review wording', () => {
    render(
      <div>
        <StudentRequestReviewPanel request={{ id: 3, tenant_id: 1, student_id: 2, request_type: 'LEAVE', description: 'Leave request', decision_note: null, archived_at: null, status: 'UNDER_REVIEW', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }} />
        <StudentAppealReviewPanel appeal={{ id: 4, tenant_id: 1, student_id: 2, appeal_type: 'GRADE', description: 'Appeal request', decision_note: null, archived_at: null, status: 'COMMITTEE_REVIEW', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }} />
      </div>,
    );

    expect(screen.getByText(/decision metadata only/i)).toBeInTheDocument();
    expect(screen.getByText(/no autonomous appeal decision/i)).toBeInTheDocument();
  });

  it('renders intervention support-only and audit-backed panels', () => {
    render(
      <div>
        <InterventionPlanPanel plan={{ id: 5, tenant_id: 1, student_id: 2, signal_type: 'ATTENDANCE', plan_summary: 'Advisor outreach', hidden_score_present: false, followups: [{ step: 'Call' }], archived_at: null, status: 'ADVISOR_REVIEW_REQUIRED', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }} />
        <InterventionFollowupTimeline plan={{ id: 5, tenant_id: 1, student_id: 2, signal_type: 'ATTENDANCE', plan_summary: 'Advisor outreach', hidden_score_present: false, followups: [{ step: 'Call' }, { step: 'Email' }], archived_at: null, status: 'ADVISOR_REVIEW_REQUIRED', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }} />
        <AuditTrailPanel events={[{ id: 6, tenant_id: 1, entity_type: 'intervention', entity_id: 5, event_type: 'INTERVENTION_PLAN_CREATED', actor_user_id: 'advisor', previous_status: null, new_status: 'ADVISOR_REVIEW_REQUIRED', human_review_required: true, automated_decision: false, provider_integration_enabled: false, action: 'create_plan', request_id: 'req-2', payload: {}, created_at: '2026-05-22T00:00:00Z' }]} />
      </div>,
    );

    expect(screen.getByText(/no punitive automation/i)).toBeInTheDocument();
    expect(screen.getByText(/call/i)).toBeInTheDocument();
    expect(screen.getByText(/action: create_plan/i)).toBeInTheDocument();
  });

  it('renders applicant and enrollment timeline panels', () => {
    render(
      <div>
        <ApplicantStatusTimeline history={[{ id: 7, tenant_id: 1, applicant_id: 1, previous_status: 'SUBMITTED', new_status: 'UNDER_REVIEW', reason: 'Ready for review', actor_user_id: 'reviewer', request_id: 'req-3', created_at: '2026-05-22T00:00:00Z' }]} />
        <EnrollmentReviewPanel enrollment={{ id: 8, tenant_id: 1, student_id: 2, term_code: '2026-FALL', notes: null, archived_at: null, status: 'REGISTRAR_REVIEW', created_at: '2026-05-22T00:00:00Z', updated_at: '2026-05-22T00:00:00Z', human_review_required: true, automated_decision: false, provider_integration_enabled: false, limitations: [] }} />
      </div>,
    );

    expect(screen.getByText(/ready for review/i)).toBeInTheDocument();
    expect(screen.getByText(/2026-FALL/i)).toBeInTheDocument();
  });
});