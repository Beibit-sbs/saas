"use client";

import { useState } from "react";

export interface AdmissionsFilterState {
  search: string;
  status: string;
  intakeTerm: string;
}

export function AdmissionsFilters({
  onChange,
  initial,
}: {
  onChange?: (value: AdmissionsFilterState) => void;
  initial?: Partial<AdmissionsFilterState>;
}) {
  const [state, setState] = useState<AdmissionsFilterState>({
    search: initial?.search ?? "",
    status: initial?.status ?? "all",
    intakeTerm: initial?.intakeTerm ?? "all",
  });

  const update = (patch: Partial<AdmissionsFilterState>) => {
    const next = { ...state, ...patch };
    setState(next);
    onChange?.(next);
  };

  return (
    <section className="grid gap-3 rounded-xl border bg-card p-4 md:grid-cols-3" data-testid="acrm-filters">
      <label className="text-sm">
        <span className="mb-1 block text-xs text-muted-foreground">Search</span>
        <input
          value={state.search}
          onChange={(event) => update({ search: event.target.value })}
          className="w-full rounded border px-3 py-2"
          placeholder="Name, email, reference"
        />
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-xs text-muted-foreground">Status</span>
        <select
          value={state.status}
          onChange={(event) => update({ status: event.target.value })}
          className="w-full rounded border px-3 py-2"
        >
          <option value="all">All</option>
          <option value="lead_created">Lead Created</option>
          <option value="lead_qualified">Lead Qualified</option>
          <option value="applicant_created">Applicant Created</option>
          <option value="application_started">Application Started</option>
          <option value="application_submitted">Application Submitted</option>
          <option value="archived">Archived</option>
        </select>
      </label>
      <label className="text-sm">
        <span className="mb-1 block text-xs text-muted-foreground">Intake</span>
        <select
          value={state.intakeTerm}
          onChange={(event) => update({ intakeTerm: event.target.value })}
          className="w-full rounded border px-3 py-2"
        >
          <option value="all">All</option>
          <option value="2026-FALL">2026-FALL</option>
          <option value="2027-SPRING">2027-SPRING</option>
        </select>
      </label>
    </section>
  );
}
