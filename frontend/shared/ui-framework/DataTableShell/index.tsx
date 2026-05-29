'use client';

import type { ReactNode } from 'react';
import { EmptyState } from '../EmptyState';
import { ErrorState } from '../ErrorState';
import { LoadingState } from '../LoadingState';

export function DataTableShell({
  toolbar,
  table,
  pagination,
  sorting,
  rowActions,
  isLoading,
  error,
  isEmpty,
  emptyTitle,
  emptyDescription,
}: {
  toolbar?: ReactNode;
  table: ReactNode;
  pagination?: ReactNode;
  sorting?: ReactNode;
  rowActions?: ReactNode;
  isLoading?: boolean;
  error?: string;
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
}) {
  if (isLoading) return <LoadingState title="Loading table data" />;
  if (error) return <ErrorState description={error} />;
  if (isEmpty) {
    return <EmptyState variant="no_data" title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className="space-y-3" data-testid="ui-framework-data-table-shell">
      {toolbar}
      {sorting}
      <div className="rounded-lg border bg-background">{table}</div>
      {rowActions}
      {pagination}
    </div>
  );
}