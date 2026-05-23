import { describe, expect, it } from 'vitest';
import {
  RESEARCH_SCIENCE_PERMISSIONS,
  ResearchScienceDataQualityError,
  assertTrustedResearchScienceDashboard,
  assertTrustedResearchScienceHealth,
  assertTrustedResearchScienceMatrixSummary,
  canCreateResearchBridge,
  canCreateResearchProject,
  canReadAudit,
  canReadBridges,
  canReadResearchScienceDashboard,
  canUpdateResearchProject,
  getResearchScienceBoundaryLabels,
  hasResearchSciencePermission,
  isForbiddenResearchScienceAction,
} from '@/modules/research-science/guards';
import { MASTER_MATRIX_COMMIT, MASTER_MATRIX_ROW_COUNT } from '@/modules/research-science/constants';

const adminUser = {
  permissions: [
    RESEARCH_SCIENCE_PERMISSIONS.dashboardRead,
    RESEARCH_SCIENCE_PERMISSIONS.projectsCreate,
    RESEARCH_SCIENCE_PERMISSIONS.projectsUpdate,
    RESEARCH_SCIENCE_PERMISSIONS.auditRead,
    RESEARCH_SCIENCE_PERMISSIONS.bridgesRead,
    RESEARCH_SCIENCE_PERMISSIONS.bridgesCreate,
  ],
};

describe('Research Science guards', () => {
  it('evaluates permission sets from user permissions', () => {
    expect(hasResearchSciencePermission(adminUser, RESEARCH_SCIENCE_PERMISSIONS.dashboardRead)).toBe(true);
    expect(canReadResearchScienceDashboard(adminUser)).toBe(true);
    expect(canCreateResearchProject(adminUser)).toBe(true);
    expect(canUpdateResearchProject(adminUser)).toBe(true);
    expect(canReadAudit(adminUser)).toBe(true);
    expect(canReadBridges(adminUser)).toBe(true);
    expect(canCreateResearchBridge(adminUser)).toBe(true);
  });

  it('returns false for every forbidden action helper check', () => {
    expect(isForbiddenResearchScienceAction('auto_approve_ethics')).toBe(false);
    expect(isForbiddenResearchScienceAction('sync_scopus')).toBe(false);
    expect(isForbiddenResearchScienceAction('generate_official_ranking')).toBe(false);
    expect(isForbiddenResearchScienceAction('hidden_score')).toBe(false);
  });

  it('returns page-specific boundary labels for publications and bridges', () => {
    const publicationLabels = getResearchScienceBoundaryLabels('publications');
    const bridgeLabels = getResearchScienceBoundaryLabels('bridges');

    expect(publicationLabels.some((label) => /no fake publications/i.test(label))).toBe(true);
    expect(publicationLabels.some((label) => /citation scores/i.test(label))).toBe(true);
    expect(bridgeLabels.some((label) => /read-only-first bridge/i.test(label))).toBe(true);
  });

  it('keeps forbidden permission names out of the exported permission map', () => {
    const permissionValues = Object.values(RESEARCH_SCIENCE_PERMISSIONS).join(' ');

    expect(permissionValues).not.toMatch(/auto_approve|auto_submit|auto_verify/i);
    expect(permissionValues).not.toMatch(/hidden_score|fake_metric|external_database\.live_sync/i);
  });

  it('asserts dashboard, health, and matrix trust boundaries', () => {
    expect(() =>
      assertTrustedResearchScienceDashboard({
        tenant_id: 1,
        human_review_required: true,
        autonomous_decision: false,
        provider_integration_enabled: false,
        external_database_sync_enabled: false,
        official_verification_enabled: false,
        hidden_score_present: false,
        fake_metrics: true,
        incomplete_data: true,
        limitations: [],
        generated_at: '2026-01-01T00:00:00Z',
        contract_version: 'A-037.2',
        source_spec_commit: '02b5564',
        master_matrix_commit: MASTER_MATRIX_COMMIT,
        master_matrix_rows: MASTER_MATRIX_ROW_COUNT,
        capability_count: 60,
        data_source: 'computed_from_research_science_metadata',
        projects_summary: {},
        student_research_summary: {},
        supervision_summary: {},
        publications_summary: {},
        conferences_summary: {},
        grants_summary: {},
        ethics_summary: {},
        evidence_summary: {},
        bridge_summary: {},
        brain_readiness_summary: {},
        boundary_summary: {},
      }),
    ).toThrow(ResearchScienceDataQualityError);

    expect(() =>
      assertTrustedResearchScienceHealth({
        tenant_id: 1,
        module: 'research_science',
        target_level: 'L4',
        foundation_status: 'READY',
        runtime_mode: 'METADATA_EVIDENCE_ONLY',
        contract_version: 'A-037.2',
        provider_integration_enabled: false,
        external_database_sync_enabled: false,
        official_verification_enabled: false,
        hidden_score_present: false,
        fake_metrics: false,
        incomplete_data: true,
        limitations: [],
        route_count: 999,
        table_count: 15,
      }),
    ).toThrow(/route count mismatch/i);

    expect(() =>
      assertTrustedResearchScienceMatrixSummary({
        contract_version: 'A-037.2',
        source_spec_commit: '02b5564',
        source_product_map_commit: '10d833e',
        master_matrix_commit: 'wrong',
        master_matrix_rows: MASTER_MATRIX_ROW_COUNT,
        capability_count: 60,
        runtime_mode: 'METADATA_EVIDENCE_ONLY',
        autonomy_mode: 'HUMAN_REVIEW_REQUIRED',
        route_count_expected: '38-45 routes expected',
        table_count_expected: 15,
      }),
    ).toThrow(/matrix commit mismatch/i);
  });
});