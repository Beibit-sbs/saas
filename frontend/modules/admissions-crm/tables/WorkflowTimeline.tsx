"use client";

export function WorkflowTimeline({ items }: { items: Array<{ label: string; state: string }> }) {
  return (
    <section className="rounded-xl border bg-card p-4" data-testid="acrm-workflow-timeline">
      <h3 className="mb-3 text-base font-semibold">Workflow Timeline</h3>
      <ul className="space-y-2 text-sm">
        {items.map((item) => (
          <li key={`${item.label}-${item.state}`} className="rounded border p-2">
            <span className="font-medium">{item.label}</span>
            <span className="ml-2 text-muted-foreground">{item.state}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
