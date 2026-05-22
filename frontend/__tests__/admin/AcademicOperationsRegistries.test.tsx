import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  AcademicGroupsRegistry,
  AdvisorTutorRegistry,
  CohortsRegistry,
  GradebookMetadataRegistry,
  RetakePlansRegistry,
  SummerSemesterRegistry,
} from '@/modules/academic-operations/components';

describe('Academic Operations registries', () => {
  it('renders academic groups and cohorts registries', () => {
    render(
      <div>
        <AcademicGroupsRegistry groups={[{ id: 1, tenant_id: 1, status: 'ACTIVE', created_at: '2026-05-22', updated_at: '2026-05-22', archived_at: null, human_review_required: true, automated_decision: false, provider_integration_enabled: false, platonus_sync_enabled: false, sis_sync_enabled: false, hidden_score_present: false, fake_metrics: false, official_grade_publication_enabled: false, automated_grading_enabled: false, automatic_sanction_enabled: false, incomplete_data: true, limitations: [], source_matrix_row_id: 'AO-1', source_capability_id: 'CAP-1', group_code: 'AG-1', group_name: 'Group 1', external_ref: null, notes: null }]} />
        <CohortsRegistry cohorts={[{ id: 2, tenant_id: 1, status: 'ACTIVE', created_at: '2026-05-22', updated_at: '2026-05-22', archived_at: null, human_review_required: true, automated_decision: false, provider_integration_enabled: false, platonus_sync_enabled: false, sis_sync_enabled: false, hidden_score_present: false, fake_metrics: false, official_grade_publication_enabled: false, automated_grading_enabled: false, automatic_sanction_enabled: false, incomplete_data: true, limitations: [], source_matrix_row_id: 'AO-2', source_capability_id: 'CAP-2', cohort_code: 'CO-1', cohort_name: 'Cohort 1', academic_group_ref: 'AG-1', notes: null }]} />
      </div>,
    );

    expect(screen.getByText('Group 1')).toBeInTheDocument();
    expect(screen.getByText('Cohort 1')).toBeInTheDocument();
  });

  it('renders gradebook and retake boundary copy', () => {
    render(
      <div>
        <GradebookMetadataRegistry items={[{ id: 3, tenant_id: 1, status: 'ACTIVE', created_at: '2026-05-22', updated_at: '2026-05-22', archived_at: null, human_review_required: true, automated_decision: false, provider_integration_enabled: false, platonus_sync_enabled: false, sis_sync_enabled: false, hidden_score_present: false, fake_metrics: false, official_grade_publication_enabled: false, automated_grading_enabled: false, automatic_sanction_enabled: false, incomplete_data: true, limitations: [], source_matrix_row_id: 'AO-3', source_capability_id: 'CAP-3', student_ref: 'S-1', course_ref: 'C-1', gradebook_key: 'GB-1', metadata: {} }]} />
        <RetakePlansRegistry items={[{ id: 4, tenant_id: 1, status: 'ACTIVE', created_at: '2026-05-22', updated_at: '2026-05-22', archived_at: null, human_review_required: true, automated_decision: false, provider_integration_enabled: false, platonus_sync_enabled: false, sis_sync_enabled: false, hidden_score_present: false, fake_metrics: false, official_grade_publication_enabled: false, automated_grading_enabled: false, automatic_sanction_enabled: false, incomplete_data: true, limitations: [], source_matrix_row_id: 'AO-4', source_capability_id: 'CAP-4', student_ref: 'S-1', course_ref: 'C-1', plan_code: 'RP-1', retake_window: '2026-08' }]} />
      </div>,
    );

    expect(screen.getByText(/no official grade publication/i)).toBeInTheDocument();
    expect(screen.getByText(/no automatic retake denial, sanction, or dismissal/i)).toBeInTheDocument();
  });

  it('renders summer semester and advisor or tutor registries', () => {
    render(
      <div>
        <SummerSemesterRegistry terms={[{ id: 5, tenant_id: 1, status: 'ACTIVE', created_at: '2026-05-22', updated_at: '2026-05-22', archived_at: null, human_review_required: true, automated_decision: false, provider_integration_enabled: false, platonus_sync_enabled: false, sis_sync_enabled: false, hidden_score_present: false, fake_metrics: false, official_grade_publication_enabled: false, automated_grading_enabled: false, automatic_sanction_enabled: false, incomplete_data: true, limitations: [], source_matrix_row_id: 'AO-5', source_capability_id: 'CAP-5', term_code: '2026-SUM', display_name: 'Summer 2026', calendar_ref: 'CAL-1' }]} />
        <AdvisorTutorRegistry assignments={[{ id: 6, tenant_id: 1, status: 'ACTIVE', created_at: '2026-05-22', updated_at: '2026-05-22', archived_at: null, human_review_required: true, automated_decision: false, provider_integration_enabled: false, platonus_sync_enabled: false, sis_sync_enabled: false, hidden_score_present: false, fake_metrics: false, official_grade_publication_enabled: false, automated_grading_enabled: false, automatic_sanction_enabled: false, incomplete_data: true, limitations: [], source_matrix_row_id: 'AO-6', source_capability_id: 'CAP-6', student_ref: 'S-1', faculty_ref: 'F-1', assignment_code: 'AT-1', notes: null }]} />
      </div>,
    );

    expect(screen.getByText('Summer 2026')).toBeInTheDocument();
    expect(screen.getByText('AT-1')).toBeInTheDocument();
    expect(screen.getByText(/no hidden score/i)).toBeInTheDocument();
  });
});