import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BridgeMetadataPanel } from '@/modules/academic-operations/components';

const baseFlags = {
  tenant_id: 1,
  status: 'ACTIVE',
  created_at: '2026-05-22',
  updated_at: '2026-05-22',
  archived_at: null,
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
  limitations: [],
  source_matrix_row_id: 'AO-1',
  source_capability_id: 'CAP-1',
};

describe('Academic Operations bridges', () => {
  it('renders canonical reuse and read-only-first labels', () => {
    render(
      <BridgeMetadataPanel
        bridges={[{ id: 1, ...baseFlags, bridge_type: 'course_catalog', canonical_module_ref: 'course_catalog_management', external_ref: null, metadata: {} }]}
        studentLifecycle={[{ id: 2, ...baseFlags, bridge_key: 'student_lifecycle_bridge', student_ref: 'S-1', external_ref: null, metadata: {} }]}
        documentWorkflow={[]}
        executiveGovernance={[]}
        qualityAccreditation={[]}
      />,
    );

    expect(screen.getAllByText(/canonical reuse/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/read-only-first bridge/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/no duplicate modules/i).length).toBeGreaterThan(0);
  });

  it('renders bridge registry groups', () => {
    render(
      <BridgeMetadataPanel
        bridges={[{ id: 1, ...baseFlags, bridge_type: 'course_catalog', canonical_module_ref: 'course_catalog_management', external_ref: null, metadata: {} }]}
        studentLifecycle={[{ id: 2, ...baseFlags, bridge_key: 'student_lifecycle_bridge', student_ref: 'S-1', external_ref: null, metadata: {} }]}
        documentWorkflow={[{ id: 3, ...baseFlags, bridge_key: 'document_workflow_bridge', student_ref: null, external_ref: 'DOC-1', metadata: {} }]}
        executiveGovernance={[{ id: 4, ...baseFlags, bridge_key: 'executive_governance_bridge', student_ref: null, external_ref: 'EX-1', metadata: {} }]}
        qualityAccreditation={[{ id: 5, ...baseFlags, bridge_key: 'quality_accreditation_bridge', student_ref: null, external_ref: 'QA-1', metadata: {} }]}
      />,
    );

    expect(screen.getByTestId('bridge-metadata-panel')).toBeInTheDocument();
    expect(screen.getByText(/student lifecycle bridge/i)).toBeInTheDocument();
    expect(screen.getByText(/document workflow bridge/i)).toBeInTheDocument();
  });
});