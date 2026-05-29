'use client';

import type { AuditTrailEvent } from '../types';

export function AuditTrailPanel({ events }: { events: AuditTrailEvent[] }) {
  return (
    <section className="rounded-lg border bg-background p-4" data-testid="ui-framework-audit-trail-panel">
      <h3 className="text-base font-semibold">Audit Trail</h3>
      <div className="mt-3 space-y-3">
        {events.map((eventItem) => (
          <article key={eventItem.id} className="rounded-md border p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-medium">{eventItem.event}</p>
              <span className="text-xs text-muted-foreground">{eventItem.timestamp}</span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">Actor: {eventItem.actor}</p>
            <p className="mt-1 text-xs text-muted-foreground">Status: {eventItem.status}</p>
            {eventItem.metadata ? (
              <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                {Object.entries(eventItem.metadata).map(([key, value]) => (
                  <li key={key}>
                    {key}: {String(value)}
                  </li>
                ))}
              </ul>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}