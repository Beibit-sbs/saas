import { describe, expect, it } from 'vitest';
import {
  QUALITY_ACCREDITATION_FORBIDDEN_ACTIONS,
  SOURCE_BACKEND_SPEC_COMMIT,
  SOURCE_PRODUCT_MAP_COMMIT,
  SOURCE_VERTICAL_SELECTION_COMMIT,
} from '@/modules/quality-accreditation/constants';
import {
  QUALITY_ACCREDITATION_PERMISSIONS,
  QualityAccreditationDataQualityError,
  assertTrustedQualityAccreditationDashboard,
  assertTrustedQualityAccreditationHealth,
  assertTrustedQualityAccreditationMatrixSummary,
  canCreateQualityBridge,
  canCreateQualityFramework,
  canReadQualityAccreditationDashboard,
  canReadQualityAudit,
  canReadQualityBridges,
  canReviewQualityEvidence,
  canUpdateQualityFramework,
  getQualityAccreditationBoundaryLabels,
  hasQualityAccreditationPermission,
  isForbiddenQualityAccreditationAction,
} from '@/modules/quality-accreditation/guards';

const adminUser = {
  permissions: [
    QUALITY_ACCREDITATION_PERMISSIONS.dashboardRead,
    QUALITY_ACCREDITATION_PERMISSIONS.standardsCreate,
    QUALITY_ACCREDITATION_PERMISSIONS.standardsUpdate,
    QUALITY_ACCREDITATION_PERMISSIONS.evidenceReview,
    QUALITY_ACCREDITATION_PERMISSIONS.auditRead,
    QUALITY_ACCREDITATION_PERMISSIONS.bridgesRead,
    QUALITY_ACCREDITATION_PERMISSIONS.bridgesCreate,
  ],
};

describe('Quality Accreditation guards', () => {
  it('evaluates permission sets from user permissions', () => {
    expect(hasQualityAccreditationPermission(adminUser, QUALITY_ACCREDITATION_PERMISSIONS.dashboardRead)).toBe(true);
    expect(canReadQualityAccreditationDashboard(adminUser)).toBe(true);
    expect(canCreateQualityFramework(adminUser)).toBe(true);
    expect(canUpdateQualityFramework(adminUser)).toBe(true);
    expect(canReviewQualityEvidence(adminUser)).toBe(true);
    expect(canReadQualityAudit(adminUser)).toBe(true);
    expect(canReadQualityBridges(adminUser)).toBe(true);
    expect(canCreateQualityBridge(adminUser)).toBe(true);
  });

  it('returns true for every forbidden action helper check', () => {
    for (const action of QUALITY_ACCREDITATION_FORBIDDEN_ACTIONS) {
      expect(isForbiddenQualityAccreditationAction(action)).toBe(true);
    }
    expect(isForbiddenQualityAccreditationAction('safe_metadata_read')).toBe(false);
  });

  it('returns page-specific boundary labels for standards and bridges', () => {
    const standardsLabels = getQualityAccreditationBoundaryLabels('standards');
    const bridgeLabels = getQualityAccreditationBoundaryLabels('bridges');

    expect(standardsLabels.some((label) => /official compliance/i.test(label))).toBe(true);
    expect(bridgeLabels.some((label) => /read-only-first bridge/i.test(label))).toBe(true);
  });

  it('keeps forbidden permission names out of the exported permission map', () => {
    const permissionValues = Object.values(QUALITY_ACCREDITATION_PERMISSIONS).join(' ');

    expect(permissionValues).not.toMatch(/auto_approve|auto_submit|auto_claim/i);
    expect(permissionValues).not.toMatch(/fake_evidence|hidden_score|live_sync|program\.auto_close|sanction\.auto_apply/i);
  });

  it('asserts dashboard, health, and matrix trust boundaries', () => {
    expect(() =>
      assertTrustedQualityAccreditationDashboard({
        tenant_id: 1,
        human_review_required: true,
        fake_metrics: true,
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
        generated_at: '2026-05-25T00:00:00Z',
        contract_version: 'A-038.3',
        source_spec_commit: SOURCE_BACKEND_SPEC_COMMIT,
        source_product_map_commit: SOURCE_PRODUCT_MAP_COMMIT,
        source_vertical_selection_commit: SOURCE_VERTICAL_SELECTION_COMMIT,
        master_matrix_commit: 'qa-matrix-1',
        master_matrix_rows: 512,
        detailed_capability_count: 32,
        capability_family_count: 9,
        data_source: 'computed_from_quality_accreditation_metadata',
        frameworks_summary: {},
        standards_summary: {},
        evidence_summary: {},
        readiness_summary: {},
        self_assessment_summary: {},
        improvement_summary: {},
        audit_summary: {},
        program_review_summary: {},
        bridge_summary: {},
        brain_signal_summary: {},
        boundary_summary: {},
      }),
    ).toThrow(QualityAccreditationDataQualityError);

    expect(() =>
      assertTrustedQualityAccreditationHealth({
        tenant_id: 1,
        module: 'quality_accreditation',
        target_level: 'L4',
        foundation_status: 'READY',
        runtime_mode: 'METADATA_EVIDENCE_ONLY',
        contract_version: 'A-038.2',
        provider_integration_enabled: false,
        external_database_sync_enabled: false,
        official_accreditation_approval_enabled: false,
        official_ministry_submission_enabled: false,
        official_ranking_claim_enabled: false,
        hidden_score_present: false,
        fake_metrics: false,
        incomplete_data: true,
        limitations: [],
        route_count: 999,
        table_count: 32,
      }),
    ).toThrow(/route count mismatch/i);

    expect(() =>
      assertTrustedQualityAccreditationMatrixSummary({
        contract_version: 'A-038.2',
        source_spec_commit: 'wrong',
        source_product_map_commit: SOURCE_PRODUCT_MAP_COMMIT,
        source_vertical_selection_commit: SOURCE_VERTICAL_SELECTION_COMMIT,
        master_matrix_commit: 'qa-matrix-1',
        master_matrix_rows: 512,
        detailed_capability_count: 32,
        capability_family_count: 9,
        runtime_mode: 'METADATA_EVIDENCE_ONLY',
        route_count_expected: '65-70 routes expected',
        table_count_expected: 32,
        permission_count_expected: 55,
      }),
    ).toThrow(/spec commit mismatch/i);
  });
});