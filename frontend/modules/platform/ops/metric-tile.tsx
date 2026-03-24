import { Skeleton } from "@/shared/ui/skeleton";

interface MetricTileProps {
  label: string;
  value: number | string | null;
  loading?: boolean;
  hint?: string;
  testId?: string;
}

export function MetricTile({ label, value, loading = false, hint, testId }: MetricTileProps) {
  return (
    <div className="rounded-md border bg-card p-3" data-testid={testId}>
      <p className="text-xs text-muted-foreground">{label}</p>
      {loading ? (
        <Skeleton className="mt-2 h-6 w-20" />
      ) : (
        <p className="mt-1 text-xl font-semibold text-foreground">
          {value === null ? "Unknown" : String(value)}
        </p>
      )}
      {hint && <p className="mt-1 text-[11px] text-muted-foreground">{hint}</p>}
    </div>
  );
}