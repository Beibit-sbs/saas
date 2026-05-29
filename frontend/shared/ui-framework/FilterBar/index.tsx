'use client';

import { Button } from '@/shared/ui/button';
import type { ReactNode } from 'react';

export function FilterBar({
  children,
  onApply,
  onClear,
  disabled,
  onPersistToUrl,
}: {
  children: ReactNode;
  onApply?: () => void;
  onClear?: () => void;
  disabled?: boolean;
  onPersistToUrl?: () => void;
}) {
  const handleApply = () => {
    onApply?.();
    onPersistToUrl?.();
  };

  return (
    <div className="flex flex-col gap-3 rounded-lg border bg-background p-3 md:flex-row md:items-center md:justify-between" data-testid="ui-framework-filter-bar">
      <div className="flex flex-wrap items-center gap-2">{children}</div>
      <div className="flex flex-wrap items-center gap-2">
        {onClear ? (
          <Button variant="ghost" onClick={onClear} disabled={disabled} data-testid="ui-framework-filter-clear">
            Clear filters
          </Button>
        ) : null}
        {onApply ? (
          <Button variant="default" onClick={handleApply} disabled={disabled} data-testid="ui-framework-filter-apply">
            Apply filters
          </Button>
        ) : null}
      </div>
    </div>
  );
}