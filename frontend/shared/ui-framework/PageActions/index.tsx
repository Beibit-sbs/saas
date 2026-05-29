'use client';

import type { ReactNode } from 'react';

export function PageActions({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center gap-2" data-testid="ui-framework-page-actions">
      {children}
    </div>
  );
}