"use client";

export function StatusHistoryPanel({ title, history }: { title: string; history: string[] }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-status-history-panel">
      <h3 className="mb-3 text-base font-semibold">{title}</h3>
      <ol className="list-decimal space-y-1 pl-5 text-sm text-muted-foreground">
        {history.length === 0 ? <li>No status events available in current runtime scope.</li> : null}
        {history.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ol>
    </section>
  );
}
