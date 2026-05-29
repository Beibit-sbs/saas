'use client';

import type { ReactNode } from 'react';
import { InboxIcon } from 'lucide-react';
import type { EmptyStateVariant } from '../types';

const defaultCopy: Record<EmptyStateVariant, { title: string; description: string }> = {
  no_data: { title: 'No data', description: 'No records are currently available.' },
  no_results: { title: 'No results', description: 'No results match the current filters.' },
  permission_denied: { title: 'Access unavailable', description: 'You do not have permission for this view.' },
  unavailable: { title: 'Unavailable', description: 'This view is temporarily unavailable.' },
  metadata_only: { title: 'Metadata only', description: 'Only metadata and evidence are currently exposed.' },
  future_scope: { title: 'Future scope', description: 'This workflow is planned for a future phase.' },
};

export function EmptyState({
  variant,
  title,
  description,
  action,
  limitation,
}: {
  variant: EmptyStateVariant;
  title?: string;
  description?: string;
  action?: ReactNode;
  limitation?: string;
}) {
  const copy = defaultCopy[variant];
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border bg-background px-4 py-14 text-center" data-testid={`ui-framework-empty-${variant}`}>
      <InboxIcon className="mb-4 h-10 w-10 text-muted-foreground/40" />
      <h3 className="text-lg font-semibold">{title ?? copy.title}</h3>
      <p className="mt-2 max-w-lg text-sm text-muted-foreground">{description ?? copy.description}</p>
      {limitation ? <p className="mt-2 text-xs text-muted-foreground">{limitation}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}