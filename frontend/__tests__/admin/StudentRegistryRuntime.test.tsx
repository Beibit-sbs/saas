import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getStudentRegistryRuntime: vi.fn(),
  },
}));

vi.mock('@/modules/student-success/api', () => ({ studentSuccessApi: mockApi }));

import { StudentRegistryRuntimePage } from '@/modules/student-success/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Student Registry runtime', () => {
  beforeEach(() => {
    mockApi.getStudentRegistryRuntime.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'student_success_brain',
      runtime_surface: 'STUDENT_REGISTRY_RUNTIME',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-12T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      student_registry_summary: {
        owner_module: 'student_lifecycle',
        records: 20,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle'],
      },
      enrollment_summary: {
        owner_module: 'student_lifecycle',
        records: 10,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle'],
      },
      academic_standing_summary: {
        owner_module: 'student_success_brain',
        records: 8,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'student_lifecycle'],
      },
      retention_link_summary: {
        owner_module: 'student_success_brain',
        records: 7,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle', 'student_success_analytics'],
      },
      advisor_link_summary: {
        owner_module: 'student_success_brain',
        records: 6,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_services', 'interventions'],
      },
      risk_link_summary: {
        owner_module: 'student_success_brain',
        records: 5,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'student_services', 'student_lifecycle'],
      },
      lifecycle_status_summary: {
        owner_module: 'student_lifecycle',
        records: 30,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_lifecycle'],
      },
      safety: {
        read_only: true,
        aggregator_only: true,
        tenant_aware: true,
        summary_read_required: true,
        write_operations_enabled: false,
        workflow_execution_enabled: false,
        approval_execution_enabled: false,
        background_jobs_enabled: false,
        provider_mutation_enabled: false,
        outbound_calls_enabled: false,
        limitations: ['read_only_runtime', 'no_outbound_calls'],
      },
    });
  });

  it('renders Student Registry sections and runtime safety constraints', async () => {
    renderWithClient(<StudentRegistryRuntimePage />);

    expect(await screen.findByTestId('student-registry-runtime')).toBeInTheDocument();
    expect(screen.getByTestId('student-registry-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-registry-enrollment-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-registry-academic-standing-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-registry-retention-link-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-registry-advisor-link-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-registry-risk-link-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-registry-lifecycle-status-summary')).toBeInTheDocument();
    expect(screen.getByTestId('student-registry-runtime-safety')).toBeInTheDocument();
    expect(screen.getByText('no_outbound_calls')).toBeInTheDocument();
  });
});
