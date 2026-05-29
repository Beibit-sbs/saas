'use client';

import { Skeleton } from '@/shared/ui/skeleton';

export function LoadingState({ title = 'Loading' }: { title?: string }) {
  return (
    <div className="space-y-3 rounded-lg border bg-background p-4" data-testid="ui-framework-loading-state">
      <p className="text-sm text-muted-foreground">{title}</p>
      <Skeleton className="h-8 w-1/3" />
      <Skeleton className="h-28 w-full" />
      <Skeleton className="h-28 w-full" />
    </div>
  );
}