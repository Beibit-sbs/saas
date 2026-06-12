import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { mockApi } = vi.hoisted(() => ({
  mockApi: {
    getRuntimeShell: vi.fn(),
  },
}));

vi.mock('@/modules/academic-operations-runtime/api', () => ({ academicOperationsRuntimeApi: mockApi }));

import { AcademicOperationsRuntimeShellPage } from '@/modules/academic-operations-runtime/pages';

function renderWithClient(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('Academic Operations runtime shell', () => {
  beforeEach(() => {
    mockApi.getRuntimeShell.mockResolvedValue({
      tenant_id: 1,
      owner_module: 'academic_operations',
      runtime_shell: 'ACADEMIC_OPERATIONS_RUNTIME_SHELL',
      runtime_mode: 'READ_ONLY_AGGREGATOR',
      generated_at: '2026-06-12T00:00:00Z',
      read_only: true,
      aggregator_only: true,
      runtime_shell_summary: {
        owner_module: 'academic_operations',
        records: 32,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations'],
      },
      runtime_shell_domain: {
        owner_module: 'academic_operations',
        records: 18,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'course_catalog_management'],
      },
      runtime_shell_runtime: {
        owner_module: 'academic_operations_runtime',
        records: 45,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations', 'scheduling', 'grades'],
      },
      runtime_shell_integration: {
        owner_module: 'academic_operations_runtime',
        records: 7,
        read_only: true,
        aggregator_only: true,
        source_modules: ['student_information_system_integration', 'learning_management_system_integration'],
      },
      runtime_shell_readiness: {
        owner_module: 'academic_operations_runtime',
        records: 2,
        read_only: true,
        aggregator_only: true,
        source_modules: ['academic_operations_runtime'],
      },
      safety: {
        read_only: true,
        aggregator_only: true,
        tenant_aware: true,
        summary_read_required: true,
        workflow_execution_enabled: false,
        approval_execution_enabled: false,
        background_jobs_enabled: false,
        provider_mutation_enabled: false,
        limitations: ['read_only_runtime', 'no_provider_mutation'],
      },
    });
  });

  it('renders runtime shell sections and safety boundaries', async () => {
    renderWithClient(<AcademicOperationsRuntimeShellPage />);

    expect(await screen.findByTestId('academic-operations-runtime-shell')).toBeInTheDocument();
    expect(screen.getByTestId('runtime-shell-summary-panel')).toBeInTheDocument();
    expect(screen.getByTestId('runtime-shell-domain-panel')).toBeInTheDocument();
    expect(screen.getByTestId('runtime-shell-runtime-panel')).toBeInTheDocument();
    expect(screen.getByTestId('runtime-shell-integration-panel')).toBeInTheDocument();
    expect(screen.getByTestId('runtime-shell-readiness-panel')).toBeInTheDocument();
    expect(screen.getByTestId('academic-operations-runtime-safety')).toBeInTheDocument();
    expect(screen.getByText('read_only_runtime')).toBeInTheDocument();
  });
});
