import React from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AuditEvidencePanel } from '@/modules/academic-operations/components';

describe('Academic Operations audit and evidence', () => {
  it('renders audit and evidence metadata lists', () => {
    render(
      <AuditEvidencePanel
        audit={[{ id: 1, tenant_id: 1, entity_type: 'gradebook_metadata', entity_id: 2, event_type: 'GRADEBOOK_METADATA_REVIEWED', action: 'review', actor_user_id: 'admin', previous_status: 'DRAFT', new_status: 'REVIEWED', human_review_required: true, automated_decision: false, provider_integration_enabled: false, payload: {}, created_at: '2026-05-22' }]}
        evidence={[{ id: 2, tenant_id: 1, status: 'ACTIVE', created_at: '2026-05-22', updated_at: '2026-05-22', archived_at: null, human_review_required: true, automated_decision: false, provider_integration_enabled: false, platonus_sync_enabled: false, sis_sync_enabled: false, hidden_score_present: false, fake_metrics: false, official_grade_publication_enabled: false, automated_grading_enabled: false, automatic_sanction_enabled: false, incomplete_data: true, limitations: [], source_matrix_row_id: 'AO-7', source_capability_id: 'CAP-7', entity_type: 'retake_plan', entity_id: 3, evidence_kind: 'NOTE', external_ref: 'E-1', metadata: {} }]}
      />,
    );

    expect(screen.getByTestId('audit-evidence-panel')).toBeInTheDocument();
    expect(screen.getByText(/gradebook_metadata_reviewed/i)).toBeInTheDocument();
    expect(screen.getByText('NOTE')).toBeInTheDocument();
  });

  it('renders no fake evidence and no official legal document claim labels', () => {
    render(<AuditEvidencePanel audit={[]} evidence={[]} />);

    expect(screen.getByText(/no fake evidence/i)).toBeInTheDocument();
    expect(screen.getByText(/no official legal document claim/i)).toBeInTheDocument();
  });
});