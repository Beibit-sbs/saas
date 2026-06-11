import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    useAuditFindingsRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/quality-accreditation/api', () => ({ qualityAccreditationApi: mockApi }));
vi.mock('@/shared/ui/permission-gate', () => ({ RequirePermission: ({ children }: { children: React.ReactNode }) => <>{children}</> }));

import { QualityAccreditationAuditFindingsRuntimePage } from '@/modules/quality-accreditation/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Audit findings runtime', () => {
  beforeEach(() => {
    mockApi.useAuditFindingsRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'quality_accreditation',
      runtime_registry: 'AUDIT_FINDINGS_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-11T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      findings: [
        {
          finding_id: 'AF-1',
          finding_source: 'INTERNAL_AUDIT',
          finding_type: 'INTERNAL_AUDIT_FINDING',
          finding_title: 'Evidence traceability gap',
          severity: 'HIGH',
          impacted_standard: 'STD-ACADEMIC-01',
          remediation_status: 'IN_PROGRESS',
          closure_tracking_status: 'TRACKED',
          opened_at: '2026-01-10T00:00:00Z',
          due_date: '2026-07-10T00:00:00Z',
          read_only: true,
          aggregator_only: true,
        },
      ],
      non_conformities: [
        {
          non_conformity_id: 'NC-1',
          category: 'DOCUMENT_CONTROL',
          severity: 'HIGH',
          affected_area: 'PROGRAM_REVIEW',
          status: 'OPEN',
          read_only: true,
          aggregator_only: true,
        },
      ],
      observations: [
        {
          observation_id: 'OBS-1',
          observation_type: 'PROCESS_OBSERVATION',
          summary: 'Review cadence inconsistency',
          impact_level: 'MEDIUM',
          read_only: true,
          aggregator_only: true,
        },
      ],
      recommendations: [
        {
          recommendation_id: 'REC-1',
          recommendation_title: 'Standardize evidence taxonomy',
          priority: 'HIGH',
          owner_unit: 'quality_accreditation',
          target_date: '2026-08-01T00:00:00Z',
          status: 'IN_PROGRESS',
          read_only: true,
          aggregator_only: true,
        },
      ],
      risk_severity_analysis: [
        {
          risk_band: 'HIGH',
          findings_count: 1,
          non_conformities_count: 1,
          recommendations_open: 1,
          read_only: true,
          aggregator_only: true,
        },
      ],
      remediation_status: [
        {
          remediation_state: 'IN_PROGRESS',
          findings_count: 1,
          average_completion_percentage: 60,
          read_only: true,
          aggregator_only: true,
        },
      ],
      audit_readiness_indicators: [
        {
          indicator_name: 'AUDIT_EVIDENCE_COMPLETENESS',
          indicator_value: 82,
          threshold: 90,
          status: 'WATCH',
          read_only: true,
          aggregator_only: true,
        },
      ],
    });
  });

  it('renders audit findings runtime sections', async () => {
    renderWithClient(<QualityAccreditationAuditFindingsRuntimePage />);

    expect(await screen.findByTestId('audit-findings-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('audit-findings-panel')).toBeInTheDocument();
    expect(screen.getByTestId('non-conformities-panel')).toBeInTheDocument();
    expect(screen.getByTestId('audit-observations-panel')).toBeInTheDocument();
    expect(screen.getByTestId('audit-recommendations-panel')).toBeInTheDocument();
    expect(screen.getByTestId('audit-risk-analysis-panel')).toBeInTheDocument();
    expect(screen.getByTestId('audit-remediation-status-panel')).toBeInTheDocument();
    expect(screen.getByTestId('audit-readiness-panel')).toBeInTheDocument();
  });

  it('integrates with audit findings runtime API contract', async () => {
    renderWithClient(<QualityAccreditationAuditFindingsRuntimePage />);

    expect(await screen.findByRole('heading', { name: 'Audit Findings Runtime', level: 1 })).toBeInTheDocument();
    expect(mockApi.useAuditFindingsRuntime).toHaveBeenCalled();
  });
});
