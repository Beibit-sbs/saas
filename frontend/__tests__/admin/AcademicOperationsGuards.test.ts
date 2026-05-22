import { describe, expect, it } from 'vitest';
import {
  ACADEMIC_OPERATIONS_PERMISSIONS,
  AcademicOperationsDataQualityError,
  assertTrustedAcademicOperationsDashboard,
  assertTrustedAcademicOperationsHealth,
  assertTrustedAcademicOperationsMatrixSummary,
  canReadAcademicGroups,
  canReadAuditEvidence,
  canReadBridges,
  canReadDashboard,
  getAcademicOperationsBoundaryLabels,
  hasAcademicOperationsPermission,
  isForbiddenAcademicOperationsAction,
} from '@/modules/academic-operations/guards';
import { MASTER_MATRIX_COMMIT, MASTER_MATRIX_ROW_COUNT } from '@/modules/academic-operations/constants';

const adminUser = {
  permissions: [
    ACADEMIC_OPERATIONS_PERMISSIONS.dashboardRead,
    ACADEMIC_OPERATIONS_PERMISSIONS.academicGroupsRead,
    ACADEMIC_OPERATIONS_PERMISSIONS.canonicalBridgeRead,
    ACADEMIC_OPERATIONS_PERMISSIONS.auditRead,
  ],
};

describe('Academic Operations guards', () => {
  it('evaluates permission sets from user permissions', () => {
    expect(hasAcademicOperationsPermission(adminUser, ACADEMIC_OPERATIONS_PERMISSIONS.dashboardRead)).toBe(true);
    expect(canReadDashboard(adminUser)).toBe(true);
    expect(canReadAcademicGroups(adminUser)).toBe(true);
    expect(canReadBridges(adminUser)).toBe(true);
    expect(canReadAuditEvidence(adminUser)).toBe(true);
  });

  it('blocks forbidden UI actions', () => {
    expect(isForbiddenAcademicOperationsAction('delete')).toBe(true);
    expect(isForbiddenAcademicOperationsAction('sync with SIS')).toBe(true);
    expect(isForbiddenAcademicOperationsAction('approve grade')).toBe(true);
    expect(isForbiddenAcademicOperationsAction('open details')).toBe(false);
  });

  it('returns page-specific boundary labels for gradebook views', () => {
    const labels = getAcademicOperationsBoundaryLabels('gradebook');
    expect(labels.some((label) => /no official grade publication/i.test(label))).toBe(true);
    expect(labels.some((label) => /no automated grading/i.test(label))).toBe(true);
  });

  it('asserts dashboard, health, and matrix trust boundaries', () => {
    expect(() =>
      assertTrustedAcademicOperationsDashboard({
        tenant_id: 1,
        fake_metrics: true,
        data_source: 'computed_from_academic_operations_metadata',
        master_matrix_commit: MASTER_MATRIX_COMMIT,
        master_matrix_rows: MASTER_MATRIX_ROW_COUNT,
        incomplete_data: true,
        limitations: [],
        counts: {},
        canonical_bridge_counts: {},
      }),
    ).toThrow(AcademicOperationsDataQualityError);

    expect(() =>
      assertTrustedAcademicOperationsHealth({
        tenant_id: 1,
        module: 'academic_operations',
        target_level: 'L4',
        foundation_status: 'READY',
        duplicate_module_policy: 'canonical_reuse_required',
        provider_integration_enabled: false,
        platonus_sync_enabled: false,
        sis_sync_enabled: false,
        hidden_score_present: false,
        fake_metrics: false,
        incomplete_data: true,
        limitations: [],
        route_count: 999,
        table_count: 19,
      }),
    ).toThrow(/route count mismatch/i);

    expect(() =>
      assertTrustedAcademicOperationsMatrixSummary({
        master_matrix_commit: 'wrong',
        master_matrix_rows: MASTER_MATRIX_ROW_COUNT,
        contract_version: '1',
        target_level: 'L4',
        duplicate_module_policy: 'canonical_reuse_required',
        true_new_modules: [],
        canonical_reuse_map: {},
        bridge_map: {},
        forbidden_runtime_claims: [],
        required_limitations: [],
      }),
    ).toThrow(/matrix commit mismatch/i);
  });
});