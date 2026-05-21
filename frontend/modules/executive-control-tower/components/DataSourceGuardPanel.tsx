'use client';

import { ShieldAlert } from 'lucide-react';

export function DataSourceGuardPanel({ reason }: { reason: string }) {
  return (
    <div
      className="flex min-h-[220px] flex-col items-center justify-center gap-3 rounded-lg border border-red-200 bg-red-50 px-6 py-10 text-center"
      data-testid="executive-control-tower-data-quality-error"
      role="alert"
    >
      <ShieldAlert className="h-8 w-8 text-red-500" />
      <p className="font-semibold text-red-800">Dashboard data could not be verified.</p>
      <p className="max-w-2xl text-sm text-red-700">{reason}</p>
      <p className="text-xs text-red-600">Computed metrics are hidden until the backend trust contract is restored.</p>
    </div>
  );
}