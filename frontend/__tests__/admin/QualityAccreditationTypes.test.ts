import { describe, expect, it } from 'vitest';
import {
  API_PREFIX,
  DATA_SOURCE,
  MODULE_NAME,
  QUALITY_ACCREDITATION_BACKEND_PERMISSION_COUNT,
  QUALITY_ACCREDITATION_BACKEND_ROUTE_COUNT,
  QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT,
  QUALITY_ACCREDITATION_ROUTES,
  RUNTIME_MODE,
  SOURCE_BACKEND_B1_COMMIT,
  SOURCE_BACKEND_RUNTIME_COMMIT,
  SOURCE_BACKEND_SPEC_COMMIT,
  SOURCE_PRODUCT_MAP_COMMIT,
  SOURCE_VERTICAL_SELECTION_COMMIT,
  UI_BASE_PATH,
} from '@/modules/quality-accreditation/constants';
import type {
  QualityAccreditationBoundaryFlags,
  QualityAccreditationDashboardResponse,
  QualityFramework,
} from '@/modules/quality-accreditation/types';

describe('Quality Accreditation types', () => {
  it('exports the expected module and runtime constants', () => {
    expect(MODULE_NAME).toBe('quality-accreditation');
    expect(API_PREFIX).toBe('/api/admin/quality-accreditation');
    expect(UI_BASE_PATH).toBe('/console/quality-accreditation');
    expect(QUALITY_ACCREDITATION_BACKEND_TABLE_COUNT).toBe(32);
    expect(QUALITY_ACCREDITATION_BACKEND_ROUTE_COUNT).toBe(70);
    expect(QUALITY_ACCREDITATION_BACKEND_PERMISSION_COUNT).toBe(55);
    expect(SOURCE_BACKEND_RUNTIME_COMMIT).toBe('f97ce31');
    expect(SOURCE_BACKEND_B1_COMMIT).toBe('fb2734c');
    expect(SOURCE_BACKEND_SPEC_COMMIT).toBe('ad2cad9');
    expect(SOURCE_PRODUCT_MAP_COMMIT).toBe('1253e19');
    expect(SOURCE_VERTICAL_SELECTION_COMMIT).toBe('7da0c70');
    expect(RUNTIME_MODE).toBe('METADATA_EVIDENCE_ONLY');
    expect(DATA_SOURCE).toBe('computed_from_quality_accreditation_metadata');
  });

  it('keeps the full route contract explicit and at 27 pages', () => {
    expect(Object.keys(QUALITY_ACCREDITATION_ROUTES)).toHaveLength(27);
    expect(QUALITY_ACCREDITATION_ROUTES.overview).toBe('/console/quality-accreditation');
    expect(QUALITY_ACCREDITATION_ROUTES.dashboard).toBe('/console/quality-accreditation/dashboard');
    expect(QUALITY_ACCREDITATION_ROUTES.limitations).toBe('/console/quality-accreditation/limitations');
  });

  it('models the safety boundary flags explicitly', () => {
    const flags: QualityAccreditationBoundaryFlags = {
      human_review_required: true,
      fake_metrics: false,
      fake_evidence: false,
      official_accreditation_approval_enabled: false,
      official_ministry_submission_enabled: false,
      official_ranking_claim_enabled: false,
      automatic_accreditation_decision_enabled: false,
      provider_integration_enabled: false,
      external_database_sync_enabled: false,
      hidden_score_present: false,
      autonomous_decision: false,
      incomplete_data: true,
      limitations: ['Metadata/evidence-only quality foundation'],
      source_capability_id: 'QA-001',
      source_family_id: 'QA-FAMILY',
    };

    expect(flags.fake_metrics).toBe(false);
    expect(flags.fake_evidence).toBe(false);
    expect(flags.hidden_score_present).toBe(false);
  });

  it('models dashboard and entity trust fields explicitly', () => {
    const dashboard: QualityAccreditationDashboardResponse = {
      tenant_id: 1,
      human_review_required: true,
      fake_metrics: false,
      fake_evidence: false,
      official_accreditation_approval_enabled: false,
      official_ministry_submission_enabled: false,
      official_ranking_claim_enabled: false,
      automatic_accreditation_decision_enabled: false,
      provider_integration_enabled: false,
      external_database_sync_enabled: false,
      hidden_score_present: false,
      autonomous_decision: false,
      incomplete_data: true,
      limitations: ['Evidence metadata only'],
      generated_at: '2026-05-25T00:00:00Z',
      contract_version: 'A-038.3',
      source_spec_commit: 'ad2cad9',
      source_product_map_commit: SOURCE_PRODUCT_MAP_COMMIT,
      source_vertical_selection_commit: SOURCE_VERTICAL_SELECTION_COMMIT,
      master_matrix_commit: 'qa-matrix-1',
      master_matrix_rows: 512,
      detailed_capability_count: 32,
      capability_family_count: 9,
      data_source: DATA_SOURCE,
      frameworks_summary: { ACTIVE: 2 },
      standards_summary: { ACTIVE: 4 },
      evidence_summary: { READY: 6 },
      readiness_summary: { PROGRAM: 3 },
      self_assessment_summary: { DRAFT: 1 },
      improvement_summary: { OPEN: 2 },
      audit_summary: { OPEN: 1 },
      program_review_summary: { PLANNED: 1 },
      bridge_summary: { academic_operations: 2 },
      brain_signal_summary: { review: 1 },
      boundary_summary: { fake_metrics: false },
    };

    const framework: QualityFramework = {
      id: 1,
      tenant_id: 1,
      status: 'ACTIVE',
      metadata: {},
      created_at: '2026-05-25T00:00:00Z',
      updated_at: '2026-05-25T00:00:00Z',
      archived_at: null,
      created_by_user_id: null,
      updated_by_user_id: null,
      human_review_required: true,
      fake_metrics: false,
      fake_evidence: false,
      official_accreditation_approval_enabled: false,
      official_ministry_submission_enabled: false,
      official_ranking_claim_enabled: false,
      automatic_accreditation_decision_enabled: false,
      provider_integration_enabled: false,
      external_database_sync_enabled: false,
      hidden_score_present: false,
      autonomous_decision: false,
      incomplete_data: true,
      limitations: [],
      source_capability_id: 'QA-001',
      source_family_id: 'QA-FAMILY',
      title: 'Institutional Quality Framework',
      description: null,
      notes: null,
      framework_ref: 'QF-1',
      policy_ref: null,
      standard_ref: null,
      criterion_ref: null,
      requirement_ref: null,
      evidence_ref: null,
      limitation_ref: null,
      readiness_ref: null,
      report_ref: null,
      section_ref: null,
      plan_ref: null,
      action_ref: null,
      audit_ref: null,
      finding_ref: null,
      cycle_ref: null,
      assessment_ref: null,
      feedback_ref: null,
      survey_ref: null,
      review_ref: null,
      response_plan_ref: null,
      workflow_ref: null,
      gap_ref: null,
      calendar_ref: null,
      risk_ref: null,
      bridge_ref: null,
      signal_ref: null,
      source_entity_type: null,
      source_entity_id: null,
      source_entity_ref: null,
      source_vertical_ref: null,
      target_reference: null,
      owner_ref: null,
      reviewer_ref: null,
      committee_ref: null,
      program_ref: null,
      department_ref: null,
      faculty_ref: null,
      student_group_ref: null,
      event_type: null,
      signal_type: null,
      limitation_code: null,
      limitation_text: null,
      risk_band: null,
      completion_percent: null,
      reference_uri: null,
      read_only_first: true,
      mutation_allowed: false,
    };

    expect(dashboard.data_source).toBe(DATA_SOURCE);
    expect(framework.framework_ref).toBe('QF-1');
    expect(framework.mutation_allowed).toBe(false);
  });
});