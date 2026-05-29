import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';

import {
  DataTableShell,
  EmptyState,
  ExportButton,
  FilterBar,
  PageActionBar,
  PermissionDeniedState,
  SearchInput,
  StatusFilter,
} from '../../shared/ui-framework';

describe('shared ui framework', () => {
  it('renders permission-aware and disabled actions', () => {
    render(
      <PageActionBar
        primaryAction={{ id: 'create', label: 'Create', disabled: true, disabledReason: 'No create endpoint' }}
        secondaryActions={[
          {
            id: 'export',
            label: 'Export',
            requiredPermission: 'admin.export',
            hasPermission: false,
          },
        ]}
      />,
    );

    const create = screen.getByTestId('ui-framework-action-create');
    const exportBtn = screen.getByTestId('ui-framework-action-export');

    expect(create).toBeDisabled();
    expect(exportBtn).toBeDisabled();
    expect(exportBtn).toHaveAttribute('title', 'Requires permission: admin.export');
  });

  it('renders empty and permission-denied states', () => {
    render(
      <div>
        <EmptyState variant="metadata_only" />
        <PermissionDeniedState role="tenant_admin" requiredPermission="finance.read" />
      </div>,
    );

    expect(screen.getByTestId('ui-framework-empty-metadata_only')).toBeInTheDocument();
    expect(screen.getByTestId('ui-framework-permission-denied-state')).toBeInTheDocument();
    expect(screen.getByText(/Required permission: finance.read/i)).toBeInTheDocument();
  });

  it('renders filter framework controls and calls apply/clear', () => {
    const onApply = vi.fn();
    const onClear = vi.fn();
    const onSearch = vi.fn();
    const onStatus = vi.fn();

    render(
      <FilterBar onApply={onApply} onClear={onClear}>
        <SearchInput value="" onChange={onSearch} />
        <StatusFilter
          value=""
          onChange={onStatus}
          options={[
            { value: 'active', label: 'Active' },
            { value: 'draft', label: 'Draft' },
          ]}
        />
      </FilterBar>,
    );

    fireEvent.click(screen.getByTestId('ui-framework-filter-apply'));
    fireEvent.click(screen.getByTestId('ui-framework-filter-clear'));

    expect(onApply).toHaveBeenCalledTimes(1);
    expect(onClear).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('ui-framework-search-input')).toBeInTheDocument();
    expect(screen.getByTestId('ui-framework-status-filter')).toBeInTheDocument();
  });

  it('renders data table shell loading, error, and empty states', () => {
    const { rerender } = render(
      <DataTableShell table={<div>table</div>} isLoading={true} />,
    );
    expect(screen.getByTestId('ui-framework-loading-state')).toBeInTheDocument();

    rerender(<DataTableShell table={<div>table</div>} error="boom" />);
    expect(screen.getByTestId('ui-framework-error-state')).toBeInTheDocument();

    rerender(<DataTableShell table={<div>table</div>} isEmpty={true} />);
    expect(screen.getByTestId('ui-framework-empty-no_data')).toBeInTheDocument();
  });

  it('renders export disabled state when endpoint is unavailable', () => {
    render(<ExportButton exportAvailable={false} unavailableReason="No export contract" />);

    const button = screen.getByTestId('ui-framework-export-button');
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('title', 'No export contract');
  });
});
