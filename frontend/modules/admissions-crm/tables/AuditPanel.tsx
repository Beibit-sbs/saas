"use client";

export function AuditPanel({ rows }: { rows: Array<{ action: string; entity: string; actor: string }> }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-audit-panel">
      <h3 className="mb-3 text-base font-semibold">Audit Panel</h3>
      <ul className="space-y-2 text-sm text-muted-foreground">
        {rows.length === 0 ? <li>No audit feed endpoint in Batch 1 runtime scope.</li> : null}
        {rows.map((row, index) => (
          <li key={`${row.action}-${index}`} className="rounded border p-2">
            {row.action} / {row.entity} / {row.actor}
          </li>
        ))}
      </ul>
    </section>
  );
}
