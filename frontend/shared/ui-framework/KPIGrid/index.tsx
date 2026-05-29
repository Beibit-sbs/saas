'use client';

import type { ReactNode } from 'react';

export function KPIGrid({ children }: { children: ReactNode }) {
  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" data-testid="ui-framework-kpi-grid">
      {children}
    </section>
  );
}