'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { cn } from '@/shared/utils/cn';
import { ACADEMIC_OPERATIONS_NAV_ITEMS } from '../constants';
import { BoundaryBanner } from './BoundaryBanner';

export function AcademicOperationsShell({
  title,
  description,
  currentPath,
  boundaryLabels,
  children,
}: {
  title: string;
  description: string;
  currentPath: string;
  boundaryLabels: string[];
  children: ReactNode;
}) {
  return (
    <div className="space-y-6" data-testid="academic-operations-page">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold">{title}</h1>
        <p className="text-sm text-muted-foreground">{description}</p>
      </header>

      <nav className="flex flex-wrap gap-2" aria-label="Academic Operations navigation">
        {ACADEMIC_OPERATIONS_NAV_ITEMS.map((item) => {
          const active = currentPath === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                'rounded-full border px-3 py-1.5 text-sm transition-colors',
                active ? 'border-foreground bg-foreground text-background' : 'border-border text-foreground hover:bg-muted',
              )}
            >
              {item.title}
            </Link>
          );
        })}
      </nav>

      <BoundaryBanner labels={boundaryLabels} />
      {children}
    </div>
  );
}