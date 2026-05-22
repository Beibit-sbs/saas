import { describe, expect, it } from 'vitest';
import {
  ACADEMIC_OPERATIONS_BACKEND_PERMISSION_COUNT,
  ACADEMIC_OPERATIONS_BACKEND_ROUTE_COUNT,
  API_BASE_PATH,
  MASTER_MATRIX_COMMIT,
  MASTER_MATRIX_ROW_COUNT,
  MODULE_NAME,
  UI_BASE_PATH,
} from '@/modules/academic-operations/constants';
import type { AcademicOperationsBoundaryFlags, AcademicOperationsDashboard } from '@/modules/academic-operations/types';

describe('Academic Operations types', () => {
  it('exports the expected module and matrix constants', () => {
    expect(MODULE_NAME).toBe('academic-operations');
    expect(API_BASE_PATH).toBe('/api/admin/academic-operations');
    expect(UI_BASE_PATH).toBe('/console/academic-operations');
    expect(MASTER_MATRIX_COMMIT).toBe('c79cc31');
    expect(MASTER_MATRIX_ROW_COUNT).toBe(467);
    expect(ACADEMIC_OPERATIONS_BACKEND_ROUTE_COUNT).toBe(40);
    expect(ACADEMIC_OPERATIONS_BACKEND_PERMISSION_COUNT).toBe(40);
  });

  it('keeps the full safety contract explicit in boundary flags fixtures', () => {
    const flags: AcademicOperationsBoundaryFlags = {
      human_review_required: true,
      automated_decision: false,
      provider_integration_enabled: false,
      platonus_sync_enabled: false,
      sis_sync_enabled: false,
      hidden_score_present: false,
      fake_metrics: false,
      official_grade_publication_enabled: false,
      automated_grading_enabled: false,
      automatic_sanction_enabled: false,
      incomplete_data: true,
      limitations: ['Metadata-only foundation'],
      source_matrix_row_id: 'AO-001',
      source_capability_id: 'CAP-001',
    };

    expect(flags.official_grade_publication_enabled).toBe(false);
    expect(flags.automated_grading_enabled).toBe(false);
    expect(flags.hidden_score_present).toBe(false);
  });

  it('models dashboard trust fields explicitly', () => {
    const dashboard: AcademicOperationsDashboard = {
      tenant_id: 1,
      fake_metrics: false,
      data_source: 'computed_from_academic_operations_metadata',
      master_matrix_commit: MASTER_MATRIX_COMMIT,
      master_matrix_rows: MASTER_MATRIX_ROW_COUNT,
      incomplete_data: true,
      limitations: ['No official grade publication'],
      counts: { academic_groups: 4, cohorts: 2 },
      canonical_bridge_counts: { student_lifecycle: 3 },
    };

    expect(dashboard.fake_metrics).toBe(false);
    expect(dashboard.master_matrix_commit).toBe(MASTER_MATRIX_COMMIT);
    expect(dashboard.master_matrix_rows).toBe(MASTER_MATRIX_ROW_COUNT);
  });
});