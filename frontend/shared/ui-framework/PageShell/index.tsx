'use client';

import type { ReactNode } from 'react';

export function PageShell({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={className ?? 'min-h-screen bg-gray-50'} data-testid="ui-framework-page-shell">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8">{children}</div>
    </div>
  );
}