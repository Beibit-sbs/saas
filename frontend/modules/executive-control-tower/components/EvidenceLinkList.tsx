'use client';

import type { EvidenceLink } from '../types';

export function EvidenceLinkList({ evidenceLinks }: { evidenceLinks: EvidenceLink[] }) {
  if (evidenceLinks.length === 0) {
    return <p className="text-xs text-muted-foreground">Evidence link unavailable</p>;
  }

  return (
    <ul className="space-y-2 text-xs text-muted-foreground" data-testid="evidence-link-list">
      {evidenceLinks.map((link, index) => (
        <li key={`${link.label}-${index}`} className="rounded-md border border-dashed px-3 py-2">
          <p className="font-medium text-foreground">{link.label}</p>
          <p>{link.source_module}</p>
          <p>{link.source_table ?? 'Source table unavailable'}</p>
          {link.limitations.length > 0 ? <p>{link.limitations.join(' ')}</p> : null}
        </li>
      ))}
    </ul>
  );
}

export function MetricLimitationsPanel({ limitations }: { limitations: string[] }) {
  if (limitations.length === 0) {
    return null;
  }

  return (
    <div className="rounded-md border bg-muted/20 p-3" data-testid="metric-limitations-panel">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Limitations</p>
      <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
        {limitations.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}