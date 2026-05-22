import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AcademicOperationsDashboard } from '@/modules/academic-operations/components';
import { MASTER_MATRIX_COMMIT, MASTER_MATRIX_ROW_COUNT } from '@/modules/academic-operations/constants';

const dashboard = {
  tenant_id: 1,
  fake_metrics: false,
  data_source: 'computed_from_academic_operations_metadata',
  master_matrix_commit: MASTER_MATRIX_COMMIT,
  master_matrix_rows: MASTER_MATRIX_ROW_COUNT,
  incomplete_data: true,
  limitations: ['No official grade publication', 'Full 467-row runtime is not implemented.'],
  counts: { academic_groups: 3, cohorts: 2, gradebook_metadata: 4 },
  canonical_bridge_counts: { student_lifecycle: 3, document_workflow: 2 },
};

const health = {
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
  limitations: ['Metadata-only foundation'],
  route_count: 40,
  table_count: 19,
};

const matrixSummary = {
  master_matrix_commit: MASTER_MATRIX_COMMIT,
  master_matrix_rows: MASTER_MATRIX_ROW_COUNT,
  contract_version: '1.0',
  target_level: 'L4',
  duplicate_module_policy: 'canonical_reuse_required',
  true_new_modules: ['academic_group_management'],
  canonical_reuse_map: { course_catalog: 'course_catalog_management' },
  bridge_map: { student_lifecycle: 'academic_operations_to_student_lifecycle_bridge' },
  forbidden_runtime_claims: ['official grade publication'],
  required_limitations: ['No official grade publication'],
};

describe('Academic Operations dashboard', () => {
  it('renders fake_metrics=false and matrix anchors', () => {
    render(<AcademicOperationsDashboard dashboard={dashboard} health={health} matrixSummary={matrixSummary} canonicalReuseSummary={matrixSummary} />);

    expect(screen.getByTestId('academic-operations-dashboard')).toBeInTheDocument();
    expect(screen.getByText(/fake_metrics=false/i)).toBeInTheDocument();
    expect(screen.getByText(MASTER_MATRIX_COMMIT)).toBeInTheDocument();
    expect(screen.getAllByText(String(MASTER_MATRIX_ROW_COUNT)).length).toBeGreaterThan(0);
  });

  it('renders limitations and canonical reuse sections', () => {
    render(<AcademicOperationsDashboard dashboard={dashboard} health={health} matrixSummary={matrixSummary} canonicalReuseSummary={matrixSummary} />);

    expect(screen.getByText(/no official grade publication/i)).toBeInTheDocument();
    expect(screen.getAllByText(/canonical reuse/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/full 467-row runtime is not implemented/i)).toBeInTheDocument();
  });

  it('renders module count summaries', () => {
    render(<AcademicOperationsDashboard dashboard={dashboard} health={health} matrixSummary={matrixSummary} canonicalReuseSummary={matrixSummary} />);

    expect(screen.getByTestId('academic-operations-module-counts')).toBeInTheDocument();
    expect(screen.getByTestId('academic-operations-bridge-counts')).toBeInTheDocument();
    expect(screen.getByText(/tracked metadata records/i)).toBeInTheDocument();
  });
});