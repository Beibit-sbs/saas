import { describe, expect, it } from 'vitest';
import {
  API_PREFIX,
  MASTER_MATRIX_COMMIT,
  MASTER_MATRIX_ROW_COUNT,
  MODULE_NAME,
  RESEARCH_SCIENCE_BACKEND_PERMISSION_COUNT,
  RESEARCH_SCIENCE_BACKEND_ROUTE_COUNT,
  RESEARCH_SCIENCE_ROUTES,
  RESEARCH_SCIENCE_TABLE_COUNT,
  RUNTIME_MODE,
  SOURCE_BACKEND_B1_R1_COMMIT,
  SOURCE_BACKEND_RUNTIME_COMMIT,
  SOURCE_FRONTEND_SPEC_COMMIT,
  UI_BASE_PATH,
} from '@/modules/research-science/constants';
import type {
  PublicationMetadata,
  ResearchProject,
  ResearchScienceBoundaryFlags,
  ResearchScienceDashboardResponse,
} from '@/modules/research-science/types';

describe('Research Science types', () => {
  it('exports the expected module and runtime constants', () => {
    expect(MODULE_NAME).toBe('research-science');
    expect(API_PREFIX).toBe('/api/admin/research-science');
    expect(UI_BASE_PATH).toBe('/console/research-science');
    expect(RESEARCH_SCIENCE_TABLE_COUNT).toBe(15);
    expect(RESEARCH_SCIENCE_BACKEND_ROUTE_COUNT).toBe(43);
    expect(RESEARCH_SCIENCE_BACKEND_PERMISSION_COUNT).toBe(40);
    expect(MASTER_MATRIX_COMMIT).toBe('c79cc31');
    expect(MASTER_MATRIX_ROW_COUNT).toBe(467);
    expect(SOURCE_BACKEND_RUNTIME_COMMIT).toBe('a149c36');
    expect(SOURCE_BACKEND_B1_R1_COMMIT).toBe('da12c7d');
    expect(SOURCE_FRONTEND_SPEC_COMMIT).toBe('0d85d8b');
    expect(RUNTIME_MODE).toBe('METADATA_EVIDENCE_ONLY');
  });

  it('keeps the full route contract explicit and at 13 pages', () => {
    expect(Object.keys(RESEARCH_SCIENCE_ROUTES)).toHaveLength(13);
    expect(RESEARCH_SCIENCE_ROUTES.overview).toBe('/console/research-science');
    expect(RESEARCH_SCIENCE_ROUTES.audit).toBe('/console/research-science/audit');
    expect(RESEARCH_SCIENCE_ROUTES.limitations).toBe('/console/research-science/limitations');
  });

  it('models the safety boundary flags explicitly', () => {
    const flags: ResearchScienceBoundaryFlags = {
      human_review_required: true,
      autonomous_decision: false,
      provider_integration_enabled: false,
      external_database_sync_enabled: false,
      official_verification_enabled: false,
      hidden_score_present: false,
      fake_metrics: false,
      fake_evidence: false,
      fake_publication: false,
      fake_certificate: false,
      fake_grant_evidence: false,
      autonomous_ethics_approval_enabled: false,
      autonomous_grant_submission_enabled: false,
      autonomous_publication_verification_enabled: false,
      incomplete_data: true,
      limitations: ['Metadata-only research foundation'],
      source_matrix_row_id: 'RS-001',
      source_capability_id: 'CAP-001',
    };

    expect(flags.fake_publication).toBe(false);
    expect(flags.hidden_score_present).toBe(false);
    expect(flags.autonomous_grant_submission_enabled).toBe(false);
  });

  it('models dashboard and entity trust fields explicitly', () => {
    const dashboard: ResearchScienceDashboardResponse = {
      tenant_id: 1,
      human_review_required: true,
      autonomous_decision: false,
      provider_integration_enabled: false,
      external_database_sync_enabled: false,
      official_verification_enabled: false,
      hidden_score_present: false,
      fake_metrics: false,
      incomplete_data: true,
      limitations: ['Evidence metadata only'],
      generated_at: '2026-05-23T00:00:00Z',
      contract_version: 'A-037.2',
      source_spec_commit: '02b5564',
      master_matrix_commit: MASTER_MATRIX_COMMIT,
      master_matrix_rows: MASTER_MATRIX_ROW_COUNT,
      capability_count: 60,
      data_source: 'computed_from_research_science_metadata',
      projects_summary: { ACTIVE: 1 },
      student_research_summary: {},
      supervision_summary: {},
      publications_summary: {},
      conferences_summary: {},
      grants_summary: {},
      ethics_summary: {},
      evidence_summary: {},
      bridge_summary: {},
      brain_readiness_summary: {},
      boundary_summary: { fake_metrics: false },
    };
    const project: ResearchProject = {
      id: 1,
      tenant_id: 1,
      status: 'ACTIVE',
      metadata: {},
      created_at: '2026-05-23T00:00:00Z',
      updated_at: '2026-05-23T00:00:00Z',
      archived_at: null,
      human_review_required: true,
      autonomous_decision: false,
      provider_integration_enabled: false,
      external_database_sync_enabled: false,
      official_verification_enabled: false,
      hidden_score_present: false,
      incomplete_data: true,
      limitations: [],
      project_ref: 'RP-1',
      department_ref: 'DEP-1',
      program_ref: 'PRG-1',
      external_ref: null,
      title: 'Project One',
      notes: null,
    };
    const publication: PublicationMetadata = {
      ...project,
      publication_ref: 'PUB-1',
      faculty_ref: 'FAC-1',
      student_ref: 'STU-1',
      project_ref: 'RP-1',
      title: 'Metadata Publication',
      fake_publication: false,
      autonomous_publication_verification_enabled: false,
    };

    expect(dashboard.fake_metrics).toBe(false);
    expect(project.project_ref).toBe('RP-1');
    expect(publication.fake_publication).toBe(false);
  });
});