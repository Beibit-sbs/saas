function humanize(value: string) {
  return value.toLowerCase().replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export function AcademicOperationsCountsPanel({ title, counts, testId }: { title: string; counts: Record<string, number>; testId?: string }) {
  const entries = Object.entries(counts);

  return (
    <section className="rounded-lg border p-4" data-testid={testId ?? `academic-operations-counts-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <h3 className="text-sm font-semibold">{title}</h3>
      {entries.length ? (
        <ul className="mt-3 space-y-2 text-sm">
          {entries.map(([key, value]) => (
            <li key={key} className="flex items-center justify-between gap-3">
              <span>{humanize(key)}</span>
              <span className="font-medium">{value}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">No metadata counts available.</p>
      )}
    </section>
  );
}