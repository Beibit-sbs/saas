"use client";

export function DataStatePanel({
  loading,
  error,
  empty,
  emptyMessage,
}: {
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyMessage?: string;
}) {
  if (loading) {
    return <div className="rounded-lg border p-4 text-sm text-muted-foreground">Loading admissions data...</div>;
  }
  if (error) {
    return <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error}</div>;
  }
  if (empty) {
    return <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">{emptyMessage ?? "No data available."}</div>;
  }
  return null;
}
