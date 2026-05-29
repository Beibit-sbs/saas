'use client';

export function MetricCard({
  label,
  value,
  source,
  timestamp,
  limitations,
  incompleteData,
}: {
  label: string;
  value: string | number;
  source: string;
  timestamp: string;
  limitations: string[];
  incompleteData: boolean;
}) {
  return (
    <article className="rounded-lg border bg-background p-4" data-testid={`ui-framework-metric-card-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}>
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
      <p className="mt-2 text-xs text-muted-foreground">Source: {source}</p>
      <p className="text-xs text-muted-foreground">Timestamp: {timestamp}</p>
      <p className="text-xs text-muted-foreground">Incomplete data: {String(incompleteData)}</p>
      {limitations.length ? <p className="mt-1 text-xs text-muted-foreground">Limitations: {limitations.join(', ')}</p> : null}
    </article>
  );
}