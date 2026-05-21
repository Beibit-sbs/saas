'use client';

export function IncompleteDataNotice({ message = 'Incomplete data' }: { message?: string }) {
  return (
    <div
      className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
      data-testid="incomplete-data-notice"
    >
      {message}
    </div>
  );
}